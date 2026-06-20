import os
import sys
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BILI2TEXT_DIR = PROJECT_ROOT / "bili2text"
if str(BILI2TEXT_DIR) not in sys.path:
    sys.path.insert(0, str(BILI2TEXT_DIR))

import downBili  # noqa: E402


class TestDownBiliYoutubeArgs(unittest.TestCase):
    def test_resolve_youtube_proxy_priority(self):
        with patch.dict(
            os.environ,
            {
                "HTTP_PROXY": "http://http-proxy:7890",
                "YOUTUBE_PROXY": "http://youtube-proxy:7890",
                "YTDLP_PROXY": "http://preferred-proxy:7890",
            },
            clear=True,
        ):
            self.assertEqual(downBili._resolve_youtube_proxy(), "http://preferred-proxy:7890")

    def test_resolve_youtube_proxy_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(downBili._resolve_youtube_proxy())

    def test_youtube_https_proxy_fallback_logs_source(self):
        stderr = StringIO()
        with patch.dict(os.environ, {"HTTPS_PROXY": "http://https-proxy:7890"}, clear=True), redirect_stderr(stderr):
            args = downBili._youtube_ytdlp_network_args()

        self.assertIn("--proxy", args)
        proxy_index = args.index("--proxy")
        self.assertEqual(args[proxy_index + 1], "http://https-proxy:7890")
        self.assertIn("HTTPS_PROXY", stderr.getvalue())

    def test_download_audio_new_adds_youtube_network_args(self):
        captured = {}

        def fake_run(args, **kwargs):
            if "--version" in args:
                return SimpleNamespace(returncode=0, stdout="test-version\n", stderr="")
            if "-f" in args:
                captured["args"] = args
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        def fake_exists(path):
            return str(path).endswith("youtube_cookies.txt")

        with patch.dict(os.environ, {"YTDLP_PROXY": "http://proxy.test:7897"}, clear=True), patch(
            "downBili.get_project_root", return_value="/tmp/project"
        ), patch("downBili.os.path.exists", side_effect=fake_exists), patch(
            "downBili.subprocess.run", side_effect=fake_run
        ):
            downBili.download_audio_new(
                url="https://www.youtube.com/watch?v=demo",
                title="demo-title",
                video_save_dir="/tmp/video",
                autio_save_dir=None,
                video_type="youtube",
            )

        args = captured["args"]
        for required in (
            "--js-runtimes",
            "node",
            "--proxy",
            "http://proxy.test:7897",
            "--retries",
            "30",
            "--fragment-retries",
            "--extractor-retries",
            "--retry-sleep",
            "--socket-timeout",
            "--force-ipv4",
            "--cookies",
            "/tmp/project/youtube_cookies.txt",
        ):
            self.assertIn(required, args)

    def test_download_audio_new_without_explicit_proxy_uses_no_proxy_arg(self):
        captured = {}

        def fake_run(args, **kwargs):
            if "--version" in args:
                return SimpleNamespace(returncode=0, stdout="test-version\n", stderr="")
            if "-f" in args:
                captured["args"] = args
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        def fake_exists(path):
            return str(path).endswith("youtube_cookies.txt")

        with patch.dict(os.environ, {}, clear=True), patch(
            "downBili.get_project_root", return_value="/tmp/project"
        ), patch("downBili.os.path.exists", side_effect=fake_exists), patch(
            "downBili.subprocess.run", side_effect=fake_run
        ):
            downBili.download_audio_new(
                url="https://www.youtube.com/watch?v=demo",
                title="demo-title",
                video_save_dir="/tmp/video",
                autio_save_dir=None,
                video_type="youtube",
            )

        args = captured["args"]
        self.assertIn("--js-runtimes", args)
        self.assertIn("--force-ipv4", args)
        self.assertNotIn("--proxy", args)

    def test_download_audio_new_bili_not_add_youtube_network_args(self):
        captured = {}

        def fake_run(args, **kwargs):
            if "--version" in args:
                return SimpleNamespace(returncode=0, stdout="test-version\n", stderr="")
            if "-f" in args:
                captured["args"] = args
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        def fake_exists(path):
            return str(path).endswith("bili_cookies.txt")

        with patch("downBili.get_project_root", return_value="/tmp/project"), patch(
            "downBili.os.path.exists", side_effect=fake_exists
        ), patch("downBili.subprocess.run", side_effect=fake_run):
            downBili.download_audio_new(
                url="https://b23.tv/demo",
                title="demo-title",
                video_save_dir="/tmp/video",
                autio_save_dir=None,
                video_type="bili",
            )

        args = captured["args"]
        self.assertIn("--proxy", args)
        proxy_index = args.index("--proxy")
        self.assertEqual(args[proxy_index + 1], "")
        self.assertNotIn("--force-ipv4", args)
        self.assertNotIn("--js-runtimes", args)
        self.assertIn("--cookies", args)
        self.assertIn("/tmp/project/bili_cookies.txt", args)

    def test_fetch_remote_title_uses_youtube_network_args(self):
        captured = {}

        def fake_run(args, **kwargs):
            captured["args"] = args
            return SimpleNamespace(returncode=0, stdout="line1\nfinal-title\n")

        def fake_exists(path):
            return str(path).endswith("youtube_cookies.txt")

        with patch.dict(os.environ, {"YTDLP_PROXY": "http://proxy.test:7897"}, clear=True), patch(
            "downBili.get_project_root", return_value="/tmp/project"
        ), patch("downBili.os.path.exists", side_effect=fake_exists), patch(
            "downBili.subprocess.run", side_effect=fake_run
        ):
            title = downBili._fetch_remote_video_title(
                "https://www.youtube.com/watch?v=demo",
                "youtube",
            )

        self.assertEqual(title, "final-title")
        args = captured["args"]
        self.assertIn("--proxy", args)
        self.assertIn("http://proxy.test:7897", args)
        self.assertIn("--js-runtimes", args)
        self.assertIn("--cookies", args)
        self.assertIn("/tmp/project/youtube_cookies.txt", args)

    def test_download_audio_new_failure_contains_youtube_guidance(self):
        def fake_exists(path):
            return str(path).endswith("youtube_cookies.txt")

        def fake_run(args, **kwargs):
            if "--version" in args:
                return SimpleNamespace(returncode=0, stdout="test-version\n", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="network failed")

        with patch.dict(os.environ, {"YTDLP_PROXY": "http://proxy.test:7897"}, clear=True), patch(
            "downBili.get_project_root", return_value="/tmp/project"
        ), patch("downBili.os.path.exists", side_effect=fake_exists), patch(
            "downBili.subprocess.run", side_effect=fake_run
        ), patch("downBili.time.sleep", return_value=None):
            with self.assertRaises(Exception) as ctx:
                downBili.download_audio_new(
                    url="https://www.youtube.com/watch?v=demo",
                    title="demo-title",
                    video_save_dir="/tmp/video",
                    autio_save_dir=None,
                    video_type="youtube",
                )
        message = str(ctx.exception)
        self.assertIn("排查建议(YouTube)", message)
        self.assertIn("return_code=1", message)
        self.assertIn("http://proxy.test:7897", message)
        self.assertIn("python -m unittest bili2text/test/test_downbili_youtube_args.py", message)
        self.assertIn(
            "test_download_audio_new_adds_youtube_network_args",
            message,
        )


if __name__ == "__main__":
    unittest.main()
