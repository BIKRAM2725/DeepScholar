import os
from openai import OpenAI
from rag_prompts import CONVERSATION_SYSTEM
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY")
)
from rag_llm import validate_query

def build_context(history):
    blocks = []

    for i, msg in enumerate(history, 1):
        block = f"""Turn {i}:
Content: {msg}
"""
        blocks.append(block)

    return "\n\n".join(blocks)


def generate_chat(query, history):
    
    if not validate_query(query):
        msg = (
            "Your query does not appear to be a scientific question. "
            "Please ask something that can be answered using scientific "
            "literature or research."
        )
        print(f"[Orchestrator] Query rejected: {query}")
        return msg
    if not history:
        history = []
    context = build_context(history)

    messages = [
        {
            "role": "system",
            "content": CONVERSATION_SYSTEM
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

    return "".join(result)