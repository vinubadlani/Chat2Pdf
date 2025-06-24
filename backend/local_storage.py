import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class LocalPDFStorage:
    def __init__(self, storage_file="pdf_chunks.json"):
        self.storage_file = storage_file
        self.chunks = []
        self.load_chunks()
    
    def load_chunks(self):
        """Load chunks from local JSON file"""
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
                print(f"📁 Loaded {len(self.chunks)} chunks from local storage")
        else:
            self.chunks = []
            print("📁 No existing chunks found, starting fresh")
    
    def save_chunks(self):
        """Save chunks to local JSON file"""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved {len(self.chunks)} chunks to local storage")
    
    def add_chunk(self, content, metadata=None):
        """Add a new chunk with embedding"""
        embedding = embedding_model.encode(content).tolist()
        chunk = {
            'content': content,
            'embedding': embedding,
            'metadata': metadata or {}
        }
        self.chunks.append(chunk)
        self.save_chunks()
        return True
    
    def clear_chunks(self):
        """Clear all chunks"""
        self.chunks = []
        self.save_chunks()
        print("🗑️ Cleared all chunks from local storage")
    
    def search_similar_chunks(self, query, k=5, threshold=0.1):
        """Search for similar chunks using cosine similarity"""
        if not self.chunks:
            return []
        
        query_embedding = embedding_model.encode(query)
        
        # Calculate similarities
        similarities = []
        for i, chunk in enumerate(self.chunks):
            chunk_embedding = np.array(chunk['embedding'])
            similarity = cosine_similarity([query_embedding], [chunk_embedding])[0][0]
            similarities.append((i, similarity, chunk))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and return top k
        results = []
        for i, similarity, chunk in similarities[:k]:
            if similarity >= threshold:
                results.append(chunk['content'])
                print(f"✅ Found similar chunk (similarity: {similarity:.3f})")
        
        return results
    
    def get_all_chunks(self):
        """Get all chunk contents"""
        return [chunk['content'] for chunk in self.chunks]
    
    def get_chunk_count(self):
        """Get total number of chunks"""
        return len(self.chunks)

# Global storage instance
local_storage = LocalPDFStorage()