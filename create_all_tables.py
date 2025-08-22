#!/usr/bin/env python
"""
Create all required database tables including users, pricing_plans, and ocr_data
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_all_tables():
    """Create all required tables for the application"""
    
    # SQL to create all tables
    create_tables_sql = """
    -- Create users table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        role VARCHAR(50) DEFAULT 'USER',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create pricing_plans table
    CREATE TABLE IF NOT EXISTS pricing_plans (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price_monthly DECIMAL(10,2) DEFAULT 0,
        price_yearly DECIMAL(10,2) DEFAULT 0,
        max_file_size INTEGER,
        daily_conversions_limit INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create uploads table
    CREATE TABLE IF NOT EXISTS uploads (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        file_name VARCHAR(255) NOT NULL,
        file_size INTEGER NOT NULL,
        status VARCHAR(50) DEFAULT 'PENDING',
        xml_path VARCHAR(500),
        is_xml_valid BOOLEAN,
        html_path VARCHAR(500),
        epub_path VARCHAR(500),
        mobi_path VARCHAR(500),
        page_count INTEGER,
        image_count INTEGER,
        formula_count INTEGER,
        processing_time FLOAT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create ocr_data table
    CREATE TABLE IF NOT EXISTS ocr_data (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255),
        extracted_text TEXT,
        extracted_json JSON,
        extracted_images JSON,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes
    CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
    CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
    CREATE INDEX IF NOT EXISTS ix_pricing_plans_id ON pricing_plans (id);
    CREATE INDEX IF NOT EXISTS ix_uploads_id ON uploads (id);
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
                
                # Create all tables
                cursor.execute(create_tables_sql)
                print("✅ Created all database tables successfully!")
                
                # Insert default data
                insert_default_data(cursor)
                
                # Verify tables were created
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                
                tables = cursor.fetchall()
                if tables:
                    print("\n📋 Created tables:")
                    for table in tables:
                        print(f"  - {table[0]}")
                
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
        print(f"❌ Error creating tables: {e}")
        return False
    
    print("❌ Could not connect to any database")
    return False

def insert_default_data(cursor):
    """Insert default data into tables"""
    try:
        # Insert default pricing plans
        cursor.execute("""
            INSERT INTO pricing_plans (name, description, price_monthly, price_yearly, max_file_size, daily_conversions_limit, is_active)
            VALUES 
            ('Free', 'Basic e-book processing', 0, 0, 10485760, 3, TRUE),
            ('Premium', 'Advanced e-book processing with higher limits', 9.99, 99.99, 104857600, 20, TRUE)
            ON CONFLICT DO NOTHING;
        """)
        
        # Insert default admin user (password: adminpassword)
        cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, role, is_active)
            VALUES ('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq/Uy/O', 'Admin User', 'ADMIN', TRUE)
            ON CONFLICT (email) DO NOTHING;
        """)
        
        print("✅ Inserted default data")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not insert default data: {e}")

if __name__ == "__main__":
    if create_all_tables():
        print("\n🎉 Success! All database tables are ready.")
        print("You can now restart your FastAPI server.")
        print("\nDefault admin user:")
        print("  Email: admin@example.com")
        print("  Password: adminpassword")
    else:
        print("\n💡 Troubleshooting:")
        print("1. Make sure PostgreSQL service is running")
        print("2. Check if password '123456789' is correct")
        print("3. Try connecting with pgAdmin or another tool first")
