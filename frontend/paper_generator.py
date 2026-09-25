import re
import time
from datetime import date

from rag_llm import client, MODEL
from rag_web import search_results
from llm_generator import clean_results
from paper_pdf import build_ieee_pdf

MAX_SOURCES = 15
SNIPPET_CHARS = 600

SYSTEM = """You are an academic writer drafting ONE section of an IEEE-style research paper.
Rules:
- Formal, precise, third-person academic tone.
- Plain text only: no markdown, no headings, no bullet points, no bold.
- Separate paragraphs with a blank line.
- Cite ONLY the numbered sources provided, written like [1] or [2][3]. Never invent a citation number, author, statistic or result.
- State only facts supported by the provided sources or the author's notes. If evidence is missing, write more generally instead of making up specifics.
- Output only the section text."""


# ---------- LLM helper with retry (handles empty replies) ----------
def _llm(user_prompt, max_tokens=3000, retries=2):
    for attempt in range(retries + 1):
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
                reasoning_effort="low",   # remove this line if your client rejects it
            )
            text = (completion.choices[0].message.content or "").strip()
            if text:
                return text
            print(f"[Paper] empty response, retry {attempt + 1}")
        except Exception as e:
            print(f"[Paper] LLM error: {type(e).__name__}: {e}")
        time.sleep(1.5)
    return ""


# ---------- source collection ----------
def collect_sources(topic):
    queries = [
        topic,
        f"{topic} review",
        f"{topic} recent advances",
        f"{topic} methods dataset",
    ]
    raw = []
    for q in queries:
        try:
            raw.extend(search_results(q) or [])
        except Exception as e:
            print(f"[Paper] search failed for '{q}': {e}")
    return clean_results(raw)[:MAX_SOURCES]


def _sources_block(sources):
    return "\n\n".join(
        f"[{i}] {s['title']}\n{s['content'][:SNIPPET_CHARS]}"
        for i, s in enumerate(sources, 1)
    )


# ---------- text cleanup ----------
def _clean_text(text, n_sources):
    text = re.sub(r"[*#`]", "", text)
    text = re.sub(r"(?m)^\s*[-•]\s+", "", text)

    def fix(m):
        return m.group(0) if int(m.group(1)) <= n_sources else ""

    text = re.sub(r"\[(\d+)\]", fix, text)          # drop invalid citations
    return text.strip()


def _paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# ---------- section plan ----------
def _plan(has_notes):
    if has_notes:
        method = ("Methodology",
                  "Describe the methodology using ONLY the author's notes "
                  "(model, dataset, training setup, metrics). Do not add "
                  "details that are not in the notes. About 350 words.")
        results = ("Results and Discussion",
                   "Report results using ONLY numbers given in the author's "
                   "notes. Never invent a metric. Discuss implications and "
                   "compare qualitatively with the cited work. About 400 words.")
    else:
        method = ("Review Methodology",
                  "Explain how the literature was gathered (sources retrieved "
                  "through web and scholarly search for this topic and screened "
                  "for relevance) and how it is organised for analysis. Do not "
                  "claim any original experiment. About 250 words.")
        results = ("Discussion",
                   "Synthesise the findings across sources: common approaches, "
                   "reported performance only where a source states it, gaps "
                   "and open challenges. No original experiments. About 450 words.")

    return [
        ("introduction", "Introduction",
         "Motivate the topic, state the problem, and outline the paper's "
         "contribution and structure. About 400 words."),
        ("related", "Related Work",
         "Survey and compare prior work from the sources, grouped by theme. "
         "About 550 words."),
        ("method", *method),
        ("results", *results),
        ("conclusion", "Conclusion",
         "Summarise the key points and suggest future work. About 180 words."),
    ]


# ---------- main entry ----------
def generate_paper_pdf(topic, notes="", authors="Author Name"):
    notes = (notes or "").strip()
    sources = collect_sources(topic)
    if not sources:
        raise ValueError("No sources found for this topic.")

    src = _sources_block(sources)
    done = {}            # key -> cleaned text
    sections = []        # (heading, [paragraphs]) in paper order

    for key, heading, instruction in _plan(bool(notes)):
        prior = "\n\n".join(f"{k.upper()}: {v[:600]}" for k, v in done.items())
        prompt = (
            f"Paper topic: {topic}\n"
            f"Section to write: {heading}\n"
            f"Instruction: {instruction}\n\n"
            f"Author's notes (may be empty):\n{notes or '(none)'}\n\n"
            f"Sources:\n{src}\n\n"
            f"Previously written sections (for consistency, do not repeat):\n"
            f"{prior or '(none yet)'}"
        )
        print(f"[Paper] writing: {heading}")
        text = _clean_text(_llm(prompt), len(sources))
        if not text:
            text = "This section could not be generated. Please retry."
        done[key] = text
        sections.append((heading, _paragraphs(text)))

    # Abstract, keywords and title are written last, from the finished body
    body = "\n\n".join(f"{k.upper()}: {v[:900]}" for k, v in done.items())

    print("[Paper] writing: abstract")
    abstract = _clean_text(_llm(
        f"Write a single-paragraph abstract (150-200 words) for this paper on "
        f"'{topic}'. No citations.\n\nPaper content:\n{body}\n\n"
        f"Author's notes:\n{notes or '(none)'}", max_tokens=1500), 0)

    keywords = _clean_text(_llm(
        f"Give 5-6 comma-separated index terms for a paper on '{topic}'. "
        f"Output only the terms.", max_tokens=300), 0)

    title = _clean_text(_llm(
        f"Write one concise IEEE-style paper title (max 14 words) for a paper "
        f"on '{topic}'. Output only the title, no quotes.", max_tokens=300), 0)

    today = date.today().strftime("%b. %d, %Y")
    references = [
        f"{s['title']}, {s['source'] or 'Web'}. [Online]. "
        f"Available: {s['url']} (accessed {today})."
        for s in sources
    ]

    return build_ieee_pdf(
        title=title or topic.title(),
        authors=authors,
        abstract=abstract or "Abstract could not be generated.",
        keywords=keywords or topic,
        sections=sections,
        references=references,
    )