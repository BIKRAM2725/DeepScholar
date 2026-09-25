from rag_prompts import RAG_SYSTEM
from rag_llm import client, MODEL

MAX_CONTENT_CHARS = 1500  # keep each source short so the prompt stays focused


def clean_results(results):
    """Drop empty sources and remove duplicate URLs."""
    cleaned = []
    seen = set()

    for r in results or []:
        content = (r.get("content") or "").strip()
        url = (r.get("url") or "").strip()

        if not content or not url or url in seen:
            continue

        seen.add(url)
        cleaned.append({
            "title": (r.get("title") or "Untitled").strip(),
            "content": content[:MAX_CONTENT_CHARS],
            "url": url,
            "source": r.get("source", ""),
        })

    return cleaned


def build_context(results):
    """Number each source [1], [2], ... so citations match the Sources list."""
    blocks = []

    for i, r in enumerate(results, 1):
        blocks.append(
            f"[{i}]\n"
            f"Title: {r['title']}\n"
            f"Content: {r['content']}\n"
            f"URL: {r['url']}\n"
            f"Source: {r['source']}"
        )

    return "\n\n".join(blocks)


def generate_answer(query, results):
    sources = clean_results(results)

    if not sources:
        return {
            "response": "I don't know",
            "results": "",
            "sources": [],
        }

    context = build_context(sources)

    messages = [
        {"role": "system", "content": RAG_SYSTEM},
        {
            "role": "user",
            "content": (
                f"<context>\n{context}\n</context>\n\n"
                f"Question: {query}"
            ),
        },
    ]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=2048,
        )

        answer = (completion.choices[0].message.content or "").strip()

        if not answer:
            answer = "I don't know"

        return {
            "response": answer,
            "results": context,
            "sources": sources,
        }

    except Exception as e:
        print(f"Error generating answer: {type(e).__name__}: {e}")
        return {
            "response": "Sorry, something went wrong while generating the answer.",
            "results": context,
            "sources": sources,
        }