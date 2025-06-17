import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from upload_pdf import extract_text_from_pdf, split_text
from store_embeddings import get_embedding, get_supabase_client
from rag_chat import chat

load_dotenv()

app = FastAPI(title="Chat to PDF RAG API")

# Define all frontend domains to allow
allowed_origins = [
    # Wildcard for development/testing
    "*",
    
    # Local development URLs
    "http://localhost:3000",
    "http://localhost:5173",
    
    # Production URLs
    "https://chat2pdf-main.vercel.app",
    "https://chat2-pdf-eub3-git-main-vinubadlanis-projects.vercel.app",
    "https://chat2-pdf-eub3-c57ofn8u3-vinubadlanis-projects.vercel.app",
    "https://chat2-pdf.vercel.app",
    "https://chat2-pdf-git-main-vinubadlanis-projects.vercel.app",
    "https://chat2-dp04x294a-vinubadlanis-projects.vercel.app"
]

# Add frontend URL from environment variable if present
if os.environ.get("FRONTEND_URL"):
    allowed_origins.append(os.environ.get("FRONTEND_URL"))

# Enable CORS with additional headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use wildcard to accept all origins for immediate fix
    allow_credentials=False,  # Changed to False to avoid issues with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Content-Type-Options"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Additional CORS handling for more complex cases
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Handle preflight OPTIONS requests explicitly
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )

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
            "successful_chunks": successful_chunks
        }
    
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temp file
        print(f"🗑️ Cleaning up temporary file: {tmp_file_path}")
        os.unlink(tmp_file_path)

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    """Ask a question about the uploaded PDF"""
    try:
        answer = chat(question)
        return {"answer": answer, "question": question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/health/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)