# DeepScholar

DeepScholar is a full-stack scientific question-answering system powered by a Retrieval-Augmented Generation (RAG) pipeline. It combines semantic search over scientific literature, real-time web search, and Large Language Model (LLM) answer generation to provide accurate, evidence-based responses to scientific queries.

---

## 🏗 Architecture Components

DeepScholar consists of three primary components:

1. **Frontend (React/Vue)**: Handles user interaction and displays chat interfaces and citations.
2. **Express Backend (Node.js/TypeScript)**: Manages authentication (Clerk), chat sessions, message history (PostgreSQL), and acts as a gateway to the AI orchestrator.
3. **Python RAG Orchestrator (FastAPI)**: Runs the core AI pipelines, including query validation, semantic retrieval natively via FAISS, web search, and LLM generation.

---

## ✨ Core Features

- **Scientific Query Validation**: Rejects off-topic, non-scientific queries using LLM-based classification.
- **Semantic Vector Search**: Locally built FAISS index using Hierarchical Navigable Small World (HNSW) to retrieve relevant scientific text.
- **Real-Time Web Integration**: Enhances local retrieval with live data from Tavily and Google Scholar (via SerpAPI).
- **Advanced Answer Generation**: Uses high-performance models (like NVIDIA Nemotron and Cerebras Qwen) to stream answers with proper source citations.
- **Chat History & Persistence**: Fully functional conversation storage maintained in PostgreSQL.
- **Secure Authentication**: Built-in Clerk-based user sessions and API rate-limiting.

---

## 🚀 Getting Started

### Prerequisites

- **Node.js**: v18+ & npm/yarn
- **Python**: v3.9+
- **Database**: PostgreSQL 13+
- **API Keys**: Clerk, Cerebras, NVIDIA, Tavily, SerpAPI, (Cohere optional)

## Setup

### Backend
```bash
cd backend
npm install
npx tsx db/migrations/runMigration.ts
npm run dev
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### RAG System
```bash
cd rag
setup-rag.bat
uvicorn rag_llm_orchestrator:app --reload --port 8000
```

## Environment Variables

Create `.env` files in each folder using the `.env.example` templates.

## Ports

- Frontend: http://localhost:5173
- Backend: http://localhost:8080
- RAG: http://localhost:8000
