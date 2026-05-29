# RAG System Setup Guide

## Problem: Original requirements.txt has issues

The original `requirements.txt` file has:
1. Encoding issues (corrupted characters)
2. CUDA-specific PyTorch versions (`torch==2.5.1+cu121`)
3. Version conflicts with Python 3.12

## Solution: Use requirements-clean.txt

### Quick Setup (Recommended)

**Windows:**
```bash
cd rag
setup-rag.bat
```

**Mac/Linux:**
```bash
cd rag
chmod +x setup-rag.sh
./setup-rag.sh
```

### Manual Setup

1. **Create virtual environment:**
```bash
cd rag
python -m venv venv
```

2. **Activate virtual environment:**

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

3. **Upgrade pip:**
```bash
python -m pip install --upgrade pip
```

4. **Install dependencies:**
```bash
pip install -r requirements-clean.txt
```

This will install CPU versions of PyTorch compatible with Python 3.12.

### Start the Server

```bash
uvicorn rag_llm_orchestrator:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Troubleshooting

### Error: "No module named 'cerebras'"

**Solution:** Install dependencies from `requirements-clean.txt`:
```bash
pip install -r requirements-clean.txt
```

### Error: "Could not find a version that satisfies the requirement torch==2.5.1+cu121"

**Problem:** The `+cu121` suffix is for CUDA GPU support, which requires special installation.

**Solution:** Use `requirements-clean.txt` which installs CPU version:
```bash
pip install -r requirements-clean.txt
```

If you need GPU support:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Error: "Requires-Python >=3.8,<3.12"

**Problem:** You're using Python 3.12, but some packages don't support it yet.

**Solution:** The `requirements-clean.txt` uses compatible versions for Python 3.12.

### Error: "ModuleNotFoundError" for any package

**Solution:** Make sure virtual environment is activated:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

Then reinstall:
```bash
pip install -r requirements-clean.txt
```

### Server starts but crashes immediately

**Check:**
1. All API keys are set in `.env` file
2. FAISS index files exist at `../faiss_output/index_hnsw.faiss`
3. Metadata file exists at `../faiss_output/metadata.pkl`

If index files are missing, you may need to run the data ingestion scripts first.

## Environment Variables

Make sure `rag/.env` contains:
```env
COHERE_API_KEY=your_key_here
CEREBRAS_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
NVIDIA_API_KEY=your_key_here
SERP_API_KEY=your_key_here
```

## Testing the API

Once running, test with:

```bash
curl -X POST http://127.0.0.1:8000/chatllm \
  -H "Content-Type: application/json" \
  -d '{"query": "What is quantum computing?", "history": []}'
```

Or visit: http://127.0.0.1:8000/docs for interactive API documentation.

## Python Version Compatibility

- ✅ Python 3.9, 3.10, 3.11, 3.12 - Use `requirements-clean.txt`
- ❌ Python 3.13+ - Not yet supported by all dependencies

To check your Python version:
```bash
python --version
```

## Next Steps

After successful setup:
1. Verify all endpoints work: `/query` and `/chatllm`
2. Check logs for any warnings
3. Test integration with backend
4. Monitor API rate limits
