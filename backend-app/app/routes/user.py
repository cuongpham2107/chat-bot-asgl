from fastapi import APIRouter, HTTPException, Depends
from ..models.user import UserCreate, UserResponse, UserUpdate
from prisma.models import User
from ..database import prisma
from ..utils.auth import get_current_user, hash_password

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_user)):
    # Check if user with email already exists
    existing_user = await prisma.user.find_unique(where={"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing
    hashed_password = hash_password(user.password)
    
    # Create the user
    new_user = await prisma.user.create(
        data={
            "email": user.email,
            "name": user.name,
            "password": hashed_password,
        }
    )
    return new_user

@router.get("/", response_model=list[UserResponse])
async def get_users(current_user: User = Depends(get_current_user)):
    users = await prisma.user.find_many()
    return users

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    user = await prisma.user.find_unique(where={"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: User = Depends(get_current_user)):
    # Check if user exists
    existing_user = await prisma.user.find_unique(where={"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if the current user is updating their own profile or is an admin
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    # Prepare update data
    update_data = user_data.dict(exclude_unset=True)
    
    # Hash the password if it's being updated
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    
    # Update the user
    updated_user = await prisma.user.update(
        where={"id": user_id},
        data=update_data
    )
    return updated_user

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    # Check if user exists
    existing_user = await prisma.user.find_unique(where={"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if the current user is deleting their own profile or is an admin
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    # Delete the user
    deleted_user = await prisma.user.delete(where={"id": user_id})
    return deleted_user
