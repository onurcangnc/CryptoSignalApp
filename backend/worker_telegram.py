#!/usr/bin/env python3
"""Telegram Notification Worker for CryptoSignal AI"""

import asyncio
import json
import sqlite3
import httpx
import redis
import os
from datetime import datetime
from typing import List

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DB_PATH = "/opt/cryptosignal-app/backend/cryptosignal.db"
REDIS_PASSWORD = "3f9af2788cb89aa74c06bd48dd290658"

try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, password=REDIS_PASSWORD)
    r.ping()
    print("[TG] Redis connected")
except:
    r = None

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS telegram_users (
        user_id TEXT PRIMARY KEY, chat_id TEXT, username TEXT,
        notifications_enabled INTEGER DEFAULT 1, connected_at TEXT)''')
    conn.commit()
    conn.close()
    print("[TG] Tables OK")

def save_telegram_user(user_id: str, chat_id: str, username: str = None):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO telegram_users (user_id, chat_id, username, connected_at)
        VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET
        chat_id = excluded.chat_id, username = excluded.username''',
        (user_id, chat_id, username, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    print(f"[TG] User saved: {user_id}")

def get_user_portfolio(user_id: str) -> list:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT holdings FROM portfolios WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        # Handle {"holdings": [...]} format
        if isinstance(data, dict) and "holdings" in data:
            return data["holdings"]
        return data if isinstance(data, list) else []
    return []

async def send_message(chat_id: str, text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            print(f"[TG] Sent: {resp.status_code}")
            return resp.status_code == 200
    except Exception as e:
        print(f"[TG] Send error: {e}")
        return False

async def get_updates(offset: int = 0) -> List[dict]:
    if not TELEGRAM_BOT_TOKEN:
        return []
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30})
            if resp.status_code == 200:
                results = resp.json().get("result", [])
                if results:
                    print(f"[TG] Got {len(results)} updates")
                return results
    except httpx.TimeoutException:
        pass
    except Exception as e:
        print(f"[TG] Updates error: {e}")
    return []

async def process_updates():
    last_id = int(r.get("tg_last_update") or "0") if r else 0
    updates = await get_updates(last_id + 1)
    
    for upd in updates:
        update_id = upd.get("update_id", 0)
        msg = upd.get("message", {})
        text = msg.get("text", "")
        chat_id = str(msg.get("chat", {}).get("id", ""))
        username = msg.get("from", {}).get("username", "")
        
        print(f"[TG] From {username}: {text}")
        
        if text.startswith("/start"):
            parts = text.split()
            if len(parts) > 1 and parts[1].startswith("connect_"):
                user_id = parts[1].replace("connect_", "")
                save_telegram_user(user_id, chat_id, username)
                await send_message(chat_id,
                    "✅ <b>Bağlantı Başarılı!</b>\n\n"
                    "CryptoSignal AI'a bağlandınız! 🎉\n\n"
                    "/portfolio - Portföy\n/help - Yardım")
            else:
                await send_message(chat_id,
                    "👋 <b>Merhaba!</b>\n\n"
                    "Web panelinden 'Telegram Bağla' butonunu kullanın.")
        
        elif text == "/portfolio":
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT user_id FROM telegram_users WHERE chat_id = ?", (chat_id,))
            row = c.fetchone()
            conn.close()
            
            if row:
                holdings = get_user_portfolio(row[0])
                print(f"[TG] Holdings: {holdings}")
                if holdings:
                    prices = json.loads(r.get("prices_data") or "{}") if r else {}
                    lines = []
                    total = 0
                    total_invested = 0
                    for h in holdings:
                        coin = h.get("coin", "?")
                        qty = h.get("quantity", 0)
                        invested = h.get("invested_usd", 0)
                        price = prices.get(coin, {}).get("price", 0)
                        val = qty * price
                        total += val
                        total_invested += invested
                        if invested > 0:
                            pnl = ((val - invested) / invested) * 100
                            emoji = "🟢" if pnl >= 0 else "🔴"
                            lines.append(f"{emoji} <b>{coin}</b>: ${val:.2f} ({pnl:+.1f}%)")
                        else:
                            lines.append(f"• <b>{coin}</b>: ${val:.2f}")
                    
                    total_pnl = ((total - total_invested) / total_invested * 100) if total_invested > 0 else 0
                    pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
                    
                    await send_message(chat_id, 
                        f"📊 <b>Portföy Özeti</b>\n\n" + 
                        "\n".join(lines) + 
                        f"\n\n💰 <b>Toplam:</b> ${total:.2f} {pnl_emoji} ({total_pnl:+.1f}%)")
                else:
                    await send_message(chat_id, "📊 Portföyünüz boş.")
            else:
                await send_message(chat_id, "❌ Hesap bağlı değil.\nWeb panelinden bağlayın.")
        
        elif text == "/help":
            await send_message(chat_id, "📚 <b>Komutlar</b>\n\n/start - Başlat\n/portfolio - Portföy\n/help - Yardım")
        
        if r:
            r.set("tg_last_update", str(update_id))

async def main():
    print("=" * 40)
    print("[TG] CryptoSignal AI Bot")
    print("=" * 40)
    
    if not TELEGRAM_BOT_TOKEN:
        print("[TG] ERROR: No token!")
        return
    
    init_tables()
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe")
        if resp.status_code == 200:
            print(f"[TG] Bot: @{resp.json()['result']['username']}")
        else:
            print("[TG] Bot error!")
            return
    
    print("[TG] Waiting...")
    while True:
        try:
            await process_updates()
        except Exception as e:
            print(f"[TG] Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())