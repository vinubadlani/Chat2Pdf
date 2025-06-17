# ChatPDF Pro

AI-powered chat interface for PDF documents. Upload a PDF and have a conversation with it using RAG (Retrieval Augmented Generation).

## Features

- Upload and analyze PDF documents
- Ask questions about the document content
- Retrieval-based responses with AI
- Elegant and responsive UI
- Real-time typing animations

## Project Structure

- `frontend/`: React-based UI built with Vite
- `backend/`: Python FastAPI backend for handling PDF processing and queries

## Environment Setup

### Backend (.env)

Create a `.env` file in the root directory:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

### Frontend (.env)

Create a `.env` file in the frontend directory:

```
VITE_BACKEND_URL=http://localhost:8000
```

For production, update to your deployed backend URL.

## Running Locally

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
cd backend
uvicorn main:app --reload
```

### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Run the development server
npm run dev
```

## Deployment

### Backend
- Deploy to services like Render, Railway, or Vercel
- Set up required environment variables

### Frontend
- Deploy to Vercel or Netlify
- Configure the backend URL as an environment variable

## Technologies

- **Frontend**: React, Vite, Axios, Lucide React
- **Backend**: FastAPI, Supabase (vector storage), OpenAI (embeddings & completion)
- **PDF Processing**: PyPDF2 or similar libraries

## License

MIT