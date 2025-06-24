import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from supabase import create_client, Client
from upload_pdf import extract_text_from_pdf, split_text

load_dotenv()

# Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_supabase_client():
    """Get Supabase client connection"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    return create_client(url, key)

def get_embedding(text):
    """Generate embeddings using sentence-transformers"""
    print(f"🔄 Generating embedding for text (length: {len(text)} chars)")
    embedding = embedding_model.encode(text)
    print(f"✅ Generated embedding with {len(embedding)} dimensions")
    return embedding.tolist()

def process_pdf_and_store(path):
    print(f"📄 Processing PDF: {path}")
    text = extract_text_from_pdf(path)
    print(f"📝 Extracted {len(text)} characters from PDF")
    
    chunks = split_text(text)
    print(f"✂️ Split into {len(chunks)} chunks")
    
    # Get Supabase client
    supabase = get_supabase_client()

    successful_chunks = 0
    for i, chunk in enumerate(chunks):
        try:
            print(f"🔄 Processing chunk {i+1}/{len(chunks)} (length: {len(chunk)} chars)")
            embedding = get_embedding(chunk)
            
            # Insert using Supabase client
            response = supabase.table('pdf_chunks').insert({
                'content': chunk,
                'embedding': embedding,
                'metadata': {"source": "upload", "chunk_index": i}
            }).execute()
            
            successful_chunks += 1
            print(f"✅ Stored chunk {i+1} successfully")
            
        except Exception as e:
            print(f"❌ Error storing chunk {i+1}: {e}")
    
    print(f"🎉 Successfully stored {successful_chunks}/{len(chunks)} chunks")
    return successful_chunks

if __name__ == "__main__":
    process_pdf_and_store("yourfile.pdf")