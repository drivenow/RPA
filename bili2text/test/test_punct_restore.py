"""Tests for punctuation restoration (restore_punctuation / punct_daemon).

Run from RPA project root:
    python -m pytest bili2text/test/test_punct_restore.py -v
    python -m unittest bili2text.test.test_punct_restore -v

Requires: funasr, torch  (heavy deps — skip in CI with `pytest -m "not slow"`)
"""

import json
import os
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BILI2TEXT_DIR = PROJECT_ROOT / "bili2text"
if str(BILI2TEXT_DIR) not in sys.path:
    sys.path.insert(0, str(BILI2TEXT_DIR))


# ---------------------------------------------------------------------------
# Unit tests (no model required)
# ---------------------------------------------------------------------------

class TestRestorePunctuationUnit(unittest.TestCase):
    """Unit tests that mock the model — fast, no GPU/model needed."""

    def test_empty_text_returns_empty(self):
        from speech2text import restore_punctuation
        self.assertEqual(restore_punctuation(""), "")
        self.assertEqual(restore_punctuation("   "), "   ")
        self.assertEqual(restore_punctuation("\n"), "\n")

    def test_daemon_success_skips_model(self):
        """When daemon responds, in-process model should NOT be loaded."""
        from speech2text import restore_punctuation, _punct_model

        mock_resp = json.dumps({"text": "你好，世界。"}) + "\n"

        with patch("speech2text._try_daemon", return_value="你好，世界。") as mock_try:
            result = restore_punctuation("你好世界")
            self.assertEqual(result, "你好，世界。")
            mock_try.assert_called_once_with("你好世界")

    def test_daemon_failure_falls_back(self):
        """When daemon returns None, should fall back to in-process model."""
        import speech2text
        from speech2text import restore_punctuation

        # Set up a mock model in the global
        mock_inner = MagicMock()
        mock_inner.inference.return_value = ([{"text": "测试。"}], {})
        mock_model = MagicMock()
        mock_model.model = mock_inner
        mock_model.kwargs = {}

        with patch("speech2text._try_daemon", return_value=None):
            speech2text._punct_model = mock_model
            result = restore_punctuation("测试")
            self.assertIn("测试", result)
            mock_inner.inference.assert_called_once()
            speech2text._punct_model = None  # cleanup


class TestTryDaemon(unittest.TestCase):
    """Test _try_daemon socket communication logic."""

    def test_socket_connection_failure_returns_none(self):
        from speech2text import _try_daemon
        with patch("speech2text._PUNCT_PORT", 19999):  # unlikely to have a daemon on this port
            with patch("speech2text._start_daemon"):
                result = _try_daemon("test")
                self.assertIsNone(result)

    def test_socket_error_response_returns_none(self):
        from speech2text import _try_daemon
        mock_resp = json.dumps({"error": "something failed"}) + "\n"

        mock_socket = MagicMock()
        mock_socket.recv.return_value = mock_resp.encode("utf-8")

        with patch("socket.socket", return_value=mock_socket):
            result = _try_daemon("test")
            self.assertIsNone(result)


class TestPunctDaemonProtocol(unittest.TestCase):
    """Test daemon's JSON protocol handling."""

    def test_handle_client_valid_request(self):
        """Daemon should accept JSON and return JSON with 'text' key."""
        from punct_daemon import _handle_client

        req = json.dumps({"text": "你好世界"}) + "\n"
        mock_conn = MagicMock()
        mock_conn.recv.return_value = req.encode("utf-8")

        with patch("punct_daemon._restore", return_value="你好，世界。"):
            _handle_client(mock_conn)
            sent_data = mock_conn.sendall.call_args[0][0]
            resp = json.loads(sent_data.decode("utf-8"))
            self.assertIn("text", resp)
            self.assertEqual(resp["text"], "你好，世界。")

    def test_handle_client_invalid_json(self):
        """Daemon should return error on invalid JSON."""
        from punct_daemon import _handle_client

        mock_conn = MagicMock()
        mock_conn.recv.return_value = b"not json\n"

        _handle_client(mock_conn)
        sent_data = mock_conn.sendall.call_args[0][0]
        resp = json.loads(sent_data.decode("utf-8"))
        self.assertIn("error", resp)

    def test_handle_client_empty_text(self):
        """Daemon should handle empty text gracefully."""
        from punct_daemon import _handle_client

        req = json.dumps({"text": ""}) + "\n"
        mock_conn = MagicMock()
        mock_conn.recv.return_value = req.encode("utf-8")

        _handle_client(mock_conn)
        sent_data = mock_conn.sendall.call_args[0][0]
        resp = json.loads(sent_data.decode("utf-8"))
        self.assertEqual(resp["text"], "")


# ---------------------------------------------------------------------------
# Integration tests (require model — mark as slow)
# ---------------------------------------------------------------------------

@unittest.skipUnless(
    os.environ.get("RUN_SLOW_TESTS", ""),
    "Set RUN_SLOW_TESTS=1 to run (requires funasr + model download)",
)
class TestRestorePunctuationIntegration(unittest.TestCase):
    """Integration tests with the real ct-punc model."""

    @classmethod
    def setUpClass(cls):
        from funasr import AutoModel
        cls.model = AutoModel(model="ct-punc", disable_update=True)

    def test_adds_question_mark(self):
        from speech2text import restore_punctuation
        result = restore_punctuation("你有没有想过")
        self.assertIn("？", result)

    def test_adds_period(self):
        from speech2text import restore_punctuation
        result = restore_punctuation("其实从根上搞错了它的发光原理")
        self.assertIn("。", result)

    def test_preserves_line_count(self):
        from speech2text import restore_punctuation
        lines = [
            "第一句话",
            "第二句话",
            "第三句话",
        ]
        result = restore_punctuation("\n".join(lines))
        result_lines = result.strip().split("\n")
        self.assertEqual(len(result_lines), len(lines))

    def test_inference_matches_generate(self):
        """Direct inference() must produce identical output to generate()."""
        import torch
        inner = self.model.model
        inner.eval()

        test_lines = [
            "你有没有想过你按了十几年的电灯开关",
            "其实从根上搞错了它的发光原理",
            "你是不是从小就笃定电流就是电子",
        ]

        for line in test_lines:
            gen = self.model.generate(input=line)[0]["text"]
            with torch.no_grad():
                res = inner.inference(data_in=[line], key=["p"], **self.model.kwargs)
            inf = (res[0] if isinstance(res, (list, tuple)) else res)[0]["text"]
            self.assertEqual(gen, inf, f"Mismatch for: {line}")

    def test_inference_speed(self):
        """inference() should be >20x faster than generate()."""
        import torch
        inner = self.model.model
        inner.eval()

        lines = ["测试句子" + str(i) for i in range(20)]

        # generate() loop
        t0 = time.time()
        for line in lines:
            self.model.generate(input=line)
        t_generate = time.time() - t0

        # inference() loop
        t0 = time.time()
        with torch.no_grad():
            for line in lines:
                inner.inference(data_in=[line], key=["p"], **self.model.kwargs)
        t_inference = time.time() - t0

        speedup = t_generate / t_inference
        self.assertGreater(speedup, 20, f"Speedup only {speedup:.1f}x, expected >20x")


@unittest.skipUnless(
    os.environ.get("RUN_SLOW_TESTS", ""),
    "Set RUN_SLOW_TESTS=1 to run (requires funasr + model download)",
)
class TestPunctDaemonIntegration(unittest.TestCase):
    """Integration test: start daemon, send request via socket."""

    def test_daemon_roundtrip(self):
        """Start daemon, send text, get punctuated result back."""
        import subprocess
        from speech2text import _PUNCT_HOST, _PUNCT_PORT

        test_port = _PUNCT_PORT + 1  # avoid conflict with any running daemon

        # Check if something already on test_port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((_PUNCT_HOST, test_port))
            s.close()
            self.skipTest(f"Port {test_port} already in use")
        except (ConnectionRefusedError, OSError):
            pass

        # Start daemon
        daemon_script = str(BILI2TEXT_DIR / "punct_daemon.py")
        proc = subprocess.Popen(
            [sys.executable, daemon_script, "--port", str(test_port)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

        try:
            # Wait for daemon to be ready (poll TCP)
            for _ in range(120):
                time.sleep(1)
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1)
                    s.connect((_PUNCT_HOST, test_port))
                    s.close()
                    break
                except (ConnectionRefusedError, OSError):
                    continue
            else:
                self.fail("Daemon did not start within 120s")

            # Send request
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(60)
            s.connect((_PUNCT_HOST, test_port))
            req = json.dumps({"text": "你好世界\n测试标点恢复"}) + "\n"
            s.sendall(req.encode("utf-8"))

            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
            s.close()

            resp = json.loads(buf.decode("utf-8"))
            self.assertIn("text", resp)
            self.assertIn("？", resp["text"] + "。", "Should add punctuation")
            # Should preserve line count
            self.assertEqual(len(resp["text"].split("\n")), 2)
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
