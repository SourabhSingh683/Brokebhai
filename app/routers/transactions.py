# app/routers/transactions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models import TransactionModel, TransactionCreate
from app.database import db
from typing import List

router = APIRouter()

@router.post("/", response_model=TransactionModel, status_code=201)
async def create_transaction(transaction: TransactionCreate, user_id: str = Query(..., description="User ID for the transaction")):
    """Create a new transaction for a user"""
    if db.client is None or db.database is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Verify user exists
        user = await db.database.users.find_one({"$or": [{"clerk_user_id": user_id}, {"email": user_id}]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        transaction_dict = transaction.model_dump()
        transaction_dict["user_id"] = user_id
        
        result = await db.database.transactions.insert_one(transaction_dict)
        created_transaction = await db.database.transactions.find_one({"_id": result.inserted_id})
        return TransactionModel(**created_transaction)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating transaction: {str(e)}")

@router.get("/user/{user_id}", response_model=List[TransactionModel])
async def get_user_transactions(user_id: str):
    """Get all transactions for a specific user"""
    if db.client is None or db.database is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        transactions = await db.database.transactions.find({"user_id": user_id}).to_list(100)
        return [TransactionModel(**transaction) for transaction in transactions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")