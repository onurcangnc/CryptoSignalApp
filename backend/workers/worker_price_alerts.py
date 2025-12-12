#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoSignal - Price Alerts Worker
===================================
Fiyat alarmlarını kontrol eden worker

Her 5 dakikada bir çalışır:
1. Tüm aktif alarmları getir
2. Her alarm için mevcut fiyatı kontrol et
3. Koşul sağlanmışsa tetikle ve bildirim gönder
"""

import sys
import os
import time
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_active_price_alerts, trigger_price_alert, redis_client
from config import TELEGRAM_ADMIN_BOT_TOKEN, ADMIN_CHAT_ID


def get_current_price(symbol: str) -> float:
    """
    CoinGecko'dan mevcut fiyatı getir

    Args:
        symbol: Coin sembolü (BTC, ETH, vb.)

    Returns:
        Current price in USD
    """
    try:
        # Try Redis cache first
        cached_price = redis_client.get(f"price:{symbol}")
        if cached_price:
            return float(cached_price)

        # Fallback: CoinGecko API
        coin_id_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOGE': 'dogecoin',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2'
        }

        coin_id = coin_id_map.get(symbol, symbol.lower())

        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd'
        }

        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if coin_id in data and 'usd' in data[coin_id]:
                price = data[coin_id]['usd']
                # Cache for 30 seconds
                redis_client.setex(f"price:{symbol}", 30, str(price))
                return price

        return 0.0
    except Exception as e:
        print(f"[PRICE] Error fetching price for {symbol}: {e}")
        return 0.0


def send_telegram_notification(user_id: str, symbol: str, target_price: float, current_price: float, condition: str):
    """
    Telegram bildirimi gönder

    Args:
        user_id: User ID
        symbol: Coin symbol
        target_price: Target price
        current_price: Current price
        condition: 'above' or 'below'
    """
    try:
        if not TELEGRAM_ADMIN_BOT_TOKEN or not ADMIN_CHAT_ID:
            print(f"[TELEGRAM] Config missing, skipping notification")
            return

        condition_text = "yukarı çıktı" if condition == "above" else "aşağı düştü"

        message = f"""
🚨 **Fiyat Alarmı Tetiklendi!**

🪙 Coin: {symbol}
💰 Hedef Fiyat: ${target_price:,.2f}
📊 Mevcut Fiyat: ${current_price:,.2f}
📈 Durum: Fiyat {condition_text}

👤 User ID: {user_id}
⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

        url = f"https://api.telegram.org/bot{TELEGRAM_ADMIN_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': ADMIN_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }

        requests.post(url, json=data, timeout=10)
        print(f"[TELEGRAM] Notification sent for {symbol} alert")

    except Exception as e:
        print(f"[TELEGRAM] Error sending notification: {e}")


def check_price_alerts():
    """Tüm aktif fiyat alarmlarını kontrol et"""
    try:
        alerts = get_active_price_alerts()

        if not alerts:
            print(f"[ALERTS] No active alerts to check")
            return

        print(f"[ALERTS] Checking {len(alerts)} active alerts...")

        triggered_count = 0

        for alert in alerts:
            symbol = alert['symbol']
            target_price = alert['target_price']
            condition = alert['condition']
            alert_id = alert['id']
            user_id = alert['user_id']

            # Get current price
            current_price = get_current_price(symbol)

            if current_price == 0:
                print(f"[ALERTS] Could not fetch price for {symbol}, skipping")
                continue

            # Check condition
            triggered = False

            if condition == 'above' and current_price >= target_price:
                triggered = True
            elif condition == 'below' and current_price <= target_price:
                triggered = True

            if triggered:
                print(f"[ALERTS] ✅ Alert triggered: {symbol} {condition} ${target_price} (current: ${current_price})")

                # Mark as triggered
                trigger_price_alert(alert_id)

                # Send notification
                send_telegram_notification(user_id, symbol, target_price, current_price, condition)

                triggered_count += 1

        if triggered_count > 0:
            print(f"[ALERTS] ✅ {triggered_count} alerts triggered")
        else:
            print(f"[ALERTS] No alerts triggered this round")

    except Exception as e:
        print(f"[ALERTS] Error checking alerts: {e}")


def main():
    """Ana worker loop"""
    print("[PRICE ALERTS WORKER] Starting...")
    print(f"[PRICE ALERTS WORKER] Check interval: 5 minutes")

    while True:
        try:
            print(f"\n[PRICE ALERTS] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC - Checking alerts...")
            check_price_alerts()

        except Exception as e:
            print(f"[PRICE ALERTS] Fatal error: {e}")
            import traceback
            traceback.print_exc()

        # Sleep 5 minutes
        print(f"[PRICE ALERTS] Sleeping for 5 minutes...")
        time.sleep(300)


if __name__ == "__main__":
    main()
