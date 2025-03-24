from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from ..utils.auth import oauth2_scheme, get_current_user
import jwt
from jwt.exceptions import PyJWTError
import os
from dotenv import load_dotenv
from starlette.types import ASGIApp, Receive, Scope, Send

# Load environment variables
load_dotenv()

# Get JWT secret key from environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "af9f6af88d4fc94c1038e80e53969edb364a05271dab0a499a73f826b03d6486")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# List of paths that don't require authentication
PUBLIC_PATHS = [
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/login/json",
    "/api/auth/register"
]

class AuthMiddleware:
    """Middleware to check JWT authentication for protected routes."""
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create a request object
        request = Request(scope)
        
        # Check if the path is public
        path = request.url.path
        if any(path.startswith(public_path) for public_path in PUBLIC_PATHS):
            await self.app(scope, receive, send)
            return
        
        # Get the authorization header
        headers = dict(request.headers)
        auth_header = headers.get(b"authorization", b"").decode()
        
        if not auth_header:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            await response(scope, receive, send)
            return
        
        # Extract the token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return
        except ValueError:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token format"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            await response(scope, receive, send)
            return
        
        # Validate the token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token payload"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return
        except PyJWTError:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token or token expired"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            await response(scope, receive, send)
            return
        
        # If we get here, the token is valid
        await self.app(scope, receive, send)
