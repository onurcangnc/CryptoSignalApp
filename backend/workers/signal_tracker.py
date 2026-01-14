#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoSignal - Signal Tracker Worker v2.0
==========================================
Tracks open positions and manages exits

v2.0 Changes:
- TRAILING STOP implementation (was calculated but never used!)
- Tracks highest_price / lowest_price for dynamic trailing
- Better exit reason tracking

Runs every 60 seconds:
- Get current price from Redis (prices_data)
- Check Stop-Loss
- Check Trailing Stop (NEW!)
- Check Take-Profit
- Check 7-day time limit
- Calculate profit/loss and update DB
"""

import asyncio
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
import os

# Parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

# Redis connection
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None
)

# Config
MAX_HOLD_DAYS = 7


class SignalTracker:
    """Signal tracker with trailing stop support - v2.0"""

    def __init__(self):
        self.closed_count = 0
        self.exits = {
            "STOP_LOSS": 0,
            "TAKE_PROFIT": 0,
            "TRAILING_STOP": 0,
            "TIME_EXPIRED": 0,
            "MANUAL": 0
        }

    def get_current_price(self, symbol: str, prices_data: Dict) -> Optional[float]:
        """Get current price from Redis prices_data"""
        try:
            coin_data = prices_data.get(symbol)
            if coin_data:
                return coin_data.get("price")
        except Exception:
            pass
        return None

    def update_trailing_stop(
        self,
        signal_id: int,
        current_price: float,
        is_long: bool,
        entry_price: float,
        trailing_stop: float,
        trailing_stop_pct: float,
        highest_price: float,
        lowest_price: float
    ) -> tuple:
        """
        Update trailing stop based on price movement.

        Returns: (new_trailing_stop, new_highest, new_lowest, should_exit)
        """
        should_exit = False
        new_trailing = trailing_stop
        new_highest = highest_price
        new_lowest = lowest_price

        if is_long:
            # LONG: Track highest price, raise trailing stop
            if current_price > highest_price:
                new_highest = current_price
                # Calculate new trailing stop
                new_trailing = new_highest * (1 - trailing_stop_pct / 100)
                # Only raise trailing stop, never lower it
                if new_trailing <= trailing_stop:
                    new_trailing = trailing_stop

            # Check if trailing stop is hit
            if current_price <= trailing_stop and trailing_stop > entry_price * 0.5:
                should_exit = True
        else:
            # SHORT: Track lowest price, lower trailing stop
            if current_price < lowest_price:
                new_lowest = current_price
                # Calculate new trailing stop
                new_trailing = new_lowest * (1 + trailing_stop_pct / 100)
                # Only lower trailing stop, never raise it
                if new_trailing >= trailing_stop:
                    new_trailing = trailing_stop

            # Check if trailing stop is hit
            if current_price >= trailing_stop:
                should_exit = True

        return new_trailing, new_highest, new_lowest, should_exit

    def process_signal(self, signal_row: Dict, prices_data: Dict) -> Optional[str]:
        """
        Process a single signal with trailing stop support.

        Returns:
            exit_reason or None (still open)
        """
        signal_id = signal_row.get("id")
        symbol = signal_row.get("symbol")
        signal = signal_row.get("signal")
        entry_price = signal_row.get("entry_price", 0)
        stop_loss = signal_row.get("stop_loss")
        take_profit = signal_row.get("target_price")  # DB uses target_price
        trailing_stop = signal_row.get("trailing_stop")
        trailing_stop_pct = signal_row.get("trailing_stop_pct", 2.0)
        highest_price = signal_row.get("highest_price") or entry_price
        lowest_price = signal_row.get("lowest_price") or entry_price
        created_at = signal_row.get("created_at", "")

        if not entry_price or not stop_loss or not take_profit:
            return None  # Missing data, skip

        # Get current price
        current_price = self.get_current_price(symbol, prices_data)
        if not current_price:
            return None  # Can't get price, skip

        # LONG or SHORT?
        is_long = signal in ["BUY", "STRONG_BUY", "AL", "GÜÇLÜ AL"]

        # Initialize trailing stop if missing
        if not trailing_stop:
            if is_long:
                trailing_stop = entry_price * (1 - (trailing_stop_pct or 2.0) / 100)
            else:
                trailing_stop = entry_price * (1 + (trailing_stop_pct or 2.0) / 100)

        exit_reason = None

        # 1. TIME EXPIRED CHECK
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created_dt.tzinfo:
                    created_dt = created_dt.replace(tzinfo=None)
                days_held = (datetime.utcnow() - created_dt).days
                if days_held >= MAX_HOLD_DAYS:
                    exit_reason = "TIME_EXPIRED"
            except Exception:
                pass

        # 2. UPDATE TRAILING STOP
        if not exit_reason and trailing_stop_pct:
            new_trailing, new_highest, new_lowest, trailing_hit = self.update_trailing_stop(
                signal_id, current_price, is_long, entry_price,
                trailing_stop, trailing_stop_pct, highest_price, lowest_price
            )

            # Update highest/lowest in DB even if not exiting
            if new_highest != highest_price or new_lowest != lowest_price or new_trailing != trailing_stop:
                try:
                    with get_db() as conn:
                        conn.execute("""
                            UPDATE signal_tracking
                            SET highest_price = ?,
                                lowest_price = ?,
                                trailing_stop = ?
                            WHERE id = ?
                        """, (new_highest, new_lowest, new_trailing, signal_id))
                        conn.commit()
                except Exception as e:
                    print(f"  [Tracker] Error updating trailing: {e}", flush=True)

            trailing_stop = new_trailing
            highest_price = new_highest
            lowest_price = new_lowest

        # 3. EXIT CONDITION CHECKS (in order of priority)
        if not exit_reason:
            if is_long:
                # LONG position exit checks
                # Check SL first (worst case)
                if current_price <= stop_loss:
                    exit_reason = "STOP_LOSS"
                # Check trailing stop (if profit exists)
                elif trailing_stop > entry_price and current_price <= trailing_stop:
                    exit_reason = "TRAILING_STOP"
                # Check TP (best case)
                elif current_price >= take_profit:
                    exit_reason = "TAKE_PROFIT"
            else:
                # SHORT position exit checks
                if current_price >= stop_loss:
                    exit_reason = "STOP_LOSS"
                elif trailing_stop < entry_price and current_price >= trailing_stop:
                    exit_reason = "TRAILING_STOP"
                elif current_price <= take_profit:
                    exit_reason = "TAKE_PROFIT"

        # 4. UPDATE DB IF EXIT
        if exit_reason:
            # Calculate profit/loss
            if is_long:
                profit_loss_pct = ((current_price - entry_price) / entry_price * 100)
            else:
                profit_loss_pct = ((entry_price - current_price) / entry_price * 100)

            is_successful = 1 if profit_loss_pct > 0 else 0

            # Determine result status
            if exit_reason in ["TAKE_PROFIT", "TRAILING_STOP"] and profit_loss_pct > 0:
                result_status = "SUCCESS"
            elif exit_reason == "STOP_LOSS":
                result_status = "STOPPED"
            elif exit_reason == "TIME_EXPIRED":
                result_status = "EXPIRED"
            else:
                result_status = "CLOSED"

            try:
                with get_db() as conn:
                    conn.execute("""
                        UPDATE signal_tracking
                        SET result = ?,
                            actual_price = ?,
                            profit_loss_pct = ?,
                            is_successful = ?,
                            exit_reason = ?,
                            closed_at = ?,
                            highest_price = ?,
                            lowest_price = ?
                        WHERE id = ?
                    """, (
                        result_status,
                        current_price,
                        round(profit_loss_pct, 2),
                        is_successful,
                        exit_reason,
                        datetime.utcnow().isoformat(),
                        highest_price,
                        lowest_price,
                        signal_id
                    ))
                    conn.commit()
            except Exception as e:
                print(f"  [Tracker] Error closing signal: {e}", flush=True)
                return None

            self.closed_count += 1
            self.exits[exit_reason] = self.exits.get(exit_reason, 0) + 1

            # Log significant exits
            emoji = "✅" if profit_loss_pct > 0 else "❌"
            print(f"  {emoji} {symbol}: {exit_reason} | P/L: {profit_loss_pct:+.2f}%", flush=True)

            return exit_reason

        return None

    def process_all_signals(self) -> Dict:
        """
        Process all open signals.

        Returns:
            Dict with stats
        """
        self.closed_count = 0
        self.exits = {
            "STOP_LOSS": 0,
            "TAKE_PROFIT": 0,
            "TRAILING_STOP": 0,
            "TIME_EXPIRED": 0,
            "MANUAL": 0
        }

        try:
            # Get current prices from Redis
            prices_raw = redis_client.get("prices_data")
            prices_data = json.loads(prices_raw) if prices_raw else {}

            if not prices_data:
                return {"closed": 0, "exits": self.exits, "open": 0, "error": "No price data"}

            with get_db() as conn:
                # Get open signals
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
    """Main loop - runs every 60 seconds"""
    print("[Signal Tracker v2.0] Starting with Trailing Stop support...", flush=True)
    print(f"  Check interval: 60 seconds", flush=True)
    print(f"  Max hold time: {MAX_HOLD_DAYS} days", flush=True)
    print(f"  Exit types: STOP_LOSS, TAKE_PROFIT, TRAILING_STOP, TIME_EXPIRED", flush=True)

    while True:
        try:
            stats = signal_tracker.process_all_signals()

            if stats.get("closed", 0) > 0:
                exits = stats['exits']
                print(f"  [Tracker] Closed: {stats['closed']} | "
                      f"TP: {exits.get('TAKE_PROFIT', 0)} | "
                      f"SL: {exits.get('STOP_LOSS', 0)} | "
                      f"Trail: {exits.get('TRAILING_STOP', 0)} | "
                      f"Exp: {exits.get('TIME_EXPIRED', 0)}", flush=True)

            await asyncio.sleep(60)

        except Exception as e:
            print(f"[Tracker] Error: {e}", flush=True)
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
