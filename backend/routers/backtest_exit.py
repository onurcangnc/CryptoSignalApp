# -*- coding: utf-8 -*-
from fastapi import APIRouter, Query, Body
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.backtest_engine import BacktestEngine

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = BacktestEngine()
    return _engine

@router.get("/quick")
async def quick_backtest(
    symbol: str = Query(default="BTC"),
    days: int = Query(default=30, ge=7, le=90),
    timeframe: str = Query(default="1d")
):
    engine = get_engine()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return await engine.run_backtest([symbol.upper()], start_date, end_date, 24, timeframe)

@router.post("/run")
async def run_backtest(
    symbols: List[str] = Body(default=["BTC", "ETH", "SOL"], embed=True),
    days: int = Body(default=30, ge=7, le=90, embed=True),
    timeframe: str = Body(default="1d", embed=True)
):
    engine = get_engine()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return await engine.run_backtest(symbols, start_date, end_date, 24, timeframe)

@router.get("/compare")
async def compare_timeframes(symbol: str = Query(default="BTC"), days: int = Query(default=30)):
    engine = get_engine()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    results = {}
    for tf in ["1d", "1w", "1m"]:
        r = await engine.run_backtest([symbol.upper()], start_date, end_date, 24, tf)
        if r["summary"]:
            results[tf] = {"success_rate": r["summary"]["success_rate"],
                          "total_return_pct": r["summary"]["total_return_pct"],
                          "profit_factor": r["summary"]["profit_factor"]}
    best = max(results.keys(), key=lambda x: results[x]["success_rate"]) if results else None
    return {"symbol": symbol, "comparison": results, "best_timeframe": best}
