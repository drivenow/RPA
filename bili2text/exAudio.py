from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import os
import numpy as np
import time


def split_mp3(filename, slice_length=1200000, target_folder="audio/slice"):
    # 加载MP3文件
    audio = AudioSegment.from_mp3(filename)

    # 计算分割的数量
    total_slices = int(np.ceil(len(audio) / slice_length))

    for i in range(total_slices):
        # 分割音频
        start = i * slice_length
        end = start + slice_length
        slice = audio[start:end]

        # 构建保存路径
        slice_filename = f"{i + 1}.mp3"
        slice_path = os.path.join(target_folder, slice_filename)
    
        # 导出分割的音频片段
        # 放慢音频的播放速度，将其减慢到原来的0.8倍
        slice = slice.speedup(playback_speed=0.8)
        slice.export(slice_path, format="mp3")
        print(f"Slice {i} saved: {slice_path}")


# 运行切割函数
def run_split(video_title, vidio_folder, audio_folder, audio_split_folder, split = True):
    # 将FLV视频文件加载为一个VideoFileClip对象
    file_name = [i for i in os.listdir(vidio_folder) if video_title in i and not "temp" in i]
    if not file_name:
        raise ValueError("No video file found. {}".format(video_title))
    file_name = file_name[0]
    clip = VideoFileClip(os.path.join(vidio_folder, file_name))
    # 提取音频部分
    audio = clip.audio
    if audio is None:
        raise ValueError("无法从视频中提取音频: {}".format(video_title))
    # 将音频保存为一个文件（例如MP3），写入conv文件夹
    audio.write_audiofile(f"{audio_folder}/{video_title}.mp3")
    # 关闭视频文件
    clip.close()

    # 运行切割
    if split:
        split_mp3(f"{audio_folder}/{video_title}.mp3", target_folder=audio_split_folder)
    return True
