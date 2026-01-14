#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoSignal - Signal Tracker Worker v1.0
==========================================
Açık pozisyonları takip eden worker

Her 60 saniyede çalışır:
- Güncel fiyatı Redis'ten al (prices_data)
- Stop-Loss kontrolü
- Take-Profit kontrolü
- 7 gün süre kontrolü
- Exit reason ve profit_loss hesaplama
"""

import asyncio
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
import os

# Parent path ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

# Redis connection (worker_signals ile aynı pattern)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None
)

# Config
MAX_HOLD_DAYS = 7  # Max 7 gün tutma


class SignalTracker:
    """Sinyal tracker - açık pozisyonları takip eder"""

    def __init__(self):
        self.closed_count = 0
        self.exits = {
            "STOP_LOSS": 0,
            "TAKE_PROFIT": 0,
            "TIME_EXPIRED": 0,
            "MANUAL": 0
        }

    def get_current_price(self, symbol: str, prices_data: Dict) -> Optional[float]:
        """Redis prices_data'dan güncel fiyatı al"""
        try:
            coin_data = prices_data.get(symbol)
            if coin_data:
                return coin_data.get("price")
        except Exception as e:
            pass
        return None

    def process_signal(self, signal_row: Dict, prices_data: Dict) -> Optional[str]:
        """
        Tek sinyal işle

        Returns:
            exit_reason or None (hala açık)
        """
        signal_id = signal_row.get("id")
        symbol = signal_row.get("symbol")
        signal = signal_row.get("signal")
        entry_price = signal_row.get("entry_price", 0)
        stop_loss = signal_row.get("stop_loss")
        take_profit = signal_row.get("target_price")  # DB'de target_price olarak kayıtlı
        created_at = signal_row.get("created_at", "")

        if not entry_price or not stop_loss or not take_profit:
            return None  # Eksik veri, atla

        # Mevcut fiyatı al
        current_price = self.get_current_price(symbol, prices_data)
        if not current_price:
            return None  # Fiyat alınamadı, atla

        # Exit kontrolü
        exit_reason = None

        # LONG / SHORT belirle
        is_long = signal in ["BUY", "STRONG_BUY", "AL", "GÜÇLÜ AL"]

        # Time expired kontrolü
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created_dt.tzinfo:
                    created_dt = created_dt.replace(tzinfo=None)
                days_held = (datetime.utcnow() - created_dt).days
                if days_held >= MAX_HOLD_DAYS:
                    exit_reason = "TIME_EXPIRED"
            except:
                pass

        # Stop-Loss / Take-Profit kontrolü (henüz exit olmadıysa)
        if not exit_reason:
            if is_long:
                # LONG pozisyon
                if current_price <= stop_loss:
                    exit_reason = "STOP_LOSS"
                elif current_price >= take_profit:
                    exit_reason = "TAKE_PROFIT"
            else:
                # SHORT pozisyon
                if current_price >= stop_loss:
                    exit_reason = "STOP_LOSS"
                elif current_price <= take_profit:
                    exit_reason = "TAKE_PROFIT"

        # Exit olduysa güncelle
        if exit_reason:
            # Profit/Loss hesapla
            if is_long:
                profit_loss_pct = ((current_price - entry_price) / entry_price * 100)
            else:
                profit_loss_pct = ((entry_price - current_price) / entry_price * 100)

            is_successful = 1 if profit_loss_pct > 0 else 0

            with get_db() as conn:
                conn.execute("""
                    UPDATE signal_tracking
                    SET result = ?,
                        actual_price = ?,
                        profit_loss_pct = ?,
                        is_successful = ?,
                        exit_reason = ?,
                        closed_at = ?
                    WHERE id = ?
                """, (
                    "STOPPED" if exit_reason == "STOP_LOSS" else "SUCCESS",
                    current_price,
                    round(profit_loss_pct, 2),
                    is_successful,
                    exit_reason,
                    datetime.utcnow().isoformat(),
                    signal_id
                ))
                conn.commit()

            self.closed_count += 1
            self.exits[exit_reason] = self.exits.get(exit_reason, 0) + 1
            return exit_reason

        return None

    def process_all_signals(self) -> Dict:
        """
        Tüm açık sinyalleri işle

        Returns:
            Dict with stats
        """
        self.closed_count = 0
        self.exits = {
            "STOP_LOSS": 0,
            "TAKE_PROFIT": 0,
            "TIME_EXPIRED": 0,
            "MANUAL": 0
        }

        try:
            # Redis'ten güncel fiyatları al
            prices_raw = redis_client.get("prices_data")
            prices_data = json.loads(prices_raw) if prices_raw else {}

            if not prices_data:
                return {"closed": 0, "exits": self.exits, "open": 0, "error": "No price data"}

            with get_db() as conn:
                # Açık sinyalleri al
                rows = conn.execute("""
                    SELECT * FROM signal_tracking
                    WHERE result IS NULL
                    ORDER BY created_at DESC
                """).fetchall()

                if not rows:
                    return {"closed": 0, "exits": self.exits, "open": 0}

                open_count = len(rows)

                for row in rows:
                    try:
                        self.process_signal(dict(row), prices_data)
                    except Exception as e:
                        print(f"  [Tracker] Error processing signal: {e}", flush=True)
                        continue

                return {
                    "closed": self.closed_count,
                    "exits": self.exits,
                    "open": open_count - self.closed_count
                }

        except Exception as e:
            print(f"  [Tracker] Database error: {e}", flush=True)
            return {"closed": 0, "exits": self.exits, "open": 0, "error": str(e)}


# Singleton instance
signal_tracker = SignalTracker()


async def main():
    """Main loop - her 60 saniyede çalış"""
    print("[Signal Tracker v1.0] Starting...", flush=True)
    print(f"  Check interval: 60 seconds", flush=True)
    print(f"  Max hold time: {MAX_HOLD_DAYS} days", flush=True)

    while True:
        try:
            stats = signal_tracker.process_all_signals()

            if stats.get("closed", 0) > 0:
                print(f"  [Tracker] Closed: {stats['closed']} | Exits: {stats['exits']}", flush=True)

            await asyncio.sleep(60)

        except Exception as e:
            print(f"[Tracker] Error: {e}", flush=True)
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
