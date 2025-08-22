#!/usr/bin/env python3
"""
Complete Setup Script
1. Creates .env file from .env.example
2. Fixes database schema (adds missing file_path column)
3. Starts the FastAPI server
"""

import os
import sys
import sqlite3
import shutil
import subprocess
from pathlib import Path

def setup_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    try:
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from .env.example")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def fix_database_schema():
    """Fix SQLite database schema by adding missing file_path column"""
    print("🔧 Fixing database schema...")
    
    db_path = "ebook_app.db"
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if uploads table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploads';")
        if not cursor.fetchone():
            print("Creating uploads table with correct schema...")
            # Create uploads table with all required columns
            cursor.execute("""
                CREATE TABLE uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_name VARCHAR NOT NULL,
                    file_path VARCHAR NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'PENDING',
                    xml_path VARCHAR,
                    is_xml_valid BOOLEAN,
                    html_path VARCHAR,
                    epub_path VARCHAR,
                    mobi_path VARCHAR,
                    page_count INTEGER,
                    image_count INTEGER,
                    formula_count INTEGER,
                    processing_time REAL,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create users table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR UNIQUE NOT NULL,
                    full_name VARCHAR,
                    hashed_password VARCHAR NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    role VARCHAR DEFAULT 'FREE',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            conn.close()
            print("✓ Database tables created successfully")
            return True
        
        # Check if file_path column exists
        cursor.execute("PRAGMA table_info(uploads);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'file_path' in columns:
            print("✓ file_path column already exists")
            conn.close()
            return True
        
        # Add the missing file_path column
        print("Adding file_path column to uploads table...")
        cursor.execute("ALTER TABLE uploads ADD COLUMN file_path TEXT NOT NULL DEFAULT '';")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✓ file_path column added successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    try:
        # Use uvicorn to start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main execution function"""
    print("🔧 Complete Setup Script")
    print("This will set up your environment and start the server")
    
    # Check if we're in the right directory
    if not os.path.exists('app'):
        print("❌ Error: Please run this script from the backend directory")
        sys.exit(1)
    
    # Step 1: Setup environment file
    if not setup_env_file():
        print("❌ Failed to setup environment file")
        sys.exit(1)
    
    # Step 2: Fix database schema
    if not fix_database_schema():
        print("❌ Failed to fix database schema")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")
    print("🌐 Server will start at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/api/v1/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Step 3: Start the server
    start_server()

if __name__ == "__main__":
    main()
