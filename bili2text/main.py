from downBili import download_audio_new
from exAudio import *
from speech2text import *
from tqdm import tqdm
import pandas as pd
import time
from datetime import datetime
import re
from tools_data_process.engine_excel import ExcelEngine
from tools_data_process.engine_mysql import MysqlEngine
from tools_data_process.utils_path import get_file_path
from main_run_speech_to_text import summarize_text, judge_text_type


def main():

    sheet_name = "489667127"  # kloa聊开源
    sheet_names = ['有駜矣 合集·毛选思维进阶学习系列', '一点就炸B站号 合集·认知思维', '一点就炸B站号 合集·工作职场',
                '一点就炸B站号 合集·辩证看人', '15741969', '有駜矣 合集·综合思考（政治经济商业创业及哲学）',
                '一点就炸B站号 合集·情感婚恋', '一点就炸B站号 合集·个人经历']
    sheet_names = ["1871365234"]#["高效能人士的七个习惯"]
    excel_engine = ExcelEngine()
    mysql_engine = MysqlEngine()
    mysql_engine.sql_to_excel(plateform="bili", )  # start_date=datetime.now().strftime("%Y-%m-%d")
    sub_file_path, main_file_path = excel_engine.get_summary_path("bili")
    for sheet_name in sheet_names:
        df = pd.read_excel(main_file_path, sheet_name=sheet_name)
        # df = df[df["重要性"] == 1]
        print(df["bvid"].tolist())

        vidio_urls = df["bvid"].tolist()
        title_list = df["标题"].tolist()
        print(df)
        print(vidio_urls)
        print(title_list)
        # vidio_urls = ["RDu13diS9qs"]
        # title_list = ["《说话就是生产力》说话提升效率,生产力倍增,语言背后的高效生产力"]

        audio_save_folder, text_save_path = get_file_path("bili", sheet_name)
        # 视频下载路径
        video_save_folder = fr"X:\RAG\bilibili_video/{sheet_name}"
        for title, av in list(zip(title_list, vidio_urls)):
            t1 = time.time()

            if av and type(title) == str and len(title) > 0:
                try:
                    title = title.strip(). \
                        replace("?", "").replace("*", "").replace("<", ""). \
                        replace(",", " ").replace(".", "").replace(";", ""). \
                        replace(":", "").replace(">", "").replace("|", "").replace("\"", "")

                    print("================", title, av, "=================")
                    # 音频切片保存路径
                    audio_split_folder = os.path.join(audio_save_folder, fr"{title}/")
                    # 文本保存路径
                    os.makedirs(video_save_folder, exist_ok=True)
                    os.makedirs(audio_save_folder, exist_ok=True)
                    os.makedirs(audio_split_folder, exist_ok=True)
                    os.makedirs(text_save_path, exist_ok=True)
                    if os.path.exists(f"{text_save_path}/{title}.txt"):
                        print("{}文件已存在！".format(title))
                        continue
                    # 下载视频
                    # video_title = download_video(av, title, base_dir=video_save_folder) # 已废弃
                    video_type = "bili" if av.startswith("BV") else "youtube"
                    video_title = download_audio_new(av, title, video_save_dir=video_save_folder, autio_save_dir=None,
                                                    video_type=video_type)
                    video_title = title
                    print(1111111111)
                    if video_title:
                        run_split(video_title, video_save_folder, audio_save_folder, audio_split_folder)
                        load_whisper("large-v2")
                        run_speech_to_text(video_title, audio_split_folder, text_save_path,
                                    prompt="以下是普通话的句子。请注意添加标点符号。".format(
                                        title.split(".")[0]), )
                        print("转换完成！耗时：{}, {}".format(time.time() - t1, text_save_path))
                    else:
                        print("下载失败！", title)
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    print("{} 出现错误！".format(title), e)

        if False:
            # 文本摘要
            summary_output_dir = os.path.join(text_save_path, "summary")
            summarize_text(text_save_path, summary_output_dir, text_type=judge_text_type(sheet_name))

if __name__=="__main__":
    main()