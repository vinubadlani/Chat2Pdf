"""
Entry point for Vercel serverless deployment.
This is a standalone ASGI application for Vercel.
"""
import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import the required modules directly
from upload_pdf import extract_text_from_pdf, split_text
from store_embeddings import get_embedding, get_supabase_client
from rag_chat import chat

load_dotenv()

app = FastAPI(title="Chat to PDF RAG API")

# Enable CORS for all origins (needed for Vercel deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint for testing
@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Chat2PDF API is online"}

# Show health status
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Test endpoint for GET requests to /upload/
@app.get("/upload")
@app.get("/upload/")
async def upload_pdf_get():
    return {
        "message": "Upload endpoint is working. Use POST to upload PDF files.",
        "status": "online"
    }

# Main PDF upload endpoint
@app.post("/upload")
@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file"""
    print(f"📤 Received upload request for: {file.filename}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Extract text and create chunks
        print("📄 Extracting text from PDF...")
        text = extract_text_from_pdf(tmp_file_path)
        print(f"📝 Extracted {len(text)} characters")
        
        chunks = split_text(text)
        print(f"✂️ Split into {len(chunks)} chunks")
        
        # Store embeddings using Supabase client
        supabase = get_supabase_client()
        
        successful_chunks = 0
        for i, chunk in enumerate(chunks):
            try:
                embedding = get_embedding(chunk)
                
                response = supabase.table('pdf_chunks').insert({
                    'content': chunk,
                    'embedding': embedding,
                    'metadata': {"source": file.filename, "chunk_index": i}
                }).execute()
                
                successful_chunks += 1
                
            except Exception as chunk_error:
                print(f"❌ Error storing chunk {i+1}: {chunk_error}")
        
        return {
            "message": f"Successfully processed {successful_chunks}/{len(chunks)} chunks from {file.filename}",
            "total_chunks": len(chunks),
            "successful_chunks": successful_chunks
        }
    
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temp file
        os.unlink(tmp_file_path)

# Ask questions about the PDF
@app.post("/ask")
@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    """Ask a question about the uploaded PDF"""
    try:
        answer = chat(question)
        return {"answer": answer, "question": question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")