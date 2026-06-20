# import imageio
# imageio.plugins.ffmpeg.download()
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests
import time, hashlib, urllib.request, re, json
# from moviepy.editor import *
import os, sys
import json
import shlex
import shutil
from retrying import retry
import subprocess
import requests
from src.tools_data_process.utils_path import get_project_root
from platform import system
from typing import Optional

def _get_ytdlp_bin() -> str:
    """获取 yt-dlp 可执行文件路径。优先级: 环境变量 > PATH > 项目内置二进制。"""
    env_bin = (os.environ.get("YTDLP_BIN") or "").strip()
    if env_bin:
        return env_bin

    # When the process PATH does not include the active venv/conda bin,
    # resolve yt-dlp next to the current Python interpreter first.
    py_dir = os.path.dirname(sys.executable or "")
    py_sibling = os.path.join(py_dir, "yt-dlp") if py_dir else ""
    if py_sibling and os.path.isfile(py_sibling) and os.access(py_sibling, os.X_OK):
        return py_sibling

    path_bin = shutil.which("yt-dlp")
    if path_bin:
        return path_bin

    root = get_project_root()
    if system() == "Darwin":
        candidate = os.path.join(root, "yt-dlp_macos")
    else:
        candidate = os.path.join(root, "yt-dlp")
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return "yt-dlp"  # fallback: 依赖 PATH


def _get_youget_bin() -> str:
    """获取 you-get 可执行文件路径。"""
    py_dir = os.path.dirname(sys.executable or "")
    py_sibling = os.path.join(py_dir, "you-get") if py_dir else ""
    if py_sibling and os.path.isfile(py_sibling) and os.access(py_sibling, os.X_OK):
        return py_sibling
    path_bin = shutil.which("you-get")
    if path_bin:
        return path_bin
    return "you-get"


def _resolve_proxy_with_source() -> tuple[Optional[str], Optional[str]]:
    """
    解析显式配置的下载代理。
    """
    for key in ("YTDLP_PROXY", "YOUTUBE_PROXY", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = (os.environ.get(key) or "").strip()
        if value:
            return value, key
    return None, None


def _resolve_proxy() -> Optional[str]:
    proxy, _source = _resolve_proxy_with_source()
    return proxy


def _resolve_youtube_proxy() -> Optional[str]:
    """
    解析显式配置的 YouTube 下载代理；未配置时不传应用层代理。
    仅 YouTube 流程使用，避免影响其他站点。
    （向后兼容，实际调用 _resolve_proxy）
    """
    return _resolve_proxy()


def _resolve_youtube_proxy_with_source() -> tuple[Optional[str], Optional[str]]:
    return _resolve_proxy_with_source()


def _youtube_ytdlp_network_args():
    """
    YouTube 专用：增强网络容错，降低网络链路抖动导致的 EOF/超时失败。
    """
    proxy, source = _resolve_youtube_proxy_with_source()
    args = [
        "--js-runtimes", "node",
        "--retries", "30",
        "--fragment-retries", "30",
        "--extractor-retries", "5",
        "--retry-sleep", "3",
        "--socket-timeout", "30",
        "--force-ipv4",
    ]
    if proxy:
        print(f"[youtube] using explicit proxy from {source}: {proxy}", file=sys.stderr)
        args.extend(["--proxy", proxy])
    return args


def _bili_ytdlp_network_args():
    """
    Bilibili 专用：禁用 yt-dlp 应用层代理并保留重试，不强制 curl/impersonate。
    实测某些 CDN 音频分片在 curl_cffi/impersonate 路径下会出现 TLS 失败。
    """
    return [
        "--proxy", "",
        "--socket-timeout", "30",
        "--retries", "20",
        "--fragment-retries", "20",
        "--extractor-retries", "5",
    ]


def _fetch_video_title(ytdlp: str, url: str, extra_args: list) -> Optional[str]:
    """用 yt-dlp --print 获取视频标题，用于匹配字幕文件名。"""
    args = [ytdlp, "--skip-download", "--print", "%(title)s", url] + extra_args
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    return lines[-1] if lines else None


def _find_subtitle_by_title(save_dir: str, title: str) -> Optional[str]:
    """根据视频标题在目录中匹配字幕文件（格式: {title}.{lang}.srt）。

    对标题和文件名都做 sanitize，以匹配 yt-dlp 保存文件时的行为。
    """
    if not title:
        return None

    _LANG_RE = re.compile(r'^[a-z]{2,3}(-[A-Za-z]{2,4})?$')

    def _normalize(t: str) -> str:
        """只做小写 + 空格折叠，保留标点，对齐 yt-dlp 实际文件名。"""
        t = (t or "").strip()
        t = " ".join(t.split())
        return t.lower()

    norm_title = _normalize(title)
    for f in os.listdir(save_dir):
        if not f.endswith(".srt"):
            continue
        # 去掉 .srt 和可能的语言后缀
        stem = f[:-4]
        if "." in stem:
            potential_lang = stem.rsplit(".", 1)[1]
            if _LANG_RE.match(potential_lang):
                stem = stem.rsplit(".", 1)[0]
        norm_stem = _normalize(stem)
        if norm_stem == norm_title:
            return os.path.join(save_dir, f)
    return None


def download_subtitle(url: str, save_dir: str, video_type: str = "bili") -> Optional[str]:
    """
    尝试用 yt-dlp 下载视频字幕（不下载视频本身）。
    返回下载的 .srt 文件路径，无字幕时返回 None。
    """
    os.makedirs(save_dir, exist_ok=True)
    ytdlp = _get_ytdlp_bin()
    is_youtube = _is_youtube_source(url, video_type)
    is_bili = "bilibili.com" in (url or "") or video_type == "bili"

    # 构建网络参数
    if is_youtube:
        network_args = _youtube_ytdlp_network_args()
    elif is_bili:
        network_args = _bili_ytdlp_network_args()
    else:
        network_args = []

    cookie_file = _resolve_cookie_file(video_type)
    cookie_args = ["--cookies", cookie_file] if os.path.exists(cookie_file) else []

    # 先获取视频标题，用于精确匹配字幕文件
    title = _fetch_video_title(ytdlp, url, network_args + cookie_args)
    if not title:
        print(f"[subtitle] Could not fetch video title for {url}")
        return None
    print(f"[subtitle] Video title: {title}")

    # 如果目录里已有该视频的字幕，直接返回
    existing = _find_subtitle_by_title(save_dir, title)
    if existing:
        print(f"[subtitle] Already exists: {existing}")
        return existing

    # 语言优先级：中文优先，最后兜底全部
    if is_bili:
        lang_attempts = ["ai-zh", "--all-subs"]
    elif is_youtube:
        lang_attempts = ["zh-Hans,zh-Hant,zh,zh-CN", "en", "--all-subs"]
    else:
        lang_attempts = ["zh", "en", "--all-subs"]

    for langs in lang_attempts:
        args = [
            ytdlp,
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--convert-subs", "srt",
            "-o", os.path.join(save_dir, "%(title)s"),
            url,
        ]
        if langs == "--all-subs":
            args.insert(3, "--all-subs")
        else:
            args.extend(["--sub-langs", langs])
        args.extend(network_args)
        args.extend(cookie_args)

        print(f"[subtitle] Trying langs={langs}")
        result = subprocess.run(args, capture_output=True, text=True)

        # 根据视频标题精确匹配字幕文件
        srt_path = _find_subtitle_by_title(save_dir, title)
        if srt_path:
            print(f"[subtitle] Found: {srt_path}")
            return srt_path

    print(f"[subtitle] No subtitles found for {url}")
    return None


def srt_to_text(srt_path: str) -> str:
    """将 SRT 字幕文件转换为纯文本（去掉序号和时间轴）。"""
    lines = []
    with open(srt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 序号行：纯数字且较短（避免误过滤内容行如 "2024"）
            if re.match(r'^\d{1,6}$', line):
                continue
            if "-->" in line:
                continue
            lines.append(line)
    return "\n".join(lines)


def _get_ytdlp_version(ytdlp_bin: str) -> str:
    """
    返回 yt-dlp 版本号；读取失败时返回占位信息，避免影响主流程。
    """
    try:
        result = subprocess.run(
            [ytdlp_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            return f"unknown(return_code={result.returncode})"
        version = (result.stdout or "").strip().splitlines()
        return version[0].strip() if version else "unknown(empty_output)"
    except Exception as exc:
        return f"unknown({type(exc).__name__})"


def _build_download_failure_guidance(
    *,
    url: str,
    video_type: str,
    stage: str,
    return_code: int,
    cmd_args,
    ytdlp_bin: str,
    ytdlp_version: str,
    cookie_file: str,
    has_cookie_file: bool,
    stderr: str = "",
) -> str:
    cmd_text = " ".join(shlex.quote(item) for item in (cmd_args or []))
    lines = [
        f"yt-dlp 执行失败: stage={stage}, return_code={return_code}",
        f"url={url}",
        f"video_type={video_type}",
        f"ytdlp_bin={ytdlp_bin}",
        f"ytdlp_version={ytdlp_version}",
        f"command={cmd_text}",
    ]

    if stderr:
        lines.extend(["", "原始报错 (stderr):", stderr[-2000:]])

    is_bili_source = (
        "bili" in (video_type or "").lower()
        or "bilibili.com" in (url or "")
        or "b23.tv" in (url or "")
    )

    if _is_youtube_source(url, video_type):
        proxy_hint, proxy_source = _resolve_youtube_proxy_with_source()
        proxy_text = proxy_hint or "未显式配置（依赖 TUN/系统网络路径）"
        if proxy_source:
            proxy_text = f"{proxy_text} (source={proxy_source})"
        lines.extend(
            [
                "",
                "排查建议(YouTube):",
                "1) 先确认网络链路稳定（可访问 youtube.com 和 googlevideo.com）。",
                f"2) 当前显式代理解析值: {proxy_text}",
                "3) 检查日志关键词: UNEXPECTED_EOF / timed out / Sign in / 403。",
                "4) 确认 Node 可用（--js-runtimes node 依赖 node）。",
                "5) 先跑内置排查用例（在 RPA 项目根目录执行）：",
                "   python -m unittest bili2text/test/test_downbili_youtube_args.py",
                "   python -m unittest bili2text.test.test_downbili_youtube_args.TestDownBiliYoutubeArgs.test_resolve_youtube_proxy_priority",
                "   python -m unittest bili2text.test.test_downbili_youtube_args.TestDownBiliYoutubeArgs.test_download_audio_new_adds_youtube_network_args",
            ]
        )
        if has_cookie_file:
            lines.append(f"6) cookies 文件已存在: {cookie_file}")
        else:
            lines.append(f"6) cookies 文件不存在，请重新导出: {cookie_file}")
    elif is_bili_source:
        lines.extend(
            [
                "",
                "排查建议(Bilibili):",
                "1) HTTP 412 优先检查 cookies 是否为完整登录态，尤其需要 SESSDATA。",
                f"2) 当前 cookies 文件: {cookie_file} ({'存在' if has_cookie_file else '不存在'})",
                "3) 重新导出 cookies 后直接重试；不要只复制 document.cookie，可能缺 HttpOnly 字段。",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "排查建议:",
                "1) 复用上面 command 在终端直接执行，查看底层 ERROR 输出。",
            ]
        )
    return "\n".join(lines)


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

start_time = 0


def check_folder():
    # 检查文件夹是否被创建：
    if not os.path.exists("bilibili_video"):
        os.makedirs("bilibili_video")

    if not os.path.exists("outputs"):
        os.makedirs("outputs")


@retry(stop_max_attempt_number=6, wait_fixed=10000)
def download_video(bv_number, title, base_dir):
    try:
        # Step 1: 请求元数据，使用了zhouql.vip的接口，感谢！
        meta_url = f"https://bili.zhouql.vip/meta/{bv_number}"
        meta_response = requests.get(meta_url)
        content = meta_response.content.decode("utf-8", errors="replace")
        meta_data = json.loads(content, strict=False)  # download_response.json()

        # 检查元数据请求是否成功
        if meta_data["code"] != 0:
            print("元数据请求失败:", meta_data["message"])
            return

        # 提取cid和aid
        cid = meta_data["data"]["cid"]
        aid = meta_data["data"]["aid"]
        print(f"获取的cid: {cid}, aid: {aid}")

        # Step 2: 请求下载链接
        download_url = f"https://bili.zhouql.vip/download/{aid}/{cid}"
        download_response = requests.get(download_url)
        content = download_response.content.decode("utf-8", errors="replace")
        download_data = json.loads(content, strict=False)  # download_response.json()

        # 检查下载链接请求是否成功
        if download_data["code"] != 0:
            print("下载链接请求失败:", download_data["message"])
            return

        # 获取视频下载URL
        video_url = download_data["data"]["durl"][0]["url"]
        print(f"视频下载链接: {video_url}")

        # Step 3: 下载视频
        video_response = requests.get(video_url, stream=True, headers=HEADERS)

        # 定义保存视频的文件名
        check_folder()
        file_name = os.path.join(base_dir, f'{title}.mp4')
        # 获取总大小
        total_size = int(video_response.headers.get('content-length', 0))
        downloaded_size = 0  # 已下载大小

        # 保存视频到本地并显示进度条
        if not os.path.exists(file_name):
            with open(file_name, "wb") as file:
                for chunk in video_response.iter_content(chunk_size=1024 * 2):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)

                        # 计算进度
                        percent_complete = downloaded_size / total_size * 100
                        # 打印进度条
                        progress = int(percent_complete // 2)  # 控制进度条宽度
                        if int(round(percent_complete, 2) * 100) % 100 == 0:
                            # print(int(round(percent_complete,2)*100))
                            sys.stdout.write(
                                f"\r下载进度: [{'#' * progress}{' ' * (50 - progress)}] {percent_complete:.2f}%")
                            sys.stdout.flush()

            print(f"\n视频已成功下载到: {file_name}")
        return title

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("发生错误:", str(e))


def download_audio_new(url, title, video_save_dir=None, autio_save_dir=None, video_type="bili"):
    """下载视频/音频，支持 yt-dlp 和 you-get 备选（Bilibili）。"""
    try:
        if video_type == "bili":
            cookie_file = os.path.join(get_project_root(), "bili_cookies.txt")
        elif video_type == "douyin":
            cookie_file = os.path.join(get_project_root(), "douyin_cookies.txt")
        else:
            cookie_file = os.path.join(get_project_root(), "youtube_cookies.txt")
        _ytdlp = _get_ytdlp_bin()
        _ytdlp_version = _get_ytdlp_version(_ytdlp)
        is_youtube = (
            "youtube" in (video_type or "").lower()
            or "youtube.com" in (url or "")
            or "youtu.be" in (url or "")
        )
        is_bili = "bilibili.com" in (url or "") or video_type == "bili"
        has_cookie_file = os.path.exists(cookie_file)
        last_args = []
        last_stage = "unknown"
        last_return_code = None
        last_stderr = ""

        def _run_cmd(args, stage):
            nonlocal last_args, last_stage, last_return_code, last_stderr
            last_args = list(args)
            last_stage = stage
            print(" ".join(shlex.quote(item) for item in args))
            # Ensure Node.js is in PATH for yt-dlp's n-challenge solver
            env = os.environ.copy()
            node_paths = ["/usr/local/opt/node@22/bin", "/usr/local/bin"]
            current_path = env.get("PATH", "")
            for node_path in node_paths:
                if node_path not in current_path:
                    env["PATH"] = f"{node_path}:{current_path}"
                    current_path = env["PATH"]
            result = subprocess.run(args, env=env, capture_output=True, text=True)
            last_return_code = result.returncode
            last_stderr = result.stderr or ""
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return last_return_code

        def _run_cmd_with_retry(args, stage, retry_count=1, sleep_seconds=30):
            """
            Run yt-dlp command with a simple fixed-delay retry.
            retry_count=1 means total 2 attempts.
            """
            attempts = max(1, 1 + int(retry_count))
            for attempt in range(1, attempts + 1):
                result = _run_cmd(args, stage=stage)
                if result == 0:
                    return 0
                if attempt < attempts:
                    print(
                        f"[yt-dlp] {stage} failed (attempt {attempt}/{attempts}, return_code={result}), "
                        f"sleep {sleep_seconds}s then retry..."
                    )
                    time.sleep(max(0, int(sleep_seconds)))
            return result

        def _try_curl_download(save_dir):
            """使用系统 curl 下载 Bilibili（绕过 Python SSL 问题）。"""
            if not is_bili:
                return False
            output_file = os.path.join(save_dir, f"temp_{int(time.time())}.mp4")
            print(f"[curl] Trying download as fallback for Bilibili...")

            args = ["curl", "-L", "-o", output_file, "--max-time", "300", "-s", "-S"]
            args.extend(["-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"])
            
            if has_cookie_file:
                args.extend(["-b", cookie_file])
            
            # Bilibili 是境内站点，curl fallback 不走代理
            args.append(url)
            
            result = subprocess.run(args, capture_output=True, text=True)
            if result.returncode != 0 or not os.path.exists(output_file):
                print(f"[curl] Download failed: {result.stderr[:200]}")
                return False

            # 兜底下载经常拿到的是分享页 HTML，不能当作视频继续后续流程。
            file_size = os.path.getsize(output_file)
            if file_size < 512 * 1024:
                print(f"[curl] Download invalid (too small: {file_size} bytes): {output_file}")
                try:
                    os.remove(output_file)
                except OSError:
                    pass
                return False

            try:
                with open(output_file, "rb") as fh:
                    header = fh.read(2048).lower()
                if b"<html" in header or b"<!doctype html" in header:
                    print(f"[curl] Download invalid (html content): {output_file}")
                    try:
                        os.remove(output_file)
                    except OSError:
                        pass
                    return False
            except OSError:
                return False

            print(f"[curl] Download successful: {output_file}")
            return True

        if video_save_dir:
            save_dir = video_save_dir
            output_tmpl = os.path.join(save_dir, f"{title}.%(ext)s")
            args = [
                _ytdlp,
                "-f",
                # 优先低码率音频分片，规避部分高码率音频 CDN 的 TLS EOF/握手失败。
                "b[height<=480]/bv*[height<=480]+ba[abr<=100]/bv*[height<=480]+ba/wv*+ba[abr<=100]/wv*+ba/w",
                url,
                "-o",
                output_tmpl,
            ]
            if is_youtube:
                args.extend(_youtube_ytdlp_network_args())
            elif is_bili:
                args.extend(_bili_ytdlp_network_args())
            else:
                proxy, proxy_source = _resolve_proxy_with_source()
                if proxy:
                    print(f"[yt-dlp] using explicit proxy from {proxy_source}: {proxy}", file=sys.stderr)
                    args.extend(["--proxy", proxy])
            if has_cookie_file:
                args.extend(["--cookies", cookie_file])
            result = _run_cmd_with_retry(args, stage="video_download", retry_count=1, sleep_seconds=30)
            
            # Bilibili 失败时尝试 curl 备选（绕过 Python SSL 问题）
            if result != 0 and is_bili:
                if _try_curl_download(save_dir):
                    result = 0
            
            if result != 0:
                raise RuntimeError(
                    _build_download_failure_guidance(
                        url=url,
                        video_type=video_type,
                        stage=last_stage,
                        return_code=result,
                        cmd_args=last_args,
                        ytdlp_bin=_ytdlp,
                        ytdlp_version=_ytdlp_version,
                        cookie_file=cookie_file,
                        has_cookie_file=has_cookie_file,
                        stderr=last_stderr,
                    )
                )

        if autio_save_dir:
            save_dir = autio_save_dir
            output_tmpl = os.path.join(save_dir, f"{title}.%(ext)s")
            args = [
                _ytdlp,
                "-f",
                "ba",
                url,
                "-o",
                output_tmpl,
                "--extract-audio",
                "--audio-format",
                "mp3",
            ]
            if is_youtube:
                args.extend(_youtube_ytdlp_network_args())
            elif is_bili:
                args.extend(_bili_ytdlp_network_args())
            else:
                proxy, proxy_source = _resolve_proxy_with_source()
                if proxy:
                    print(f"[yt-dlp] using explicit proxy from {proxy_source}: {proxy}", file=sys.stderr)
                    args.extend(["--proxy", proxy])
            if has_cookie_file:
                args.extend(["--cookies", cookie_file])
            result = _run_cmd_with_retry(args, stage="audio_extract", retry_count=1, sleep_seconds=30)
            if result != 0:
                raise RuntimeError(
                    _build_download_failure_guidance(
                        url=url,
                        video_type=video_type,
                        stage=last_stage,
                        return_code=result,
                        cmd_args=last_args,
                        ytdlp_bin=_ytdlp,
                        ytdlp_version=_ytdlp_version,
                        cookie_file=cookie_file,
                        has_cookie_file=has_cookie_file,
                        stderr=last_stderr,
                    )
                )
        return title
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"发生错误: {e}")


def _resolve_cookie_file(video_type: str) -> str:
    if video_type == "bili":
        return os.path.join(get_project_root(), "bili_cookies.txt")
    if video_type == "douyin":
        return os.path.join(get_project_root(), "douyin_cookies.txt")
    return os.path.join(get_project_root(), "youtube_cookies.txt")


def _is_youtube_source(url: str, video_type: str) -> bool:
    normalized_type = (video_type or "").lower()
    return (
        "youtube" in normalized_type
        or "youtube.com" in (url or "")
        or "youtu.be" in (url or "")
    )


def _safe_filename(name: str, fallback: str) -> str:
    title = (name or "").strip()
    invalid_chars = '<>:"/\\|?*'
    translation = str.maketrans({ch: "" for ch in invalid_chars})
    title = title.translate(translation)
    title = " ".join(title.split())
    return title or fallback


def _find_downloaded_video_path(video_save_dir: str, temp_title: str):
    if not os.path.isdir(video_save_dir):
        return None
    candidates = [
        name for name in os.listdir(video_save_dir)
        if os.path.isfile(os.path.join(video_save_dir, name)) and "temp" not in name
    ]
    if not candidates:
        return None

    exact = [name for name in candidates if os.path.splitext(name)[0] == temp_title]
    if exact:
        candidates = exact
    else:
        fuzzy = [name for name in candidates if temp_title in name]
        if fuzzy:
            candidates = fuzzy

    candidates.sort(
        key=lambda name: os.path.getmtime(os.path.join(video_save_dir, name)),
        reverse=True,
    )
    return os.path.join(video_save_dir, candidates[0])


def _fetch_remote_video_title(url: str, video_type: str):
    ytdlp = _get_ytdlp_bin()
    cookie_file = _resolve_cookie_file(video_type)
    extra_args = []
    if _is_youtube_source(url, video_type):
        extra_args.extend(_youtube_ytdlp_network_args())
    if os.path.exists(cookie_file):
        extra_args.extend(["--cookies", cookie_file])
    return _fetch_video_title(ytdlp, url, extra_args)


def restore_original_video_title(url: str, temp_title: str, video_save_dir: str, video_type: str = "bili") -> str:
    """
    解析完成后，把下载视频从临时标题恢复为站点原始标题（仅重命名视频文件本身）。
    返回最终使用的视频标题（不含扩展名）。
    """
    try:
        source_path = _find_downloaded_video_path(video_save_dir, temp_title)
        if not source_path:
            return temp_title

        remote_title = _fetch_remote_video_title(url, video_type)
        normalized_title = _safe_filename(remote_title or "", fallback=temp_title)
        if normalized_title == temp_title:
            return temp_title

        ext = os.path.splitext(source_path)[1]
        target_path = os.path.join(video_save_dir, f"{normalized_title}{ext}")
        if os.path.abspath(target_path) == os.path.abspath(source_path):
            return temp_title

        suffix = 1
        while os.path.exists(target_path):
            target_path = os.path.join(video_save_dir, f"{normalized_title}_{suffix}{ext}")
            suffix += 1

        os.replace(source_path, target_path)
        final_title = os.path.splitext(os.path.basename(target_path))[0]
        print(f"视频文件重命名成功: {os.path.basename(source_path)} -> {os.path.basename(target_path)}")
        return final_title
    except Exception as e:
        print(f"视频文件重命名失败，保留原文件名: {e}")
        return temp_title


def extract_real_audio_url(asset_url: str) -> str:
    """
    优先提取 assetUrl 中 jt= 的真实音频链接；若无 jt 参数，则直接返回 assetUrl。
    """
    if not asset_url:
        return ""
    parsed = urlparse(asset_url)
    query_params = parse_qs(parsed.query)
    jt_values = query_params.get("jt") or []
    if jt_values:
        return jt_values[0]
    return asset_url


def audio_stream_download(url: str, out_path: str, chunk_size: int = 1 << 14) -> None:
    """
    流式下载音频文件，避免占用过多内存。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Python-requests",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with requests.get(url, headers=headers, stream=True, timeout=30) as response:
        response.raise_for_status()
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        with open(out_path, "wb") as file_obj:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                file_obj.write(chunk)
                downloaded += len(chunk)
                if total:
                    done = int(50 * downloaded / total)
                    bar = "█" * done + "·" * (50 - done)
                    print(f"\r[{bar}] {downloaded}/{total} bytes", end="")
    print(f"\n✅ 已保存到: {out_path}")
