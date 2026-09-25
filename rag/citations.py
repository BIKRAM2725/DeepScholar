
import re
import time
from difflib import SequenceMatcher

import requests

TIMEOUT = 6
MATCH_THRESHOLD = 0.72
_CACHE: dict = {}


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()


def _similar(a, b):
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _authors_str(names):
    """names: list of 'F. Last' strings -> IEEE-style author list."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) <= 3:
        return ", ".join(names[:-1]) + " and " + names[-1]
    return f"{names[0]} et al."


def _initial_last(given, family):
    given, family = (given or "").strip(), (family or "").strip()
    if not family:
        return given or None
    return f"{given[0]}. {family}" if given else family


def _crossref(title):
    try:
        r = requests.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": title, "rows": 3},
            timeout=TIMEOUT,
            headers={"User-Agent": "deep-scholar/1.0 (mailto:dev@example.com)"},
        )
        r.raise_for_status()
        for item in r.json().get("message", {}).get("items", []):
            cand = (item.get("title") or [""])[0]
            if _similar(title, cand) < MATCH_THRESHOLD:
                continue
            authors = [
                _initial_last(a.get("given"), a.get("family"))
                for a in item.get("author", []) if a.get("family")
            ]
            year = None
            for key in ("published-print", "published-online", "issued"):
                parts = item.get(key, {}).get("date-parts", [[None]])
                if parts and parts[0] and parts[0][0]:
                    year = parts[0][0]
                    break
            venue = (item.get("container-title") or [""])[0]
            return {
                "title": cand or title,
                "authors": [a for a in authors if a],
                "year": year,
                "venue": venue,
                "doi": item.get("DOI"),
            }
    except Exception as e:
        print(f"[Citations] Crossref lookup failed: {type(e).__name__}: {e}")
    return None


def _semantic_scholar(title):
    try:
        r = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": title, "limit": 3,
                    "fields": "title,year,venue,authors,externalIds"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        for item in r.json().get("data", []):
            cand = item.get("title") or ""
            if _similar(title, cand) < MATCH_THRESHOLD:
                continue
            authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]
            doi = (item.get("externalIds") or {}).get("DOI")
            return {
                "title": cand or title,
                "authors": authors,
                "year": item.get("year"),
                "venue": item.get("venue") or "",
                "doi": doi,
            }
    except Exception as e:
        print(f"[Citations] Semantic Scholar lookup failed: {type(e).__name__}: {e}")
    return None


def lookup(title):
    """Return {authors, year, venue, doi} or None. Cached per process."""
    key = _norm(title)
    if not key:
        return None
    if key in _CACHE:
        return _CACHE[key]

    hit = _crossref(title)
    if not hit or not hit.get("authors"):
        time.sleep(0.15)   # be polite to the free Semantic Scholar tier
        hit = _semantic_scholar(title) or hit

    _CACHE[key] = hit
    return hit


def format_ieee(source, accessed_date):
    """
    source: {"title": str, "url": str, "source": str (venue fallback)}
    Returns a formatted IEEE reference string. Uses real authors/year/venue/DOI
    when a confident match was found; otherwise falls back to a title + URL
    entry, exactly as before, so nothing is ever invented.
    """
    # Many web results carry the venue in the title ("Title | Journal Name");
    # strip that before querying Crossref/Semantic Scholar so the lookup
    # matches on the paper's actual title, not the combined string.
    parts = [p.strip() for p in source["title"].split(" | ") if p.strip()]
    clean_title = (parts[0] if parts else source["title"]).rstrip(".,")
    fallback_venue = ", ".join(parts[1:]) or source.get("source") or ""

    hit = lookup(clean_title)

    if hit and hit.get("authors"):
        who = _authors_str(hit["authors"])
        title = hit["title"].rstrip(".,")
        venue = hit.get("venue") or fallback_venue
        year = f", {hit['year']}" if hit.get("year") else ""
        doi = f", doi: {hit['doi']}" if hit.get("doi") else ""
        venue_part = f" {venue}" if venue else ""
        return f"{who}, \u201c{title},\u201d{venue_part}{year}{doi}."

    # Fallback: no confident match, cite the retrieved web page honestly.
    venue_part = f" {fallback_venue}." if fallback_venue else ""
    return (f"\u201c{clean_title},\u201d{venue_part} Accessed: {accessed_date}. "
            f"[Online]. Available: {source['url']}")