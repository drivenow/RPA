import os
import pandas as pd
from datetime import datetime
from platform import system
file_type = "record"
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

def get_root_media_save_path(file_type, sheet_name):
    base_dir = get_media_root()
    if file_type == "bili":
        if not sheet_name:
            raise ValueError("file_type为bili时, sheet_name参数不能为空")
        voice_slice_dir = os.path.join(base_dir, f"audio/{sheet_name}/")
        voice_dir = voice_slice_dir
        text_output_dir = os.path.join(base_dir, f"rag_data/{sheet_name}/")
        video_save_folder = os.path.join(base_dir, f"bilibili_video/{sheet_name}/")
        return voice_dir, text_output_dir, video_save_folder
    elif file_type == "crawl4ai":
        voice_dir = None
        text_output_dir = os.path.join(base_dir, f"rag_data/{sheet_name}/")
    elif file_type == "coputer_record":
        if base_dir.startswith("X"):
            voice_dir = "C:\\Users\\fullmetal\\Documents\\录音\\SJL"
        else:
            voice_dir = "/mnt/c/Users/fullmetal/Documents/录音/SJL/"
        text_output_dir = os.path.join(voice_dir, "outputs")
    elif file_type == "phone_record":
        if base_dir.startswith("X"):
            voice_dir = "D:\\shenjl\\Maigc5\\sounds\\"
        else:
            voice_dir = "/mnt/d/shenjl/Maigc5/sounds/"
        text_output_dir = os.path.join(voice_dir, "outputs")
    elif file_type == "homepage_url":
        voice_dir = None
        text_output_dir = os.path.join(base_dir, "rpa_data/", "batch_urls")
    else:
        raise ValueError("type参数错误：" + file_type)
    return voice_dir, text_output_dir


def get_media_url_excel_path(media_type: str, date=None):
    base_dir = os.path.dirname(get_root_media_save_path("bili", "tmp")[1])
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
    print(get_project_root())
