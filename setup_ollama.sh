#!/bin/bash

echo "🔧 Setting up Chat2PDF with Ollama and Llama2"
echo "=============================================="

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install Ollama first:"
    echo "   Visit: https://ollama.ai/download"
    echo "   Or run: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

echo "✅ Ollama found!"

# Check if Ollama service is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Pull Llama2 model if not already available
echo "🦙 Checking for Llama2 model..."
if ! ollama list | grep -q "llama2"; then
    echo "📥 Downloading Llama2 model (this may take a while)..."
    ollama pull llama2
else
    echo "✅ Llama2 model already available!"
fi

# Test Ollama connection
echo "🧪 Testing Ollama connection..."
if ollama list | grep -q "llama2"; then
    echo "✅ Ollama setup complete!"
    echo ""
    echo "🎉 Next steps:"
    echo "   1. Update your Supabase database with the new schema:"
    echo "      - Run the updated setup_database.sql in Supabase SQL Editor"
    echo "   2. Start the backend server: cd backend && python main.py"
    echo "   3. Start the frontend: cd frontend && npm run dev"
else
    echo "❌ Failed to set up Llama2 model"
    exit 1
fi