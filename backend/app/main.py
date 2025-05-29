from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from app.models import UserCreate, UserLogin, User, Token, WalletBalance, PasswordReset
from app.auth import get_password_hash, authenticate_user, create_access_token, get_current_user
from app.airtable_service import get_user_by_email, create_user, update_user_password, get_wallet_balance, get_transactions

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

app = FastAPI(title="Knods Token Wallet API")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.middleware("http")
async def airtable_error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(f"Error: {e}")
        return {
            "status_code": 500,
            "detail": "An error occurred while connecting to the database. Please try again later."
        }

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    
    user = create_user(user_data.email, hashed_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return User(email=user.email, id=user.id)

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/auth/reset-password", response_model=dict)
async def reset_password(reset_data: PasswordReset):
    user = get_user_by_email(reset_data.email)
    if not user:
        return {"message": "Password reset instructions sent if email exists"}
    
    hashed_password = get_password_hash(reset_data.new_password)
    success = update_user_password(reset_data.email, hashed_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )
    
    return {"message": "Password reset successfully"}

@app.get("/wallet/balance", response_model=WalletBalance)
async def get_user_wallet_balance(current_user: User = Depends(get_current_user)):
    balance = get_wallet_balance(current_user.email)
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return balance

@app.get("/wallet/transactions")
async def get_user_transactions(current_user: User = Depends(get_current_user)):
    transactions = get_transactions(current_user.email)
    return transactions
