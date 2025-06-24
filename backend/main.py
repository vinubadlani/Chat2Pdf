import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from upload_pdf import extract_text_from_pdf, split_text
from store_embeddings import get_embedding, get_supabase_client
from rag_chat import chat

load_dotenv()

app = FastAPI(title="Chat to PDF RAG API")

# Allow frontend domains for CORS
allowed_origins = [
    "http://localhost:3000",     # React default
    "http://localhost:5173",     # Vite default
    "http://localhost:5174",     # Vite alternate port
    "https://chat2pdf.vercel.app",  # Expected production URL (adjust as needed)
]

# Add your deployed frontend URL to environment variable
if os.environ.get("FRONTEND_URL"):
    allowed_origins.append(os.environ.get("FRONTEND_URL"))

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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