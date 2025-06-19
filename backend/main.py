import os
import tempfile
import time
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv
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

@app.post("/upload")
@app.post("/upload/")
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

@app.get("/upload")
@app.get("/upload/")
async def upload_pdf_get():
    """Handler for GET requests to /upload/ to avoid 404 errors"""
    return {
        "message": "This endpoint is working but requires a POST request with a PDF file", 
        "status": "online",
        "method": "POST",
        "content_type": "multipart/form-data"
    }

# Add the missing /update endpoint
@app.post("/update")
@app.post("/update/")
async def update_pdf(file: UploadFile = File(...)):
    """Update/replace PDF file - same as upload but with different endpoint"""
    return await upload_pdf(file)

@app.get("/update")
@app.get("/update/")
async def update_pdf_get():
    """Handler for GET requests to /update/ to avoid 404 errors"""
    return {
        "message": "This endpoint is working but requires a POST request with a PDF file to update", 
        "status": "online",
        "method": "POST",
        "content_type": "multipart/form-data"
    }


@app.post("/ask")
@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    """Ask a question about the uploaded PDF"""
    try:
        answer = chat(question)
        return {"answer": answer, "question": question, "status": "success"}
    except Exception as e:
        print(f"❌ Error in ask endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/health")
@app.get("/health/")
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
    
    # Check embedding model
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_embedding = model.encode("test")
        health_status["embedding_model"] = "loaded"
        health_status["embedding_dimensions"] = len(test_embedding)
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["embedding_model"] = "error"
        health_status["errors"].append(f"Embedding model error: {str(e)}")
    
    # Check environment variables
    required_env_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "GROQ_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        health_status["status"] = "degraded"
        health_status["errors"].append(f"Missing environment variables: {missing_vars}")
    
    return health_status

@app.get("/health/page")
@app.get("/health/page/")
async def health_page():
    """HTML health check page for browser viewing"""
    health_data = await health_check()
    
    status_color = {
        "healthy": "#10b981",
        "degraded": "#f59e0b", 
        "error": "#ef4444"
    }.get(health_data["status"], "#6b7280")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat2PDF API Health Status</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); padding: 30px; }}
            .status {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; background: {status_color}; }}
            .section {{ margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 8px; }}
            .error {{ color: #dc2626; background: #fef2f2; border: 1px solid #fecaca; }}
            .success {{ color: #059669; }}
            .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
            h1 {{ color: #1f2937; margin-bottom: 10px; }}
            h2 {{ color: #374151; margin-top: 25px; margin-bottom: 15px; }}
            .timestamp {{ color: #6b7280; font-size: 14px; }}
        </style>
        <script>
            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Chat2PDF API Health Status</h1>
            <div class="timestamp">Last checked: {health_data["timestamp"]}</div>
            
            <div class="section">
                <h2>Overall Status</h2>
                <span class="status">{health_data["status"].upper()}</span>
            </div>
            
            <div class="section">
                <h2>📊 Service Metrics</h2>
                <div class="metric">
                    <span>🖥️ Server Status:</span>
                    <span class="success">{health_data["server"]}</span>
                </div>
                <div class="metric">
                    <span>🗄️ Database Status:</span>
                    <span class="{'success' if health_data['database'] == 'connected' else 'error'}">{health_data["database"]}</span>
                </div>
                <div class="metric">
                    <span>🧠 Embedding Model:</span>
                    <span class="{'success' if health_data['embedding_model'] == 'loaded' else 'error'}">{health_data["embedding_model"]}</span>
                </div>
                {"<div class='metric'><span>⚡ DB Response Time:</span><span>" + str(health_data.get('db_response_time_ms', 'N/A')) + " ms</span></div>" if 'db_response_time_ms' in health_data else ""}
                {"<div class='metric'><span>📄 PDF Chunks Stored:</span><span>" + str(health_data.get('pdf_chunks_count', 'N/A')) + "</span></div>" if 'pdf_chunks_count' in health_data else ""}
            </div>
            
            {"<div class='section error'><h2>❌ Errors</h2>" + "<br>".join(health_data['errors']) + "</div>" if health_data['errors'] else ""}
            
            <div class="section">
                <h2>🔗 API Endpoints</h2>
                <div class="metric"><span>POST /upload/</span><span>Upload PDF files</span></div>
                <div class="metric"><span>POST /ask/</span><span>Ask questions about PDF</span></div>
                <div class="metric"><span>GET /health/</span><span>JSON health status</span></div>
                <div class="metric"><span>GET /</span><span>API information</span></div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px;">
                Auto-refreshes every 30 seconds
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/")
async def root():
    """Root endpoint for API health verification"""
    return {
        "message": "Chat2PDF API is running", 
        "version": "1.0.0",
        "endpoints": {
            "POST /upload/": "Upload PDF files",
            "POST /update/": "Update/replace PDF files", 
            "POST /ask/": "Ask questions about PDF",
            "GET /health/": "JSON health status",
            "GET /health/page/": "HTML health page",
            "GET /": "API information"
        },
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)