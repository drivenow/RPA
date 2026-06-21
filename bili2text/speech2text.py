import os
import re
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import contextlib
import traceback
import requests
from retrying import retry
from tqdm import tqdm
from typing import Optional, Dict

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
DEFAULT_SILICONFLOW_API_KEY = "sk-vwoalamuqgjixnzqxeeegrgwysiutayvbgscvakwiqqyauof"

# ---- 标点恢复：daemon + fallback ----
# 使用 TCP localhost 替代 Unix socket，兼容 Windows / macOS / Linux
_PUNCT_HOST = os.environ.get("OPENCLAW_PUNCT_HOST", "127.0.0.1")
_PUNCT_PORT = int(os.environ.get("OPENCLAW_PUNCT_PORT", "19832"))
_punct_model = None  # fallback: in-process model


def _try_daemon(text: str) -> str | None:
    """Try sending text to punct_daemon via TCP. Returns None on failure."""
    for attempt in range(2):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(300)
            s.connect((_PUNCT_HOST, _PUNCT_PORT))
            req = json.dumps({"text": text}, ensure_ascii=False) + "\n"
            s.sendall(req.encode("utf-8"))
            buf = b""
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in buf:
                    break
            s.close()
            resp = json.loads(buf.decode("utf-8"))
            if "error" in resp:
                return None
            return resp.get("text")
        except (ConnectionRefusedError, OSError) as exc:
            if attempt == 0:
                # Try starting the daemon
                print(f"[PUNCT-WARN] daemon unavailable, trying to start it: {type(exc).__name__}: {exc}")
                _start_daemon()
                continue
            print(f"[PUNCT-WARN] daemon unavailable after retry: {type(exc).__name__}: {exc}")
            return None
    return None


def _start_daemon():
    """Start punct_daemon.py and wait until it's ready (model loaded, socket listening)."""
    daemon_script = os.path.join(os.path.dirname(__file__), "punct_daemon.py")
    if not os.path.exists(daemon_script):
        return
    try:
        # Windows: 不使用 start_new_session，避免产生无法关闭的后台进程
        kwargs = {}
        if sys.platform != "win32":
            kwargs["start_new_session"] = True
        subprocess.Popen(
            [sys.executable or "python3", daemon_script, "--port", str(_PUNCT_PORT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **kwargs,
        )
        # Poll TCP — daemon binds after model load (~45s first time)
        import time
        for _ in range(120):  # up to 120s
            time.sleep(1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((_PUNCT_HOST, _PUNCT_PORT))
                s.close()
                return  # daemon is ready
            except (ConnectionRefusedError, OSError):
                continue
    except Exception as exc:
        print(f"[PUNCT-WARN] failed to start daemon: {type(exc).__name__}: {exc}")
        traceback.print_exc()


def restore_punctuation(text: str) -> str:
    """使用 FunASR ct-punc 模型为无标点文本恢复标点符号。

    优先通过 TCP 连接常驻 daemon（模型已预加载，响应快）。
    Daemon 未运行时自动启动；启动失败则回退到进程内直接加载。
    """
    if not text or not text.strip():
        return text

    # Try daemon first
    result = _try_daemon(text)
    if result is not None:
        return result

    # Fallback: in-process model (direct inference, bypass tqdm overhead)
    import logging

    global _punct_model
    if _punct_model is None:
        try:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            from funasr import AutoModel
            print("正在加载标点恢复模型 FunASR ct-punc ...")
            with _suppress_output():
                # 优先使用本地缓存路径，避免 SSL 证书问题
                _local_model = os.path.join(
                    os.path.expanduser("~"),
                    ".cache", "modelscope", "hub", "models", "iic",
                    "punc_ct-transformer_cn-en-common-vocab471067-large",
                )
                _model_path = _local_model if os.path.isdir(_local_model) else "ct-punc"
                _punct_model = AutoModel(model=_model_path, disable_update=True)
            print("标点恢复模型加载完成。")
        except Exception as exc:
            print(f"[PUNCT-ERROR] FunASR 标点模型加载失败: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            raise

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return text

    import torch
    inner = _punct_model.model
    inner.eval()
    restored = []
    try:
        with torch.no_grad():
            for para in paragraphs:
                res = inner.inference(data_in=[para], key=["p"], **_punct_model.kwargs)
                results = res[0] if isinstance(res, (list, tuple)) else res
                restored.append(results[0]["text"])
    except Exception as exc:
        print(f"[PUNCT-ERROR] FunASR 标点推理失败: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise
    return "\n".join(restored)


@contextlib.contextmanager
def _suppress_output():
    """临时抑制 FunASR / jieba / modelscope 的日志和进度条输出。"""
    import logging
    import os

    # 保存并提升所有相关 logger 级别
    loggers = [logging.getLogger(n) for n in ("", "jieba", "modelscope", "funasr", "root")]
    saved = [(lg, lg.level) for lg in loggers]
    for lg in loggers:
        lg.setLevel(logging.CRITICAL)

    # 重定向 stderr 以抑制 tqdm 进度条和 print 直接输出
    devnull = open(os.devnull, "w")
    old_stderr = os.dup(2)
    os.dup2(devnull.fileno(), 2)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)
        devnull.close()
        for lg, level in saved:
            lg.setLevel(level)


def _collect_audio_paths(audio_split_folder: str):
    """收集音频文件路径"""
    audio_paths = []
    for filename in sorted(os.listdir(audio_split_folder)):
        if any(filename.lower().endswith(ext) for ext in AUDIO_EXTENSIONS):
            audio_paths.append(os.path.join(audio_split_folder, filename))
    return audio_paths


def _format_transcript_with_punctuation_lines(text: str) -> str:
    """按标点切分长文本，提升 txt 可读性。"""
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""

    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"([。！？!?])\s*", r"\1\n", normalized)
    normalized = re.sub(r"\n{2,}", "\n", normalized)
    return normalized.strip()


def _write_transcript(text_save_path: str, title: str, combined_text: str):
    """写入转录文本到文件"""
    # 内容为空时不写文件，避免产生残缺文件触发 skip_existing 永久跳过
    if not combined_text or not combined_text.strip():
        print(f"[警告] 转录内容为空，跳过写入: {title}")
        return

    # 如果传入的是目录，自动生成文件名
    if os.path.isdir(text_save_path):
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        text_save_path = os.path.join(text_save_path, f"{safe_title.lower()}.txt")

    formatted_text = _format_transcript_with_punctuation_lines(combined_text)

    os.makedirs(os.path.dirname(text_save_path), exist_ok=True)
    with open(text_save_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(formatted_text)
    print(f"文本已保存到: {text_save_path}")


def _transcribe_groq(audio_path: str, api_key: str = None) -> str:
    """使用 Groq API 转录音频（免费额度大，速度快）。

    使用 curl 子进程而非 requests，与 SiliconFlow 保持一致，
    绕过 Anaconda Python 的 OpenSSL SSL 握手兼容性问题。
    """
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("需要设置 GROQ_API_KEY 环境变量")

    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    # curl -F 的 file=@path 语法中，逗号会被解析为多字段分隔符
    tmp_file = None
    safe_path = audio_path
    if "," in audio_path or "@" in audio_path:
        ext = os.path.splitext(audio_path)[1] or ".mp3"
        fd, tmp_file = tempfile.mkstemp(suffix=ext, prefix="groq_")
        os.close(fd)
        shutil.copy2(audio_path, tmp_file)
        safe_path = tmp_file

    try:
        args = [
            "curl", "-s", "-S", "--max-time", "120",
            "-H", f"Authorization: Bearer {api_key}",
            "-F", f"file=@{safe_path}",
            "-F", "model=whisper-large-v3",
            "-F", "language=zh",
            "-F", "response_format=verbose_json",
            "-F", "timestamp_granularities[]=segment",
            "-F", "prompt=Please transcribe this Chinese speech and include appropriate punctuation marks such as commas, periods, question marks, and exclamation marks.",
            url,
        ]

        result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=130)
        if result.returncode != 0:
            raise RuntimeError(f"Groq curl transcription failed: {result.stderr[:500]}")

        data = json.loads(result.stdout)

        # 检查 API 错误响应
        if "error" in data:
            raise RuntimeError(f"Groq API error: {data['error']}")

        # 使用 verbose_json 格式获取分段文本，更好地保留标点
        segments = data.get("segments", [])
        if segments:
            texts = [seg.get("text", "").strip() for seg in segments if seg.get("text")]
            result_text = " ".join(texts)
            if result_text:
                return result_text
        # 如果 segments 为空或没有提取到文本，回退到顶层 text 字段
        return data.get("text", "")
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)


def _transcribe_siliconflow(audio_path: str, api_key: str = None) -> str:
    """使用 SiliconFlow API 转录音频（备用方案）。

    使用 curl 子进程而非 requests，以绕过 Anaconda Python 的 OpenSSL 3.6.1
    与 SiliconFlow 阿里云 SLB 之间的 TLS 握手兼容性问题。
    macOS 系统 curl 使用 LibreSSL/SecureTransport，已被验证可正常连接。
    """
    if not api_key:
        api_key = os.environ.get("SILICONFLOW_API_KEY", DEFAULT_SILICONFLOW_API_KEY)

    url = "https://api.siliconflow.cn/v1/audio/transcriptions"

    # curl -F 的 file=@path 语法中，逗号会被解析为多字段分隔符。
    # 如果路径含逗号等特殊字符，先复制到临时文件再传给 curl。
    tmp_file = None
    safe_path = audio_path
    if "," in audio_path or "@" in audio_path:
        ext = os.path.splitext(audio_path)[1] or ".mp3"
        fd, tmp_file = tempfile.mkstemp(suffix=ext, prefix="sf_")
        os.close(fd)
        shutil.copy2(audio_path, tmp_file)
        safe_path = tmp_file

    try:
        args = [
            "curl", "-s", "-S", "--max-time", "300",
            "--noproxy", "api.siliconflow.cn",  # 国内 API 直连，绕过本地代理
            "-H", f"Authorization: Bearer {api_key}",
            "-F", f"file=@{safe_path}",
            "-F", "model=FunAudioLLM/SenseVoiceSmall",
            url,
        ]

        result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=311)
        if result.returncode != 0:
            raise RuntimeError(f"SiliconFlow curl transcription failed: {result.stderr[:500]}")

        data = json.loads(result.stdout)
        return data.get("text", "")
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def run_speech_to_text(
    title: str,
    audio_split_folder: str,
    text_save_path: str,
    *,
    engine: str = "siliconflow",
    engine_kwargs: Optional[Dict[str, Dict[str, object]]] = None,
):
    """
    语音转文字主函数

    Args:
        title: 视频标题
        audio_split_folder: 音频文件夹路径
        text_save_path: 文本保存路径
        engine: 使用的引擎，可选 "siliconflow"（默认）或 "groq"（备用）
        engine_kwargs: 引擎参数，如 {"groq": {"api_key": "xxx"}}
    """
    audio_paths = _collect_audio_paths(audio_split_folder)
    if not audio_paths:
        raise ValueError("未找到可用的音频文件。")

    groq_api_key = (engine_kwargs or {}).get("groq", {}).get("api_key") or os.environ.get("GROQ_API_KEY")
    siliconflow_api_key = (
        (engine_kwargs or {}).get("siliconflow", {}).get("api_key")
        or os.environ.get("SILICONFLOW_API_KEY")
        or DEFAULT_SILICONFLOW_API_KEY
    )

    # 根据 engine 选择转录方法
    if engine == "groq":
        if not groq_api_key:
            print("未检测到 GROQ_API_KEY，使用默认方案 SiliconFlow...")
            engine = "siliconflow"

    if engine == "groq":
        print("正在使用 Groq API 转换文本...")
        api_key = groq_api_key
        transcribe_func = lambda path: _transcribe_groq(path, api_key)
        desc = "Transcribing (Groq)"
    else:  # 默认使用 siliconflow
        print("正在使用 SiliconFlow API 转换文本...")
        api_key = siliconflow_api_key
        transcribe_func = lambda path: _transcribe_siliconflow(path, api_key)
        desc = "Transcribing (SiliconFlow)"

    transcripts = []

    for idx, audio_path in enumerate(tqdm(audio_paths, desc=desc), start=1):
        print(f"正在转换第{idx}个音频... {os.path.basename(audio_path)}")
        try:
            text = transcribe_func(audio_path)
            if text:
                transcripts.append(text)
        except Exception as e:
            print(f"转换音频 {audio_path} 失败: {e}")
            # SiliconFlow 失败时尝试切换到 Groq
            if engine == "siliconflow" and groq_api_key:
                print("尝试使用备用方案 Groq...")
                try:
                    text = _transcribe_groq(audio_path, groq_api_key)
                    if text:
                        transcripts.append(text)
                        continue
                except Exception as e2:
                    print(f"备用方案也失败: {e2}")
            raise e

    combined = "\n".join(text for text in transcripts if text)

    punctuation_count = sum(combined.count(mark) for mark in (",", "，", "。", ".", "！", "？"))
    if punctuation_count < 3 and len(combined) > 50:
        print("警告：音频转换文本标点极少！")

    _write_transcript(text_save_path, title, combined)
    return combined
