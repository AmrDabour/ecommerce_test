"""
Admin Service - Main Application
Microservice for E-Commerce Admin Dashboard

NOTE: This admin service connects to admin_db as primary database.
For cross-database admin operations (viewing Users, Products, Orders from other DBs),
you have two options:
1. Use PostgreSQL Foreign Data Wrapper (FDW) - recommended for production
2. Make API calls to respective services - current approach

For now, we focus on admin_db (notifications, messages, audit_logs, system_settings).
User/Product/Order management should be done via their respective service APIs.
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

from config import get_admin_db_url

# Database connection - Connect to admin_db
DATABASE_URL = get_admin_db_url()
print(f"🔌 Connecting to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Auto-import foreign schemas on startup - HARDCODED SOLUTION
def import_foreign_schemas_if_needed():
    """Import foreign schemas automatically on every startup - hardcoded solution"""
    import time
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with engine.begin() as conn:
                # Check if any foreign tables from auth_db exist
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_foreign_table ft
                    JOIN pg_foreign_server fs ON ft.ftserver = fs.oid
                    WHERE fs.srvname = 'auth_db_server'
                """))
                auth_tables_count = result.scalar()
                
                # Import auth_db if no tables exist
                if auth_tables_count == 0:
                    print(f"📥 [Attempt {attempt + 1}] Importing auth_db foreign schema...")
                    conn.execute(text("IMPORT FOREIGN SCHEMA public FROM SERVER auth_db_server INTO public"))
                    print("✅ Imported auth_db schema")
                else:
                    print(f"✅ auth_db schema already imported ({auth_tables_count} tables)")
                
                # Check product_db
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_foreign_table ft
                    JOIN pg_foreign_server fs ON ft.ftserver = fs.oid
                    WHERE fs.srvname = 'product_db_server'
                """))
                product_tables_count = result.scalar()
                
                if product_tables_count == 0:
                    print(f"📥 [Attempt {attempt + 1}] Importing product_db foreign schema...")
                    conn.execute(text("IMPORT FOREIGN SCHEMA public FROM SERVER product_db_server INTO public"))
                    print("✅ Imported product_db schema")
                else:
                    print(f"✅ product_db schema already imported ({product_tables_count} tables)")
                
                # Check order_db
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_foreign_table ft
                    JOIN pg_foreign_server fs ON ft.ftserver = fs.oid
                    WHERE fs.srvname = 'order_db_server'
                """))
                order_tables_count = result.scalar()
                
                if order_tables_count == 0:
                    print(f"📥 [Attempt {attempt + 1}] Importing order_db foreign schema...")
                    conn.execute(text("IMPORT FOREIGN SCHEMA public FROM SERVER order_db_server INTO public"))
                    print("✅ Imported order_db schema")
                else:
                    print(f"✅ order_db schema already imported ({order_tables_count} tables)")
                
                # If we got here, all imports succeeded
                print("✅ All foreign schemas imported successfully!")
                return
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Import attempt {attempt + 1} failed: {e}")
                print(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"❌ Failed to import foreign schemas after {max_retries} attempts: {e}")
                print("⚠️  Admin panel may not work until schemas are imported manually")

# Import foreign schemas on startup - ALWAYS RUNS
print("🔄 Checking and importing foreign schemas on startup...")
import_foreign_schemas_if_needed()

# Create FastAPI app
app = FastAPI(
    title="E-Commerce Admin Dashboard",
    description="Admin panel for managing e-commerce platform",
    version="1.0.0"
)

# Create admin interface
admin = Admin(app, engine, title="E-Commerce Admin")

# Register admin views - Now with FDW setup, we can access all databases!
from admin_views_all import register_all_admin_views
register_all_admin_views(admin, {})

# Register API routes for cross-service data access
from api_views import router as api_router
app.include_router(api_router)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {
        "service": "Admin Dashboard",
        "admin_panel": "/admin",
        "admin_db_tables": "Notifications, Messages, Audit Logs, System Settings",
        "cross_service_api": "/api/users, /api/products, /api/orders, /api/stats/dashboard",
        "api_docs": "/docs",
        "version": "1.0.0",
        "note": "User/Product/Order data accessed via API calls to respective services"
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

