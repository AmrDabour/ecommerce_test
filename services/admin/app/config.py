"""
Configuration for Admin Service
"""

import os

def get_database_url():
    """Get database URL from environment variables"""
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
    DB_NAME = os.getenv("DB_NAME", "ecommerce_db")
    DB_PORT = os.getenv("DB_PORT", "5432")
    
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

