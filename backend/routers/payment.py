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
import asyncio
import os

router = APIRouter(prefix="/api/payment", tags=["payment"])

# Telegram Admin Notification
async def notify_admin_payment(user_email: str, user_id: int, amount: float):
    """Admin bot'a ödeme bildirimi gönder"""
    try:
        # Import here to avoid circular dependency
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))

        from worker_telegram_admin import notify_payment

        # Background task olarak çalıştır
        asyncio.create_task(notify_payment(user_email, user_id, amount))
        print(f"[PAYMENT] Admin notification sent for user {user_id}")
    except Exception as e:
        print(f"[PAYMENT] Admin notification error: {e}")


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

    # Database'e kaydet (payment_notifications table)
    from database import get_db
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO payment_notifications (user_id, tier, amount, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (user['id'], request.tier, request.amount, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    # Telegram Admin'e bildirim gönder
    await notify_admin_payment(user['email'], user['id'], request.amount)

    # Log
    print(f"[PAYMENT] Notification saved: user_id={user['id']}, amount=${request.amount}")

    return {
        "success": True,
        "message": "Ödeme bildiriminiz alındı. 1-2 saat içinde hesabınız aktif olacak."
    }
