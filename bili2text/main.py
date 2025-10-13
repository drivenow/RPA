from tqdm import tqdm
import pandas as pd
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Iterable, List, Optional
import os
import traceback
from tools_data_process.engine_excel import ExcelEngine
from tools_data_process.engine_mysql import MysqlEngine
from tools_data_process.utils_path import get_root_media_save_path
from tools_data_process.utils_path import get_media_url_excel_path
from main_run_speech_to_text import summarize_text, judge_text_type


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
    title = raw_title.strip()
    invalid_chars = r'<>:"/\\|?*'
    translation = str.maketrans({ch: " " if ch in {",", ";"} else "" for ch in invalid_chars + ",;."})
    title = title.translate(translation)
    title = " ".join(title.split())
    return title or fallback

class BiliSpeechPipeline:
    def __init__(
        self,
        whisper_model: str = "large-v2",
    ) -> None:
        self.excel_engine = ExcelEngine()
        self.mysql_engine = MysqlEngine()
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
        from downBili import download_audio_new, extract_real_audio_url, audio_stream_download
        from speech2text import run_speech_to_text
        from exAudio import run_split
        start = time.time()
        # 视频下载路径
        video_dir, audio_dir, text_path = self.ensure_paths(job)
        if skip_existing and os.path.exists(os.path.join(text_path, f"{job.title}.txt")):
            print(f"==== 跳过已存在: {text_path}  ====")
            return JobResult(job=job, status="skipped", elapsed=0.0, message="transcript already exists")
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
                download_audio_new(
                    job.url,
                    job.title,
                    video_save_dir=video_dir,
                    autio_save_dir=None,
                    video_type=job.video_type,
                )
                audio_split_dir = run_split(job.title, video_dir, audio_dir)
                audio_input = audio_split_dir
            run_speech_to_text(job.title, audio_input, text_path, engine="funasr")
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
    """
    pipeline = BiliSpeechPipeline()
    if True:
        # jobs = pipeline.build_jobs_from_excel("bili", "15741969")
        # jobs = pipeline.build_jobs_from_excel("youtube_browser", "stone记")
        jobs = pipeline.build_jobs_from_excel("podcasts", "科学有故事")
    else:
        jobs = [VideoJob(media_type='bili', url='https://www.bilibili.com/video/BV1hNJ1zLEb8',
            title='【正片】周鸿祎×罗永浩！近四小时高密度输出！周鸿祎深度谈 AI', sheet_name='自定义', video_type='bili'),
            VideoJob(media_type='bili', url='https://www.youtube.com/watch?v=NUeluCHIf8A',
            title='中美翻脸了，终于等到一个绝好的加仓机会了', sheet_name='自定义', video_type='youtube'),
            ]
    print(jobs)

    results = []
    for job in jobs:
        results.append(pipeline.process_job(job, skip_existing=True))
