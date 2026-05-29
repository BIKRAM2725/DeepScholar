# search_results.py

import os
from dotenv import load_dotenv
from tavily import TavilyClient
try:
    from serpapi import GoogleSearch
except ImportError:
    # Newer serpapi versions use different import
    try:
        from serpapi.google_search import GoogleSearch
    except ImportError:
        GoogleSearch = None
import cohere

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

DOMAINS = [
    "scholar.google.com",
    "ncbi.nlm.nih.gov/pmc",
    "pubmed.ncbi.nlm.nih.gov",
    "arxiv.org",
    "sciencedirect.com",
    "webofscience.com",
    "researchgate.net",
    "ieeexplore.ieee.org",
    "jstor.org",
    "biorxiv.org",
    "scopus.com",
    "pubs.acs.org",
    "peerj.com",
    "plos.org",
    "dl.acm.org",
    "nature.com",
    "medrxiv.org",
    "ssrn.com",
    "link.springer.com",
    "europepmc.org",
    "onlinelibrary.wiley.com"
]

co = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None


def _tavily_search(query: str, k: int = 10):
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)

        res = client.search(
            query=query,
            max_results=k,
            include_domains=DOMAINS
        )

        results = []
        for r in res.get("results", []):
            results.append({
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
                "source": "tavily"
            })

        return results
    except Exception:
        return []


def _scholar_search(query: str, k: int = 10):
    if not GoogleSearch:
        print("[Warning] SerpAPI GoogleSearch not available, skipping scholar search")
        return []
    
    try:
        params = {
            "engine": "google_scholar",
            "q": query,
            "num": k,
            "api_key": SERP_API_KEY
        }

        search = GoogleSearch(params)
        data = search.get_dict()

        results = []
        for r in data.get("organic_results", []):
            results.append({
                "title": r.get("title"),
                "url": r.get("link"),
                "content": r.get("snippet"),
                "source": "scholar"
            })

        return results
    except Exception as e:
        print(f"[Warning] Scholar search failed: {e}")
        return []


def _rerank(query: str, docs: list, top_k: int = 5):
    if not co or not docs:
        return docs[:top_k]

    texts = [d["content"] or "" for d in docs]

    try:
        res = co.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=texts,
            top_n=top_k
        )

        ranked = []
        for r in res.results:
            ranked.append(docs[r.index])

        return ranked
    except Exception:
        return docs[:top_k]


def search_results(query: str, k: int = 10):

    results = []

    if TAVILY_API_KEY:
        results.extend(_tavily_search(query, k))

    if SERP_API_KEY and GoogleSearch:
        results.extend(_scholar_search(query, k))
    elif SERP_API_KEY and not GoogleSearch:
        print("[Warning] SERP_API_KEY set but GoogleSearch not available")

    if not results:
        return None

    reranked = _rerank(query, results, top_k=5)

    for i, r in enumerate(reranked, 1):
        print(f"\n{i}. {r['title']}")
        print(f"URL: {r['url']}")
        print(f"Source: {r['source']}")
        print(f"Snippet: {r['content'][:200]}")

    return reranked
if __name__ == "__main__":
    sample_query = "Do cows have friends?"

    print(f"\nRunning sample search for: {sample_query}\n")

    results = search_results(sample_query)

    if not results:
        print("\nNo results found.")