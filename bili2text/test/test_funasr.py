import os

from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from src.tools_data_process.utils_path import get_root_media_save_path


def get_whisper_model_dir():
    if os.path.exists("/mnt/c/Users/fullmetal/.cache/whisper/"):
        return "/mnt/c/Users/fullmetal/.cache/whisper/"
    elif os.path.exists("/mnt/x/RAG_192.168.1.2/.cache/whisper/"):
        return "/mnt/x/RAG_192.168.1.2/.cache/whisper/"
    else:
        return "~/.cache/whisper"


def format_timestamp(ms_value):
    """Convert millisecond timestamp to HH:MM:SS.mmm string."""
    if ms_value is None:
        return "00:00:00.000"
    total_ms = int(ms_value)
    seconds, milliseconds = divmod(total_ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

voice_dir, text_output_dir, video_save_folder = get_root_media_save_path("bili", "自定义")
voice_path =  os.path.join(voice_dir, "经济形态发展，夜之城、皮城-祖安式的结构？.mp3")
print(voice_path)
# https://github.com/modelscope/FunASR/blob/main/README_zh.md
# model_dir = "iic/SenseVoiceSmall" #多种语音理解能力，涵盖了自动语音识别（ASR）、语言识别（LID）、情感识别（SER）以及音频事件检测（AED）,无时间戳
model_dir = "paraformer-zh" #语音识别，带时间戳输出，非实时

model = AutoModel(
    model=model_dir,
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
    spk_model="cam++", # 说话人分离
    punc_model="ct-punc", # 标点恢复
    device="cuda:0",
)

# en
res = model.generate(
    input=voice_path,
    cache={},
    language="auto",  # "zn", "en", "yue", "ja", "ko", "nospeech"
    use_itn=True,
    batch_size_s=60,
    merge_vad=True,  #
    merge_length_s=15,
    sentence_timestamp=True,
)
if not res:
    raise RuntimeError("FunASR 未返回任何识别结果。")

result = res[0]
text = rich_transcription_postprocess(result.get("text", ""))
print(text)

sentence_info = result.get("sentence_info") or []
if not sentence_info:
    token_timestamps = result.get("timestamp") or []
    start_ms = token_timestamps[0][0] if token_timestamps else 0
    end_ms = token_timestamps[-1][1] if token_timestamps else start_ms
    sentence_info = [
        {
            "start": start_ms,
            "end": end_ms,
            "text": text,
            "spk": result.get("spk", 0),
        }
    ]

os.makedirs(text_output_dir, exist_ok=True)
base_name = os.path.splitext(os.path.basename(voice_path))[0]
txt_output_path = os.path.join(text_output_dir, f"{base_name}_timestamp_speaker.txt")

with open(txt_output_path, "w", encoding="utf-8") as txt_file:
    previous_speaker = None
    previous_end_ms = None
    block_index = 0
    for idx, segment in enumerate(sentence_info, start=1):
        start_ms = segment.get("start")
        end_ms = segment.get("end")
        speaker_id = segment.get("spk")
        segment_text = rich_transcription_postprocess(segment.get("text", "").strip())
        insert_timestamp = False
        if previous_speaker is None:
            insert_timestamp = True
        elif speaker_id != previous_speaker:
            insert_timestamp = True
        elif (
            start_ms is not None
            and previous_end_ms is not None
            and start_ms - previous_end_ms > 60_000
        ):
            insert_timestamp = True

        if insert_timestamp:
            block_index += 1
            start_label = format_timestamp(start_ms)
            end_label = format_timestamp(end_ms)
            speaker_label = f"\n\nSPK{speaker_id}" if speaker_id is not None else "SPK?"
            txt_file.write(f"{block_index}")
            txt_file.write(f"{start_label} --> {end_label} [{speaker_label}]\n")

        if "。" in segment_text:
            segment_text = segment_text.replace("。", "。\n")
        txt_file.write(f"{segment_text}")
        previous_speaker = speaker_id
        if end_ms is not None:
            previous_end_ms = end_ms

print(f"带时间戳和说话人信息的文本已保存至: {txt_output_path}")
