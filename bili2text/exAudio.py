from moviepy import VideoFileClip
from pydub import AudioSegment
import os
import numpy as np
import shutil
from tqdm import tqdm

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus"}
VIDEO_EXTENSIONS = {".mp4", ".flv", ".webm", ".mkv", ".mov", ".m4v"}


def _is_transient_file(name: str) -> bool:
    lower = name.lower()
    return lower.startswith("temp_") or lower.endswith(".part") or lower.endswith(".ytdl")


def _list_media_candidates(video_title: str, media_dir: str):
    files = [f for f in os.listdir(media_dir) if os.path.isfile(os.path.join(media_dir, f))]
    files = [f for f in files if os.path.splitext(f)[1].lower() in (AUDIO_EXTENSIONS | VIDEO_EXTENSIONS)]
    title_matches = [f for f in files if video_title in f]
    if title_matches:
        return sorted(
            title_matches,
            key=lambda name: (
                1 if _is_transient_file(name) else 0,
                0 if os.path.splitext(name)[1].lower() in AUDIO_EXTENSIONS else 1,
                name.lower(),
            ),
        )
    transient_matches = [f for f in files if _is_transient_file(f)]
    return sorted(
        transient_matches,
        key=lambda name: os.path.getmtime(os.path.join(media_dir, name)),
        reverse=True,
    )


def _export_audio_as_mp3(source_path: str, target_mp3_path: str):
    ext = os.path.splitext(source_path)[1].lower()
    if ext == ".mp3":
        if os.path.abspath(source_path) != os.path.abspath(target_mp3_path):
            shutil.copy2(source_path, target_mp3_path)
        return
    segment = AudioSegment.from_file(source_path)
    segment.export(target_mp3_path, format="mp3")


def _extract_audio_from_video(video_path: str, target_mp3_path: str) -> bool:
    clip = None
    try:
        clip = VideoFileClip(video_path)
        audio = clip.audio
        if audio is None:
            return False
        audio.write_audiofile(target_mp3_path)
        return True
    finally:
        try:
            if clip is not None:
                if clip.audio is not None:
                    clip.audio.close()
                clip.close()
        except Exception:
            pass

def split_mp3(filename, slice_length=1200000, target_folder="audio/slice"):
    # 加载MP3文件
    audio = AudioSegment.from_mp3(filename)

    # 计算分割的数量
    total_slices = int(np.ceil(len(audio) / slice_length))

    for i in tqdm(range(total_slices), desc="切割音频"):
        # 分割音频
        start = i * slice_length
        end = start + slice_length
        slice = audio[start:end]

        # 构建保存路径
        slice_filename = f"{i + 1}.mp3"
        slice_path = os.path.join(target_folder, slice_filename)
    
        # 导出分割的音频片段
        # 放慢音频的播放速度，将其减慢到原来的0.8倍
        # slice = slice.speedup(playback_speed=0.8)
        slice.export(slice_path, format="mp3")
        print(f"Slice {i} saved: {slice_path}")


# 运行切割函数
def run_split(video_title, vidio_folder, audio_folder, audio_split_folder=None, split=True):
    os.makedirs(audio_folder, exist_ok=True)
    target_mp3 = os.path.join(audio_folder, f"{video_title}.mp3")

    candidates = _list_media_candidates(video_title, vidio_folder)
    if not candidates:
        raise ValueError(f"No media file found for title: {video_title}")

    errors = []
    extracted = False

    for file_name in candidates:
        source_path = os.path.join(vidio_folder, file_name)
        ext = os.path.splitext(file_name)[1].lower()
        try:
            if ext in AUDIO_EXTENSIONS:
                _export_audio_as_mp3(source_path, target_mp3)
                print(f"[run_split] 使用音频文件: {file_name}")
                extracted = True
                break
            if ext in VIDEO_EXTENSIONS and _extract_audio_from_video(source_path, target_mp3):
                print(f"[run_split] 从视频提取音频: {file_name}")
                extracted = True
                break
            errors.append(f"{file_name}: no audio stream")
        except Exception as exc:
            errors.append(f"{file_name}: {exc}")

    if not extracted:
        error_text = "; ".join(errors[:5])
        raise ValueError(f"无法从候选媒体中提取音频: {video_title}. details={error_text}")

    # 运行切割
    if split:
        if audio_split_folder is None:
            audio_split_folder = os.path.join(audio_folder, video_title)
        os.makedirs(audio_split_folder, exist_ok=True)
        split_mp3(target_mp3, target_folder=audio_split_folder)
        return audio_split_folder
    else:
        return target_mp3
