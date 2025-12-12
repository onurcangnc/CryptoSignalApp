# -*- coding: utf-8 -*-
"""
CryptoSignal - Dependencies
===========================
FastAPI dependency injection fonksiyonları
"""

from fastapi import Request, HTTPException, Depends
from typing import Optional, Dict

from auth import verify_token
from database import get_user_by_id, get_llm_usage, get_ad_credits, today_str
from config import LLM_LIMITS


async def get_current_user(request: Request) -> Dict:
    """
    Authorization header'dan kullanıcıyı al
    Kullanım: user = Depends(get_current_user)
    """
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split(" ", 1)[1]
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


async def get_optional_user(request: Request) -> Optional[Dict]:
    """
    Opsiyonel kullanıcı - login olmadan da çalışır
    Kullanım: user = Depends(get_optional_user)
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def get_admin_user(user: Dict = Depends(get_current_user)) -> Dict:
    """
    Sadece admin kullanıcılar için
    Kullanım: user = Depends(get_admin_user)
    """
    if user.get("tier") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def get_pro_user(user: Dict = Depends(get_current_user)) -> Dict:
    """
    Pro veya admin kullanıcılar için
    Kullanım: user = Depends(get_pro_user)
    """
    if user.get("tier") not in ["pro", "admin"]:
        raise HTTPException(status_code=403, detail="Pro access required")
    return user


def check_llm_quota(user: Dict) -> tuple:
    """
    LLM kullanım kotasını kontrol et
    Free kullanıcılar için ad_credits de hesaba katılır
    Returns: (can_use, used_today, daily_limit, remaining, ad_credits)
    """
    tier = user.get("tier", "free")
    limit = LLM_LIMITS.get(tier, 0)
    used = get_llm_usage(user["id"], today_str())
    ad_credits = get_ad_credits(user["id"]) if tier == "free" else 0

    # Free kullanıcılar: ad_credits varsa kullanabilir
    # Pro/Admin: normal limit sistemi
    if tier == "free":
        can_use = ad_credits > 0
        remaining = ad_credits
    else:
        can_use = used < limit
        remaining = max(0, limit - used)

    return can_use, used, limit, remaining, ad_credits


async def require_llm_quota(user: Dict = Depends(get_current_user)) -> Dict:
    """
    LLM kotası olan kullanıcılar için
    Kullanım: user = Depends(require_llm_quota)
    """
    can_use, used, limit, remaining, ad_credits = check_llm_quota(user)

    if not can_use:
        tier = user.get("tier", "free")
        if tier == "free":
            raise HTTPException(
                status_code=429,
                detail="No AI credits available. Watch an ad to earn credits."
            )
        else:
            raise HTTPException(
                status_code=429,
                detail=f"Daily AI limit reached ({used}/{limit}). Resets at midnight UTC."
            )

    return user
