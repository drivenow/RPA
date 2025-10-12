import os
import whisper
from tools_ai.text_llm import deepseek_invoke, qwen_revise_text
from tools_data_process.utils_path import get_root_media_save_path
import ray
from tqdm import tqdm

whisper_model = None
chat_model = deepseek_invoke
corret_text_model = qwen_revise_text


def convert_audio_format(audio_file, output_file):
    # 重命名音频文件
    from pydub import AudioSegment
    # 指定输出的WAV文件路径
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # 使用pydub加载M4A文件
    if audio_file.endswith(".m4a"):
        audio = AudioSegment.from_file(audio_file, format="m4a")
    elif audio_file.endswith(".mp3"):
        audio = AudioSegment.from_file(audio_file, format="mp3")
    else:
        audio = AudioSegment.from_file(audio_file, format="wav")
    # 导出为WAV文件
    audio.export(output_file, format="wav")


def convert_audio_to_text(voice_dir, text_output_dir, text_output_file_name, flag0_rename_voice_file=False,
                          target_filelist=None):
    """
    :param voice_dir: 语音文件目录
    :param output_dir: 语音转换为文本后的输出目录
    :param output_file_name: 输出的文件名
    :param flag0_rename_voice_file: 是否重命名音频文件
    :param target_filelist: str列表，指定要转换的音频文件名
    :return:
    """
    global whisper_model
    if not whisper_model:
        whisper_model = whisper.load_model("large-v2", device="cuda")
    os.makedirs(text_output_dir, exist_ok=True)
    for first_level_path_name in os.listdir(voice_dir):
        try:
            if os.path.isfile(f"{voice_dir}/{first_level_path_name}"):
                tmp_name = first_level_path_name.split(".")[0]
                if target_filelist and first_level_path_name not in target_filelist or \
                        os.path.exists(f"{text_output_dir}/{tmp_name}"):
                    continue
                audio_list = [first_level_path_name]
            else:
                audio_list = [f for f in
                              os.listdir(os.path.join(voice_dir, first_level_path_name))
                              if f.endswith(".mp3")]
                audio_list = sorted(audio_list, key=lambda x: int(x.split(".")[0]))
                audio_list = [f"{first_level_path_name}/{f}" for f in audio_list]
            print(first_level_path_name, audio_list)
            i = 1
            for fn in audio_list:
                print(f"正在转换第{i}/{len(audio_list)}个音频... {fn}")
                # 识别音频
                result = whisper_model.transcribe(f"{voice_dir}/{fn}", initial_prompt="以下是普通话的句子。")
                result_text = "".join([i["text"] for i in result["segments"] if i is not None])
                print(result_text)

                if flag0_rename_voice_file:
                    # 指定M4A文件路径
                    m4a_file = f"{voice_dir}/{fn}"
                    os.makedirs(f"{voice_dir}/new", exist_ok=True)
                    result_text1 = result_text.strip(). \
                        replace("?", "").replace("*", "").replace("<", ""). \
                        replace(",", " ").replace(".", "").replace(";", ""). \
                        replace(":", "").replace(">", "").replace("|", "").replace("\"", "")
                    wav_file = f"{voice_dir}/new/shen-{result_text1}.wav"
                    convert_audio_format(m4a_file, wav_file)

                # 保存结果到文件
                filename = eval(text_output_file_name).strip(). \
                    replace("?", "").replace("*", "").replace("<", ""). \
                    replace(",", " ").replace(".", "").replace(";", ""). \
                    replace(":", "").replace(">", "").replace("|", "").replace("\"", "")
                with open(f"{text_output_dir}/{filename}.txt", "a", encoding="utf-8") as f:
                    content = "".join([i["text"] for i in result["segments"] if i is not None])
                    lines = content.split("。")
                    for line in lines:
                        f.write(line + "。\r\n")
                i += 1
        except:
            import traceback
            traceback.print_exc()
            print("ERROR:", first_level_path_name)


def summarize_text(text_dir, summary_output_dir, text_type="tech", overwrite=False):
    """
    总结文本内容
    :param text_dir: 文本文件目录
    :param summary_output_dir: summary输出目录
    :param text_type:  文本类型，tech/social，将调用不同的deepseek prompt
    :return:
    """
    os.makedirs(summary_output_dir, exist_ok=True)
    text_dir_name = os.path.basename(text_dir)
    if os.path.exists(f"{summary_output_dir}/{text_dir_name}.txt"):
        old_content = "".join(open(f"{summary_output_dir}/{text_dir_name}.txt", "r", encoding="utf-8").readlines())
    else:
        old_content = ""

    ray.init(num_cpus=3)
    remote_func = ray.remote(num_cpus=1)(chat_model)
    tasks = []
    files = []
    file_list = os.listdir(text_dir)
    print(file_list)
    if overwrite:
        if os.path.exists(f"{summary_output_dir}/{text_dir_name}.txt"):
            os.remove(f"{summary_output_dir}/{text_dir_name}.txt")
    for first_level_path_name in file_list:
        if os.path.isfile(f"{text_dir}/{first_level_path_name}"):
            if first_level_path_name in old_content:
                # 已经转换过了，跳过
                print("跳过已转换文件:", first_level_path_name)
                continue
            text_list = [f"{text_dir}/{first_level_path_name}"]
        else:
            continue
            # raise Exception("暂不支持目录输入")

        print(first_level_path_name, text_list)
        for fn in text_list:
            content = "".join(open(fn, "r", encoding="utf-8").readlines())
            tasks.append(remote_func.remote(content, text_type))
            files.append(os.path.basename(fn))

    results = ray.get(tasks)
    ray.shutdown()

    for ridx, result in enumerate(results):
        print(result)
        if result:
            with open(f"{summary_output_dir}/{text_dir_name}.txt", "a", encoding="utf-8") as f:
                f.write(
                    f"=============================================================\r\n")
                f.write(f"# [第{ridx + 1}/{len(tasks)}个文件]: {files[ridx]}\r\n")
                f.write(result)
                f.write("\r\n")


def corret_text(text_dir, corret_text_dir=None):
    if not os.path.isdir(text_dir):
        raise ValueError("text_dir参数错误：{}, 必须为文件夹！".format(text_dir))
    else:
        if text_dir[-1] != "/":
            text_dir += "/"
    # 将文本内容纠错
    if not corret_text_dir:
        corret_text_dir = text_dir[:-1] + "_corret"
        os.makedirs(corret_text_dir, exist_ok=True)
    file_list = os.listdir(text_dir)
    for fn in tqdm(file_list):
        print(f"{text_dir}/{fn}")
        if os.path.isfile(f"{text_dir}/{fn}"):
            target_file = f"{corret_text_dir}/{fn}"
            if not os.path.exists(target_file):
                content = "".join(open(f"{text_dir}/{fn}", "r", encoding="utf-8").readlines())
                # 调用语言模型进行纠错 
                result = corret_text_model(content)
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(result)
                print("纠错完成!!!" + fn)


def judge_text_type(sheet_name):
    if sheet_name in ["比亚迪汉L 电机原理"]:
        text_type = "tech"
    elif sheet_name in ["梧桐木桥"]:
        text_type = "mao"
    elif sheet_name in ["高频量化 做市策略", "章位福"]:
        text_type = "quant"
    elif sheet_name in ["树莓派"]:
        text_type = "normal"
    else:
        text_type = "social"
    return text_type


if __name__ == '__main__':
    media_type = "bili"
    sheet_name = "像素范"
    voice_dir, text_output_dir = get_root_media_save_path(media_type, sheet_name)

    if media_type == "bili":
        target_filelist = []  #
        text_output_file_name = "first_level_path_name"  # 以voice_dir的第一层目录名作为输出文件名
        flag0_rename_voice_file = False  # 第0步，是否转换音频存储格式
        flag1_convert_text = False  # 第一步，是否语音转换为文本
        flag2_summary = False  # 第二步，是否总结文章
        flag3_corret_text = True  # 第三步，是否纠错文本
        summary_output_dir = os.path.join(text_output_dir, "summary")
    elif media_type == "computer_record":
        target_filelist = []
        text_output_file_name = "result_text"  # 输出文件名为识别的文本
        flag0_rename_voice_file = True
        flag1_convert_text = True
        flag2_summary = False
        flag3_corret_text = False
    elif media_type == "phone_record":
        ##########################################################
        target_filelist = ["t0策略规划.wav", "策略规划1.wav", "策略规划2.wav", "策略规划3.wav"][:1]
        text_output_file_name = "first_level_path_name"  # 输出文件名为源文件名
        flag0_rename_voice_file = False
        flag1_convert_text = True
        flag2_summary = False
        flag3_corret_text = False
    else:
        raise ValueError("type参数错误")

    if flag1_convert_text:
        # 第一步，语音转换为文本
        convert_audio_to_text(voice_dir, text_output_dir, text_output_file_name, flag0_rename_voice_file,
                              target_filelist=target_filelist)
    if flag2_summary:
        # 第二步，总结文本内容
        summarize_text(text_output_dir, summary_output_dir, text_type=judge_text_type(sheet_name))

    if flag3_corret_text:
        # 第三步，纠错文本
        corret_text(text_output_dir)
    if False:
        # 测试音频格式转换
        audio_file = "C:\\Users\\fullmetal\\Desktop\\为什么美国的能源安全，大家就不安全？.mp3"
        output_file = "C:\\Users\\fullmetal\\Desktop\\wang.wav"
        convert_audio_format(audio_file, output_file)
