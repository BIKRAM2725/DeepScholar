import base64
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rag_llm import validate_query, rewrite_query
from rag_web import search_results
from llm_generator import generate_answer
from chat_llm import generate_chat
from paper_generator import generate_paper_pdf

# ================= APP =================
app = FastAPI()

# CORS (VERY IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # lets the browser read the PDF filename
)


# ================= MODELS =================
class QueryRequest(BaseModel):
    query: str
    history: list[str] = []


class QueryResponse(BaseModel):
    answer: Any


class FigureIn(BaseModel):
    caption: str = "Figure."
    image_base64: str                 # PNG/JPG, raw base64 or a data: URL


class PaperRequest(BaseModel):
    topic: str
    title: str = ""                   # optional fixed title
    authors: str = "Author Name"      # use "\n" for extra lines (affiliation, email)
    notes: str = ""                   # your REAL experiment details/results
    steps: list[str] = []             # pipeline steps for the flowchart
    metrics: dict[str, float] = {}    # your REAL results, e.g. {"mAP50": 0.93}
    figures: list[FigureIn] = []      # your own figures (training curves, samples...)


MAX_FIGURES = 4
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _decode_figures(figures):
    out = []
    for f in figures[:MAX_FIGURES]:
        raw = f.image_base64.split(",", 1)[-1].strip()   # strip "data:image/png;base64,"
        try:
            data = base64.b64decode(raw)
        except Exception:
            raise ValueError("A figure is not valid base64.")
        if not data or len(data) > MAX_IMAGE_BYTES:
            raise ValueError("Each figure must be under 5 MB.")
        out.append({"caption": f.caption.strip() or "Figure.", "data": data})
    return out


# ================= RAG PIPELINE =================
def run(query: str) -> Any:
    print("\n[Orchestrator] Validating query...")

    if not validate_query(query):
        return "Please ask a scientific question."

    print("[Orchestrator] Rewriting query...")
    rewritten = rewrite_query(query)

    print("[Orchestrator] Searching web...")
    web_results = search_results(rewritten) or []

    combined = []
    seen = set()

    for r in web_results:
        url = r.get("url")
        if url and url not in seen:
            seen.add(url)
            combined.append(r)

    if not combined:
        return "No results found."

    print("[Orchestrator] Generating answer...")
    return generate_answer(query, combined)


# ================= ROUTES =================

# 🔹 Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# 🔹 RAG query
@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    return {"answer": run(request.query)}


# 🔹 Chat LLM
@app.post("/chatllm", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest):
    return {"answer": generate_chat(request.query, request.history)}


# 🔹 Research paper (IEEE-style PDF)
# Plain `def` on purpose: FastAPI runs it in a thread pool, so the 1-3 minute
# generation does not block the other endpoints.
@app.post("/generate-paper")
def generate_paper_endpoint(req: PaperRequest):
    topic = req.topic.strip()
    if not topic:
        return JSONResponse({"error": "Topic is required."}, status_code=400)

    if not validate_query(topic):
        return JSONResponse(
            {"error": "Please give a scientific topic."}, status_code=400
        )

    try:
        images = _decode_figures(req.figures)
        pdf = generate_paper_pdf(
            topic,
            notes=req.notes,
            authors=req.authors,
            steps=req.steps or None,
            metrics=req.metrics or None,
            images=images or None,
            title=req.title.strip() or None,
        )
    except ValueError as e:           # bad image, no sources found, ...
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        print(f"[Paper] failed: {type(e).__name__}: {e}")
        return JSONResponse({"error": "Paper generation failed."}, status_code=500)

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="paper.pdf"'},
    )


# 🔹 AUTH SYNC
@app.post("/auth/sync")
async def sync_user(request: Request):
    try:
        data = await request.json()
        print("Sync called:", data)
    except Exception:
        print("No JSON body received")

    return {"status": "ok"}


@app.post("/chats")
async def create_chat(request: Request):
    try:
        data = await request.json()
        print("Chat created:", data)
    except Exception:
        print("No chat data received")

    return {
        "chatId": "demo-chat-123",
        "status": "created",
    }