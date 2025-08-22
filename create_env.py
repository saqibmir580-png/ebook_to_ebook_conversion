#!/usr/bin/env python
"""
Create .env file from .env.example
"""

import shutil
import os

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    env_example = ".env.example"
    env_file = ".env"
    
    if not os.path.exists(env_file) and os.path.exists(env_example):
        shutil.copy(env_example, env_file)
        print(f"✅ Created {env_file} from {env_example}")
        print("Please update the values in .env as needed")
    elif os.path.exists(env_file):
        print(f"⏭️  {env_file} already exists")
    else:
        print(f"❌ {env_example} not found")

if __name__ == "__main__":
    create_env_file()