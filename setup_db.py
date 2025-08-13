#!/usr/bin/env python
"""
Setup script to create initial database structure and insert seed data.
This should be run after setting up the database connection.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base_class import Base
from app.models.user import User, UserRole
from app.models.pricing import PricingPlan
from app.utils.jwt_handler import get_password_hash


def setup_db():
    """Create tables and insert initial data"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            # Create admin user
            admin = User(
                email="admin@example.com",
                hashed_password=get_password_hash("adminpassword"),
                full_name="Admin User",
                role=UserRole.ADMIN
            )
            db.add(admin)
            print("Admin user created.")
        else:
            print("Admin user already exists.")
        
        # Check if pricing plans exist
        plans = db.query(PricingPlan).all()
        if not plans:
            # Create pricing plans
            free_plan = PricingPlan(
                name="Free",
                description="Basic e-book processing",
                price_monthly=0,
                price_yearly=0,
                max_file_size=10485760,  # 10MB
                daily_conversions_limit=3,
                is_active=True
            )
            
            premium_plan = PricingPlan(
                name="Premium",
                description="Advanced e-book processing with higher limits",
                price_monthly=9.99,
                price_yearly=99.99,
                max_file_size=104857600,  # 100MB
                daily_conversions_limit=20,
                is_active=True
            )
            
            db.add(free_plan)
            db.add(premium_plan)
            print("Pricing plans created.")
        else:
            print("Pricing plans already exist.")
        
        # Commit changes
        db.commit()
        
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    setup_db()