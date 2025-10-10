import whisper
import os
import time
from retrying import retry
from tqdm import tqdm

whisper_model = None


def is_cuda_available():
    return whisper.torch.cuda.is_available()


def is_rocm_available():
    import torch
    return hasattr(torch, 'hip') and torch.hip.is_available()


def load_whisper(model="tiny"):
    global whisper_model
    start_time = time.time()
    if whisper_model is None:
        device = "cuda" if is_cuda_available() else "xpu" if is_rocm_available() else "cpu"
        whisper_model = whisper.load_model(model, device=device)
        print("Whisper模型加载耗时：", time.time() - start_time, "秒：" + model)


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def run_speech_to_text(title, audio_split_folder, text_save_path, prompt="以下是普通话的句子。"):
    global whisper_model
    # 读取列表中的音频文件
    audio_list = os.listdir(audio_split_folder)
    audio_list = sorted(audio_list, key=lambda x: int(x.split(".")[0]))
    print(audio_list)

    print("正在转换文本...")

    i = 1
    for fn in tqdm(audio_list[:2]):
        print(f"正在转换第{i}/{len(audio_list)}个音频... {fn}")
        # 识别音频
        result = whisper_model.transcribe(f"{audio_split_folder}/{fn}", initial_prompt=prompt)
        content = " ".join([i["text"] for i in result["segments"] if i is not None])

        print(content)
        # 统计content中的逗号个数，如果小于1%，就抛出异常
        if content.count(",")+content.count("。") <8:
            raise ValueError("音频转换文本失败！")

        with open(f"{text_save_path}/{title}.txt", "a", encoding="utf-8") as f:
            content = "".join([i["text"] for i in result["segments"] if i is not None])
            lines = content.split("。")
            for line in lines:
                f.write(line + "。\r\n")
        i += 1
    return content
