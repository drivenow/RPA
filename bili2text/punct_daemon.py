#!/usr/bin/env python3
"""标点恢复 daemon — 加载一次 FunASR ct-punc 模型，通过 TCP socket 处理多次请求。

用法:
    python3 punct_daemon.py [--port 19832]

客户端（restore_punctuation）会自动启动此 daemon 并通过 TCP 通信。
使用 TCP localhost 替代 Unix socket，兼容 Windows / macOS / Linux。
"""

import json
import os
import signal
import socket
import sys
import threading

PUNCT_HOST = os.environ.get("OPENCLAW_PUNCT_HOST", "127.0.0.1")
PUNCT_PORT = int(os.environ.get("OPENCLAW_PUNCT_PORT", "19832"))

_model = None
_model_lock = threading.Lock()


def _load_model():
    global _model
    if _model is not None:
        return
    with _model_lock:
        if _model is not None:
            return
        # suppress FunASR / modelscope / jieba noise
        import logging
        import contextlib

        loggers = [logging.getLogger(n) for n in ("", "jieba", "modelscope", "funasr", "root")]
        saved = [(lg, lg.level) for lg in loggers]
        for lg in loggers:
            lg.setLevel(logging.CRITICAL)

        devnull = open(os.devnull, "w")
        old_stderr = os.dup(2)
        os.dup2(devnull.fileno(), 2)
        try:
            from funasr import AutoModel
            _model = AutoModel(model="ct-punc", disable_update=True)
        finally:
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            devnull.close()
            for lg, level in saved:
                lg.setLevel(level)


def _restore(text: str) -> str:
    if not text or not text.strip():
        return text

    _load_model()

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return text

    import torch
    inner = _model.model
    inner.eval()
    restored = []
    with torch.no_grad():
        for para in paragraphs:
            res = inner.inference(data_in=[para], key=["p"], **_model.kwargs)
            results = res[0] if isinstance(res, (list, tuple)) else res
            restored.append(results[0]["text"])
    return "\n".join(restored)


def _handle_client(conn: socket.socket):
    """Handle a single client connection (one JSON request, one JSON response)."""
    try:
        conn.settimeout(300)
        # Read newline-delimited JSON
        buf = b""
        while True:
            chunk = conn.recv(65536)
            if not chunk:
                return
            buf += chunk
            if b"\n" in buf:
                break
        data = json.loads(buf.decode("utf-8"))
        text = data.get("text", "")
        result = _restore(text)
        resp = json.dumps({"text": result}, ensure_ascii=False) + "\n"
        conn.sendall(resp.encode("utf-8"))
    except Exception as e:
        resp = json.dumps({"error": str(e)}, ensure_ascii=False) + "\n"
        try:
            conn.sendall(resp.encode("utf-8"))
        except Exception:
            pass
    finally:
        conn.close()


def main():
    host = PUNCT_HOST
    port = PUNCT_PORT
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        port = int(sys.argv[2])

    # Check if daemon already running on this port
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, port))
        s.close()
        print(f"Daemon already running on {host}:{port}", file=sys.stderr)
        sys.exit(0)
    except (ConnectionRefusedError, OSError):
        pass

    # Bind and listen
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(4)

    # Graceful shutdown
    def _cleanup(signum=None, frame=None):
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    # Preload model in background so socket is immediately available
    threading.Thread(target=_load_model, daemon=True).start()

    print(f"ready port={port}", flush=True)

    while True:
        try:
            conn, _ = server.accept()
            t = threading.Thread(target=_handle_client, args=(conn,), daemon=True)
            t.start()
        except OSError:
            break

    _cleanup()


if __name__ == "__main__":
    main()
