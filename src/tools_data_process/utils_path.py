import os
import pandas as pd
from datetime import datetime
from platform import system
from tqdm import tqdm
import shutil
import os
media_type = "record"
sheet_name = "树莓派"

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_media_root():
    if system() == "Windows":
        if os.path.exists("X:\\RAG\\"):
            base_dir = "X:\\RAG\\"
        elif os.path.exists("X:\\RAG_192.168.1.2"):
            base_dir = "X:\\RAG_192.168.1.2\\"
        else:
            raise ValueError("未找到有效路径")
    else:   
        if os.path.exists("/mnt/x/RAG_192.168.1.2"):
            base_dir = "/mnt/x/RAG_192.168.1.2/"
        elif os.path.exists("/mnt/e/RAG"):
            base_dir = "/mnt/e/RAG/"
        else:
            raise ValueError("未找到有效路径")
    return base_dir

def get_root_media_save_path(media_type, sheet_name):
    base_dir = get_media_root()
    if media_type.lower() in ["bili", "youtube_browser", "podcasts"]:
        if not sheet_name:
            raise ValueError("media_type为bili时, sheet_name参数不能为空")
        voice_slice_dir = os.path.join(base_dir, f"audio/{sheet_name}/")
        voice_dir = voice_slice_dir
        text_output_dir = os.path.join(base_dir, f"rag_data/{sheet_name}/")
        video_save_folder = os.path.join(base_dir, f"bilibili_video/{sheet_name}/")
        return voice_dir, text_output_dir, video_save_folder
    elif media_type.lower() == "crawl4ai":
        voice_dir = None
        text_output_dir = os.path.join(base_dir, f"rag_data/{sheet_name}/")
    elif media_type.lower() == "coputer_record":
        if base_dir.startswith("X"):
            voice_dir = "C:\\Users\\fullmetal\\Documents\\录音\\SJL"
        else:
            voice_dir = "/mnt/c/Users/fullmetal/Documents/录音/SJL/"
        text_output_dir = os.path.join(voice_dir, "outputs")
    elif media_type == "phone_record":
        if base_dir.startswith("X"):
            voice_dir = "D:\\shenjl\\Maigc5\\sounds\\"
        else:
            voice_dir = "/mnt/d/shenjl/Maigc5/sounds/"
        text_output_dir = os.path.join(voice_dir, "outputs")
    elif media_type.lower() == "homepage_url":
        voice_dir = None
        text_output_dir = os.path.join(base_dir, "rpa_data/", "batch_urls")
    else:
        raise ValueError("type参数错误：" + media_type)
    return voice_dir, text_output_dir


def get_media_url_excel_path(media_type: str, date=None):
    base_dir = get_media_root()
    base_dir = os.path.join(base_dir, "media_urls")
    if not os.path.exists(os.path.join(base_dir, media_type)):
        print(f"WARNIGN: 创建新目录, {os.path.join(base_dir, media_type)}")
        os.makedirs(os.path.join(base_dir, media_type))
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    else:
        date = pd.to_datetime(date).strftime('%Y-%m-%d')
    # 今日新增内容的文件路径
    sub_file_path = os.path.join(base_dir, media_type, f"{media_type}_{date}.xlsx")
    # 合并所有内容的文件路径
    main_file_path = os.path.join(base_dir, media_type, f"{media_type}_summary.xlsx")
    print("get_summary_path: ", sub_file_path, main_file_path)
    return sub_file_path, main_file_path

if __name__ == "__main__":
    voice_dir, text_output_dir, video_save_folder = get_root_media_save_path(media_type="bili", sheet_name="tmp")
    voice_dir = os.path.dirname(voice_dir)
    text_output_dir = os.path.dirname(text_output_dir)
    video_save_folder = os.path.dirname(video_save_folder)


def copy_to_z_drive(src_dir, dst_dir="Z:/RAG"):
    """
    将指定目录拷贝到 Z:/ 盘，若目标已存在同名文件则覆盖。
    """
    if not os.path.exists(src_dir):
        print(f"源目录不存在: {src_dir}")
        return
    if not os.path.exists(dst_dir):
        print(f"目标盘符不存在: {dst_dir}")
        return
    
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
    print(f"已将 {src_dir} 拷贝到 {dst_dir}，同名文件已覆盖。")

if __name__ == "__main__":
    voice_dir, text_output_dir, video_save_folder = get_root_media_save_path(media_type="bili", sheet_name="tmp")
    voice_dir = os.path.dirname(os.path.dirname(voice_dir))
    text_output_dir = os.path.dirname(os.path.dirname(text_output_dir))
    video_save_folder = os.path.dirname(os.path.dirname(video_save_folder))

    import os
    print(os.listdir("Z:/RAG"))

    # # 将文件拷贝到Z:/盘， 若有同名文件，覆盖原文件
    copy_to_z_drive(text_output_dir)
    copy_to_z_drive(voice_dir)
    # copy_to_z_drive(video_save_folder)

