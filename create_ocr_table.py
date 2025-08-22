#!/usr/bin/env python
"""
Direct script to create ocr_data table without using migrations
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_ocr_table():
    """Create the ocr_data table directly"""
    
    # SQL to create the ocr_data table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS ocr_data (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255),
        extracted_text TEXT,
        extracted_json JSON,
        extracted_images JSON,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS ix_ocr_data_id ON ocr_data (id);
    CREATE INDEX IF NOT EXISTS ix_ocr_data_filename ON ocr_data (filename);
    """
    
    try:
        # Try different database connections
        databases_to_try = ["ebook_app", "postgres"]
        
        for db_name in databases_to_try:
            try:
                print(f"Trying to connect to database: {db_name}")
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database=db_name,
                    user="postgres",
                    password="123456789"
                )
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                cursor = conn.cursor()
                
                # If connecting to postgres db, create ebook_app first
                if db_name == "postgres":
                    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'ebook_app'")
                    if not cursor.fetchone():
                        cursor.execute("CREATE DATABASE ebook_app")
                        print("✅ Created database 'ebook_app'")
                    
                    # Now connect to ebook_app
                    cursor.close()
                    conn.close()
                    
                    conn = psycopg2.connect(
                        host="localhost",
                        port=5432,
                        database="ebook_app",
                        user="postgres",
                        password="123456789"
                    )
                    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    cursor = conn.cursor()
                
                # Create the ocr_data table
                cursor.execute(create_table_sql)
                print("✅ Created ocr_data table successfully!")
                
                # Verify table was created
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'ocr_data'
                    ORDER BY ordinal_position;
                """)
                
                columns = cursor.fetchall()
                if columns:
                    print("\n📋 Table structure:")
                    for col_name, col_type in columns:
                        print(f"  - {col_name}: {col_type}")
                
                cursor.close()
                conn.close()
                return True
                
            except psycopg2.OperationalError as e:
                if "does not exist" in str(e) and db_name == "ebook_app":
                    print(f"Database {db_name} doesn't exist, trying postgres...")
                    continue
                else:
                    print(f"Connection failed for {db_name}: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
    
    print("❌ Could not connect to any database")
    return False

if __name__ == "__main__":
    if create_ocr_table():
        print("\n🎉 Success! The ocr_data table is ready.")
        print("You can now restart your FastAPI server and try the OCR upload again.")
    else:
        print("\n💡 Troubleshooting:")
        print("1. Make sure PostgreSQL service is running")
        print("2. Check if password '123456789' is correct")
        print("3. Try connecting with pgAdmin or another tool first")
