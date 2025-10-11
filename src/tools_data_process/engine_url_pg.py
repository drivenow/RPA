import os
import sys
import json
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse
from dotenv import load_dotenv

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import AsyncOpenAI
import psycopg2
from psycopg2 import sql
import pandas as pd
from tools_data_process.utils_format_text import parse_json_markdown,format_folder_name
from tools_data_process.utils_path import get_root_media_save_path, get_project_root


class PostgresEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)  # 首次创建实例
        return cls._instance  # 始终返回同一个实例

    def __init__(self):
        # 连接数据库
        self.conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="ybsDW246401.",
            host="localhost",
            port="5432"
        )
        self.cursor = self.conn.cursor()

    def insert_data(self, query, data):
        try:
            # 执行插入操作
            self.cursor.execute(query, data)
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            print(f"Error inserting chunk: {e}")
            self.conn.rollback()
            return 0

    def select_data(self, query):
        try:
            # 执行查询操作
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error seleting data: {e}")
            self.conn.rollback()
            return None

    def retrieve_vector(self, query_embedding, source):
        try:
            # 调用PostgreSQL函数
            self.cursor.execute(
                """
                SELECT * FROM match_site_pages(
                    query_embedding => %s::vector,
                    match_count => %s,
                    filter := '{"source": "ai.pydantic.dev"}'::jsonb
                )
                """,
                (query_embedding, 5)
            )

            # 获取结果（假设返回多行）
            result = self.cursor.fetchall()
            # 将result转换为结构化输出
            result = [
                dict(zip(['id', 'url', 'chunk_number', 'title', 'summary', 'content', 'metadata', 'similarity'], row))
                for row in result]
            print(f"检索到 {len(result)} 条记录")
            # 提交事务
            self.conn.commit()
            return result

        except psycopg2.DatabaseError as e:
            self.conn.rollback()
            print(f"执行失败：{e}")

    def __del__(self):
        # 关闭数据库连接
        self.cursor.close()
        self.conn.close()


postgres_engine = PostgresEngine()

load_dotenv()

# os.environ['OPENAI_API_KEY'] = 'sk-CJpKFYcAMJYlKpn9721bD96f4aFc443b91D36aA0C2217a92'
# os.environ['OPENAI_BASE_URL'] = 'http://192.168.1.2:11434/v1'
# os.environ["LLM_MODEL"] = "qwen2.5:14b"
os.environ['OPENAI_API_KEY'] = 'sk-CJpKFYcAMJYlKpn9721bD96f4aFc443b91D36aA0C2217a92'
os.environ['OPENAI_BASE_URL'] = 'https://api.ai-yyds.com/v1'
os.environ["LLM_MODEL"] = "gpt-4o-mini"
os.environ['OPENAI_BASE_URL'] = "https://api.siliconflow.cn/v1"
os.environ['OPENAI_API_KEY'] = "sk-kcprjafyronffotrpxxovupsxzqolveqkypbmubjsopdbxec"
os.environ["LLM_MODEL"] = "Pro/deepseek-ai/DeepSeek-V3"
# os.environ['OPENAI_BASE_URL'] = "https://api.deepseek.com"
# os.environ['OPENAI_API_KEY'] = "sk-eb7b2844c60a4c88918a325417ac81f7"
# model_name = "deepseek-chat"  # deepseek-reasoner

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))


@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]


def chunk_text(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks, respecting code blocks and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + chunk_size

        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind('```')
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block

        # If no code block, try to break at a paragraph
        elif '\n\n' in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind('\n\n')
            if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_break

        # If no paragraph break, try to break at a sentence
        elif '. ' in chunk:
            # Find the last sentence break
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1

        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position for next chunk
        start = max(start + 1, end)

    return chunks


async def get_title_and_summary(chunk: str, url: str) -> Dict[str, str]:
    """Extract title and summary using GPT-4."""
    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return a JSON object with 'title' and 'summary' keys.
    For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
    For the summary: Create a concise summary of the main points in this chunk.
    Keep both title and summary concise but informative. 
    An example is:
    {"title": "a story about how to use an embedding feature", "summary": "This article describes how to use a new feature in a particular software application."}
    Another example is:
    {"title": 基于知识图谱的实体识别, "summary": "这段内容探讨了如何利用知识图谱进行实体识别，包括构建知识图谱、实体识别的基本方法以及知识图谱在实体识别中的具体应用和优势。"}
    """
    try:
        response = await openai_client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"URL: {url}\n\nContent:\n{chunk[:1000]}..."}
                # Send first 1000 chars for context
            ],
            # response_format={"type": "json_object"},
            stream=False
        )
        # print(chunk)
        # print(111, response.choices[0].message.content)
        result = parse_json_markdown(response.choices[0].message.content)
        # print(222, result)
        return result
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(f"Error getting title and summary: {e}")
        return {"title": "Error processing title", "summary": "Error processing summary"}


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from OpenAI."""
    if False:
        try:
            response = await openai_client.embeddings.create(
                model="text-embedding-3-small",  # 长度1536
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0] * 1536  # Return zero vector on error
    else:
        try:
            from tools_ai.text_embedding import setup_embedding_model
            import numpy as np
            retrieve_model, rerank_model = setup_embedding_model()
            embedding = retrieve_model.encode(text)
            return list(embedding.astype(float))
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0] * 1024  # Return zero vector on error


async def process_chunk(chunk: str, chunk_number: int, topic_keyword: str, url: str) -> ProcessedChunk:
    """Process a single chunk of text."""
    # Get title and summary
    extracted = await get_title_and_summary(chunk, url)
    # Get embedding
    embedding = await get_embedding(chunk)

    # Create metadata
    metadata = {
        "source": topic_keyword,
        "chunk_size": len(chunk),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "url_path": urlparse(url).path
    }

    return ProcessedChunk(
        url=url,
        chunk_number=chunk_number,
        title=extracted['title'],
        summary=extracted['summary'],
        content=chunk,  # Store the original chunk content
        metadata=metadata,
        embedding=embedding
    )


async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into Supabase."""
    # 插入数据的 SQL 语句
    query = sql.SQL("""
               INSERT INTO site_pages (
                   url, chunk_number, title, summary, content, metadata, embedding
               ) VALUES (
                   %s, %s, %s, %s, %s, %s, %s
               )
           """)

    # 数据参数
    data = (
        chunk.url,
        chunk.chunk_number,
        chunk.title,
        chunk.summary,
        chunk.content,
        json.dumps(chunk.metadata),
        chunk.embedding
    )
    rowcount = postgres_engine.insert_data(query, data)
    print(f"Inserted chunk {chunk.chunk_number} for {chunk.url} {rowcount}")
    return rowcount  # 返回插入的行数


async def process_and_store_document(topic_keyword: str, url: str, markdown: str):
    """Process a document and store its chunks in parallel."""
    # Split into chunks
    chunks = chunk_text(markdown)

    # Process chunks in parallel
    tasks = [
        process_chunk(chunk, i, topic_keyword, url)
        for i, chunk in enumerate(chunks)
    ]
    processed_chunks = await asyncio.gather(*tasks)

    # Store chunks in parallel
    insert_tasks = [
        insert_chunk(chunk)
        for chunk in processed_chunks if chunk.title != "Error processing title"
    ]
    await asyncio.gather(*insert_tasks)


async def url_to_sql_vector(topic_keyword: str, topic_urls: List[str], topic_titles: List[str], max_concurrent: int = 5,
                            save_markdown=True):
    """Crawl multiple URLs in parallel with a concurrency limit."""
    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        text_mode=False,
        use_persistent_context=True,
        user_data_dir=os.path.join(get_project_root(), "playwright_tools/chromedriver-win64/"),
        browser_type="chromium",
        proxy_config={
            "server": "http://127.0.0.1:7897"
        },
        # cookies=new_cookies,
        verbose=True
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Create the crawler instance
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_url(url: str, title: str):
            voice_dir, text_save_path = get_root_media_save_path("crawl4ai", format_folder_name(topic_keyword))
            os.makedirs(text_save_path, exist_ok=True)
            file_name = format_folder_name(title) + ".txt"
            if os.path.exists(os.path.join(text_save_path, file_name)) and os.path.getsize(
                    os.path.join(text_save_path, file_name)) > 0:
                print(f"Skip {title} .")
                return
            async with semaphore:
                try:
                    result = await crawler.arun(
                        url=url,
                        config=crawl_config,
                        session_id="session1"
                    )
                    if result.success:
                        print(f"Successfully crawled: {url}")
                        if save_markdown:
                            with open(os.path.join(text_save_path, file_name), "w", encoding="utf-8") as f:
                                f.write(result.markdown.raw_markdown)
                        await process_and_store_document(topic_keyword, url, result.markdown.raw_markdown)
                    else:
                        print(f"Failed: {url} - Error: {result.error_message}")
                except  Exception as e:
                    print(f"ERROR: Failed: {title} - {url}- Error: {e}")

        # Process all URLs in parallel with limited concurrency
        await asyncio.gather(*[process_url(url, title) for url, title in zip(topic_urls, topic_titles)])
    finally:
        await crawler.close()


if __name__ == "__main__":
    from tools_browser.fetch_detail_batch_urls import get_batch_urls

    # urls, titles, keywords = get_batch_urls(sitemap_url="https://ai.pydantic.dev/sitemap.xml")
    # urls, titles, keywords = get_batch_urls(sitemap_url="gkdata")
    batch_urls_base_dir = get_root_media_save_path("homepage_url", None)[1]
    weixin_df = pd.read_excel(os.path.join(batch_urls_base_dir, r"home_page_url.xlsx"))
    for homepage_name in weixin_df["主页名称"]:
        batch_urls, batch_titles, keywords = get_batch_urls(sitemap_url=f"weixin_{homepage_name}")
        print(batch_urls, batch_titles, keywords)
        asyncio.run(url_to_sql_vector(keywords, batch_urls, batch_titles, max_concurrent=2,
                                      save_markdown=True))

    # postgres_engine.query_vector([0.9] * 1024, "ai.pydantic.dev")
