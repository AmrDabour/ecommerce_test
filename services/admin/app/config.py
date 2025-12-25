"""
Configuration for Admin Service
"""

import os

def get_database_url(db_name=None):
    """Get database URL from environment variables

    Args:
        db_name: Specific database name (admin_db, auth_db, product_db, order_db)
                 If None, uses DB_NAME from environment (defaults to admin_db)
    """
    DB_HOST = os.getenv("DB_HOST", "postgres")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "admin_service")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "admin_secure_pass_456!")

    # Use provided db_name or fall back to environment variable
    if db_name is None:
        db_name = os.getenv("DB_NAME", "admin_db")

    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"

def get_auth_db_url():
    """Get Auth database URL"""
    auth_db = os.getenv("AUTH_DB_NAME", "auth_db")
    return get_database_url(auth_db)

def get_product_db_url():
    """Get Product database URL"""
    product_db = os.getenv("PRODUCT_DB_NAME", "product_db")
    return get_database_url(product_db)

def get_order_db_url():
    """Get Order database URL"""
    order_db = os.getenv("ORDER_DB_NAME", "order_db")
    return get_database_url(order_db)

def get_admin_db_url():
    """Get Admin database URL"""
    admin_db = os.getenv("ADMIN_DB_NAME", "admin_db")
    return get_database_url(admin_db)

