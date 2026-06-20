#!/usr/bin/env python3
"""标点恢复 daemon — 加载一次 FunASR ct-punc 模型，通过 Unix socket 处理多次请求。

用法:
    python3 punct_daemon.py [--socket /tmp/openclaw-punct.sock]

客户端（restore_punctuation）会自动启动此 daemon 并通过 socket 通信。
"""

import json
import os
import signal
import socket
import sys
import threading

SOCKET_PATH = os.environ.get(
    "OPENCLAW_PUNCT_SOCKET",
    os.path.join(os.environ.get("TMPDIR", "/tmp"), "openclaw-punct.sock"),
)

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
    socket_path = SOCKET_PATH
    if len(sys.argv) > 2 and sys.argv[1] == "--socket":
        socket_path = sys.argv[2]

    # Clean up stale socket
    if os.path.exists(socket_path):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(socket_path)
            s.close()
            # Daemon already running, exit
            print(f"Daemon already running on {socket_path}", file=sys.stderr)
            sys.exit(0)
        except ConnectionRefusedError:
            os.unlink(socket_path)

    # Bind and listen FIRST so clients can connect immediately
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(socket_path)
    server.listen(4)

    pid_path = socket_path + ".pid"
    with open(pid_path, "w") as f:
        f.write(str(os.getpid()))

    # Graceful shutdown
    def _cleanup(signum, frame):
        server.close()
        try:
            os.unlink(socket_path)
        except OSError:
            pass
        try:
            os.unlink(pid_path)
        except OSError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)

    # Preload model in background so socket is immediately available
    threading.Thread(target=_load_model, daemon=True).start()

    print("ready", flush=True)

    while True:
        try:
            conn, _ = server.accept()
            t = threading.Thread(target=_handle_client, args=(conn,), daemon=True)
            t.start()
        except OSError:
            break

    _cleanup(None, None)


if __name__ == "__main__":
    main()
