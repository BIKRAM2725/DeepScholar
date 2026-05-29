@echo off
echo 🐍 Setting up Python RAG System...
echo.

REM Check Python version
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies from clean requirements
echo Installing dependencies...
echo This may take a few minutes...
pip install -r requirements-clean.txt
echo.

echo ✅ Setup complete!
echo.
echo To start the RAG server:
echo   1. Activate venv: venv\Scripts\activate
echo   2. Run server: uvicorn rag_llm_orchestrator:app --reload --port 8000
echo.
pause
