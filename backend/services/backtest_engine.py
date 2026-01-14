# -*- coding: utf-8 -*-
"""
CryptoSignal - Exit Strategy Backtest Engine v1.0
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


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
    exit_reason: str  # STOP_LOSS, TAKE_PROFIT, TIME_EXPIRED
    profit_loss_pct: float
    is_successful: bool
    hold_duration_hours: int


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


class BacktestEngine:
    def __init__(self):
        self.binance_base = "https://api.binance.com/api/v3"
        self.cache: Dict[str, List[dict]] = {}
        self.atr_period = 14
        self.timeframe_multipliers = {
            "1d": {"sl": 1.5, "tp": 3.0},
            "1w": {"sl": 2.0, "tp": 4.0},
            "1m": {"sl": 2.5, "tp": 5.0},
            "3m": {"sl": 3.0, "tp": 6.0},
            "6m": {"sl": 3.5, "tp": 7.0},
            "1y": {"sl": 4.0, "tp": 8.0}
        }
        self.max_hold_days = 7

    async def fetch_historical_klines(self, symbol: str, interval: str = "1h",
                                       start_date: datetime = None, end_date: datetime = None,
                                       limit: int = 1000) -> List[dict]:
        cache_key = f"{symbol}_{interval}_{start_date}_{end_date}"
        if cache_key in self.cache:
            return self.cache[cache_key]

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
                self.cache[cache_key] = klines
                return klines
        except Exception as e:
            print(f"[Backtest] Kline fetch error: {e}")
            return []

    def calculate_atr(self, klines: List[dict], period: int = 14) -> float:
        if len(klines) < period + 1:
            return 0
        true_ranges = []
        for i in range(1, len(klines)):
            high, low, prev_close = klines[i]["high"], klines[i]["low"], klines[i-1]["close"]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
        if len(true_ranges) >= period:
            return sum(true_ranges[-period:]) / period
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0

    def calculate_exit_levels(self, entry_price: float, atr: float, signal_type: str,
                               timeframe: str = "1d") -> Tuple[float, float]:
        multipliers = self.timeframe_multipliers.get(timeframe, {"sl": 1.5, "tp": 3.0})
        if signal_type.upper() in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]:
            stop_loss = entry_price - (atr * multipliers["sl"])
            take_profit = entry_price + (atr * multipliers["tp"])
        else:
            stop_loss = entry_price + (atr * multipliers["sl"])
            take_profit = entry_price - (atr * multipliers["tp"])
        return round(stop_loss, 8), round(take_profit, 8)

    def find_exit_point(self, klines: List[dict], entry_index: int, entry_price: float,
                        stop_loss: float, take_profit: float, signal_type: str,
                        max_bars: int = 168) -> Tuple[int, float, str]:
        is_long = signal_type.upper() in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]
        for i in range(entry_index + 1, min(entry_index + max_bars + 1, len(klines))):
            high, low = klines[i]["high"], klines[i]["low"]
            if is_long:
                if low <= stop_loss:
                    return i, stop_loss, "STOP_LOSS"
                if high >= take_profit:
                    return i, take_profit, "TAKE_PROFIT"
            else:
                if high >= stop_loss:
                    return i, stop_loss, "STOP_LOSS"
                if low <= take_profit:
                    return i, take_profit, "TAKE_PROFIT"
        if entry_index + max_bars < len(klines):
            return entry_index + max_bars, klines[entry_index + max_bars]["close"], "TIME_EXPIRED"
        return len(klines) - 1, klines[-1]["close"], "INCOMPLETE"

    async def backtest_signal(self, symbol: str, entry_date: datetime,
                               signal_type: str, timeframe: str = "1d") -> Optional[BacktestResult]:
        start_date = entry_date - timedelta(days=20)
        end_date = entry_date + timedelta(days=10)
        klines = await self.fetch_historical_klines(symbol, "1h", start_date, end_date)
        if len(klines) < 20:
            return None
        entry_index, entry_price = None, None
        for i, k in enumerate(klines):
            if k["open_time"] >= entry_date:
                entry_index, entry_price = i, k["open"]
                break
        if entry_index is None:
            return None
        atr_klines = klines[max(0, entry_index - 15):entry_index]
        atr = self.calculate_atr(atr_klines, self.atr_period)
        if atr == 0:
            atr = entry_price * 0.02
        stop_loss, take_profit = self.calculate_exit_levels(entry_price, atr, signal_type, timeframe)
        exit_index, exit_price, exit_reason = self.find_exit_point(
            klines, entry_index, entry_price, stop_loss, take_profit, signal_type)
        is_long = signal_type.upper() in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]
        if is_long:
            profit_loss_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            profit_loss_pct = ((entry_price - exit_price) / entry_price) * 100
        hold_duration = klines[exit_index]["close_time"] - klines[entry_index]["open_time"]
        return BacktestResult(
            symbol=symbol, entry_date=entry_date.strftime("%Y-%m-%d %H:%M"),
            entry_price=entry_price, signal_type=signal_type, stop_loss=stop_loss,
            take_profit=take_profit, exit_date=klines[exit_index]["close_time"].strftime("%Y-%m-%d %H:%M"),
            exit_price=exit_price, exit_reason=exit_reason, profit_loss_pct=round(profit_loss_pct, 2),
            is_successful=(exit_reason == "TAKE_PROFIT"), hold_duration_hours=int(hold_duration.total_seconds() / 3600))

    async def run_backtest(self, symbols: List[str], start_date: datetime, end_date: datetime,
                           signal_frequency_hours: int = 24, timeframe: str = "1d") -> Dict:
        print(f"[Backtest] Starting: {len(symbols)} symbols, {timeframe}")
        results: List[BacktestResult] = []
        for symbol in symbols:
            current_date = start_date
            while current_date < end_date:
                try:
                    result = await self.backtest_signal(symbol, current_date, "BUY", timeframe)
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
            "config": {"symbols": symbols, "start_date": start_date.strftime("%Y-%m-%d"),
                       "end_date": end_date.strftime("%Y-%m-%d"), "timeframe": timeframe}
        }

    def calculate_summary(self, results: List[BacktestResult]) -> Optional[BacktestSummary]:
        if not results:
            return None
        total = len(results)
        successful = sum(1 for r in results if r.exit_reason == "TAKE_PROFIT")
        failed = sum(1 for r in results if r.exit_reason == "STOP_LOSS")
        expired = sum(1 for r in results if r.exit_reason == "TIME_EXPIRED")
        profits = [r.profit_loss_pct for r in results if r.profit_loss_pct > 0]
        losses = [r.profit_loss_pct for r in results if r.profit_loss_pct < 0]
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
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
            total_signals=total, successful=successful, failed=failed, expired=expired,
            success_rate=round(successful / total * 100, 1),
            avg_profit=round(avg_profit, 2), avg_loss=round(avg_loss, 2),
            total_return_pct=round((total_return - 1) * 100, 2),
            profit_factor=round(profit_factor, 2), max_drawdown=round(max_drawdown, 2),
            avg_hold_hours=round(avg_hold, 1),
            best_trade=asdict(sorted_results[0]) if sorted_results else None,
            worst_trade=asdict(sorted_results[-1]) if sorted_results else None)
