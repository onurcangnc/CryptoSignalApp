# -*- coding: utf-8 -*-
"""
CryptoSignal - Models
=====================
Pydantic request/response modelleri
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any


# =============================================================================
# AUTH MODELS
# =============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    invite_code: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


# =============================================================================
# PORTFOLIO MODELS
# =============================================================================

class Holding(BaseModel):
    coin: str
    weight: Optional[float] = 0
    quantity: Optional[float] = 0
    invested_amount: Optional[float] = None
    invested_currency: Optional[str] = "USD"
    invested_usd: Optional[float] = 0
    input_mode: Optional[str] = "fiat"


class PortfolioUpdate(BaseModel):
    holdings: List[Holding]
    budget: Optional[float] = None
    budget_currency: Optional[str] = "USD"


# =============================================================================
# ANALYSIS MODELS
# =============================================================================

class AnalyzeRequest(BaseModel):
    symbol: str
    timeframe: Optional[str] = "1d"


class DigestRequest(BaseModel):
    coins: Optional[List[str]] = None
    focus: Optional[str] = None


# =============================================================================
# ADMIN MODELS
# =============================================================================

class CreateInviteRequest(BaseModel):
    tier: str = "free"
    note: Optional[str] = None


class UpdateUserTierRequest(BaseModel):
    user_id: str
    tier: str


# =============================================================================
# SIGNAL MODELS
# =============================================================================

class SignalFilter(BaseModel):
    timeframe: str = "1d"
    signal_type: Optional[str] = None  # BUY, SELL, HOLD
    min_confidence: Optional[int] = None
    category: Optional[str] = None  # MEGA_CAP, LARGE_CAP, ALT, MEME


# =============================================================================
# NEWS MODELS
# =============================================================================

class NewsFilter(BaseModel):
    sentiment: Optional[str] = None  # bullish, bearish, neutral
    coin: Optional[str] = None
    limit: int = 100


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
