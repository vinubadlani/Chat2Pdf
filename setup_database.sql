-- SQL script to set up the pdf_chunks table in Supabase
-- Run this in your Supabase SQL Editor

-- Enable the pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the pdf_chunks table with 384-dimensional embeddings for sentence-transformers
CREATE TABLE IF NOT EXISTS pdf_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index on the embedding column for faster similarity searches
CREATE INDEX IF NOT EXISTS pdf_chunks_embedding_idx ON pdf_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create an index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS pdf_chunks_created_at_idx ON pdf_chunks (created_at);

-- Optional: Create a function to search for similar chunks
CREATE OR REPLACE FUNCTION search_pdf_chunks(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id int,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE sql
AS $$
    SELECT
        pdf_chunks.id,
        pdf_chunks.content,
        pdf_chunks.metadata,
        1 - (pdf_chunks.embedding <=> query_embedding) AS similarity
    FROM pdf_chunks
    WHERE 1 - (pdf_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY pdf_chunks.embedding <=> query_embedding
    LIMIT match_count;
$$;