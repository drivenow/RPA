import os
from downBili import download_audio_new
from exAudio import run_split
from speech2text import load_whisper, run_speech_to_text


def process_video_to_text(video_url, title, video_save_dir="X:\\RAG\\bilibili_video", audio_save_dir=None):
    """
    将视频处理成文本的完整工具函数
    Args:
        video_url: 视频链接中的BV号或AV号
        title: 视频标题
        video_save_dir: 视频保存目录
        audio_save_dir: 音频保存目录（可选）

    Returns:
        bool: 处理是否成功
    """
    try:
        # 清理标题中的特殊字符
        title = title.strip().replace("?", "").replace("*", "").replace("<", "").\
            replace(",", " ").replace(".", "").replace(";", "").\
            replace(":", "").replace(">", "").replace("|", "").replace("\"", "")

        # 创建必要的目录
        os.makedirs(video_save_dir, exist_ok=True)
        
        # 设置音频切片和文本保存路径
        audio_save_folder = os.path.join(video_save_dir, "audio").replace('\\', '/')
        audio_split_folder = os.path.join(audio_save_folder, title).replace('\\', '/')
        text_save_path = os.path.join(video_save_dir, "text").replace('\\', '/')
        
        os.makedirs(audio_save_folder, exist_ok=True)
        os.makedirs(audio_split_folder, exist_ok=True)
        os.makedirs(text_save_path, exist_ok=True)

        # # # 检查文本文件是否已存在
        # if os.path.exists(f"{text_save_path}/{title}.txt"):
        #     print("{}文件已存在！".format(title))
        #     return True

        # # 下载视频
        # video_type = "bili" if video_url.startswith("BV") else "youtube"
        # video_title = download_audio_new(video_url, title, video_save_dir=video_save_dir,
        #                                autio_save_dir=audio_save_dir, video_type=video_type)

        # if not video_title:
        #     print("下载失败！", title)
        #     return False

        # 检查视频文件是否存在且完整
        video_files = [f for f in os.listdir(video_save_dir) if title in f and not f.endswith('.temp')]
        if not video_files:
            print("视频文件不完整！", title)
            return False

        # 分割音频
        if False:
            # 处理音频
            run_split(title, video_save_dir, audio_save_folder, audio_split_folder, split=True)
            # 加载语音识别模型
            load_whisper("large-v2")
            
            # 转换音频为文本
            content = run_speech_to_text(title, audio_split_folder, text_save_path,
                            prompt="以下是普通话的句子, 包含逗号、句号和感叹号。")
        else:
            from tools_ai import whisper_processor 
            # 处理音频
            run_split(title, video_save_dir, audio_save_folder, audio_split_folder, split=False)
            result = whisper_processor.process_audio(f"{audio_save_folder}/{title}.mp3", "large-v3-turbo-q8_0")
            print(result)
            with open(f"{text_save_path}/{title}.txt", "a", encoding="utf-8") as f:
                f.writelines(result + "。\r\n")
        i += 1

        print("处理完成：{}".format(title))
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("{} 处理出错：{}".format(title, str(e)))
        return False

if __name__ == "__main__":
    # 示例：处理B站视频
    video_url = "BV1QMW8epEFM"  # 替换为实际的BV号
    title = "示例视频标题1"
    video_save_dir = "./video_output"  # 设置本地保存目录
    
    # 调用处理函数
    success = process_video_to_text(video_url, title, video_save_dir)
    
    if success:
        print(f"视频 {title} 处理成功！")
    else:
        print(f"视频 {title} 处理失败！")
