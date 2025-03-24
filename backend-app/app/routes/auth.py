from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..models.auth import Token, LoginRequest, RegisterRequest
from pydantic import BaseModel
from ..models.user import UserResponse
from ..utils.auth import authenticate_user, create_access_token, hash_password, ACCESS_TOKEN_EXPIRE_MINUTES, is_token_valid
from ..database import prisma

router = APIRouter()

# Model for token validation request
class TokenValidationRequest(BaseModel):
    token: str

# Model for token validation response
class TokenValidationResponse(BaseModel):
    is_valid: bool

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that returns a JWT token."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user info
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    print(user.name)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "asgl_id": user.asgl_id,
            "mobile_phone": user.mobile_phone,
            "avatar_url": user.avatar_url,
        }
    }

@router.post("/login/json", response_model=Token)
async def login_json(login_data: LoginRequest):
    """Login endpoint that accepts JSON and returns a JWT token."""
    user = await authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user info
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register(register_data: RegisterRequest):
    """Register a new user."""
    # Check if username already exists
    existing_user = await prisma.user.find_unique(where={"username": register_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    hashed_password = hash_password(register_data.password)
    new_user = await prisma.user.create(
        data={
            "username": register_data.username,
            "password": hashed_password,
            "name": register_data.name
        }
    )
    
    return new_user

@router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest):
    """
    Validate if a JWT token is still valid (not expired).
    
    Args:
        request: The request containing the token to validate
        
    Returns:
        TokenValidationResponse: Object containing whether the token is valid
    """
    try:
        is_valid = await is_token_valid(request.token)
        return {"is_valid": is_valid}
    except HTTPException as e:
        # Return false if token is malformed instead of raising an exception
        return {"is_valid": False}
