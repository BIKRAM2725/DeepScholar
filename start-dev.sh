#!/bin/bash

# DeepScholar Development Startup Script

echo "🚀 Starting DeepScholar Development Environment..."
echo ""

# Check if running on Windows (Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows environment"
    
    # Start backend
    echo "📦 Starting Backend Server..."
    cd backend
    start cmd /k "npm run dev"
    cd ..
    
    # Start frontend
    echo "🎨 Starting Frontend Server..."
    cd frontend
    start cmd /k "npm run dev"
    cd ..
    
    echo ""
    echo "✅ Services starting in separate windows!"
    echo ""
    echo "📝 Manual step required:"
    echo "   Start Python RAG system manually:"
    echo "   cd rag"
    echo "   python -m venv venv (if not done)"
    echo "   venv\\Scripts\\activate"
    echo "   pip install -r requirements.txt (if not done)"
    echo "   uvicorn rag_llm_orchestrator:app --reload --port 8000"
    echo ""
else
    # Unix-like systems (macOS, Linux)
    echo "Detected Unix-like environment"
    
    # Start backend
    echo "📦 Starting Backend Server..."
    cd backend
    npm run dev &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    echo "🎨 Starting Frontend Server..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo "✅ Services started!"
    echo "   Backend PID: $BACKEND_PID"
    echo "   Frontend PID: $FRONTEND_PID"
    echo ""
    echo "📝 Manual step required:"
    echo "   Start Python RAG system manually:"
    echo "   cd rag"
    echo "   python -m venv venv (if not done)"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt (if not done)"
    echo "   uvicorn rag_llm_orchestrator:app --reload --port 8000"
    echo ""
    echo "To stop services, run: kill $BACKEND_PID $FRONTEND_PID"
fi

echo "🌐 Access points:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8080"
echo "   RAG API:  http://127.0.0.1:8000"
echo ""
