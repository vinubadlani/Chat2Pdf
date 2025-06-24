#!/usr/bin/env python3
"""
Test script to verify Ollama integration with Llama2 model
"""
import os
import ollama
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables from the backend directory
load_dotenv(dotenv_path='backend/.env')

def test_ollama_connection():
    """Test Ollama connection and Gemma 2B model"""
    try:
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma:2b")
        
        print("🔍 Testing Ollama Connection:")
        print(f"   Model: {ollama_model}")
        print()
        
        # Test basic chat
        print("🔄 Testing chat completion...")
        response = ollama.chat(
            model=ollama_model,
            messages=[
                {"role": "user", "content": "Hello! Can you briefly introduce yourself?"}
            ]
        )
        
        print("✅ Ollama chat test successful!")
        print(f"   Response: {response['message']['content'][:100]}...")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Ollama is installed and running")
        print("   2. Run: ollama serve")
        print("   3. Run: ollama pull gemma:2b")
        print("   4. Check if port 11434 is available")
        return False

def test_embeddings():
    """Test sentence-transformers embeddings"""
    try:
        print("🔄 Testing embedding model...")
        
        # Initialize the embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test embedding generation
        test_text = "This is a test sentence for embedding generation."
        embedding = model.encode(test_text)
        
        print("✅ Embedding test successful!")
        print(f"   Embedding dimensions: {len(embedding)}")
        print(f"   Sample values: {embedding[:5]}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        print("\n💡 This usually means sentence-transformers needs to be installed:")
        print("   pip install sentence-transformers")
        return False

def test_rag_integration():
    """Test the complete RAG pipeline"""
    try:
        print("🔄 Testing RAG integration...")
        
        # Import our modules
        from backend.rag_chat import chat
        
        # This will fail if no PDF data is loaded, but we can test the function exists
        print("✅ RAG modules imported successfully!")
        print("   Note: Upload a PDF first to test full functionality")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Ollama + Llama2 Integration Test")
    print("=" * 40)
    
    success = True
    
    # Test embedding model
    success &= test_embeddings()
    
    # Test Ollama connection
    success &= test_ollama_connection()
    
    # Test RAG integration
    success &= test_rag_integration()
    
    if success:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Update Supabase database schema (run setup_database.sql)")
        print("2. Start backend: cd backend && python main.py")
        print("3. Start frontend: cd frontend && npm run dev")
    else:
        print("❌ Some tests failed. Please check the errors above.")