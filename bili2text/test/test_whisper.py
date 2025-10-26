import os
from re import T
from src.tools_data_process.utils_path import get_root_media_save_path
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline


def get_whisper_model_dir():
    if os.path.exists("/mnt/c/Users/fullmetal/.cache/whisper/"):
        return "/mnt/c/Users/fullmetal/.cache/whisper/"
    elif os.path.exists("/mnt/x/RAG_192.168.1.2/.cache/whisper/"):
        return "/mnt/x/RAG_192.168.1.2/.cache/whisper/"
    else:
        return "~/.cache/whisper"

voice_dir, text_output_dir, video_save_folder = get_root_media_save_path("bili", "15741969")
voice_path =  os.path.join(voice_dir, "经济形态发展，夜之城、皮城-祖安式的结构？.mp3")
print(voice_path)

model = WhisperModel("large-v2", device="cuda", compute_type="int8_float16",
                     num_workers=4,  # CTranslate2 内部工作线程
                     cpu_threads=4,
                     download_root = get_whisper_model_dir()
                     )  # 或 "float16"/""
segments, info = model.transcribe(
    voice_path,
    initial_prompt = "以下是普通话的句子。请注意添加标点符号。",
    language="zh",
    vad_filter=True,                          # 语音活动检测，切掉静音段
    vad_parameters=dict(min_silence_duration_ms=500),
    temperature=0.0,
    beam_size=5,
    condition_on_previous_text=False,
)

text = "".join(s.text for s in segments)
print(text)

tok = AutoTokenizer.from_pretrained("KBLab/bert-base-swedish-cased-new")  # 示例模型请替换为你的多语标点模型
mdl = AutoModelForTokenClassification.from_pretrained("oliverguhr/fullstop-punctuation-multilang-large")
punct = pipeline("token-classification", model=mdl, tokenizer=tok, aggregation_strategy="simple", device = -1)
result = punct(text)
print(result)
