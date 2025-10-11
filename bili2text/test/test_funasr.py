from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from tools_data_process.utils_path import get_root_media_save_path
import os
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
model_dir = "iic/SenseVoiceSmall"

model = AutoModel(
    model=model_dir,
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
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
)
text = rich_transcription_postprocess(res[0]["text"])
print(text)