# -*- coding: utf-8 -*-
"""
CryptoSignal - Ads Router
=========================
Rewarded ad system for AI credits
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Dict

from database import (
    get_ad_credits, add_ad_credit,
    get_last_ad_reward_time, set_last_ad_reward_time
)
from dependencies import get_current_user
from config import AD_REWARD_COOLDOWN, MAX_AD_CREDITS

router = APIRouter(prefix="/api/ads", tags=["Ads"])


@router.get("/credits")
async def get_credits(user: dict = Depends(get_current_user)):
    """
    Kullanıcının mevcut AI kredilerini getir
    """
    tier = user.get("tier", "free")

    if tier != "free":
        return {
            "credits": "unlimited",
            "tier": tier,
            "message": "Pro/Admin users have unlimited AI access"
        }

    credits = get_ad_credits(user['id'])
    last_reward = get_last_ad_reward_time(user['id'])

    # Cooldown kontrolü
    can_watch = True
    cooldown_remaining = 0

    if last_reward:
        try:
            last_time = datetime.fromisoformat(last_reward)
            elapsed = (datetime.utcnow() - last_time).total_seconds()
            cooldown_remaining = max(0, AD_REWARD_COOLDOWN - elapsed)
            can_watch = cooldown_remaining == 0
        except:
            pass

    return {
        "credits": credits,
        "max_credits": MAX_AD_CREDITS,
        "can_watch_ad": can_watch and credits < MAX_AD_CREDITS,
        "cooldown_remaining": int(cooldown_remaining),
        "tier": tier
    }


@router.post("/reward")
async def claim_ad_reward(user: dict = Depends(get_current_user)):
    """
    Reklam izleme ödülünü al
    - Cooldown kontrolü yapar (60 saniye)
    - Maksimum kredi kontrolü yapar (10)
    - Başarılıysa 1 AI kredisi ekler
    """
    tier = user.get("tier", "free")

    if tier != "free":
        raise HTTPException(
            status_code=400,
            detail="Pro/Admin users don't need ad credits"
        )

    user_id = user['id']

    # Cooldown kontrolü
    last_reward = get_last_ad_reward_time(user_id)

    if last_reward:
        try:
            last_time = datetime.fromisoformat(last_reward)
            elapsed = (datetime.utcnow() - last_time).total_seconds()

            if elapsed < AD_REWARD_COOLDOWN:
                remaining = int(AD_REWARD_COOLDOWN - elapsed)
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait {remaining} seconds before watching another ad",
                    headers={"X-Cooldown-Remaining": str(remaining)}
                )
        except HTTPException:
            raise
        except:
            pass

    # Maksimum kredi kontrolü
    current_credits = get_ad_credits(user_id)

    if current_credits >= MAX_AD_CREDITS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum credits reached ({MAX_AD_CREDITS}). Use some credits first.",
            headers={"X-Max-Credits": str(MAX_AD_CREDITS)}
        )

    # Kredi ekle
    new_credits = add_ad_credit(user_id, 1)

    # Cooldown başlat
    set_last_ad_reward_time(user_id)

    return {
        "success": True,
        "credits": new_credits,
        "max_credits": MAX_AD_CREDITS,
        "message": "AI credit earned! You can now generate AI analysis.",
        "cooldown_seconds": AD_REWARD_COOLDOWN
    }


@router.get("/config")
async def get_ad_config():
    """
    Reklam sistemi konfigürasyonunu getir (public)
    """
    return {
        "reward_cooldown": AD_REWARD_COOLDOWN,
        "watch_duration": 15,  # Frontend'de kaç saniye gösterilecek
        "max_credits": MAX_AD_CREDITS,
        "credits_per_ad": 1
    }
