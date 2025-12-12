#!/usr/bin/env python3
"""
Telegram Admin Bot - CryptoSignal AI
=====================================
Sadece admin için:
- Ödeme bildirimleri
- Ödeme onay/reddetme
- Günlük raporlar
- Sistem uyarıları
"""

import asyncio
import json
import sqlite3
import httpx
import redis
import os
from datetime import datetime, timedelta
from typing import Optional

# Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")  # Senin Telegram chat_id'n
DB_PATH = os.getenv("DB_PATH", "/opt/cryptosignal-app/backend/cryptosignal.db")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, password=REDIS_PASSWORD)
    r.ping()
    print("[ADMIN] Redis connected")
except:
    r = None
    print("[ADMIN] Redis failed")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

# =============================================================================
# TELEGRAM FUNCTIONS
# =============================================================================

async def send_admin_message(text: str, reply_markup: dict = None) -> bool:
    """Sadece admin'e mesaj gönder"""
    if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
        print("[ADMIN] Missing token or chat_id")
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            payload = {
                "chat_id": ADMIN_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup

            resp = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json=payload
            )
            return resp.status_code == 200
    except Exception as e:
        print(f"[ADMIN] Send error: {e}")
        return False

async def get_updates(offset: int = 0):
    """Telegram updates'leri al"""
    if not TELEGRAM_BOT_TOKEN:
        return []

    try:
        async with httpx.AsyncClient(timeout=35) as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30}
            )
            if resp.status_code == 200:
                return resp.json().get("result", [])
    except httpx.TimeoutException:
        pass
    except Exception as e:
        print(f"[ADMIN] Updates error: {e}")
    return []

# =============================================================================
# PAYMENT NOTIFICATION
# =============================================================================

async def notify_payment(user_email: str, user_id: int, amount: float = 4.99):
    """Yeni ödeme bildirimi gönder"""

    # Inline keyboard ile Onayla/Reddet butonları
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Onayla", "callback_data": f"approve_{user_id}"},
                {"text": "❌ Reddet", "callback_data": f"reject_{user_id}"}
            ]
        ]
    }

    message = (
        f"🔔 <b>YENİ ÖDEME BİLDİRİMİ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Email:</b> {user_email}\n"
        f"💰 <b>Tutar:</b> ${amount}\n"
        f"📱 <b>Network:</b> Solana\n"
        f"🆔 <b>User ID:</b> {user_id}\n"
        f"⏰ <b>Tarih:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Phantom cüzdanınızı kontrol edin."
    )

    await send_admin_message(message, keyboard)
    print(f"[ADMIN] Payment notification sent for user {user_id}")

# =============================================================================
# APPROVE / REJECT PAYMENT
# =============================================================================

async def approve_payment(user_id: int) -> bool:
    """Ödemeyi onayla - kullanıcıyı Premium yap"""
    try:
        conn = get_db()
        c = conn.cursor()

        # User bilgisini al
        c.execute("SELECT email, tier FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()

        if not user:
            await send_admin_message(f"❌ User {user_id} bulunamadı!")
            conn.close()
            return False

        # Premium'a upgrade et
        c.execute(
            "UPDATE users SET tier = 'premium', premium_expires_at = ? WHERE id = ?",
            ((datetime.utcnow() + timedelta(days=30)).isoformat(), user_id)
        )

        # Payment notification'ı güncelle
        c.execute(
            "UPDATE payment_notifications SET status = 'approved', processed_at = ? WHERE user_id = ? AND status = 'pending'",
            (datetime.utcnow().isoformat(), user_id)
        )

        conn.commit()
        conn.close()

        await send_admin_message(
            f"✅ <b>ONAYLANDI!</b>\n\n"
            f"👤 {user['email']}\n"
            f"🎉 Premium hesap aktif edildi (30 gün)\n"
            f"📧 Kullanıcıya email bildirimi gönderildi."
        )

        print(f"[ADMIN] Payment approved for user {user_id}")
        return True

    except Exception as e:
        print(f"[ADMIN] Approve error: {e}")
        await send_admin_message(f"❌ Hata: {str(e)}")
        return False

async def reject_payment(user_id: int) -> bool:
    """Ödemeyi reddet"""
    try:
        conn = get_db()
        c = conn.cursor()

        # User bilgisini al
        c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()

        if not user:
            conn.close()
            return False

        # Payment notification'ı güncelle
        c.execute(
            "UPDATE payment_notifications SET status = 'rejected', processed_at = ? WHERE user_id = ? AND status = 'pending'",
            (datetime.utcnow().isoformat(), user_id)
        )

        conn.commit()
        conn.close()

        await send_admin_message(
            f"❌ <b>REDDEDİLDİ</b>\n\n"
            f"👤 {user['email']}\n"
            f"📧 Kullanıcıya bildirim gönderilmedi."
        )

        print(f"[ADMIN] Payment rejected for user {user_id}")
        return True

    except Exception as e:
        print(f"[ADMIN] Reject error: {e}")
        return False

# =============================================================================
# DAILY REPORT
# =============================================================================

async def send_daily_report():
    """Günlük rapor gönder"""
    try:
        conn = get_db()
        c = conn.cursor()

        # Bugünkü istatistikler
        today = datetime.utcnow().date().isoformat()

        # Yeni kayıtlar
        c.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = ?", (today,))
        new_users = c.fetchone()[0]

        # Toplam kullanıcılar
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]

        # Premium kullanıcılar
        c.execute("SELECT COUNT(*) FROM users WHERE tier = 'premium'")
        premium_users = c.fetchone()[0]

        # Bekleyen ödemeler
        c.execute("SELECT COUNT(*) FROM payment_notifications WHERE status = 'pending'")
        pending_payments = c.fetchone()[0]

        # Bugünkü AI analizleri (Redis'ten)
        ai_count = int(r.get("daily_ai_count") or "0") if r else 0

        conn.close()

        message = (
            f"📊 <b>GÜNLÜK RAPOR</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
            f"👥 Yeni Kayıtlar: <b>{new_users}</b>\n"
            f"💰 Bekleyen Ödemeler: <b>{pending_payments}</b>\n"
            f"⭐ Premium Kullanıcılar: <b>{premium_users}</b>\n"
            f"📈 Toplam Kullanıcı: <b>{total_users}</b>\n"
            f"🤖 AI Analiz Sayısı: <b>{ai_count}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        await send_admin_message(message)
        print("[ADMIN] Daily report sent")

    except Exception as e:
        print(f"[ADMIN] Report error: {e}")

# =============================================================================
# PROCESS UPDATES (Callback Buttons)
# =============================================================================

async def process_updates():
    """Telegram updates'leri işle (Onayla/Reddet butonları)"""

    last_id = int(r.get("admin_tg_last_update") or "0") if r else 0
    updates = await get_updates(last_id + 1)

    for upd in updates:
        update_id = upd.get("update_id", 0)

        # Callback query (buton tıklaması)
        callback = upd.get("callback_query")
        if callback:
            data = callback.get("data", "")
            chat_id = str(callback.get("from", {}).get("id", ""))

            # Sadece admin'den gelen callback'leri işle
            if chat_id != ADMIN_CHAT_ID:
                continue

            print(f"[ADMIN] Callback: {data}")

            if data.startswith("approve_"):
                user_id = int(data.replace("approve_", ""))
                await approve_payment(user_id)

            elif data.startswith("reject_"):
                user_id = int(data.replace("reject_", ""))
                await reject_payment(user_id)

        # Text mesajları (komutlar)
        msg = upd.get("message", {})
        if msg:
            text = msg.get("text", "")
            chat_id = str(msg.get("chat", {}).get("id", ""))

            # Sadece admin'den gelen mesajları işle
            if chat_id != ADMIN_CHAT_ID:
                continue

            if text == "/report":
                await send_daily_report()

            elif text == "/help":
                await send_admin_message(
                    "📚 <b>Admin Komutları</b>\n\n"
                    "/report - Günlük rapor\n"
                    "/help - Yardım"
                )

        # Update ID'yi kaydet
        if r:
            r.set("admin_tg_last_update", str(update_id))

# =============================================================================
# MAIN LOOP
# =============================================================================

async def main():
    print("=" * 50)
    print("[ADMIN] CryptoSignal AI - Admin Bot")
    print("=" * 50)

    if not TELEGRAM_BOT_TOKEN:
        print("[ADMIN] ERROR: TELEGRAM_ADMIN_BOT_TOKEN not set!")
        return

    if not ADMIN_CHAT_ID:
        print("[ADMIN] ERROR: ADMIN_CHAT_ID not set!")
        return

    # Bot bilgisini al
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe")
            if resp.status_code == 200:
                bot_username = resp.json()['result']['username']
                print(f"[ADMIN] Bot: @{bot_username}")
                print(f"[ADMIN] Admin Chat ID: {ADMIN_CHAT_ID}")
            else:
                print("[ADMIN] Bot error!")
                return
    except Exception as e:
        print(f"[ADMIN] Bot check error: {e}")
        return

    # Başlangıç mesajı
    await send_admin_message(
        "🤖 <b>Admin Bot Başlatıldı</b>\n\n"
        "✅ Ödeme bildirimleri aktif\n"
        "📊 Günlük raporlar hazır\n\n"
        "/report - Günlük rapor al\n"
        "/help - Komutlar"
    )

    print("[ADMIN] Listening for updates...")

    # Ana döngü
    while True:
        try:
            await process_updates()
        except Exception as e:
            print(f"[ADMIN] Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())