# -*- coding: utf-8 -*-
"""
CryptoSignal - Price Alerts Router
===================================
Fiyat alarmları API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from dependencies import get_current_user
from database import (
    create_price_alert,
    get_user_price_alerts,
    delete_price_alert,
    deactivate_price_alert
)

router = APIRouter(prefix="/api", tags=["price-alerts"])


class PriceAlertCreateRequest(BaseModel):
    symbol: str
    target_price: float
    condition: str  # 'above' or 'below'


class PriceAlertResponse(BaseModel):
    id: str
    symbol: str
    target_price: float
    condition: str
    created_at: str
    triggered: int
    triggered_at: Optional[str]
    is_active: int


@router.post("/price-alerts")
async def create_alert(
    request: PriceAlertCreateRequest,
    user=Depends(get_current_user)
):
    """Yeni fiyat alarmı oluştur"""

    # Validate condition
    if request.condition not in ['above', 'below']:
        raise HTTPException(status_code=400, detail="Condition must be 'above' or 'below'")

    # Validate target_price
    if request.target_price <= 0:
        raise HTTPException(status_code=400, detail="Target price must be greater than 0")

    alert_id = create_price_alert(
        user_id=user["id"],
        symbol=request.symbol,
        target_price=request.target_price,
        condition=request.condition
    )

    if not alert_id:
        raise HTTPException(status_code=500, detail="Alarm oluşturulamadı")

    return {
        "success": True,
        "alert_id": alert_id,
        "message": f"{request.symbol} için fiyat alarmı oluşturuldu"
    }


@router.get("/price-alerts")
async def get_alerts(
    active_only: bool = True,
    user=Depends(get_current_user)
):
    """Kullanıcının fiyat alarmlarını getir"""
    alerts = get_user_price_alerts(user["id"], active_only=active_only)

    return {
        "alerts": alerts,
        "count": len(alerts)
    }


@router.delete("/price-alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    user=Depends(get_current_user)
):
    """Fiyat alarmını sil"""
    success = delete_price_alert(alert_id, user["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Alarm bulunamadı")

    return {
        "success": True,
        "message": "Alarm silindi"
    }


@router.post("/price-alerts/{alert_id}/deactivate")
async def deactivate_alert(
    alert_id: str,
    user=Depends(get_current_user)
):
    """Fiyat alarmını deaktif et"""
    success = deactivate_price_alert(alert_id, user["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Alarm bulunamadı")

    return {
        "success": True,
        "message": "Alarm deaktif edildi"
    }
