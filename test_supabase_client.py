#!/usr/bin/env python3
"""
Alternative Supabase connection test using supabase-py client
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from the backend directory
load_dotenv(dotenv_path='backend/.env')

def test_supabase_client():
    """Test Supabase connection using the Python client"""
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        print("🔍 Supabase Client Test:")
        print(f"   URL: {url}")
        print(f"   Key: {key[:20]}...{key[-10:] if key else 'Not set'}")
        print()
        
        if not url or not key:
            print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(url, key)
        
        # Test connection by checking if pdf_chunks table exists
        print("🔄 Testing Supabase client connection...")
        
        # Try to query the table (this will fail gracefully if table doesn't exist)
        response = supabase.table('pdf_chunks').select("count", count="exact").limit(1).execute()
        
        print("✅ Supabase client connection successful!")
        print(f"   Table access: Working")
        print(f"   Row count: {response.count if hasattr(response, 'count') else 'Unknown'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase client test failed: {e}")
        print("\n💡 This might indicate:")
        print("   - Table 'pdf_chunks' doesn't exist yet")
        print("   - Need to run the database setup script")
        print("   - RLS (Row Level Security) policies need configuration")
        return False

if __name__ == "__main__":
    print("🧪 Alternative Supabase Connection Test")
    print("=" * 45)
    test_supabase_client()