from tqdm import tqdm
import pandas as pd
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Iterable, List, Optional
import os
import traceback
from src.tools_data_process.engine_excel import ExcelEngine
from src.tools_data_process.engine_mysql import MysqlEngine
from src.tools_data_process.utils_path import get_root_media_save_path
from src.tools_data_process.utils_path import get_media_url_excel_path
# from main_run_speech_to_text import summarize_text, judge_text_type


@dataclass
class VideoJob:
    media_type: str
    url: str
    title: str
    sheet_name: Optional[str]
    video_type: str

@dataclass
class JobResult:
    job: VideoJob
    status: str
    elapsed: float
    message: Optional[str] = None
    error: Optional[Exception] = None
    @property
    def succeeded(self) -> bool:
        return self.status == "success"
    @property
    def skipped(self) -> bool:
        return self.status == "skipped"

def sanitize_title(raw_title: str, fallback: str) -> str:
    """与 speech2text._write_transcript / resolve_transcript_output_path 使用同一套 sanitize 逻辑。"""
    title = (raw_title or "").strip()
    title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    title = " ".join(title.split())
    return (title or fallback).lower()


def resolve_transcript_output_path(text_dir: str, title: str) -> str:
    """Mirror speech2text._write_transcript() naming for existence checks."""
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    return os.path.join(text_dir, f"{safe_title.lower()}.txt")


def _is_valid_transcript(path: str, min_content_bytes: int = 50) -> bool:
    """检查转录文件是否有效（不只是标题头）。

    防止空内容或只有 '# title\\n\\n' 头部的残缺文件触发 skip_existing 永久跳过。
    """
    if not os.path.exists(path):
        return False
    if os.path.getsize(path) < min_content_bytes:
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False
    # 去掉 "# title\n\n" 头部，检查是否有实质内容
    lines = content.split("\n", 2)
    body = lines[2] if len(lines) > 2 else ""
    return len(body.strip()) > 0

class BiliSpeechPipeline:
    def __init__(
        self,
        whisper_model: str = "large-v2",
    ) -> None:
        # self.excel_engine = ExcelEngine()
        # self.mysql_engine = MysqlEngine()
        self.whisper_model = whisper_model
        # raise Exception()

    def build_jobs_from_excel(self, media_type: str, sheet_name: str) -> List[VideoJob]:
        # sheet_name = "489667127"  # kloa聊开源
        # sheet_names = ['有駜矣 合集·毛选思维进阶学习系列', '一点就炸B站号 合集·认知思维', '一点就炸B站号 合集·工作职场',
        #             '一点就炸B站号 合集·辩证看人', '15741969', '有駜矣 合集·综合思考（政治经济商业创业及哲学）',
        #             '一点就炸B站号 合集·情感婚恋', '一点就炸B站号 合集·个人经历']
        # sheet_names = ["1871365234"]#["高效能人士的七个习惯"]

        self.mysql_engine.sql_to_excel(media_type=media_type)
        sub_file_path, main_file_path = get_media_url_excel_path(media_type=media_type)
        df = pd.read_excel(main_file_path, sheet_name=sheet_name)
        # df = df[df["重要性"] == 1]
        print("main_file_path: ", main_file_path, df)
        jobs: List[VideoJob] = []
        for _, row in df.iterrows():
            raw_title = row.get("标题")
            title_value = "" if pd.isna(raw_title) else str(raw_title)
            if media_type == "podcasts":
                audio_url = row.get("url")
                if audio_url is None or pd.isna(audio_url):
                    print(f"跳过缺少音频链接的播客：{title_value}")
                    continue
                audio_url_str = str(audio_url).strip()                
                job = self.create_job(
                    audio_url_str,
                    title_value,
                    sheet_name,
                    media_type,
                    video_type="podcast",
                )
            else:
                url = row.get("url")
                if not url:
                    continue
                url_str = str(url)
                video_type = "bili" if url_str.startswith("https://www.bilibili.com/video/") else "youtube"
                job = self.create_job(
                    url_str,
                    title_value,
                    sheet_name,
                    media_type,
                    video_type,
                )
            if job:
                jobs.append(job)
        return jobs

    def create_job(
        self,
        url: str,
        raw_title: str,
        sheet_name: Optional[str],
        media_type: str,
        video_type: str,
    ) -> Optional[VideoJob]:
        if not url:
            return None
        if not sheet_name:
            raise ValueError("sheet_name 不能为空，当处理单个视频时请提供 --single-sheet 参数。")
        title = sanitize_title(raw_title or "", fallback=url)
        return VideoJob(
            media_type=media_type,
            url=url,
            title=title,
            sheet_name=sheet_name,
            video_type=video_type,
        )

    def ensure_paths(self, job: VideoJob):
        audio_dir, text_path, video_dir = get_root_media_save_path(job.media_type, job.sheet_name)
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(text_path, exist_ok=True)
        return video_dir, audio_dir, text_path

    
    def process_job(self, job: VideoJob, *, skip_existing: bool = True) -> JobResult:
        from downBili import (
            download_audio_new,
            extract_real_audio_url,
            audio_stream_download,
            restore_original_video_title,
            download_subtitle,
            srt_to_text,
        )
        from speech2text import run_speech_to_text, _write_transcript, restore_punctuation
        from exAudio import run_split
        start = time.time()
        # 视频下载路径
        video_dir, audio_dir, text_path = self.ensure_paths(job)
        transcript_path = resolve_transcript_output_path(text_path, job.title)
        if skip_existing and _is_valid_transcript(transcript_path):
            print(f"==== 跳过已存在: {transcript_path}  ====")
            return JobResult(job=job, status="skipped", elapsed=0.0, message="transcript already exists")
        elif skip_existing and os.path.exists(transcript_path):
            # 文件存在但内容无效（残缺），删除后重跑
            print(f"==== 发现残缺文件，删除后重跑: {transcript_path}  ====")
            os.remove(transcript_path)
        if job.url and type(job.title) == str and len(job.title) > 0:
            print(f"==== 开始处理: {job.title} ({job.url}) ====")
        try:
            if job.media_type == "podcasts":
                asset_url = extract_real_audio_url(job.url)
                if not asset_url:
                    raise ValueError(f"未找到可用的音频链接: {job.title}")
                from urllib.parse import urlparse, parse_qs
                parsed_path = urlparse(asset_url).path
                ext = os.path.splitext(parsed_path)[1] or ".m4a"
                audio_target_path = os.path.join(audio_dir, f"{job.title}{ext}")
                audio_stream_download(asset_url, audio_target_path)
                audio_input = audio_target_path
            else:
                # 优先尝试下载字幕（快速路径，无需下载视频+ASR）
                srt_path = download_subtitle(job.url, video_dir, video_type=job.video_type)
                if srt_path:
                    print(f"[subtitle] 字幕下载成功，跳过 ASR: {srt_path}")
                    transcript = srt_to_text(srt_path)
                    if transcript and transcript.strip():
                        print("[subtitle] 正在恢复标点符号...")
                        transcript = restore_punctuation(transcript)
                        _write_transcript(text_path, job.title, transcript)
                        elapsed = time.time() - start
                        print(f"==== 完成(字幕): {job.title}，耗时 {elapsed:.2f} 秒 ====")
                        return JobResult(job=job, status="success", elapsed=elapsed, message="subtitle")
                    else:
                        print("[警告] 字幕内容为空，回退到 ASR 路径")

                # 无字幕（或字幕为空），走下载视频 → 音频切片 → ASR 管线
                download_audio_new(
                    job.url,
                    job.title,
                    video_save_dir=video_dir,
                    autio_save_dir=None,
                    video_type=job.video_type,
                )
                audio_split_dir = run_split(job.title, video_dir, audio_dir)
                audio_input = audio_split_dir
            run_speech_to_text(job.title, audio_input, text_path, engine="groq")
            if job.media_type != "podcasts":
                restore_original_video_title(job.url, job.title, video_dir, job.video_type)
            elapsed = time.time() - start
            print(f"==== 完成: {job.title}，耗时 {elapsed:.2f} 秒 ====")
            return JobResult(job=job, status="success", elapsed=elapsed)
        except Exception as exc:
            elapsed = time.time() - start
            traceback.print_exc()
            print(f"==== 失败: {job.title}，耗时 {elapsed:.2f} 秒 ====")
            print(exc)
            return JobResult(job=job, status="failed", elapsed=elapsed, message=str(exc), error=exc)

        if False:
            # 文本摘要
            summary_output_dir = os.path.join(text_save_path, "summary")
            summarize_text(text_save_path, summary_output_dir, text_type=judge_text_type(job.sheet_name))


if __name__=="__main__":
    """
    美国反制！中美关系风云突变！股市惨烈，风暴将至？美国经济到底有没有韧性？在这个节骨眼下，很快就会被验证了！Figure机器人惊艳！家中要添保姆了吗？大摩相信光？给出了什么投资建议？
    https://www.youtube.com/watch?v=9iRysdU_hBc
    【正片】周鸿祎×罗永浩！近四小时高密度输出！周鸿祎深度谈 AI
    https://www.bilibili.com/video/BV1hNJ1zLEb8/?spm_id_from=333.337.search-card.all.click
    
    梁文锋作序|为什么量化投资爆火的今天 还值得深读西蒙斯?
    https://www.xiaoyuzhoufm.com/episode/6895364b638b01587983c94a?utm_source=rss
    """
    pipeline = BiliSpeechPipeline()
    if False:
        # jobs = pipeline.build_jobs_from_excel("bili", "15741969")
        # jobs = pipeline.build_jobs_from_excel("youtube_browser", "stone记")
        # jobs = pipeline.build_jobs_from_excel("podcasts", "科学有故事")
        jobs = pipeline.build_jobs_from_excel("bili", "深读一书") # ，系统性思考
    else:
        jobs = [
            #VideoJob(media_type='bili', url='https://www.bilibili.com/video/BV1hNJ1zLEb8',
            #  title='【正片】周鸿祎×罗永浩！近四小时高密度输出！周鸿祎深度谈 AI', sheet_name='自定义', video_type='bili'),
            #VideoJob(media_type='bili', url='https://www.bilibili.com/video/BV19zcqz5ETm',
            #title='这种冰危险吗', sheet_name='自定义', video_type='bili'),
            #VideoJob(media_type='bili', url='https://www.youtube.com/watch?v=NUeluCHIf8A',
            #title='中美翻脸了，终于等到一个绝好的加仓机会了', sheet_name='自定义', video_type='youtube'),
            #]
            VideoJob(media_type='bili', url='https://www.youtube.com/watch?v=Vgah1K2Qfec&t=173s',
            title='codex openclaw', sheet_name='自定义', video_type='youtube'),
            ]
    print(jobs)

    results = []
    for job in jobs:
        results.append(pipeline.process_job(job, skip_existing=True))
