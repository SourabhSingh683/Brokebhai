# app/models.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal, Dict, List
from datetime import datetime
from bson import ObjectId


class UserModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[str] = Field(default=None, alias="_id")
    clerk_user_id: Optional[str] = None
    email: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        if value is None:
            return None
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, str) and ObjectId.is_valid(value):
            return str(ObjectId(value))
        return value


class TransactionModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    amount: float
    category: str
    description: str
    date: datetime = Field(default_factory=datetime.utcnow)
    transaction_type: Literal["income", "expense"]

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        if value is None:
            return None
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, str) and ObjectId.is_valid(value):
            return str(ObjectId(value))
        return value


# Request Models
class UserCreate(BaseModel):
    email: str
    name: str
    clerk_user_id: Optional[str] = None


class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: str
    transaction_type: Literal["income", "expense"]


# Prediction Models
class PredictRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Mapping of feature name to value")


class PredictBatchRequest(BaseModel):
    batch: List[Dict[str, float]] = Field(..., description="List of feature mappings for batch prediction")


class PredictResponse(BaseModel):
    predictions: List[float]
    used_feature_order: Optional[List[str]] = None


# Loan/IOU Models
class LoanModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[str] = Field(default=None, alias="_id")
    lender_id: str
    borrower_id: str
    amount: float
    due_date: datetime
    status: Literal["pending", "repaid", "overdue"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    repaid_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        if value is None:
            return None
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, str) and ObjectId.is_valid(value):
            return str(ObjectId(value))
        return value


class LoanCreate(BaseModel):
    lender_id: str
    borrower_id: str
    amount: float
    due_date: datetime


class LoanRepayRequest(BaseModel):
    loan_id: str


class NotificationModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    loan_id: Optional[str] = None
    type: Literal["loan_created", "loan_overdue", "loan_repaid"]
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        if value is None:
            return None
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, str) and ObjectId.is_valid(value):
            return str(ObjectId(value))
        return value