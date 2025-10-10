file_type = "record"
sheet_name = "树莓派"

def get_file_path(file_type, sheet_name):
    if file_type == "bili":
        if not sheet_name:
            raise ValueError("file_type为bili时, sheet_name参数不能为空")
        voice_slice_dir = f"X:\\RAG\\audio\\{sheet_name}\\"
        voice_dir = voice_slice_dir
        text_output_dir = rf"X:/RAG/rag_data/{sheet_name}"
    elif file_type == "crawl4ai":
        voice_dir = None
        text_output_dir = rf"X:/RAG/rag_data/{sheet_name}"
    elif file_type == "coputer_record":
        voice_dir = "C:\\Users\\fullmetal\\Documents\\录音\\SJL"
        text_output_dir = os.path.join(voice_dir, "outputs")
    elif file_type == "phone_record":
        voice_dir = "D:\\shenjl\\Maigc5\\sounds\\"
        text_output_dir = os.path.join(voice_dir, "outputs")
    else:
        raise ValueError("type参数错误：" + file_type)
    return voice_dir, text_output_dir
