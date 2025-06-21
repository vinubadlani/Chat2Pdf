"""
Vercel-optimized FastAPI application for Chat2PDF backend.
This is the entry point for Vercel serverless deployment.
"""
import os
import tempfile
import time
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv

# Import our modules
from upload_pdf import extract_text_from_pdf, split_text
from store_embeddings import get_embedding, get_supabase_client
from rag_chat import chat

load_dotenv()

app = FastAPI(title="Chat to PDF RAG API")

# Simplified CORS - Allow all origins for maximum compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Set to False when using wildcard
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/api/upload")
@app.post("/api/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file"""
    print(f"\n📤 Received upload request for: {file.filename}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    print(f"💾 Saved temporary file: {tmp_file_path}")
    
    try:
        # Extract text and create chunks
        print("📄 Extracting text from PDF...")
        text = extract_text_from_pdf(tmp_file_path)
        print(f"📝 Extracted {len(text)} characters")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found in PDF")
        
        chunks = split_text(text)
        print(f"✂️ Split into {len(chunks)} chunks")
        
        # Store embeddings using Supabase client
        supabase = get_supabase_client()
        
        successful_chunks = 0
        for i, chunk in enumerate(chunks):
            try:
                print(f"🔄 Processing chunk {i+1}/{len(chunks)}")
                embedding = get_embedding(chunk)
                
                response = supabase.table('pdf_chunks').insert({
                    'content': chunk,
                    'embedding': embedding,
                    'metadata': {"source": file.filename, "chunk_index": i}
                }).execute()
                
                successful_chunks += 1
                
            except Exception as chunk_error:
                print(f"❌ Error storing chunk {i+1}: {chunk_error}")
        
        print(f"🎉 Successfully processed {successful_chunks}/{len(chunks)} chunks")
        
        return {
            "message": f"Successfully processed {successful_chunks}/{len(chunks)} chunks from {file.filename}",
            "total_chunks": len(chunks),
            "successful_chunks": successful_chunks,
            "status": "success"
        }
    
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temp file
        print(f"🗑️ Cleaning up temporary file: {tmp_file_path}")
        os.unlink(tmp_file_path)

@app.get("/api/upload")
@app.get("/api/upload/")
async def upload_pdf_get():
    """Handler for GET requests to /upload/ to avoid 404 errors"""
    return {
        "message": "This endpoint is working but requires a POST request with a PDF file", 
        "status": "online",
        "method": "POST",
        "content_type": "multipart/form-data"
    }

@app.post("/api/ask")
@app.post("/api/ask/")
async def ask_question(question: str = Form(...)):
    """Ask a question about the uploaded PDF"""
    try:
        answer = chat(question)
        return {"answer": answer, "question": question, "status": "success"}
    except Exception as e:
        print(f"❌ Error in ask endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/api/health")
@app.get("/api/health/")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "online",
        "database": "unknown",
        "embedding_model": "unknown",
        "errors": []
    }
    
    # Check database connection
    try:
        supabase = get_supabase_client()
        start_time = time.time()
        resp = supabase.table('pdf_chunks').select('id').limit(1).execute()
        db_response_time = round((time.time() - start_time) * 1000, 2)
        
        health_status["database"] = "connected"
        health_status["db_response_time_ms"] = db_response_time
        
        # Check if table has data
        count_resp = supabase.table('pdf_chunks').select('id', count='exact').execute()
        health_status["pdf_chunks_count"] = count_resp.count if hasattr(count_resp, 'count') else 0
        
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = "error"
        health_status["errors"].append(f"Database error: {str(e)}")
    
    # Check environment variables
    required_env_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "GROQ_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        health_status["status"] = "degraded"
        health_status["errors"].append(f"Missing environment variables: {missing_vars}")
    
    return health_status

@app.get("/api/")
async def root():
    """Root endpoint for API health verification"""
    return {
        "message": "Chat2PDF API is running", 
        "version": "1.0.0",
        "endpoints": {
            "POST /upload/": "Upload PDF files",
            "POST /ask/": "Ask questions about PDF",
            "GET /health/": "JSON health status",
            "GET /": "API information"
        },
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

# For Vercel deployment
handler = app