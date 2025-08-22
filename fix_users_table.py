#!/usr/bin/env python
"""
Fix users table by adding missing confirm_password column
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_users_table():
    """Add missing confirm_password column to users table"""
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="ebook_app",
            user="postgres",
            password="123456789"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if confirm_password column exists
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'confirm_password'
        """)
        
        if not cursor.fetchone():
            # Add the missing column
            cursor.execute("ALTER TABLE users ADD COLUMN confirm_password VARCHAR(255)")
            print("✅ Added confirm_password column to users table")
        else:
            print("ℹ️  confirm_password column already exists")
        
        # Verify the table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Users table structure:")
        for col_name, col_type, nullable in columns:
            print(f"  - {col_name}: {col_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing users table: {e}")
        return False

if __name__ == "__main__":
    if fix_users_table():
        print("\n🎉 Users table fixed successfully!")
        print("You can now restart your FastAPI server.")
    else:
        print("\n💡 Please check your database connection and try again.")
