"""
API-based Admin Views
Proxy endpoints to access data from other microservices
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import httpx
import os

router = APIRouter(prefix="/api", tags=["Admin API"])

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8002")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8003")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8004")


@router.get("/users")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """Get users from Auth service"""
    try:
        async with httpx.AsyncClient() as client:
            params = {"skip": skip, "limit": limit}
            if search:
                params["search"] = search

            response = await client.get(
                f"{AUTH_SERVICE_URL}/users",
                params=params,
                timeout=10.0
            )

            if response.status_code == 404:
                # Auth service doesn't have this endpoint yet
                return {
                    "message": "Auth service endpoint not implemented yet",
                    "note": "Implement GET /users endpoint in auth service"
                }

            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error calling auth service: {str(e)}")


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get specific user from Auth service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/users/{user_id}",
                timeout=10.0
            )

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="User not found")

            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error calling auth service: {str(e)}")


@router.get("/products")
async def get_products(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """Get products from Product service"""
    try:
        async with httpx.AsyncClient() as client:
            params = {"skip": skip, "limit": limit}
            if status:
                params["status"] = status

            response = await client.get(
                f"{PRODUCT_SERVICE_URL}/products",
                params=params,
                timeout=10.0
            )

            if response.status_code == 404:
                return {
                    "message": "Product service endpoint not implemented yet",
                    "note": "Implement GET /products endpoint in product service"
                }

            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error calling product service: {str(e)}")


@router.get("/orders")
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """Get orders from Order service"""
    try:
        async with httpx.AsyncClient() as client:
            params = {"skip": skip, "limit": limit}
            if status:
                params["status"] = status

            response = await client.get(
                f"{ORDER_SERVICE_URL}/orders",
                params=params,
                timeout=10.0
            )

            if response.status_code == 404:
                return {
                    "message": "Order service endpoint not implemented yet",
                    "note": "Implement GET /orders endpoint in order service"
                }

            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error calling order service: {str(e)}")


@router.get("/stats/dashboard")
async def get_dashboard_stats():
    """
    Get dashboard statistics from all services
    Aggregates data from Auth, Product, and Order services
    """
    stats = {
        "users": {"total": 0, "error": None},
        "products": {"total": 0, "error": None},
        "orders": {"total": 0, "error": None}
    }

    async with httpx.AsyncClient() as client:
        # Get user count
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/users/count", timeout=5.0)
            if response.status_code == 200:
                stats["users"]["total"] = response.json().get("count", 0)
            else:
                stats["users"]["error"] = "Endpoint not implemented"
        except Exception as e:
            stats["users"]["error"] = str(e)

        # Get product count
        try:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products/count", timeout=5.0)
            if response.status_code == 200:
                stats["products"]["total"] = response.json().get("count", 0)
            else:
                stats["products"]["error"] = "Endpoint not implemented"
        except Exception as e:
            stats["products"]["error"] = str(e)

        # Get order count
        try:
            response = await client.get(f"{ORDER_SERVICE_URL}/orders/count", timeout=5.0)
            if response.status_code == 200:
                stats["orders"]["total"] = response.json().get("count", 0)
            else:
                stats["orders"]["error"] = "Endpoint not implemented"
        except Exception as e:
            stats["orders"]["error"] = str(e)

    return stats
