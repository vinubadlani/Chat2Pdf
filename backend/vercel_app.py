"""
Vercel-optimized FastAPI application for Chat2PDF backend.
This is the entry point for Vercel serverless deployment.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Chat2PDF API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Chat2PDF API is running!", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "API is working correctly"}

@app.post("/upload")
async def upload_pdf():
    return {"message": "PDF upload endpoint - coming soon"}

@app.post("/chat")
async def chat():
    return {"message": "Chat endpoint - coming soon"}

# This is the ASGI app that Vercel will use
# The handler function for Vercel
def handler(request, context):
    return app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)