import os
import sys

# 将 bili2text 目录加入路径，以解决内部模块相对导入报错问题（如 `from downBili import ...`）
sys.path.append(os.path.join(os.path.dirname(__file__), "bili2text"))

from bili2text.main import BiliSpeechPipeline, VideoJob


def _resolve_transcript_path(text_dir: str, title: str) -> str:
    """Mirror speech2text._write_transcript() naming so MCP returns the real file path."""
    safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title)
    return os.path.join(text_dir, f"{safe_title.lower()}.txt")

def extract_text_from_video(url: str, title: str, media_type: str = None) -> dict:
    """
    最小提取调用 Demo，适合用于封装 MCP 等服务。
    参数:
        url: 视频 URL（例如 B 站或 YouTube 链接）。
        title: 视频标题（将用作保存的文件名）。
        media_type: 平台类型，不传则自动根据 url 解析（'bili' 或是 'youtube' 等）。
    返回:
        字典包含执行状态、耗时、错误信息及文本保存路径（可通过路径读取 txt）。
    """
    
    if media_type is None:
        if "bilibili.com" in url:
            media_type = "bili"
        elif "youtube.com" in url or "youtu.be" in url:
            media_type = "youtube_browser"
        elif "douyin.com" in url or "iesdouyin.com" in url:
            media_type = "douyin"
        else:
            media_type = "bili" # 默认 fallback
    
    # 初始化处理管线
    # 内部已经去除了对数据库引擎的强制依赖
    pipeline = BiliSpeechPipeline()
    
    # 构造任务对象
    job = VideoJob(
        media_type=media_type, 
        url=url,
        title=title, 
        sheet_name='mcp_service',  # 存放输出的子分类文件夹名
        video_type=media_type
    )

    print(f"🚀 开始提取任务: [{title}]({url})")
    
    # 执行处理：包括下载视频、分离音频、音频切割、SiliconFlow API 转文字
    result = pipeline.process_job(job, skip_existing=True)

    # 包装返回结果
    response = {
        "success": result.succeeded,
        "skipped": result.skipped,
        "elapsed_seconds": round(result.elapsed, 2),
        "message": result.message or "Success",
    }

    if result.succeeded or result.skipped:
        # 成功或跳过时，可以计算出最终文本的保存路径
        from src.tools_data_process.utils_path import get_root_media_save_path
        _, text_path, _ = pipeline.ensure_paths(job)
        final_txt_file = _resolve_transcript_path(text_path, job.title)
        response["text_file_path"] = final_txt_file
        
        # 如果需要直接返回提取出的文本：
        if os.path.exists(final_txt_file):
            with open(final_txt_file, "r", encoding="utf-8") as f:
                response["content"] = f.read()

    return response

if __name__ == "__main__":
    # YouTube 视频测试
    test_url = "https://www.youtube.com/watch?v=NUeluCHIf8A"
    test_title = "中美翻脸了，终于等到一个绝好的加仓机会了"


    res = extract_text_from_video(test_url, test_title)
    
    print("\n--- 执行结果 ---")
    for k, v in res.items():
        if k == "content":
            print(f"content: \n{v[:150]}... (省略)")
        else:
            print(f"{k}: {v}")
