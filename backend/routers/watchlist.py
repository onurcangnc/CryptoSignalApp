# -*- coding: utf-8 -*-
"""
CryptoSignal - Watchlist Router
================================
Favori coin listesi API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from dependencies import get_current_user
from database import (
    add_to_watchlist,
    remove_from_watchlist,
    get_user_watchlist,
    is_in_watchlist
)

router = APIRouter(prefix="/api", tags=["watchlist"])


class WatchlistAddRequest(BaseModel):
    symbol: str


class WatchlistItem(BaseModel):
    symbol: str
    added_at: str


@router.post("/watchlist/add")
async def add_watchlist_item(
    request: WatchlistAddRequest,
    user=Depends(get_current_user)
):
    """Favori listesine coin ekle"""
    if not request.symbol:
        raise HTTPException(status_code=400, detail="Symbol boş olamaz")

    success = add_to_watchlist(user["id"], request.symbol)

    if not success:
        raise HTTPException(status_code=500, detail="Favori eklenirken hata oluştu")

    return {
        "success": True,
        "message": f"{request.symbol} favorilere eklendi",
        "symbol": request.symbol.upper()
    }


@router.delete("/watchlist/remove/{symbol}")
async def remove_watchlist_item(
    symbol: str,
    user=Depends(get_current_user)
):
    """Favori listesinden coin çıkar"""
    success = remove_from_watchlist(user["id"], symbol)

    if not success:
        raise HTTPException(status_code=500, detail="Favori silinirken hata oluştu")

    return {
        "success": True,
        "message": f"{symbol} favorilerden çıkarıldı",
        "symbol": symbol.upper()
    }


@router.get("/watchlist")
async def get_watchlist(user=Depends(get_current_user)):
    """Kullanıcının favori coin listesini getir"""
    watchlist = get_user_watchlist(user["id"])

    return {
        "watchlist": watchlist,
        "count": len(watchlist)
    }


@router.get("/watchlist/check/{symbol}")
async def check_watchlist_item(
    symbol: str,
    user=Depends(get_current_user)
):
    """Coin favori listesinde mi kontrol et"""
    in_watchlist = is_in_watchlist(user["id"], symbol)

    return {
        "symbol": symbol.upper(),
        "in_watchlist": in_watchlist
    }
