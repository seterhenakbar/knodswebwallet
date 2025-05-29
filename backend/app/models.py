from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(UserBase):
    password: str

class UserInDB(UserBase):
    id: Optional[str] = None
    password_hash: str

class User(UserBase):
    id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Transaction(BaseModel):
    id: str
    amount: float
    timestamp: datetime
    description: Optional[str] = None

class WalletBalance(BaseModel):
    balance: float
    last_updated: Optional[datetime] = None

class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=8)
