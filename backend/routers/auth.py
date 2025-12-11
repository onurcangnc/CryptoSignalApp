# -*- coding: utf-8 -*-
"""
CryptoSignal - Auth Router
==========================
/api/login, /api/register endpoints
"""

from fastapi import APIRouter, HTTPException
from uuid import uuid4

from models import LoginRequest, RegisterRequest, TokenResponse
from database import verify_user, create_user, get_invite, use_invite
from auth import create_token

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/login")
async def login(data: LoginRequest):
    """Kullanıcı girişi"""
    user = verify_user(data.email, data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "tier": user["tier"],
            "role": "admin" if user["tier"] == "admin" else "user"
        }
    }


@router.post("/register")
async def register(data: RegisterRequest):
    """Yeni kullanıcı kaydı"""
    # Davet kodu kontrolü
    tier = "free"
    
    if data.invite_code:
        invite = get_invite(data.invite_code)
        if not invite:
            raise HTTPException(status_code=400, detail="Invalid invite code")
        if invite["used"]:
            raise HTTPException(status_code=400, detail="Invite code already used")
        tier = invite["tier"]
    
    # Kullanıcı oluştur
    user_id = str(uuid4())
    success = create_user(user_id, data.email, data.password, tier)
    
    if not success:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Davet kodunu kullanıldı olarak işaretle
    if data.invite_code:
        use_invite(data.invite_code, user_id)
    
    # Token oluştur
    token = create_token(user_id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": data.email,
            "tier": tier,
            "role": "admin" if tier == "admin" else "user"
        }
    }


# Alias endpoints
@router.post("/signin")
async def signin(data: LoginRequest):
    """Login alias"""
    return await login(data)


@router.post("/signup")
async def signup(data: RegisterRequest):
    """Register alias"""
    return await register(data)
