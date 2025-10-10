from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent, ModelRetry, RunContext
from openai import OpenAI
from typing import List
from model_utils import model
from tools_data_process.engine_url_pg import PostgresEngine
from tools_ai.text_embedding import setup_embedding_model

load_dotenv()

logfire.configure(send_to_logfire='if-token-present')

postgres_engine = PostgresEngine()


@dataclass
class PydanticAIDeps:
    supabase: PostgresEngine
    openai_client: OpenAI


system_prompt = """
You are an expert at Pydantic AI - a Python AI agent framework that you have access to all the documentation to,
including examples, an API reference, and other resources to help you build Pydantic AI agents.

Your only job is to assist with this and you don't answer other questions besides describing what you are able to do.

Don't ask the user before taking an action, just do it. Always make sure you look at the documentation with the provided tools before answering the user's question unless you have already.

When you first look at the documentation, always start with RAG.
Then also always check the list of available documentation pages and retrieve the content of page(s) if it'll help.

Always let the user know when you didn't find the answer in the documentation or the right URL - be honest.

Please answer in chinese.
"""

pydantic_ai_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PydanticAIDeps,
    retries=2
)


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        retrieve_model, rerank_model = setup_embedding_model()
        embedding = retrieve_model.encode_queries(text)
        return list(embedding.astype(float))
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1024  # Return zero vector on error


@pydantic_ai_expert.tool
async def retrieve_relevant_documentation(ctx: RunContext[PydanticAIDeps], user_query: str) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query

    Returns:
        A formatted string containing the top 5 most relevant documentation chunks
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(user_query)

        # Query Supabase for relevant documents
        result = ctx.deps.supabase.retrieve_vector(query_embedding, "ai.pydantic.dev")

        if not result:
            return "No relevant documentation found."

        # Format the results
        formatted_chunks = []
        for doc in result:
            chunk_text = f"""
# {doc['title']}

{doc['content']}
"""
            formatted_chunks.append(chunk_text)

        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"Error retrieving documentation: {e}")
        return f"Error retrieving documentation: {str(e)}"


@pydantic_ai_expert.tool
async def get_page_content(ctx: RunContext[PydanticAIDeps], url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.

    Args:
        ctx: The context including the Supabase client
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    try:
        # Query Supabase for all chunks of this URL, ordered by chunk_number
        result = ctx.deps.supabase \
            .select_data(
            'select title, content, chunk_number from site_pages where url = {} and metadata @> {} order by chunk_number'.format(
                url, 'pydantic_ai_docs'))
        # 将result变成结构化列表
        result = [dict(zip(['title', 'content', 'chunk_number'], row)) for row in result]
        if not result:
            return f"No content found for URL: {url}"

        # Format the page with its title and all chunks
        page_title = result[0]['title'].split(' - ')[0]  # Get the main title
        formatted_content = [f"# {page_title}\n"]

        for chunk in result:
            formatted_content.append(chunk['content'])

        # Join everything together
        return "\n\n".join(formatted_content)

    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"


if __name__ == '__main__':
    # Prepare dependencies
    deps = PydanticAIDeps(
        supabase=postgres_engine,
        openai_client=model
    )
    result = pydantic_ai_expert.run_sync(
        "给我一个pydantic ai的demo",
        deps=deps,
        message_history=[],  # pass entire conversation so far
    )
    print(result)
