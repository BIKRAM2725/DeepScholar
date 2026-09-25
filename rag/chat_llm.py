from rag_prompts import CONVERSATION_SYSTEM
from rag_llm import client, MODEL, validate_query


def build_context(history):
    blocks = []

    for i, msg in enumerate(history, 1):
        block = f"""Turn {i}:
Content: {msg}
"""
        blocks.append(block)

    return "\n\n".join(blocks)


def generate_chat(query, history):
    history = history or []

    # Validate only the first message; follow-ups like "explain more" are fine
    if not history and not validate_query(query):
        msg = (
            "Your query does not appear to be a scientific question. "
            "Please ask something that can be answered using scientific "
            "literature or research."
        )
        print(f"[Orchestrator] Query rejected: {query}")
        return msg

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

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.6,
            top_p=0.95,
            max_tokens=4096,
            stream=True
        )

        result = []

        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
                result.append(chunk.choices[0].delta.content)

        return "".join(result)

    except Exception as e:
        print(f"Error generating chat response: {type(e).__name__}: {e}")
        return "Sorry, something went wrong while generating the answer."