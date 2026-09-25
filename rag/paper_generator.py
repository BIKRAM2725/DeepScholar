
import base64
import re
import time
from datetime import date

from rag_llm import client, MODEL
from rag_web import search_results
from citations import format_ieee
from paper_pdf import (
    bar_chart, build_ieee_pdf, flowchart, image_flowable, metrics_table,
)

MAX_SOURCES = 12
MAX_FAISS_SOURCES = 6
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

_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
_STOP = {"the", "and", "for", "with", "using", "based", "from", "into",
         "that", "this", "via", "over", "under"}
_DELAYS = [4, 12, 25]
_use_reasoning = True


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
                _use_reasoning = False
                continue
        if attempt < len(_DELAYS):
            time.sleep(_DELAYS[attempt])
    return ""


# ---------------------------------------------------------------------------
# Source collection: web (+ FAISS in "deep" mode) with relevance screening
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


_FAISS_CACHE: dict = {}


def _faiss_sources(topic, top_k=MAX_FAISS_SOURCES):
    """Your local FAISS index, used only in 'deep' mode. Fails silently
    (returns []) if the index files aren't built yet, so 'deep' always
    degrades gracefully to a web-only search instead of crashing."""
    try:
        if "index" not in _FAISS_CACHE:
            from load_index import load_index
            idx, meta = load_index()
            _FAISS_CACHE["index"], _FAISS_CACHE["meta"] = idx, meta
        from rag_retrieval import retrieve
        hits = retrieve(_FAISS_CACHE["index"], _FAISS_CACHE["meta"],
                        topic, top_k=top_k) or []
        return [
            {"title": (h.get("title") or "Untitled").strip(),
             "content": (h.get("content") or "").strip(),
             "url": h["url"], "source": "faiss-index"}
            for h in hits if h.get("content") and h.get("url")
        ]
    except Exception as e:
        print(f"[Paper] FAISS index unavailable ({type(e).__name__}: {e}); "
              f"continuing with web sources only.")
        return []


def collect_sources(topic, mode="fast"):
    queries = [topic, f"{topic} review", f"{topic} recent advances",
               f"{topic} methods dataset"]
    raw = []
    for q in queries:
        try:
            raw.extend(search_results(q) or [])
        except Exception as e:
            print(f"[Paper] search failed for '{q}': {e}")

    faiss_hits = _faiss_sources(topic) if mode == "deep" else []

    seen, unique = set(), []
    for r in faiss_hits + raw:            # FAISS first: your own corpus wins ties
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
    stats = {"queries": queries, "retrieved": len(raw) + len(faiss_hits),
             "unique": len(unique), "screened": len(relevant),
             "included": len(selected), "faiss_used": len(faiss_hits),
             "mode": mode}
    print(f"[Paper] sources ({mode}): {stats['retrieved']} retrieved "
          f"({stats['faiss_used']} from FAISS), {stats['unique']} unique, "
          f"{stats['screened']} relevant, {stats['included']} used")
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
    def repl(m):
        nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
        good = [x for x in nums if 1 <= x <= n_sources]
        return ", ".join(f"[{x}]" for x in good)
    return re.sub(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]", repl, text)


def _trim_incomplete(text):
    text = text.rstrip()
    if re.search(r"[.!?][\)\]\"']?$", text):
        return text
    cut = max(text.rfind(". "), text.rfind(".\n"))
    return text[:cut + 1] if cut > len(text) * 0.5 else text


def _clean_text(text, n_sources):
    text = re.sub(r"[*`]", "", text)
    text = re.sub(r"(?m)^\s*#+\s*", "", text)
    text = re.sub(r"(?m)^\s*(?:[-\u2022]|\d{1,2}[.)])\s+", "", text)
    text = _fix_cites(text, n_sources)
    text = re.sub(r"[ \t]+([.,;:])", r"\1", text)
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
            t = s[2:].strip(" :.")
            if t:
                blocks.append(("sub", t))
        else:
            buf.append(s)
    flush()
    return blocks


def _parse_keywords(raw, topic):
    parts = [re.sub(r"^\d+[.)]\s*", "", p).strip(" .;\n\"'")
             for p in re.split(r"[,;\n]", raw)]
    parts = [p for p in parts if p][:6] or [topic]
    return ", ".join(sorted(set(parts), key=str.lower))


_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.",
           "Jul.", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]


def _ieee_date(d):
    return f"{_MONTHS[d.month - 1]} {d.day}, {d.year}"


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
    steps = [f"Records retrieved\n(n = {stats['retrieved']})"]
    if stats.get("faiss_used"):
        steps[-1] = (f"Records retrieved\n(n = {stats['retrieved']}, incl. "
                     f"{stats['faiss_used']} from local index)")
    steps += [
        f"After duplicate removal\n(n = {stats['unique']})",
        f"After relevance screening\n(n = {stats['screened']})",
        f"Included in review\n(n = {stats['included']})",
    ]
    return steps


def _build_figures(flow_steps, flow_caption, metrics, images):
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
    if not extras:
        return blocks
    first_p = next((i for i, b in enumerate(blocks) if b[0] == "p"), None)
    at = first_p + 1 if first_p is not None else len(blocks)
    return blocks[:at] + extras + blocks[at:]


# ---------------------------------------------------------------------------
# Streaming generator: yields progress, then a final "done" event
# ---------------------------------------------------------------------------
def generate_paper_stream(topic, notes="", authors="Author Name", steps=None,
                          metrics=None, images=None, title=None, mode="fast"):
    """
    mode    : "fast" (web search only) or "deep" (web + your FAISS index)
    steps   : list[str]   your own pipeline steps for the flowchart
    metrics : dict        your REAL results, e.g. {"Precision": 0.91}
    images  : list[dict]  [{"caption": str, "data": bytes}] your own figures
    title   : str         optional fixed title

    Yields dicts:
      {"type": "progress", "step": <label>, "index": i, "total": n}
      {"type": "error", "message": <str>}                     (terminal)
      {"type": "done", "pdf_base64": <str>, "title": <str>,
       "sources_used": <int>, "mode": <str>}                  (terminal)
    """
    mode = mode if mode in ("fast", "deep") else "fast"
    notes = (notes or "").strip()
    metrics = {str(k): float(v) for k, v in (metrics or {}).items()}
    images = images or []
    experiment = bool(notes or metrics or images)
    plan = _plan(experiment)
    total = len(plan) + 3   # + abstract, keywords/title, final assembly

    try:
        image_items = [(image_flowable(i["data"]),
                        (i.get("caption") or "Figure.").strip()) for i in images]
    except ValueError as e:
        yield {"type": "error", "message": str(e)}
        return

    yield {"type": "progress", "step": f"Collecting sources ({mode} mode)",
           "index": 0, "total": total}
    sources, stats = collect_sources(topic, mode)
    if not sources:
        yield {"type": "error", "message": "No relevant sources found for this topic."}
        return

    author_facts = notes
    if metrics:
        author_facts += "\nReported metrics: " + ", ".join(
            f"{k} = {_fmt(v)}" for k, v in metrics.items())

    review_facts = (
        "Search queries used: " + "; ".join(stats["queries"]) + ". "
        f"Records retrieved: {stats['retrieved']}"
        + (f" (including {stats['faiss_used']} from the local research index)"
           if stats.get("faiss_used") else "") +
        f". After removing duplicates and empty records: {stats['unique']}. "
        f"After automated relevance screening (keyword overlap between the "
        f"topic and each record's title and text snippet): {stats['screened']}. "
        f"The first {stats['included']} relevant records in search-rank order "
        f"were included. Sources are web search results and, when available, "
        f"the author's own indexed research corpus."
    )

    flow_steps = [s.strip() for s in (steps or []) if s and s.strip()][:MAX_STEPS]
    flow_caption = "Workflow of the study."
    if not flow_steps and not experiment:
        flow_steps = _review_flow(stats)
        flow_caption = "Literature selection process."
    fig_blocks, fig_hints = _build_figures(flow_steps, flow_caption,
                                           metrics, image_items)

    src = _sources_block(sources)
    done, sections, failed = {}, [], 0

    for i, (key, heading, instruction) in enumerate(plan, 1):
        yield {"type": "progress", "step": f"Writing {heading}",
               "index": i, "total": total}

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
        yield {"type": "error", "message": "The language model returned no "
              "content (check the API key / rate limits)."}
        return

    body = "\n\n".join(f"{k.upper()}: {v[:900]}" for k, v in done.items())
    rule = ("This is a literature review: describe it as a review and do not "
            "mention experiments, a proposed model or original results."
            if not experiment else
            "Use ONLY facts from the paper content and the author's notes; "
            "never add numbers that are not in them.")

    yield {"type": "progress", "step": "Writing abstract and keywords",
           "index": len(plan) + 1, "total": total}
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
    title = title or topic.title()

    yield {"type": "progress", "step": "Formatting references and building PDF",
           "index": len(plan) + 2, "total": total}
    accessed = _ieee_date(date.today())
    references = [format_ieee(s, accessed) for s in sources]

    pdf = build_ieee_pdf(
        title=title, authors=authors,
        abstract=abstract or "Abstract could not be generated.",
        keywords=keywords, sections=sections, references=references,
    )

    yield {"type": "progress", "step": "Done", "index": total, "total": total}
    yield {
        "type": "done",
        "pdf_base64": base64.b64encode(pdf).decode("ascii"),
        "title": title,
        "sources_used": len(sources),
        "mode": mode,
    }


def generate_paper_pdf(topic, notes="", authors="Author Name", steps=None,
                       metrics=None, images=None, title=None, mode="fast"):
    """Non-streaming wrapper: drains generate_paper_stream and returns PDF bytes."""
    for event in generate_paper_stream(topic, notes, authors, steps, metrics,
                                       images, title, mode):
        if event["type"] == "error":
            if "No relevant sources" in event["message"]:
                raise ValueError(event["message"])
            raise RuntimeError(event["message"])
        if event["type"] == "done":
            return base64.b64decode(event["pdf_base64"])
    raise RuntimeError("Paper generation ended without producing a PDF.")