# import imageio
# imageio.plugins.ffmpeg.download()
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests
import time, hashlib, urllib.request, re, json
# from moviepy.editor import *
import os, sys
import json
import shlex
from retrying import retry
import subprocess
import requests
from src.tools_data_process.utils_path import get_project_root
from platform import system

def _get_ytdlp_bin() -> str:
    """获取 yt-dlp 可执行文件的路径，优先使用项目根目录的平台专属版本。"""
    root = get_project_root()
    if system() == "Darwin":
        candidate = os.path.join(root, "yt-dlp_macos")
    else:
        candidate = os.path.join(root, "yt-dlp")
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return "yt-dlp"  # fallback: 依赖 PATH

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
        print(traceback.print_exc())
        print("发生错误:", str(e))


def download_audio_new(url, title, video_save_dir=None, autio_save_dir=None, video_type="bili"):
    try:
        if video_type == "bili":
            cookie_file = os.path.join(get_project_root(), "bili_cookies.txt")
        elif video_type == "douyin":
            cookie_file = os.path.join(get_project_root(), "douyin_cookies.txt")
        else:
            cookie_file = os.path.join(get_project_root(), "youtube_cookies.txt")
        _ytdlp = _get_ytdlp_bin()
        is_youtube = (
            "youtube" in (video_type or "").lower()
            or "youtube.com" in (url or "")
            or "youtu.be" in (url or "")
        )
        has_cookie_file = os.path.exists(cookie_file)

        def _run_cmd(args):
            print(" ".join(shlex.quote(item) for item in args))
            return subprocess.call(args)

        if video_save_dir:
            save_dir = video_save_dir
            output_tmpl = os.path.join(save_dir, f"{title}.%(ext)s")
            args = [
                _ytdlp,
                "-f",
                "bv*[height<=480]+ba/b[height<=480]/wv*+ba/w",
                url,
                "-o",
                output_tmpl,
            ]
            if is_youtube:
                args.extend(["--js-runtimes", "node"])
            if has_cookie_file:
                args.extend(["--cookies", cookie_file])
            result = _run_cmd(args)
            assert result == 0, "下载失败"

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
                args.extend(["--js-runtimes", "node"])
            if has_cookie_file:
                args.extend(["--cookies", cookie_file])
            result = _run_cmd(args)
            assert result == 0, "下载失败"
        return title
    except Exception as e:
        import traceback
        print(traceback.print_exc())
        raise Exception("发生错误:", str(e))
        


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
    args = [ytdlp, "--skip-download", "--print", "%(title)s", url]
    if _is_youtube_source(url, video_type):
        args.extend(["--js-runtimes", "node"])
    if os.path.exists(cookie_file):
        args.extend(["--cookies", cookie_file])

    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    return lines[-1]


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
