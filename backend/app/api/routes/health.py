from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/auth-debug")
async def auth_debug(request: Request):
    """Temporary debug endpoint to check auth headers."""
    auth_header = request.headers.get("Authorization", "")
    has_bearer = auth_header.startswith("Bearer ") if auth_header else False
    token_preview = auth_header[7:27] + "..." if has_bearer and len(auth_header) > 27 else auth_header
    
    result = {"hasAuthHeader": bool(auth_header), "hasBearer": has_bearer, "tokenPreview": token_preview}
    
    if has_bearer:
        token = auth_header.split(" ", 1)[1]
        try:
            from app.core.auth import verify_clerk_token
            payload = verify_clerk_token(token)
            result["verified"] = True
            result["sub"] = payload.get("sub", "")
            result["exp"] = payload.get("exp", 0)
        except Exception as e:
            result["verified"] = False
            result["error"] = str(e)
    
    return result
