@echo off
REM DeepScholar Development Startup Script for Windows

echo 🚀 Starting DeepScholar Development Environment...
echo.

REM Start backend
echo 📦 Starting Backend Server...
start "Backend Server" cmd /k "cd backend && npm run dev"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start frontend
echo 🎨 Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ✅ Services starting in separate windows!
echo.
echo 📝 Manual step required:
echo    Start Python RAG system manually:
echo    cd rag
echo    python -m venv venv (if not done)
echo    venv\Scripts\activate
echo    pip install -r requirements.txt (if not done)
echo    uvicorn rag_llm_orchestrator:app --reload --port 8000
echo.
echo 🌐 Access points:
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:8080
echo    RAG API:  http://127.0.0.1:8000
echo.
pause
