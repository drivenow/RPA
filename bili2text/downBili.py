# import imageio
# imageio.plugins.ffmpeg.download()

from curl_cffi import requests
import time, hashlib, urllib.request, re, json
from moviepy.editor import *
import os, sys
import json
from retrying import retry
import subprocess

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

start_time = 0


def check_folder():
    # 检查文件夹是否被创建：
    if not os.path.exists("bilibili_video"):
        os.makedirs("bilibili_video")

    if not os.path.exists("outputs"):
        os.makedirs("outputs")


@retry(stop_max_attempt_number=6, wait_fixed=10000)
def download_video(bv_number, title, base_dir):
    try:
        # Step 1: 请求元数据，使用了zhouql.vip的接口，感谢！
        meta_url = f"https://bili.zhouql.vip/meta/{bv_number}"
        meta_response = requests.get(meta_url)
        content = meta_response.content.decode("utf-8", errors="replace")
        meta_data = json.loads(content, strict=False)  # download_response.json()

        # 检查元数据请求是否成功
        if meta_data["code"] != 0:
            print("元数据请求失败:", meta_data["message"])
            return

        # 提取cid和aid
        cid = meta_data["data"]["cid"]
        aid = meta_data["data"]["aid"]
        print(f"获取的cid: {cid}, aid: {aid}")

        # Step 2: 请求下载链接
        download_url = f"https://bili.zhouql.vip/download/{aid}/{cid}"
        download_response = requests.get(download_url)
        content = download_response.content.decode("utf-8", errors="replace")
        download_data = json.loads(content, strict=False)  # download_response.json()

        # 检查下载链接请求是否成功
        if download_data["code"] != 0:
            print("下载链接请求失败:", download_data["message"])
            return

        # 获取视频下载URL
        video_url = download_data["data"]["durl"][0]["url"]
        print(f"视频下载链接: {video_url}")

        # Step 3: 下载视频
        video_response = requests.get(video_url, stream=True, headers=HEADERS)

        # 定义保存视频的文件名
        check_folder()
        file_name = os.path.join(base_dir, f'{title}.mp4')
        # 获取总大小
        total_size = int(video_response.headers.get('content-length', 0))
        downloaded_size = 0  # 已下载大小

        # 保存视频到本地并显示进度条
        if not os.path.exists(file_name):
            with open(file_name, "wb") as file:
                for chunk in video_response.iter_content(chunk_size=1024 * 2):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)

                        # 计算进度
                        percent_complete = downloaded_size / total_size * 100
                        # 打印进度条
                        progress = int(percent_complete // 2)  # 控制进度条宽度
                        if int(round(percent_complete, 2) * 100) % 100 == 0:
                            # print(int(round(percent_complete,2)*100))
                            sys.stdout.write(
                                f"\r下载进度: [{'#' * progress}{' ' * (50 - progress)}] {percent_complete:.2f}%")
                            sys.stdout.flush()

            print(f"\n视频已成功下载到: {file_name}")
        return title

    except Exception as e:
        import traceback
        print(traceback.print_exc())
        print("发生错误:", str(e))


def download_audio_new(bv_number, title, video_save_dir=None, autio_save_dir=None, video_type="bili"):
    try:
        if video_type == "bili":
            url = "https://www.bilibili.com/video/{}".format(bv_number)
            cookie_file = "X:\\RPA\\bili_cookies.txt"
        else:
            url = "https://www.youtube.com/watch?v={}".format(bv_number)
            cookie_file = "X:\\RPA\\youtube_cookies.txt"
        if video_save_dir:
            save_dir = video_save_dir
            # 调用子进程执行命令
            result = subprocess.call(
                'yt-dlp -f "bv*[height<=480]+ba/b[height<=480] / wv*+ba/w" "{}" -o "{}/{}.%(ext)s" '.format(
                    url, save_dir, title), shell=True)
            print(
                'yt-dlp -f "bv*[height<=480]+ba/b[height<=480] / wv*+ba/w" "{}" -o "{}/{}.%(ext)s" '.format(
                    url, save_dir, title))

            # 判断子进程是否执行成功
            try:
                assert result == 0, "下载失败"
            except:
                result = subprocess.call(
                    'yt-dlp -f "bv*[height<=480]+ba/b[height<=480] / wv*+ba/w" "{}" -o "{}/{}.%(ext)s" --cookies {}'.format(
                        url, save_dir, title, cookie_file), shell=True)
                print(
                    'yt-dlp -f "bv*[height<=480]+ba/b[height<=480] / wv*+ba/w" "{}" -o "{}/{}.%(ext)s" --cookies {}'.format(
                        url, save_dir, title, cookie_file))
                assert result == 0, "下载失败"

        if autio_save_dir:
            save_dir = autio_save_dir
            # 调用子进程执行命令
            result = subprocess.call(
                'yt-dlp -f ba "{}" -o "{}/{}.%(ext)s" --extract-audio --audio-format mp3'.format(
                    url, save_dir, title), shell=True)
            print("yt-dlp -f ba \"{}\" -o \"{}/{}.%(ext)s\" --extract-audio --audio-format mp3".format(url, save_dir, title))
            # 判断子进程是否执行成功
            try:
                assert result == 0, "下载失败"
            except:
                result = subprocess.call(
                    'yt-dlp -f ba "{}" -o "{}/{}.%(ext)s" --extract-audio --audio-format mp3 --cookies X:\\RPA\\bili_cookies.txt'.format(
                        url, save_dir, title), shell=True)
                print(
                    'yt-dlp -f ba "{}" -o "{}/{}.%(ext)s" --extract-audio --audio-format mp3 --cookies X:\\RPA\\bili_cookies.txt'.format(
                        url, save_dir, title))
                assert result == 0, "下载失败"
        return title
    except Exception as e:
        import traceback
        print(traceback.print_exc())
        print("发生错误:", str(e))
        return
