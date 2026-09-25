import re
import time
from datetime import date
from urllib.parse import urlparse

from rag_llm import client, MODEL
from rag_web import search_results
from paper_pdf import (
    bar_chart, build_ieee_pdf, flowchart, image_flowable, metrics_table,
)

MAX_SOURCES = 12
SNIPPET_CHARS = 500
MAX_STEPS = 8

SYSTEM = """You are an academic writer drafting ONE section of an IEEE-style research paper.
Rules:
- Formal, precise academic tone; third person or passive voice.
- Plain text only: no markdown, no bullet points, no numbered lists, no bold, no tables.
- Separate paragraphs with a blank line.
- Cite ONLY the numbered sources provided, written like [1] or [1], [2]. Never invent a citation number, author, statistic, dataset or result.
- Use only facts supported by the provided sources, the author's notes, or the review facts. If evidence is missing, write more generally instead of making up specifics.
- Output only the section text. Do not repeat the section title.
- If subsections are requested, put each subsection title alone on a line that starts with "@@ " (for example "@@ Attention-Based Detectors"), followed by its paragraphs."""

_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.",
           "Jul.", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
_STOP = {"the", "and", "for", "with", "using", "based", "from", "into",
         "that", "this", "via", "over", "under"}

_DELAYS = [4, 12, 25]          # back-off (seconds) after an empty reply / 429
_use_reasoning = True          # switched off automatically if the API rejects it


# ---------------------------------------------------------------------------
# LLM helper: retries, back-off, reasoning-effort fallback
# ---------------------------------------------------------------------------
def _llm(user_prompt, max_tokens=4000):
    global _use_reasoning
    for attempt in range(len(_DELAYS) + 1):
        kwargs = dict(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": user_prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        if _use_reasoning:
            kwargs["reasoning_effort"] = "low"
        try:
            completion = client.chat.completions.create(**kwargs)
            text = (completion.choices[0].message.content or "").strip()
            if text:
                return text
            print(f"[Paper] empty response (attempt {attempt + 1})")
        except Exception as e:
            msg = str(e)
            print(f"[Paper] LLM error: {type(e).__name__}: {msg[:200]}")
            if _use_reasoning and "reasoning" in msg.lower():
                _use_reasoning = False        # this client/model rejects it
                continue
        if attempt < len(_DELAYS):
            time.sleep(_DELAYS[attempt])
    return ""


# ---------------------------------------------------------------------------
# Source collection + relevance screening (with real statistics)
# ---------------------------------------------------------------------------
def _keywords(topic):
    return [w for w in re.findall(r"[a-z0-9]+", topic.lower())
            if w not in _STOP and len(w) > 2]


def _relevant(source, words):
    if not words:
        return True
    text = (source["title"] + " " + source["content"]).lower()
    hits = sum(w in text for w in words)
    return hits >= min(len(words), max(2, len(words) // 2))


def collect_sources(topic):
    queries = [topic, f"{topic} review", f"{topic} recent advances",
               f"{topic} methods dataset"]
    raw = []
    for q in queries:
        try:
            raw.extend(search_results(q) or [])
        except Exception as e:
            print(f"[Paper] search failed for '{q}': {e}")

    seen, unique = set(), []
    for r in raw:
        url = (r.get("url") or "").strip()
        content = (r.get("content") or "").strip()
        if not url or len(content) < 80 or url in seen:
            continue
        seen.add(url)
        unique.append({
            "title": (r.get("title") or "Untitled").strip(),
            "content": content,
            "url": url,
            "source": (r.get("source") or "").strip(),
        })

    words = _keywords(topic)
    relevant = [s for s in unique if _relevant(s, words)]
    selected = relevant[:MAX_SOURCES]
    stats = {"queries": queries, "retrieved": len(raw), "unique": len(unique),
             "screened": len(relevant), "included": len(selected)}
    print(f"[Paper] sources: {stats['retrieved']} retrieved, "
          f"{stats['unique']} unique, {stats['screened']} relevant, "
          f"{stats['included']} used")
    return selected, stats


def _sources_block(sources):
    return "\n\n".join(
        f"[{i}] {s['title']}\n{s['content'][:SNIPPET_CHARS]}"
        for i, s in enumerate(sources, 1)
    )


# ---------------------------------------------------------------------------
# Text cleanup
# ---------------------------------------------------------------------------
def _fix_cites(text, n_sources):
    """Expand '[1, 2]' -> '[1], [2]' and drop citation numbers that don't exist."""
    def repl(m):
        nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
        good = [x for x in nums if 1 <= x <= n_sources]
        return ", ".join(f"[{x}]" for x in good)
    return re.sub(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]", repl, text)


def _trim_incomplete(text):
    """If the model was cut off mid-sentence, keep only complete sentences."""
    text = text.rstrip()
    if re.search(r"[.!?][\)\]\"']?$", text):
        return text
    cut = max(text.rfind(". "), text.rfind(".\n"))
    return text[:cut + 1] if cut > len(text) * 0.5 else text


def _clean_text(text, n_sources):
    text = re.sub(r"[*`]", "", text)
    text = re.sub(r"(?m)^\s*#+\s*", "", text)               # markdown headings
    text = re.sub(r"(?m)^\s*(?:[-\u2022]|\d{1,2}[.)])\s+", "", text)  # bullets
    text = _fix_cites(text, n_sources)
    text = re.sub(r"[ \t]+([.,;:])", r"\1", text)           # " ." after a drop
    text = re.sub(r"[ \t]{2,}", " ", text)
    return _trim_incomplete(text.strip())


def _trim_words(text, max_words):
    words = text.split()
    if len(words) <= max_words:
        return text
    cut = " ".join(words[:max_words])
    end = max(cut.rfind(". "), cut.rfind("."))
    return cut[:end + 1] if end > len(cut) * 0.6 else cut + "."


def _blocks(text):
    """Split section text into ('p', text) and ('sub', title) blocks."""
    blocks, buf = [], []

    def flush():
        if buf:
            blocks.append(("p", " ".join(buf).strip()))
            buf.clear()

    for line in text.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("@@"):
            flush()
            title = s[2:].strip(" :.")
            if title:
                blocks.append(("sub", title))
        else:
            buf.append(s)
    flush()
    return blocks


def _parse_keywords(raw, topic):
    parts = [re.sub(r"^\d+[.)]\s*", "", p).strip(" .;\n\"'")
             for p in re.split(r"[,;\n]", raw)]
    parts = [p for p in parts if p][:6] or [topic]
    return ", ".join(sorted(set(parts), key=str.lower))


# ---------------------------------------------------------------------------
# References (built by code from retrieved sources -> nothing hallucinated)
# ---------------------------------------------------------------------------
def _ieee_date(d):
    return f"{_MONTHS[d.month - 1]} {d.day}, {d.year}"


def _reference(s, accessed):
    parts = [p.strip() for p in s["title"].split(" | ") if p.strip()]
    title = (parts[0] if parts else "Untitled").rstrip(".,")
    venue = ", ".join(parts[1:]) or urlparse(s["url"]).netloc.replace("www.", "")
    return (f"\u201c{title},\u201d {venue}. Accessed: {accessed}. "
            f"[Online]. Available: {s['url']}")


# ---------------------------------------------------------------------------
# Section plan
# ---------------------------------------------------------------------------
def _plan(experiment):
    if experiment:
        intro = ("Motivate the topic, state the problem, and summarise the "
                 "author's contribution using ONLY the author's notes. Do not "
                 "claim results that are not in the notes. End with exactly "
                 "this roadmap: Section II reviews related work, Section III "
                 "describes the methodology, Section IV presents results and "
                 "discussion, and Section V concludes. About 400 words.")
        method = ("Methodology",
                  "Describe the methodology using ONLY the author's notes "
                  "(model, dataset, training setup, metrics). Do not add "
                  "details that are not in the notes. About 350 words.")
        results = ("Results and Discussion",
                   "Report results using ONLY numbers given in the author's "
                   "notes. Never invent a metric. Discuss implications and "
                   "compare qualitatively with the cited work. About 400 words.")
        concl = ("Summarise the key points from the notes and suggest future "
                 "work. About 180 words.")
    else:
        intro = ("Motivate the topic and state clearly that this paper is a "
                 "literature review. Do NOT claim a new model, dataset, "
                 "experiment or results. State the scope of the review. End "
                 "with exactly this roadmap: Section II covers related work, "
                 "Section III explains the review methodology, Section IV "
                 "discusses findings, gaps and challenges, and Section V "
                 "concludes. About 350 words.")
        method = ("Review Methodology",
                  "Describe how the literature was gathered and screened using "
                  "ONLY the review facts provided. Do not mention databases, "
                  "tools, manual reading or criteria that are not in the facts. "
                  "Do not claim any original experiment. About 250 words.")
        results = ("Discussion",
                   "Synthesise the findings across sources: common approaches, "
                   "reported performance only where a source states it, gaps "
                   "and open challenges. No original experiments. Use exactly "
                   "these subsections: @@ Key Findings, @@ Research Gaps, "
                   "@@ Open Challenges. About 450 words.")
        concl = ("Summarise the review's findings and future research "
                 "directions. Do NOT say experiments were conducted. "
                 "About 180 words.")

    return [
        ("introduction", "Introduction", intro),
        ("related", "Related Work",
         "Survey and compare prior work from the sources. Organise it into 3 "
         "or 4 themed subsections (use the @@ format). Describe only the cited "
         "studies; do not describe a system proposed by this paper unless the "
         "author's notes do. About 550 words."),
        ("method", *method),
        ("results", *results),
        ("conclusion", "Conclusion", concl),
    ]


# ---------------------------------------------------------------------------
# Figures and tables (only ever built from real data)
# ---------------------------------------------------------------------------
def _fmt(v):
    return f"{v:.4g}"


def _review_flow(stats):
    return [
        f"Records retrieved from\nsearch (n = {stats['retrieved']})",
        f"After duplicate removal\n(n = {stats['unique']})",
        f"After relevance screening\n(n = {stats['screened']})",
        f"Included in review\n(n = {stats['included']})",
    ]


def _build_figures(flow_steps, flow_caption, metrics, images):
    """Return ({'method': [...], 'results': [...]}, {'method': [...], ...})
    -> (blocks per section, mention-hints per section)."""
    blocks = {"method": [], "results": []}
    hints = {"method": [], "results": []}
    fig_no = tab_no = 0

    if flow_steps:
        fig_no += 1
        blocks["method"].append(
            ("fig", flowchart(flow_steps), f"Fig. {fig_no}. {flow_caption}"))
        hints["method"].append(f"Fig. {fig_no} (process diagram: {flow_caption})")

    if metrics:
        tab_no += 1
        rows = [["Metric", "Value"]] + [[k, _fmt(v)] for k, v in metrics.items()]
        label = f"TABLE {_ROMAN[tab_no - 1]}"
        blocks["results"].append(("table", rows, label, "Reported performance metrics"))
        hints["results"].append(f"{label} (reported performance metrics)")

        vals = list(metrics.values())
        vmax = (1.0 if all(0 <= v <= 1 for v in vals)
                else 100.0 if all(0 <= v <= 100 for v in vals) else None)
        if vmax:
            fig_no += 1
            blocks["results"].append(
                ("fig", bar_chart(metrics, vmax),
                 f"Fig. {fig_no}. Reported performance metrics."))
            hints["results"].append(f"Fig. {fig_no} (bar chart of the metrics)")

    for flowable, caption in images:
        fig_no += 1
        blocks["results"].append(("fig", flowable, f"Fig. {fig_no}. {caption}"))
        hints["results"].append(f"Fig. {fig_no} ({caption})")

    return blocks, hints


def _inject(blocks, extras):
    """Place figures/tables right after the section's first paragraph."""
    if not extras:
        return blocks
    first_p = next((i for i, b in enumerate(blocks) if b[0] == "p"), None)
    at = first_p + 1 if first_p is not None else len(blocks)
    return blocks[:at] + extras + blocks[at:]


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------
def generate_paper_pdf(topic, notes="", authors="Author Name", steps=None,
                       metrics=None, images=None, title=None):
    """
    steps   : list[str]   your own pipeline steps for the flowchart
    metrics : dict        your REAL results, e.g. {"Precision": 0.91}
    images  : list[dict]  [{"caption": str, "data": bytes}] your own figures
    title   : str         optional fixed title (otherwise the LLM proposes one)
    """
    notes = (notes or "").strip()
    metrics = {str(k): float(v) for k, v in (metrics or {}).items()}
    images = images or []
    experiment = bool(notes or metrics or images)

    # Validate pictures first so a bad upload fails fast (before any LLM call)
    image_items = [(image_flowable(i["data"]), (i.get("caption") or "Figure.").strip())
                   for i in images]

    sources, stats = collect_sources(topic)
    if not sources:
        raise ValueError("No relevant sources found for this topic.")

    # ---- what the LLM is allowed to know about the author's own work ----
    author_facts = notes
    if metrics:
        author_facts += "\nReported metrics: " + ", ".join(
            f"{k} = {_fmt(v)}" for k, v in metrics.items())

    review_facts = (
        "Search queries used: " + "; ".join(stats["queries"]) + ". "
        f"Records retrieved: {stats['retrieved']}. After removing duplicates "
        f"and empty records: {stats['unique']}. After automated relevance "
        f"screening (keyword overlap between the topic and each record's title "
        f"and text snippet): {stats['screened']}. The first {stats['included']} "
        f"relevant records in search-rank order were included. Sources are web "
        f"search results (journal and publisher pages)."
    )

    # ---- flowchart + figures ----
    flow_steps = [s.strip() for s in (steps or []) if s and s.strip()][:MAX_STEPS]
    flow_caption = "Workflow of the study."
    if not flow_steps and not experiment:
        flow_steps = _review_flow(stats)
        flow_caption = "Literature selection process."
    fig_blocks, fig_hints = _build_figures(flow_steps, flow_caption,
                                           metrics, image_items)

    src = _sources_block(sources)
    done, sections, failed = {}, [], 0

    for key, heading, instruction in _plan(experiment):
        hint = fig_hints.get(key)
        extra = (" Refer to " + "; ".join(hint) + " in the text.") if hint else ""
        facts = ("\n\nReview facts (the ONLY description of the review process "
                 "you may use):\n" + review_facts
                 if key == "method" and not experiment else "")
        prior = "\n\n".join(f"{k.upper()}: {v[:500]}" for k, v in done.items())
        prompt = (
            f"Paper topic: {topic}\n"
            f"Section to write: {heading}\n"
            f"Instruction: {instruction}{extra}\n\n"
            f"Author's notes (may be empty):\n{author_facts or '(none)'}"
            f"{facts}\n\n"
            f"Sources:\n{src}\n\n"
            f"Previously written sections (for consistency, do not repeat):\n"
            f"{prior or '(none yet)'}"
        )
        print(f"[Paper] writing: {heading}")
        text = _clean_text(_llm(prompt), len(sources))
        if not text:
            failed += 1
            text = "This section could not be generated. Please retry."
        done[key] = text
        sections.append({
            "heading": heading,
            "blocks": _inject(_blocks(text), fig_blocks.get(key)),
        })

    if failed >= 3:
        raise RuntimeError("The language model returned no content "
                           "(check the API key / rate limits).")

    # ---- abstract, keywords, title: written last, from the finished body ----
    body = "\n\n".join(f"{k.upper()}: {v[:900]}" for k, v in done.items())
    rule = ("This is a literature review: describe it as a review and do not "
            "mention experiments, a proposed model or original results."
            if not experiment else
            "Use ONLY facts from the paper content and the author's notes; "
            "never add numbers that are not in them.")

    print("[Paper] writing: abstract")
    abstract = _trim_words(_clean_text(_llm(
        f"Write a single-paragraph abstract of NO MORE THAN 180 words for this "
        f"paper on '{topic}'. No citations, no equations. {rule}\n\n"
        f"Paper content:\n{body}\n\nAuthor's notes:\n{author_facts or '(none)'}",
        max_tokens=2500), 0), 200)

    keywords = _parse_keywords(_llm(
        f"Give 5 or 6 comma-separated IEEE index terms for a paper on '{topic}'. "
        f"Output only the terms.", max_tokens=1500), topic)

    if not title:
        raw_title = _llm(
            f"Write one concise IEEE-style paper title (max 14 words) for a "
            f"paper on '{topic}'"
            f"{' (a literature review)' if not experiment else ''}. "
            f"Output only the title, no quotes.", max_tokens=1500)
        title = raw_title.splitlines()[0].strip(" \"'*#.") if raw_title else ""

    accessed = _ieee_date(date.today())
    return build_ieee_pdf(
        title=title or topic.title(),
        authors=authors,
        abstract=abstract or "Abstract could not be generated.",
        keywords=keywords,
        sections=sections,
        references=[_reference(s, accessed) for s in sources],
    )