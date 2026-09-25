import base64
import json
from typing import Any, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from rag_llm import validate_query, rewrite_query
from rag_web import search_results
from llm_generator import generate_answer
from chat_llm import generate_chat
from paper_generator import generate_paper_pdf, generate_paper_stream

# ================= APP =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
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
    mode: str = "fast"                # "fast" = web only, "deep" = web + FAISS index


MAX_FIGURES = 4
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _decode_figures(figures):
    out = []
    for f in figures[:MAX_FIGURES]:
        raw = f.image_base64.split(",", 1)[-1].strip()
        try:
            data = base64.b64decode(raw)
        except Exception:
            raise ValueError("A figure is not valid base64.")
        if not data or len(data) > MAX_IMAGE_BYTES:
            raise ValueError("Each figure must be under 5 MB.")
        out.append({"caption": f.caption.strip() or "Figure.", "data": data})
    return out


def _paper_kwargs(req: PaperRequest):
    return dict(
        notes=req.notes,
        authors=req.authors,
        steps=req.steps or None,
        metrics=req.metrics or None,
        images=_decode_figures(req.figures) or None,
        title=req.title.strip() or None,
        mode=req.mode if req.mode in ("fast", "deep") else "fast",
    )


# ================= RAG CHAT PIPELINE =================
def run(query: str) -> Any:
    print("\n[Orchestrator] Validating query...")
    if not validate_query(query):
        return "Please ask a scientific question."

    print("[Orchestrator] Rewriting query...")
    rewritten = rewrite_query(query)

    print("[Orchestrator] Searching web...")
    web_results = search_results(rewritten) or []

    combined, seen = [], set()
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

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    return {"answer": run(request.query)}


@app.post("/chatllm", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest):
    return {"answer": generate_chat(request.query, request.history)}


# 🔹 Research paper — streaming (SSE): progress events, then a "done" event
# carrying the base64 PDF. The Node backend consumes this, uploads the PDF
# to Supabase Storage, and re-emits its own "done" event with the file URL.
@app.post("/generate-paper/stream")
def generate_paper_stream_endpoint(req: PaperRequest):
    topic = req.topic.strip()

    def events():
        if not topic:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Topic is required.'})}\n\n"
            return
        if not validate_query(topic):
            yield f"data: {json.dumps({'type': 'error', 'message': 'Please give a scientific topic.'})}\n\n"
            return
        try:
            kwargs = _paper_kwargs(req)
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        try:
            for event in generate_paper_stream(topic, **kwargs):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            print(f"[Paper] stream failed: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Paper generation failed.'})}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


# 🔹 Research paper — plain (non-streaming) PDF download
@app.post("/generate-paper")
def generate_paper_endpoint(req: PaperRequest):
    topic = req.topic.strip()
    if not topic:
        return JSONResponse({"error": "Topic is required."}, status_code=400)
    if not validate_query(topic):
        return JSONResponse({"error": "Please give a scientific topic."}, status_code=400)

    try:
        pdf = generate_paper_pdf(topic, **_paper_kwargs(req))
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        print(f"[Paper] failed: {type(e).__name__}: {e}")
        return JSONResponse({"error": "Paper generation failed."}, status_code=500)

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="paper.pdf"'},
    )


# 🔹 AUTH SYNC (kept for local testing without the Node backend)
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
    return {"chatId": "demo-chat-123", "status": "created"}