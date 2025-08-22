#!/usr/bin/env python
"""
Fix database by running migrations programmatically
"""

import os
import sys
from pathlib import Path

# Add the project directory to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_existing_data():
    """Fix existing uploads table data before migration"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # Check if uploads table exists and has null file_name values
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'uploads'
            """))
            
            if result.scalar() > 0:
                # Update null file_name values with a default
                conn.execute(text("""
                    UPDATE uploads 
                    SET filename = COALESCE(filename, 'unknown_file') 
                    WHERE filename IS NULL
                """))
                conn.commit()
                print("✅ Fixed existing null filename values")
            
    except Exception as e:
        print(f"Note: Could not fix existing data: {e}")

def fix_database():
    """Run Alembic upgrade to create missing tables"""
    try:
        # Fix existing data first
        fix_existing_data()
        
        # Set up Alembic config with correct path
        config_path = project_root / "migrations" / "alembic.ini"
        alembic_cfg = Config(str(config_path))
        
        print("Checking current migration status...")
        try:
            command.current(alembic_cfg, verbose=True)
        except Exception as e:
            print(f"Current status: {e}")
        
        print("\nRunning database migration to create ocr_data table...")
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Database migration completed successfully!")
        print("The ocr_data table should now be created.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        print("\nAlternative solutions:")
        print("1. Run: cd migrations && alembic upgrade head")
        print("2. Or run: alembic -c migrations/alembic.ini upgrade head")
        return False

if __name__ == "__main__":
    fix_database()
