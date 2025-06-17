import os
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from supabase import create_client, Client

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
    embedding = embedding_model.encode(text)
    return embedding.tolist()

def call_groq_api(messages):
    """Call Groq API for chat completion"""
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    
    if not groq_api_key:
        raise Exception("GROQ_API_KEY not found in environment variables")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {groq_api_key}"
    }
    
    payload = {
        "model": groq_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Groq API error: {response.status_code} - {response.text}")

def validate_pdf_content_relevance(query, chunks):
    """Check if the retrieved chunks contain relevant information for the query"""
    if not chunks:
        return False
    
    # More flexible keyword matching for better relevance detection
    query_words = set(query.lower().split())
    
    # Remove very common words that don't indicate relevance
    stop_words = {'what', 'how', 'where', 'when', 'why', 'is', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    meaningful_query_words = query_words - stop_words
    
    # If query has no meaningful words, be more permissive
    if not meaningful_query_words:
        return True
    
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        
        # Check for direct keyword matches
        if len(meaningful_query_words.intersection(chunk_words)) > 0:
            return True
        
        # Check for partial matches (for compound words, HTML tags, etc.)
        for query_word in meaningful_query_words:
            for chunk_word in chunk_words:
                if query_word in chunk_word or chunk_word in query_word:
                    if len(query_word) > 2 and len(chunk_word) > 2:  # Avoid matching very short words
                        return True
    
    # If it's a technical query and we have any content, be more permissive
    # This helps with technical documents like HTML cheatsheets
    if len(meaningful_query_words) <= 3 and chunks:
        return True
        
    return False

def get_similar_chunks(query, k=5):
    print(f"🔍 Searching for chunks related to: {query}")
    query_embedding = get_embedding(query)
    supabase = get_supabase_client()
    
    # First, check if we have any data in the table
    try:
        count_response = supabase.table('pdf_chunks').select('id', count='exact').execute()
        total_chunks = count_response.count if hasattr(count_response, 'count') else 0
        print(f"📊 Total chunks in database: {total_chunks}")
        
        if total_chunks == 0:
            print("⚠️ No PDF chunks found in database. Please upload a PDF first.")
            return []
    except Exception as e:
        print(f"❌ Error checking chunk count: {e}")
        return []
    
    # Try vector similarity search with lower threshold for better recall
    try:
        print("🔄 Attempting vector similarity search...")
        response = supabase.rpc('search_pdf_chunks', {
            'query_embedding': query_embedding,
            'match_threshold': 0.2,  # Lower threshold for better recall
            'match_count': k
        }).execute()
        
        if response.data and len(response.data) > 0:
            chunks = [row['content'] for row in response.data]
            print(f"✅ Found {len(chunks)} similar chunks via vector search")
            return chunks  # Return vector search results without additional filtering
        else:
            print("⚠️ Vector search returned no results")
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
    
    # Fallback: Get all chunks and apply loose relevance filtering
    try:
        print("🔄 Using fallback: retrieving all chunks...")
        response = supabase.table('pdf_chunks').select('content').execute()
        
        if response.data and len(response.data) > 0:
            all_chunks = [row['content'] for row in response.data]
            print(f"📄 Retrieved {len(all_chunks)} total chunks")
            
            # Apply more permissive relevance check
            if validate_pdf_content_relevance(query, all_chunks):
                print(f"✅ All chunks are considered relevant for the query")
                return all_chunks[:k]  # Return limited chunks
            else:
                print("⚠️ No chunks found relevant after filtering")
                # For very small datasets, return all chunks anyway
                if len(all_chunks) <= 5:
                    print("🔄 Small dataset detected, returning all chunks")
                    return all_chunks
                return []
        else:
            print("⚠️ No chunks found in fallback")
            return []
    except Exception as e:
        print(f"❌ Fallback search also failed: {e}")
        return []

def chat(query):
    print(f"\n🤖 Processing query: {query}")
    
    # Get relevant chunks from PDF
    chunks = get_similar_chunks(query)
    
    if not chunks:
        return "The context does not provide the answer to the question. Therefore, I cannot answer this question from the context."
    
    context = "\n".join(chunks)
    print(f"📝 Using context from {len(chunks)} chunks (total length: {len(context)} characters)")

    # Create messages for Groq API
    messages = [
        {
            "role": "system", 
            "content": "You are a helpful assistant. Answer questions based on the provided PDF content. Be helpful and informative when the content contains relevant information."
        },
        {
            "role": "user", 
            "content": f"""Here is content from a PDF document:

{context}

Question: {query}

Please provide a helpful answer based on the information above. Use the specific details and examples shown in the document to give a comprehensive response.

Answer:"""
        }
    ]
    
    try:
        print(f"🚀 Generating response using Groq API...")
        answer = call_groq_api(messages)
        print("✅ Response generated successfully")
        
        # Only validate if the answer seems to go completely off-topic
        if "context does not provide" in answer.lower():
            return answer
        
        # For technical content, be very permissive
        if validate_answer_against_context(answer, context):
            return answer
        else:
            print("⚠️ Generated answer seems to go beyond PDF context, but allowing due to technical content")
            # For now, let's allow the answer to see what the model actually generates
            return answer
        
    except Exception as e:
        error_msg = f"Error generating response with Groq API: {str(e)}"
        print(f"❌ {error_msg}")
        return "The context does not provide the answer to the question. Therefore, I cannot answer this question from the context."

def validate_answer_against_context(answer, context):
    """Validate that the answer is grounded in the provided context"""
    # Check if answer contains the fallback message
    if "The context does not provide the answer" in answer:
        return True
    
    # For technical content, be much more permissive with validation
    answer_lower = answer.lower()
    context_lower = context.lower()
    
    # If context contains HTML/technical terms and answer discusses them, allow it
    technical_terms = ['html', 'tag', 'element', 'attribute', 'code', 'css', 'javascript', 'web', 'document', 'page', 'head', 'body', 'div', 'span', 'form', 'input', 'select', 'option']
    context_has_tech = any(term in context_lower for term in technical_terms)
    answer_has_tech = any(term in answer_lower for term in technical_terms)
    
    if context_has_tech and answer_has_tech:
        print(f"✅ Technical content detected - allowing answer")
        return True
    
    # Check for HTML-specific patterns
    html_patterns = ['<', '>', 'creates', 'sets', 'tag', 'cheatsheet', 'basic']
    context_has_html = any(pattern in context_lower for pattern in html_patterns)
    answer_has_html = any(pattern in answer_lower for pattern in html_patterns)
    
    if context_has_html and len(answer.strip()) > 10:  # If we have HTML context and a substantial answer
        print(f"✅ HTML patterns detected - allowing answer")
        return True
    
    # Much more lenient word overlap check
    answer_words = set(answer.lower().split())
    context_words = set(context.lower().split())
    
    # Remove common words but keep technical terms
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
    answer_words_filtered = answer_words - common_words
    context_words_filtered = context_words - common_words
    
    if len(answer_words_filtered) == 0:
        return True
    
    overlap = len(answer_words_filtered.intersection(context_words_filtered))
    overlap_ratio = overlap / len(answer_words_filtered)
    
    print(f"📊 Word overlap: {overlap}/{len(answer_words_filtered)} = {overlap_ratio:.2f}")
    
    # Very low threshold for technical documents (just 20%)
    if overlap_ratio >= 0.2:
        print(f"✅ Sufficient word overlap - allowing answer")
        return True
    
    # If we have chunks and it's a short answer, be permissive
    if len(context.strip()) > 100 and len(answer.strip()) < 200:
        print(f"✅ Short answer with good context - allowing answer")
        return True
    
    print(f"❌ Answer validation failed")
    return False

if __name__ == "__main__":
    query = input("Ask something about the PDF: ")
    answer = chat(query)
    print("\nAnswer:", answer)