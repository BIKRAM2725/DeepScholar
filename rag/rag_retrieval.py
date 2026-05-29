
from rag_embedding import embed_query

def retrieve(index,metadata,query: str, top_k: int = 5):

    print(f"\nQuery: {query}")

    q_vec = embed_query(query)

    scores, indices = index.search(q_vec, top_k)

    results = []

    print("\nFiltered Results:\n")

    for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):

        if idx < 0 or idx >= len(metadata):
            continue

        if score < 0.7:
            continue

        doc = metadata[idx]
        url = doc.get("url")

        if not url or "None" in url:
            continue

        title = doc.get("title")
        content = doc.get("content", "")[:150]

        print(f"{rank}. Score: {score:.4f}")
        print(f"Title: {title}")
        print(f"URL: {url}")
        print(f"Snippet: {content}...\n")

        results.append({
            "title": title,
            "content": doc.get("content"),
            "url": url,
            "score": float(score)
        })

    return results if results else None

