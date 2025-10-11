from tqdm import tqdm
import pandas as pd
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Iterable, List, Optional
import os
from tools_data_process.engine_excel import ExcelEngine
from tools_data_process.engine_mysql import MysqlEngine
from tools_data_process.utils_path import get_root_media_save_path
from tools_data_process.utils_path import get_media_url_excel_path
from main_run_speech_to_text import summarize_text, judge_text_type


@dataclass
class VideoJob:
    media_type: str
    bvid: str
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
            bvid = row.get("bvid")
            raw_title = row.get("标题")
            if pd.isna(bvid):
                continue
            title_value = "" if pd.isna(raw_title) else str(raw_title)
            job = self.create_job(str(bvid), title_value, sheet_name, media_type)
            if job:
                jobs.append(job)
        return jobs

    def create_job(
        self,
        bvid: str,
        raw_title: str,
        sheet_name: Optional[str],
        media_type: str,
    ) -> Optional[VideoJob]:
        if not bvid:
            return None
        if not sheet_name:
            raise ValueError("sheet_name 不能为空，当处理单个视频时请提供 --single-sheet 参数。")
        title = sanitize_title(raw_title or "", fallback=bvid)
        video_type = "bili" if bvid.startswith("BV") else "youtube"
        return VideoJob(media_type=media_type, bvid=bvid, title=title, sheet_name=sheet_name, video_type=video_type)

    def ensure_paths(self, title) -> None:
        audio_dir, text_path, video_dir = get_root_media_save_path(job.media_type, job.sheet_name)
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(text_path, exist_ok=True)
        return video_dir, audio_dir, text_path

    
    def process_job(self, job: VideoJob, *, skip_existing: bool = True) -> JobResult:
        from downBili import download_audio_new
        from exAudio import run_split
        start = time.time()
        # 视频下载路径
        video_dir, audio_dir, text_path = self.ensure_paths(job.title)
        t1 = time.time()
        self.ensure_paths(job.title)
        if skip_existing and os.path.exists(os.path.join(text_path, f"{job.title}.txt")):
            print(f"==== 跳过已存在: {text_path}  ====")
            return JobResult(job=job, status="skipped", elapsed=0.0, message="transcript already exists")
        if job.bvid and type(job.title) == str and len(job.title) > 0:
            print(f"==== 开始处理: {job.title} ({job.bvid}) ====")
        try:
            download_audio_new(
                job.bvid,
                job.title,
                video_save_dir=video_dir,
                autio_save_dir=None,
                video_type=job.video_type,
            )
            from speech2text import load_whisper, run_speech_to_text
            load_whisper(self.whisper_model)
            audio_split_dir = run_split(job.title, video_dir, audio_dir)
            run_speech_to_text(job.title, audio_split_dir, text_path,        
                prompt="以下是普通话的句子。请注意添加标点符号。")
            elapsed = time.time() - start
            print(f"==== 完成: {job.title}，耗时 {elapsed:.2f} 秒 ====")
            return JobResult(job=job, status="success", elapsed=elapsed)
        except Exception as exc:
            elapsed = time.time() - start
            print(f"==== 失败: {job.title}，耗时 {elapsed:.2f} 秒 ====")
            print(exc)
            return JobResult(job=job, status="failed", elapsed=elapsed, message=str(exc), error=exc)

        if False:
            # 文本摘要
            summary_output_dir = os.path.join(text_save_path, "summary")
            summarize_text(text_save_path, summary_output_dir, text_type=judge_text_type(job.sheet_name))


if __name__=="__main__":
    # https://www.youtube.com/watch?v=E5mU5RYT61o
    pipeline = BiliSpeechPipeline()
    # jobs = pipeline.build_jobs_from_excel("bili", "15741969")
    jobs = [VideoJob(media_type='bili', bvid='BV1VwrzYgEc5',
         title='经济形态发展，夜之城、皮城-祖安式的结构？', sheet_name='15741969', video_type='bili')]
    print(jobs)

    results = []
    for job in jobs:
        results.append(pipeline.process_job(job, skip_existing=True))
