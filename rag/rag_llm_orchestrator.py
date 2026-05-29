from rag_llm import validate_query, rewrite_query
from rag_web import search_results
from llm_generator import generate_answer
from pydantic import BaseModel
from fastapi import FastAPI, Request
from chat_llm import generate_chat
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

# ================= APP =================
app = FastAPI()

# ✅ CORS (VERY IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MODELS =================
class QueryRequest(BaseModel):
    query: str
    history: list[str] = []

class QueryResponse(BaseModel):
    answer: Any

# ================= RAG PIPELINE =================
def run(query: str) -> str:
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

# 🔹 RAG query
@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    return {"answer": run(request.query)}

# 🔹 Chat LLM
@app.post("/chatllm", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest):
    return {"answer": generate_chat(request.query, request.history)}

# 🔹 AUTH SYNC (FIXED)
@app.post("/auth/sync")
async def sync_user(request: Request):
    try:
        data = await request.json()
        print("Sync called:", data)
    except:
        print("No JSON body received")

    return {"status": "ok"}


@app.post("/chats")
async def create_chat(request: Request):
    try:
        data = await request.json()
        print("Chat created:", data)
    except:
        print("No chat data received")

    return {
        "chatId": "demo-chat-123",
        "status": "created"
    }