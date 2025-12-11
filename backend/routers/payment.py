# -*- coding: utf-8 -*-
"""
CryptoSignal - Payment Router (Manuel USDT)
============================================
Kullanıcı ödeme bildirimi endpoint'i
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/payment", tags=["payment"])


class ManualPaymentNotification(BaseModel):
    tier: str
    amount: float


@router.post("/manual-notification")
async def manual_payment_notification(
    request: ManualPaymentNotification,
    user=Depends(get_current_user)
):
    """
    Kullanıcı ödeme yaptığını bildirdiğinde

    Admin'e bildirim gönderilir
    Manuel olarak tier güncellenecek
    """

    # Log'a yaz
    print(f"\n{'='*60}")
    print(f"[ÖDEME BİLDİRİMİ]")
    print(f"{'='*60}")
    print(f"User: {user['email']}")
    print(f"User ID: {user['id']}")
    print(f"Tier: {request.tier}")
    print(f"Amount: ${request.amount}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"{'='*60}")
    print(f"\n⚠️ BTCTurk'ü kontrol et ve tier'ı güncelle!")
    print(f"Komut: UPDATE users SET tier = '{request.tier}' WHERE id = '{user['id']}';")
    print(f"{'='*60}\n")

    # TODO: Email/Telegram bildirimi ekleyebilirsiniz
    # send_telegram_notification(...)
    # send_email_notification(...)

    return {
        "success": True,
        "message": "Ödeme bildiriminiz alındı. 1-2 saat içinde hesabınız aktif olacak."
    }
