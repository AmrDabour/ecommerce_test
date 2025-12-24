"""
Admin Service - Main Application
Microservice for E-Commerce Admin Dashboard
"""

from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add shared models to path
shared_path = os.path.join(os.path.dirname(__file__), '../../shared')
if not os.path.exists(shared_path):
    # Docker path
    shared_path = '/app/services/shared'
sys.path.insert(0, shared_path)

from admin_views import register_admin_views
from config import get_database_url

# Database connection
DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(
    title="E-Commerce Admin Dashboard",
    description="Admin panel for managing e-commerce platform",
    version="1.0.0"
)

# Create admin interface
admin = Admin(app, engine, title="E-Commerce Admin")

# Register all admin views
register_admin_views(admin)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {
        "service": "Admin Dashboard",
        "admin_panel": "/admin",
        "api_docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting E-Commerce Admin Dashboard Service...")
    print("📊 Admin Panel: http://localhost:8000/admin")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

