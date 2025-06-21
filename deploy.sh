#!/bin/bash

# Chat2PDF Vercel Deployment Script
# This script helps deploy both backend and frontend to Vercel

echo "🚀 Chat2PDF Vercel Deployment Helper"
echo "====================================="

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

echo ""
echo "📋 Deployment Instructions:"
echo ""
echo "1. BACKEND DEPLOYMENT:"
echo "   - Deploy from the root directory (chat2pdf/)"
echo "   - This will deploy the FastAPI backend"
echo "   - Make note of the backend URL for frontend configuration"
echo ""
echo "2. FRONTEND DEPLOYMENT:"
echo "   - Deploy from the frontend/ directory"
echo "   - Set VITE_BACKEND_URL environment variable to backend URL"
echo ""

read -p "Deploy backend now? (y/n): " deploy_backend

if [[ $deploy_backend == "y" || $deploy_backend == "Y" ]]; then
    echo ""
    echo "🔧 Deploying Backend..."
    echo "Make sure you have set these environment variables in Vercel:"
    echo "- SUPABASE_URL"
    echo "- SUPABASE_ANON_KEY" 
    echo "- GROQ_API_KEY"
    echo ""
    
    # Deploy backend from root directory
    vercel --prod
    
    echo ""
    echo "✅ Backend deployment initiated!"
    echo "📝 Copy the deployment URL and use it for frontend configuration"
    echo ""
fi

read -p "Deploy frontend now? (y/n): " deploy_frontend

if [[ $deploy_frontend == "y" || $deploy_frontend == "Y" ]]; then
    echo ""
    read -p "Enter your backend URL (e.g., https://your-backend.vercel.app): " backend_url
    
    if [[ -z "$backend_url" ]]; then
        echo "❌ Backend URL is required for frontend deployment"
        exit 1
    fi
    
    echo ""
    echo "🔧 Deploying Frontend..."
    echo "Setting VITE_BACKEND_URL=$backend_url"
    echo ""
    
    # Change to frontend directory and deploy
    cd frontend
    vercel --prod -e VITE_BACKEND_URL="$backend_url"
    
    echo ""
    echo "✅ Frontend deployment initiated!"
    echo ""
fi

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📚 Next Steps:"
echo "1. Test your backend health: [backend-url]/health"
echo "2. Test your frontend: [frontend-url]"
echo "3. Upload a PDF and test the chat functionality"
echo ""
echo "🔧 Troubleshooting:"
echo "- If CORS errors persist, check the allowed origins in vercel_app.py"
echo "- Verify environment variables are set in Vercel dashboard"
echo "- Check logs in Vercel dashboard for any errors"