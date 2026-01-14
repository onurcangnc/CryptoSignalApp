# -*- coding: utf-8 -*-
"""
CryptoSignal - Exit Strategy Backtest Engine v2.0

v2.0 Changes:
- Uses SHARED multipliers from analysis_service (consistency!)
- Proper ATR calculation with OHLCV data
- Configurable confidence/category for accurate backtesting
- Cleaner cache management to prevent look-ahead bias
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Import shared multiplier functions from analysis_service
from services.analysis_service import (
    get_confidence_multipliers,
    get_category_adjustments,
    get_timeframe_multipliers
)


@dataclass
class BacktestResult:
    symbol: str
    entry_date: str
    entry_price: float
    signal_type: str
    stop_loss: float
    take_profit: float
    exit_date: str
    exit_price: float
    exit_reason: str  # STOP_LOSS, TAKE_PROFIT, TIME_EXPIRED, TRAILING_STOP
    profit_loss_pct: float
    is_successful: bool
    hold_duration_hours: int
    confidence: int = 75  # Added confidence tracking
    category: str = "ALT"  # Added category tracking


@dataclass
class BacktestSummary:
    total_signals: int
    successful: int
    failed: int
    expired: int
    success_rate: float
    avg_profit: float
    avg_loss: float
    total_return_pct: float
    profit_factor: float
    max_drawdown: float
    avg_hold_hours: float
    best_trade: Optional[dict]
    worst_trade: Optional[dict]
    actual_rr_ratio: float = 0.0  # Added actual R:R tracking


class BacktestEngine:
    """
    Backtesting engine that uses the SAME multipliers as production.
    """

    def __init__(self):
        self.binance_base = "https://api.binance.com/api/v3"
        self.cache: Dict[str, List[dict]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.atr_period = 14
        self.max_hold_days = 7
        self.cache_duration = 3600  # 1 hour cache

    def clear_cache(self):
        """Clear all cached data to prevent look-ahead bias between runs."""
        self.cache.clear()
        self.cache_timestamps.clear()

    async def fetch_historical_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 1000
    ) -> List[dict]:
        """
        Fetch historical klines with proper cache management.
        """
        # Create cache key WITHOUT end_date to prevent look-ahead
        cache_key = f"{symbol}_{interval}_{start_date.strftime('%Y%m%d') if start_date else 'none'}"

        # Check cache validity
        if cache_key in self.cache:
            cache_time = self.cache_timestamps.get(cache_key)
            if cache_time and (datetime.utcnow() - cache_time).total_seconds() < self.cache_duration:
                # Filter cached data to only include up to end_date
                cached = self.cache[cache_key]
                if end_date:
                    return [k for k in cached if k["open_time"] <= end_date]
                return cached

        trading_symbol = f"{symbol.upper()}USDT"
        params = {"symbol": trading_symbol, "interval": interval, "limit": limit}

        if start_date:
            params["startTime"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["endTime"] = int(end_date.timestamp() * 1000)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self.binance_base}/klines", params=params)
                if resp.status_code != 200:
                    return []
                raw_klines = resp.json()
                klines = []
                for k in raw_klines:
                    klines.append({
                        "open_time": datetime.fromtimestamp(k[0] / 1000),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                        "close_time": datetime.fromtimestamp(k[6] / 1000)
                    })

                # Cache the full dataset
                self.cache[cache_key] = klines
                self.cache_timestamps[cache_key] = datetime.utcnow()
                return klines

        except Exception as e:
            print(f"[Backtest] Kline fetch error: {e}")
            return []

    def calculate_atr(self, klines: List[dict], period: int = 14) -> float:
        """
        Calculate TRUE ATR using High/Low/Close data.
        Same formula as analysis_service.calc_true_atr()
        """
        if len(klines) < period + 1:
            return 0

        true_ranges = []
        for i in range(1, len(klines)):
            high = klines[i]["high"]
            low = klines[i]["low"]
            prev_close = klines[i-1]["close"]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        if len(true_ranges) >= period:
            return sum(true_ranges[-period:]) / period
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0

    def calculate_exit_levels(
        self,
        entry_price: float,
        atr: float,
        signal_type: str,
        timeframe: str = "1d",
        confidence: int = 75,
        category: str = "ALT"
    ) -> Tuple[float, float, float]:
        """
        Calculate exit levels using SHARED multipliers from analysis_service.
        Returns: (stop_loss, take_profit, trailing_stop)
        """
        # Get multipliers from shared functions (SAME AS PRODUCTION!)
        sl_mult, tp_mult = get_confidence_multipliers(confidence)
        cat_sl_adj, cat_tp_adj = get_category_adjustments(category)
        tf_sl_mult, tf_tp_mult, _ = get_timeframe_multipliers(timeframe)

        # Apply all multipliers
        final_sl_mult = sl_mult * cat_sl_adj * tf_sl_mult
        final_tp_mult = tp_mult * cat_tp_adj * tf_tp_mult

        # Calculate ATR percent
        atr_percent = (atr / entry_price * 100) if entry_price > 0 else 3.0
        atr_percent = max(1.5, min(atr_percent, 10.0))

        # Calculate percentages
        stop_loss_pct = atr_percent * final_sl_mult
        take_profit_pct = atr_percent * final_tp_mult

        # Apply timeframe limits (same as analysis_service)
        if timeframe == "1d":
            stop_loss_pct = max(1.0, min(stop_loss_pct, 8.0))
            take_profit_pct = max(2.0, min(take_profit_pct, 20.0))
        elif timeframe == "1w":
            stop_loss_pct = max(3.0, min(stop_loss_pct, 15.0))
            take_profit_pct = max(6.0, min(take_profit_pct, 35.0))

        # Ensure minimum 1:2 R:R ratio
        if take_profit_pct < stop_loss_pct * 2:
            take_profit_pct = stop_loss_pct * 2.0

        is_long = signal_type.upper() in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]

        if is_long:
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
            take_profit = entry_price * (1 + take_profit_pct / 100)
            trailing_stop = entry_price * (1 - stop_loss_pct * 0.8 / 100)
        else:
            stop_loss = entry_price * (1 + stop_loss_pct / 100)
            take_profit = entry_price * (1 - take_profit_pct / 100)
            trailing_stop = entry_price * (1 + stop_loss_pct * 0.8 / 100)

        return round(stop_loss, 8), round(take_profit, 8), round(trailing_stop, 8)

    def find_exit_point(
        self,
        klines: List[dict],
        entry_index: int,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        trailing_stop: float,
        signal_type: str,
        max_bars: int = 168
    ) -> Tuple[int, float, str]:
        """
        Find exit point with trailing stop support.
        """
        is_long = signal_type.upper() in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]
        highest_price = entry_price
        lowest_price = entry_price
        current_trailing = trailing_stop
        trailing_pct = abs(entry_price - trailing_stop) / entry_price

        for i in range(entry_index + 1, min(entry_index + max_bars + 1, len(klines))):
            high = klines[i]["high"]
            low = klines[i]["low"]

            if is_long:
                # Update highest price and trailing stop
                if high > highest_price:
                    highest_price = high
                    new_trailing = highest_price * (1 - trailing_pct)
                    if new_trailing > current_trailing:
                        current_trailing = new_trailing

                # Check exits in order: SL first (worst case), then trailing, then TP
                if low <= stop_loss:
                    return i, stop_loss, "STOP_LOSS"
                if low <= current_trailing and current_trailing > stop_loss:
                    return i, current_trailing, "TRAILING_STOP"
                if high >= take_profit:
                    return i, take_profit, "TAKE_PROFIT"
            else:
                # SHORT position
                if low < lowest_price:
                    lowest_price = low
                    new_trailing = lowest_price * (1 + trailing_pct)
                    if new_trailing < current_trailing:
                        current_trailing = new_trailing

                if high >= stop_loss:
                    return i, stop_loss, "STOP_LOSS"
                if high >= current_trailing and current_trailing < stop_loss:
                    return i, current_trailing, "TRAILING_STOP"
                if low <= take_profit:
                    return i, take_profit, "TAKE_PROFIT"

        # Time expired
        if entry_index + max_bars < len(klines):
            return entry_index + max_bars, klines[entry_index + max_bars]["close"], "TIME_EXPIRED"
        return len(klines) - 1, klines[-1]["close"], "INCOMPLETE"

    async def backtest_signal(
        self,
        symbol: str,
        entry_date: datetime,
        signal_type: str,
        timeframe: str = "1d",
        confidence: int = 75,
        category: str = "ALT"
    ) -> Optional[BacktestResult]:
        """
        Backtest a single signal with configurable confidence and category.
        """
        start_date = entry_date - timedelta(days=20)
        end_date = entry_date + timedelta(days=10)
        klines = await self.fetch_historical_klines(symbol, "1h", start_date, end_date)

        if len(klines) < 20:
            return None

        # Find entry point
        entry_index, entry_price = None, None
        for i, k in enumerate(klines):
            if k["open_time"] >= entry_date:
                entry_index, entry_price = i, k["open"]
                break

        if entry_index is None:
            return None

        # Calculate ATR from candles BEFORE entry (no look-ahead)
        atr_klines = klines[max(0, entry_index - 15):entry_index]
        atr = self.calculate_atr(atr_klines, self.atr_period)
        if atr == 0:
            atr = entry_price * 0.02

        # Calculate exit levels using SHARED multipliers
        stop_loss, take_profit, trailing_stop = self.calculate_exit_levels(
            entry_price, atr, signal_type, timeframe, confidence, category
        )

        # Find exit
        exit_index, exit_price, exit_reason = self.find_exit_point(
            klines, entry_index, entry_price, stop_loss, take_profit,
            trailing_stop, signal_type
        )

        # Calculate P/L
        is_long = signal_type.upper() in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]
        if is_long:
            profit_loss_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            profit_loss_pct = ((entry_price - exit_price) / entry_price) * 100

        hold_duration = klines[exit_index]["close_time"] - klines[entry_index]["open_time"]

        return BacktestResult(
            symbol=symbol,
            entry_date=entry_date.strftime("%Y-%m-%d %H:%M"),
            entry_price=entry_price,
            signal_type=signal_type,
            stop_loss=stop_loss,
            take_profit=take_profit,
            exit_date=klines[exit_index]["close_time"].strftime("%Y-%m-%d %H:%M"),
            exit_price=exit_price,
            exit_reason=exit_reason,
            profit_loss_pct=round(profit_loss_pct, 2),
            is_successful=(exit_reason in ["TAKE_PROFIT", "TRAILING_STOP"] and profit_loss_pct > 0),
            hold_duration_hours=int(hold_duration.total_seconds() / 3600),
            confidence=confidence,
            category=category
        )

    async def run_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        signal_frequency_hours: int = 24,
        timeframe: str = "1d",
        confidence: int = 75,
        category: str = "ALT"
    ) -> Dict:
        """Run backtest across multiple symbols."""
        print(f"[Backtest] Starting: {len(symbols)} symbols, {timeframe}, conf={confidence}")

        # Clear cache before new backtest run
        self.clear_cache()

        results: List[BacktestResult] = []
        for symbol in symbols:
            current_date = start_date
            while current_date < end_date:
                try:
                    result = await self.backtest_signal(
                        symbol, current_date, "BUY", timeframe, confidence, category
                    )
                    if result and result.exit_reason != "INCOMPLETE":
                        results.append(result)
                except Exception as e:
                    pass
                current_date += timedelta(hours=signal_frequency_hours)
            await asyncio.sleep(0.3)

        summary = self.calculate_summary(results)
        return {
            "summary": asdict(summary) if summary else None,
            "results": [asdict(r) for r in results[-50:]],
            "total_results": len(results),
            "config": {
                "symbols": symbols,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timeframe": timeframe,
                "confidence": confidence,
                "category": category
            }
        }

    def calculate_summary(self, results: List[BacktestResult]) -> Optional[BacktestSummary]:
        """Calculate backtest summary with actual R:R ratio."""
        if not results:
            return None

        total = len(results)
        successful = sum(1 for r in results if r.exit_reason in ["TAKE_PROFIT", "TRAILING_STOP"])
        failed = sum(1 for r in results if r.exit_reason == "STOP_LOSS")
        expired = sum(1 for r in results if r.exit_reason == "TIME_EXPIRED")

        profits = [r.profit_loss_pct for r in results if r.profit_loss_pct > 0]
        losses = [r.profit_loss_pct for r in results if r.profit_loss_pct < 0]

        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        # Calculate actual R:R ratio
        actual_rr = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

        total_return = 1.0
        max_drawdown, peak = 0, 1.0
        for r in results:
            total_return *= (1 + r.profit_loss_pct / 100)
            if total_return > peak:
                peak = total_return
            drawdown = (peak - total_return) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        gross_profit = sum(profits) if profits else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        avg_hold = sum(r.hold_duration_hours for r in results) / total

        sorted_results = sorted(results, key=lambda x: x.profit_loss_pct, reverse=True)

        return BacktestSummary(
            total_signals=total,
            successful=successful,
            failed=failed,
            expired=expired,
            success_rate=round(successful / total * 100, 1),
            avg_profit=round(avg_profit, 2),
            avg_loss=round(avg_loss, 2),
            total_return_pct=round((total_return - 1) * 100, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_drawdown, 2),
            avg_hold_hours=round(avg_hold, 1),
            best_trade=asdict(sorted_results[0]) if sorted_results else None,
            worst_trade=asdict(sorted_results[-1]) if sorted_results else None,
            actual_rr_ratio=round(actual_rr, 2)
        )
