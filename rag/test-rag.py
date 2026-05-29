#!/usr/bin/env python3
"""
Simple test script to verify RAG system dependencies are installed correctly.
Run this after installing requirements-clean.txt
"""

import sys

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing RAG System Dependencies...\n")
    
    tests = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("Pydantic", "pydantic"),
        ("Cerebras SDK", "cerebras.cloud.sdk"),
        ("Cohere", "cohere"),
        ("OpenAI", "openai"),
        ("Tavily", "tavily"),
        ("SerpAPI", "serpapi"),
        ("FAISS", "faiss"),
        ("Sentence Transformers", "sentence_transformers"),
        ("PyTorch", "torch"),
        ("Transformers", "transformers"),
        ("NumPy", "numpy"),
        ("Pandas", "pandas"),
        ("Scikit-learn", "sklearn"),
        ("Python-dotenv", "dotenv"),
    ]
    
    passed = 0
    failed = 0
    
    for name, module in tests:
        try:
            __import__(module)
            print(f"✅ {name}")
            passed += 1
        except ImportError as e:
            print(f"❌ {name} - {str(e)}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")
    
    if failed > 0:
        print("⚠️  Some dependencies are missing!")
        print("Run: pip install -r requirements-clean.txt")
        return False
    else:
        print("✅ All dependencies installed successfully!")
        return True

def test_env_vars():
    """Test that environment variables are set"""
    import os
    from dotenv import load_dotenv
    
    print("\n🔑 Testing Environment Variables...\n")
    
    load_dotenv()
    
    required_vars = [
        "COHERE_API_KEY",
        "CEREBRAS_API_KEY",
        "TAVILY_API_KEY",
        "NVIDIA_API_KEY",
        "SERP_API_KEY",
    ]
    
    passed = 0
    failed = 0
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first 10 chars only for security
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked}")
            passed += 1
        else:
            print(f"❌ {var}: Not set")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")
    
    if failed > 0:
        print("⚠️  Some API keys are missing!")
        print("Check your .env file in the rag/ directory")
        return False
    else:
        print("✅ All API keys configured!")
        return True

def test_pytorch():
    """Test PyTorch installation"""
    print("\n🔥 Testing PyTorch...\n")
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ CUDA version: {torch.version.cuda}")
        else:
            print("ℹ️  Running on CPU (this is fine for most use cases)")
        return True
    except Exception as e:
        print(f"❌ PyTorch test failed: {e}")
        return False

def main():
    print("\n" + "="*50)
    print("RAG System Dependency Test")
    print("="*50 + "\n")
    
    results = []
    
    # Test imports
    results.append(test_imports())
    
    # Test environment variables
    results.append(test_env_vars())
    
    # Test PyTorch
    results.append(test_pytorch())
    
    # Final summary
    print("\n" + "="*50)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        print("\nYou can now start the RAG server:")
        print("  uvicorn rag_llm_orchestrator:app --reload --port 8000")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*50)
        print("\nPlease fix the issues above before starting the server.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
