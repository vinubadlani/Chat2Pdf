#!/usr/bin/env python3
"""
Script to test Supabase database connection and display connection info
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from the backend directory
load_dotenv(dotenv_path='backend/.env')

def test_connection():
    """Test database connection and display connection info"""
    try:
        # Get connection parameters from environment
        host = os.getenv("SUPABASE_HOST")
        database = os.getenv("SUPABASE_DB") 
        user = os.getenv("SUPABASE_USER")
        password = os.getenv("SUPABASE_PASSWORD")
        port = os.getenv("SUPABASE_PORT")
        
        print("🔍 Connection Parameters:")
        print(f"   Host: {host}")
        print(f"   Database: {database}")
        print(f"   Username: {user}")
        print(f"   Port: {port}")
        print(f"   Password: {'*' * len(password) if password else 'Not set'}")
        print()
        
        # Validate all parameters are present
        if not all([host, database, user, password, port]):
            print("❌ Missing required environment variables")
            print("   Make sure backend/.env file contains all database credentials")
            return False
        
        # Test connection
        print("🔄 Testing connection...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        
        # Get database info
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        
        cur.execute("SELECT current_user;")
        current_user = cur.fetchone()[0]
        
        cur.execute("SELECT current_database();")
        current_db = cur.fetchone()[0]
        
        # Check if pgvector extension exists
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
        has_vector = cur.fetchone()[0]
        
        # Check if pdf_chunks table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'pdf_chunks'
            );
        """)
        has_table = cur.fetchone()[0]
        
        print("✅ Connection successful!")
        print(f"   PostgreSQL Version: {version}")
        print(f"   Connected as user: {current_user}")
        print(f"   Current database: {current_db}")
        print(f"   pgvector extension: {'✅ Installed' if has_vector else '❌ Not installed'}")
        print(f"   pdf_chunks table: {'✅ Exists' if has_table else '❌ Not found'}")
        
        # Provide setup instructions if needed
        if not has_vector or not has_table:
            print("\n🔧 Setup Required:")
            if not has_vector:
                print("   1. Enable pgvector extension in Supabase")
            if not has_table:
                print("   2. Run the setup_database.sql script in Supabase SQL Editor")
        
        cur.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Possible solutions:")
        print("   1. Check your Supabase project is running")
        print("   2. Verify database credentials in backend/.env")
        print("   3. Ensure your IP is allowed in Supabase settings")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Supabase Database Connection Test")
    print("=" * 40)
    test_connection()