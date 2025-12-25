"""
Shared utilities across all microservices
"""
import httpx
from typing import Optional, Dict, Any
from functools import wraps
import asyncio


async def verify_token_with_auth_service(token: str, auth_service_url: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token by calling the auth service
    Used by other microservices to validate user tokens
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{auth_service_url}/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on failure
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator
