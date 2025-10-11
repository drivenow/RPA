import os
import time
from typing import Dict, Iterable, List, Optional

from retrying import retry
from tqdm import tqdm

whisper_model = None
whisper_model_name: Optional[str] = None
funasr_model = None
funasr_model_config: Optional[Dict[str, object]] = None

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def get_whisper_model_dir() -> str:
    if os.path.exists("/mnt/c/Users/fullmetal/.cache/whisper/"):
        return "/mnt/c/Users/fullmetal/.cache/whisper/"
    if os.path.exists("/mnt/x/RAG_192.168.1.2/.cache/whisper/"):
        return "/mnt/x/RAG_192.168.1.2/.cache/whisper/"
    return "~/.cache/whisper"


def is_cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def is_rocm_available() -> bool:
    try:
        import torch

        return hasattr(torch, "hip") and bool(torch.hip.is_available())
    except Exception:
        return False


def load_whisper(model: str = "tiny", **model_kwargs):
    """Load faster-whisper model only once."""
    global whisper_model, whisper_model_name
    desired_name = model or "tiny"
    if whisper_model is not None and whisper_model_name == desired_name:
        return whisper_model

    start_time = time.time()
    device = "cuda" if is_cuda_available() else "xpu" if is_rocm_available() else "cpu"
    print("device:", device)
    from faster_whisper import WhisperModel

    load_kwargs = {
        "compute_type": "int8_float16",
        "num_workers": 6,
        "cpu_threads": 6,
        "download_root": get_whisper_model_dir(),
    }
    load_kwargs.update(model_kwargs)
    whisper_model = WhisperModel(desired_name, device=device, **load_kwargs)
    whisper_model_name = desired_name
    print("Whisper模型加载耗时：", time.time() - start_time, "秒：" + desired_name)
    return whisper_model


def load_funasr(
    model_dir: str = "iic/SenseVoiceSmall",
    *,
    device: str = "cuda:0",
    vad_model: str = "fsmn-vad",
    vad_kwargs: Optional[Dict[str, int]] = None,
    **extra_kwargs,
):
    """Load FunASR AutoModel and reuse across calls."""
    global funasr_model, funasr_model_config
    start_time = time.time()
    config = {
        "model_dir": model_dir,
        "device": device,
        "vad_model": vad_model,
        "vad_kwargs": tuple(sorted((vad_kwargs or {"max_single_segment_time": 30000}).items())),
        **extra_kwargs,
    }
    if funasr_model is not None and funasr_model_config == config:
        return funasr_model

    from funasr import AutoModel

    load_kwargs = dict(extra_kwargs)
    load_kwargs.setdefault("model", model_dir)
    load_kwargs.setdefault("device", device)
    load_kwargs.setdefault("vad_model", vad_model)
    load_kwargs.setdefault("vad_kwargs", vad_kwargs or {"max_single_segment_time": 30000})
    funasr_model = AutoModel(**load_kwargs)
    funasr_model_config = config
    print("FunASR模型加载耗时：", time.time() - start_time, "秒：" + model_dir)
    return funasr_model


def _audio_sort_key(filename: str):
    stem = os.path.splitext(filename)[0]
    try:
        return int(stem)
    except ValueError:
        return stem


def _is_audio_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in AUDIO_EXTENSIONS


def _collect_audio_paths(audio_split_folder: str) -> List[str]:
    if os.path.isdir(audio_split_folder):
        candidates = [
            name
            for name in os.listdir(audio_split_folder)
            if _is_audio_file(name)
        ]
        candidates.sort(key=_audio_sort_key)
        return [os.path.join(audio_split_folder, name) for name in candidates]
    if os.path.isfile(audio_split_folder):
        return [audio_split_folder]
    raise FileNotFoundError(f"音频路径不存在：{audio_split_folder}")


def _ensure_whisper_model(load_options: Optional[Dict[str, object]] = None):
    load_options = dict(load_options or {})
    model_name = load_options.pop("model", load_options.pop("model_name", None))
    if whisper_model is None:
        load_whisper(model=model_name or "tiny", **load_options)
    elif model_name and model_name != whisper_model_name:
        load_whisper(model=model_name, **load_options)
    return whisper_model


def _transcribe_with_whisper(
    audio_paths: Iterable[str],
    *,
    load_options: Optional[Dict[str, object]] = None,
    transcribe_options: Optional[Dict[str, object]] = None,
) -> List[str]:
    model = _ensure_whisper_model(load_options)
    default_options = {
        "initial_prompt": "以下是普通话的句子, 请注意添加标点符号。",
        "language": "zh",
        "vad_filter": True,
        "vad_parameters": dict(min_silence_duration_ms=500),
        "temperature": 0.0,
        "beam_size": 5,
        "condition_on_previous_text": False,
    }
    if transcribe_options:
        default_options.update(transcribe_options)

    transcripts: List[str] = []
    paths = list(audio_paths)
    for idx, audio_path in enumerate(tqdm(paths, desc="Transcribing (whisper)"), start=1):
        print(f"正在转换第{idx}个音频... {os.path.basename(audio_path)}")
        segments, _ = model.transcribe(audio_path, **default_options)
        text = " ".join(segment.text for segment in segments if segment.text.strip())
        transcripts.append(text)
    return transcripts


def _transcribe_with_funasr(
    audio_paths: Iterable[str],
    *,
    load_options: Optional[Dict[str, object]] = None,
    generate_options: Optional[Dict[str, object]] = None,
) -> List[str]:
    load_options = dict(load_options or {})
    model_dir = load_options.pop("model_dir", load_options.pop("model", "iic/SenseVoiceSmall"))
    funasr = load_funasr(model_dir=model_dir, **load_options)

    from funasr.utils.postprocess_utils import rich_transcription_postprocess

    default_generate = {
        "cache": {},
        "language": "auto",
        "use_itn": True,
        "batch_size_s": 60,
        "merge_vad": True,
        "merge_length_s": 15,
    }
    if generate_options:
        default_generate.update(generate_options)

    transcripts: List[str] = []
    paths = list(audio_paths)
    for idx, audio_path in enumerate(tqdm(paths, desc="Transcribing (funasr)"), start=1):
        print(f"正在转换第{idx}个音频... {os.path.basename(audio_path)}")
        generate_kwargs = dict(default_generate)
        if "cache" in generate_kwargs and isinstance(generate_kwargs["cache"], dict):
            generate_kwargs["cache"] = dict(generate_kwargs["cache"])
        else:
            generate_kwargs["cache"] = {}
        result = funasr.generate(input=audio_path, **generate_kwargs)
        if result:
            text = rich_transcription_postprocess(result[0]["text"])
        else:
            text = ""
        transcripts.append(text)
    return transcripts



def _write_transcript(text_save_path: str, title: str, content: str):
    os.makedirs(text_save_path, exist_ok=True)
    output_path = os.path.join(text_save_path, f"{title}.txt")
    with open(output_path, "a", encoding="utf-8") as file_obj:
        lines = [line.strip() for line in content.split("。") if line.strip()]
        for line in lines:
            file_obj.write(line + "。\r\n")
    return output_path


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def run_speech_to_text(
    title: str,
    audio_split_folder: str,
    text_save_path: str,
    *,
    engine: str = "whisper",
    engine_kwargs: Optional[Dict[str, Dict[str, object]]] = None,
):
    audio_paths = _collect_audio_paths(audio_split_folder)
    if not audio_paths:
        raise ValueError("未找到可用的音频文件。")

    print("正在转换文本...")
    engine_kwargs = engine_kwargs or {}
    if engine == "funasr":
        transcripts = _transcribe_with_funasr(
            audio_paths,
            load_options=engine_kwargs.get("load_options"),
            generate_options=engine_kwargs.get("generate_options"),
        )
    elif engine == "whisper":
        transcripts = _transcribe_with_whisper(
            audio_paths,
            load_options=engine_kwargs.get("load_options"),
            transcribe_options=engine_kwargs.get("transcribe_options"),
        )
    else:
        raise ValueError(f"未知的语音识别引擎：{engine}")

    combined = "\n".join(text for text in transcripts if text)
    print(combined)
    punctuation_count = sum(combined.count(mark) for mark in (",", "，", "。", ".", "！", "？"))
    if punctuation_count < 3:
        raise ValueError("音频转换文本失败！")

    _write_transcript(text_save_path, title, combined)
    return combined
