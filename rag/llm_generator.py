import os
from openai import OpenAI
from rag_prompts import RAG_SYSTEM

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY")
)


def build_context(results):
    blocks = []

    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")
        url = r.get("url", "")
        source = r.get("source", "")

        block = f"""
Title: {title}
Content: {content}
URL: {url}
Source: {source}
"""
        blocks.append(block)

    return "\n\n".join(blocks)


def generate_answer(query, results):
    context = build_context(results)

    messages = [
        {
            "role": "system",
            "content": RAG_SYSTEM
        },
        {
            "role": "user",
            "content": f"""
Context:
{context}

Question:
{query}
"""
        }
    ]

    completion = client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-ultra-253b-v1",
        messages=messages,
        temperature=0.6,
        top_p=0.95,
        max_tokens=4096,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True
    )

    result = []

    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            result.append(chunk.choices[0].delta.content)

    return {
        "response": "".join(result),
        "results": context
    }