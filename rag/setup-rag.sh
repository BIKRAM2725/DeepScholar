#!/bin/bash

echo "🐍 Setting up Python RAG System..."
echo ""

# Check Python version
python3 --version
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip
echo ""

# Install dependencies from clean requirements
echo "Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements-clean.txt
echo ""

echo "✅ Setup complete!"
echo ""
echo "To start the RAG server:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Run server: uvicorn rag_llm_orchestrator:app --reload --port 8000"
echo ""
