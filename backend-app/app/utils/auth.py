from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..database import prisma
import hashlib
import os
import requests
import json
import logging
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get JWT secret key from environment variables or use a default for development
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
# Access token expires after 30 days
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days in minutes

# ASGL API configuration
ASGL_AUTH_API = os.getenv("ASGL_AUTH_API", "https://id.asgl.net.vn/api/auth/login")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against a provided password."""
    return hash_password(plain_password) == hashed_password

async def authenticate_with_asgl_api(username: str, password: str) -> Union[Dict[str, Any], None]:
    """
    Authenticate with ASGL API.
    
    Args:
        username: The username to authenticate
        password: The password to authenticate
        
    Returns:
        Dict containing user information if authentication is successful, None otherwise
    """
    try:
        # Prepare form data for API request
        form_data = {
            'login': username,
            'password': password
        }
        
        # Make request to ASGL API
        response = requests.post(ASGL_AUTH_API, data=form_data)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse response JSON
            result = response.json()
            
            # Check if authentication was successful
            if result.get('success') and 'data' in result:
                return result['data']
        
        # If we reach here, authentication failed
        logger.warning(f"Failed to authenticate with ASGL API: {response.text}")
        return None
    
    except Exception as e:
        logger.error(f"Error authenticating with ASGL API: {str(e)}")
        return None

async def save_asgl_user_to_database(asgl_data: Dict[str, Any], username: str, password: str) -> Any:
    """
    Save or update ASGL user information to local database.
    
    Args:
        asgl_data: User data from ASGL API
        
    Returns:
        The created or updated user object
    """
    try:
        user_data = asgl_data.get('user', {})
        
        if not user_data or 'username' not in user_data:
            logger.error("Invalid ASGL user data format")
            return None
        
        # Check if user already exists
        existing_user = await prisma.user.find_unique(
            where={"username": user_data['username']}
        )
        
        # Prepare user data
        user_update_data = {
            "username": username,
            "name": user_data.get('full_name', ''),
            "email": user_data.get('email', ''),
            # Store a placeholder password that can't be used for local login
            "password": hash_password(password),
            "asgl_id": user_data.get('asgl_id', ''),
            "mobile_phone": user_data.get('mobile_phone', ''),
            "avatar_url": user_data.get('avatar', ''),
            "metadata": json.dumps({
                "asgl_data": asgl_data,
                "last_login": datetime.now().isoformat()
            })
        }
        
        if existing_user:
            # Update existing user
            updated_user = await prisma.user.update(
                where={"id": existing_user.id},
                data=user_update_data
            )
            return updated_user
        else:
            # Create new user
            new_user = await prisma.user.create(
                data=user_update_data
            )
            return new_user
            
    except Exception as e:
        logger.error(f"Error saving ASGL user to database: {str(e)}")
        return None

async def authenticate_user(username: str, password: str):
    """
    Authenticate a user by username and password.
    
    First tries to authenticate with local database.
    If that fails, tries to authenticate with ASGL API.
    If ASGL authentication succeeds, saves user info to local database.
    
    Args:
        username: The username to authenticate
        password: The password to authenticate
        
    Returns:
        User object if authentication is successful, False otherwise
    """
    # Step 1: Try to authenticate with local database
    user = await prisma.user.find_unique(where={"username": username})
    
    if user and verify_password(password, user.password):
        # Local authentication successful
        return user
    
    # Step 2: If local authentication fails, try ASGL API
    asgl_data = await authenticate_with_asgl_api(username, password)
    
    if asgl_data:
        # ASGL authentication successful, save/update user in local database
        saved_user = await save_asgl_user_to_database(asgl_data, username, password)
        if saved_user:
            return saved_user
    
    # Authentication failed with both methods
    return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def is_token_valid(token: str) -> bool:
    """
    Check if the provided JWT token is still valid (not expired).
    
    Args:
        token: The JWT token to validate
        
    Returns:
        bool: True if the token is valid, False if expired
        
    Raises:
        HTTPException: If the token is malformed or invalid
    """
    try:
        # Decode the token without verifying signature to get the expiration time
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check if token has an expiration claim
        if "exp" not in payload:
            return False
            
        # Get expiration timestamp
        exp_timestamp = payload["exp"]
        
        # Get current timestamp
        current_timestamp = datetime.now().timestamp()
        
        # Compare timestamps
        return current_timestamp < exp_timestamp
    except jwt.PyJWTError:
        # If there's an error decoding the token, it's invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await prisma.user.find_unique(where={"username": username})
    if user is None:
        raise credentials_exception
    return user
