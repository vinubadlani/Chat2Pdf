# Chat2PDF Vercel Deployment Guide

This guide will help you deploy your Chat2PDF application to Vercel with separate backend and frontend hosting to eliminate CORS issues.

## 🏗️ Architecture Overview

- **Backend**: FastAPI application deployed as Vercel serverless function
- **Frontend**: React (Vite) application deployed as static site
- **Database**: Supabase (external)
- **AI Model**: Groq API (external)

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally with `npm install -g vercel`
3. **Environment Variables**: Have your Supabase and Groq credentials ready

## 🚀 Deployment Steps

### Step 1: Deploy Backend

1. **Navigate to project root directory**:
   ```bash
   cd /path/to/chat2pdf
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy backend**:
   ```bash
   vercel --prod
   ```

4. **Set environment variables in Vercel Dashboard**:
   - Go to your project in Vercel Dashboard
   - Navigate to Settings → Environment Variables
   - Add the following variables:
     ```
     SUPABASE_URL=your_supabase_project_url
     SUPABASE_ANON_KEY=your_supabase_anon_key
     GROQ_API_KEY=your_groq_api_key
     ENVIRONMENT=production
     ```

5. **Note the backend URL** (e.g., `https://chat2pdf-backend-abc123.vercel.app`)

### Step 2: Deploy Frontend

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Create environment configuration**:
   ```bash
   cp .env.example .env.local
   ```

3. **Edit `.env.local`** with your backend URL:
   ```
   VITE_BACKEND_URL=https://your-backend-url.vercel.app
   ```

4. **Deploy frontend**:
   ```bash
   vercel --prod
   ```

5. **Set environment variable during deployment**:
   ```bash
   vercel --prod -e VITE_BACKEND_URL="https://your-backend-url.vercel.app"
   ```

## 🔧 Alternative: Automated Deployment

Use the provided deployment script:

```bash
./deploy.sh
```

This script will guide you through both backend and frontend deployments.

## ✅ Verification

### Backend Health Check
Visit: `https://your-backend-url.vercel.app/health`

Expected response:
```json
{
  "status": "healthy",
  "server": "online",
  "database": "connected",
  "embedding_model": "loaded"
}
```

### Frontend Test
1. Visit your frontend URL
2. Upload a PDF file
3. Ask a question about the PDF
4. Verify the response

## 🐛 Troubleshooting

### CORS Errors
- Verify backend URL is correctly set in frontend environment variables
- Check Vercel logs for backend deployment issues
- Ensure both apps are deployed to the same Vercel account

### Backend Issues
- Check environment variables are set in Vercel Dashboard
- Verify Supabase connection details
- Check Groq API key is valid

### Frontend Issues
- Ensure `VITE_BACKEND_URL` environment variable is set correctly
- Check browser network tab for failed requests
- Verify backend is responding at `/health` endpoint

## 📁 File Structure

```
chat2pdf/
├── backend/
│   ├── vercel_app.py         # Vercel-optimized FastAPI app
│   ├── requirements.txt      # Python dependencies
│   └── ...                   # Other backend files
├── frontend/
│   ├── vercel.json          # Frontend Vercel config
│   ├── .env.example         # Environment template
│   └── ...                  # React app files
├── vercel.json              # Backend Vercel config
└── deploy.sh                # Deployment helper script
```

## 🔐 Security Notes

- Never commit `.env.local` or actual API keys to git
- Use Vercel's environment variables for sensitive data
- Backend CORS is configured to allow your frontend domain

## 🔄 Updates

To update your deployment:

1. **Backend updates**: Redeploy from project root
2. **Frontend updates**: Redeploy from frontend directory
3. **Environment changes**: Update in Vercel Dashboard

## 📞 Support

If you encounter issues:
1. Check Vercel deployment logs
2. Verify all environment variables are set
3. Test backend endpoints directly
4. Check browser console for frontend errors