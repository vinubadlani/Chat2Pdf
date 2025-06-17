#!/usr/bin/env python3
"""
Test script to debug vector search issues
"""
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(dotenv_path='backend/.env')

def test_vector_search():
    """Test the vector search function directly"""
    
    # Initialize embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Get Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    supabase = create_client(url, key)
    
    print("🔍 Testing Vector Search Function")
    print("=" * 40)
    
    # First, check what's in the database
    print("📊 Checking database contents...")
    response = supabase.table('pdf_chunks').select('id, content, metadata').execute()
    
    if response.data:
        print(f"✅ Found {len(response.data)} chunks in database:")
        for i, row in enumerate(response.data):
            content_preview = row['content'][:100] + "..." if len(row['content']) > 100 else row['content']
            print(f"   {i+1}. ID: {row['id']}, Content: {content_preview}")
    else:
        print("❌ No chunks found in database")
        return
    
    # Test embedding generation
    print("\n🔄 Testing embedding generation...")
    test_query = "what is ul"
    query_embedding = model.encode(test_query).tolist()
    print(f"✅ Generated query embedding with {len(query_embedding)} dimensions")
    
    # Test the vector search function
    print("\n🔄 Testing Supabase vector search function...")
    try:
        search_response = supabase.rpc('search_pdf_chunks', {
            'query_embedding': query_embedding,
            'match_count': 5
        }).execute()
        
        if search_response.data:
            print(f"✅ Vector search successful! Found {len(search_response.data)} results:")
            for i, result in enumerate(search_response.data):
                print(f"   {i+1}. Similarity: {result.get('similarity', 'N/A'):.3f}")
                print(f"      Content: {result['content'][:100]}...")
        else:
            print("⚠️ Vector search returned empty results")
            
    except Exception as e:
        print(f"❌ Vector search function failed: {e}")
        print("💡 This suggests the search_pdf_chunks function doesn't exist or has wrong signature")
        
        # Try a simple vector search using raw SQL
        print("\n🔄 Trying manual vector similarity search...")
        try:
            # Get all embeddings and do manual similarity
            all_chunks = supabase.table('pdf_chunks').select('id, content, embedding').execute()
            
            if all_chunks.data:
                print(f"✅ Retrieved {len(all_chunks.data)} chunks for manual search")
                
                # Simple similarity check (just check if embeddings exist)
                for chunk in all_chunks.data:
                    if chunk.get('embedding'):
                        print(f"   ✅ Chunk {chunk['id']} has embedding with {len(chunk['embedding'])} dimensions")
                    else:
                        print(f"   ❌ Chunk {chunk['id']} missing embedding")
            
        except Exception as manual_error:
            print(f"❌ Manual search also failed: {manual_error}")

if __name__ == "__main__":
    test_vector_search()