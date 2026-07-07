from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from Core.config import settings

# This tells FastAPI to look for a header named "X-API-Key" in incoming requests
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validates the API key from the frontend. 
    If it doesn't match the .env file, the request is rejected immediately.
    """
    if api_key_header == settings.FRONTEND_API_KEY:
        return api_key_header
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API credentials. Access Denied."
    )