# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.models import UserModel, UserCreate
from app.database import db
from typing import List

router = APIRouter()

@router.post("/", response_model=UserModel, status_code=201)
async def create_user(user: UserCreate):
    """Create a new user"""
    if db.client is None or db.database is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Check if user already exists
        existing_user = await db.database.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        user_dict = user.model_dump()
        result = await db.database.users.insert_one(user_dict)
        created_user = await db.database.users.find_one({"_id": result.inserted_id})
        return UserModel(**created_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/{user_id}", response_model=UserModel)
async def get_user(user_id: str):
    """Get user by ID"""
    if db.client is None or db.database is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Try to find by clerk_user_id first, then by email
        user = await db.database.users.find_one({
            "$or": [
                {"clerk_user_id": user_id},
                {"email": user_id}
            ]
        })
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserModel(**user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@router.get("/", response_model=List[UserModel])
async def get_all_users():
    """Get all users (for testing purposes)"""
    if db.client is None or db.database is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        users = await db.database.users.find().to_list(100)  # Limit to 100 users
        return [UserModel(**user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")