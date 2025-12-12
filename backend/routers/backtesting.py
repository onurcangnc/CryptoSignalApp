# -*- coding: utf-8 -*-
"""
CryptoSignal - Backtesting Router
=================================
Sinyal geçmişi analizi ve backtesting
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import json
from datetime import datetime, timedelta
from collections import defaultdict

from dependencies import get_current_user
from database import get_db, redis_client

router = APIRouter(prefix="/api/backtesting", tags=["Backtesting"])


@router.get("/history")
async def get_signal_history(
    days: int = Query(30, ge=7, le=365),
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    user=Depends(get_current_user)
):
    """
    Detaylı sinyal geçmişi

    - Tüm sinyalleri tarih sırasına göre listeler
    - Her sinyal için sonucu gösterir
    - Filtreleme seçenekleri sunar
    """
    cache_key = f"backtest_history_{days}_{symbol or 'all'}_{signal_type or 'all'}"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    signals = fetch_signal_history(days, symbol, signal_type)

    result = {
        "period_days": days,
        "filters": {
            "symbol": symbol,
            "signal_type": signal_type
        },
        "total_signals": len(signals),
        "signals": signals
    }

    # Cache 5 dakika
    redis_client.setex(cache_key, 300, json.dumps(result))

    return result


@router.get("/performance")
async def get_backtest_performance(
    days: int = Query(30, ge=7, le=365),
    user=Depends(get_current_user)
):
    """
    Backtesting performans özeti

    - Zaman bazlı performans grafiği için veri
    - Günlük/haftalık başarı oranları
    - Trend analizi
    """
    cache_key = f"backtest_performance_{days}"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    # Günlük performans verileri
    daily_data = calculate_daily_performance(days)

    # Haftalık aggregation
    weekly_data = aggregate_to_weekly(daily_data)

    # Genel istatistikler
    overall = calculate_overall_stats(daily_data)

    # Trend analizi
    trend = analyze_trend(daily_data)

    result = {
        "period_days": days,
        "overall": overall,
        "trend": trend,
        "daily": daily_data[-30:],  # Son 30 günü göster
        "weekly": weekly_data,
        "chart_data": format_chart_data(daily_data)
    }

    redis_client.setex(cache_key, 300, json.dumps(result))

    return result


@router.get("/by-coin")
async def get_performance_by_coin(
    days: int = Query(30, ge=7, le=365),
    user=Depends(get_current_user)
):
    """
    Coin bazlı performans karşılaştırması

    - Her coin için başarı oranı
    - En iyi/kötü performans gösteren coinler
    """
    cache_key = f"backtest_by_coin_{days}"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    coin_stats = calculate_coin_performance(days)

    # Sırala
    sorted_by_success = sorted(
        coin_stats.values(),
        key=lambda x: x['success_rate'],
        reverse=True
    )

    result = {
        "period_days": days,
        "coins": sorted_by_success,
        "best_performers": sorted_by_success[:5],
        "worst_performers": sorted_by_success[-5:][::-1] if len(sorted_by_success) > 5 else [],
        "total_coins": len(coin_stats)
    }

    redis_client.setex(cache_key, 300, json.dumps(result))

    return result


@router.get("/by-signal-type")
async def get_performance_by_signal_type(
    days: int = Query(30, ge=7, le=365),
    user=Depends(get_current_user)
):
    """
    Sinyal türü bazlı performans

    - AL/SAT/GÜÇLÜ AL vs. performans karşılaştırması
    """
    cache_key = f"backtest_by_type_{days}"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    type_stats = calculate_signal_type_performance(days)

    result = {
        "period_days": days,
        "signal_types": type_stats
    }

    redis_client.setex(cache_key, 300, json.dumps(result))

    return result


@router.get("/simulate")
async def simulate_strategy(
    symbol: str = Query(..., description="Coin sembolü"),
    initial_investment: float = Query(1000, ge=100),
    days: int = Query(30, ge=7, le=365),
    follow_signals: bool = Query(True, description="Sinyalleri takip et"),
    user=Depends(get_current_user)
):
    """
    Strateji simülasyonu

    - Belirli bir coin için sinyalleri takip etseydiniz ne olurdu?
    - Hold vs Signal Following karşılaştırması
    """
    # Sinyal geçmişini al
    signals = fetch_signal_history(days, symbol, None)

    if not signals:
        return {
            "symbol": symbol,
            "error": "No signals found for this period",
            "total_signals": 0
        }

    # Simülasyon
    simulation = run_simulation(
        signals=signals,
        initial_investment=initial_investment,
        follow_signals=follow_signals
    )

    return {
        "symbol": symbol,
        "period_days": days,
        "initial_investment": initial_investment,
        "strategy": "signal_following" if follow_signals else "hold",
        "simulation": simulation,
        "total_signals": len(signals)
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def fetch_signal_history(days: int, symbol: Optional[str], signal_type: Optional[str]) -> List[dict]:
    """Veritabanından sinyal geçmişini al"""
    try:
        with get_db() as conn:
            c = conn.cursor()

            query = """
                SELECT
                    coin, signal, confidence, price_at_signal,
                    created_at, target_price, actual_result, result_pct
                FROM signals
                WHERE created_at >= datetime('now', ?)
            """
            params = [f'-{days} days']

            if symbol:
                query += " AND UPPER(coin) = UPPER(?)"
                params.append(symbol)

            if signal_type:
                query += " AND signal LIKE ?"
                params.append(f"%{signal_type}%")

            query += " ORDER BY created_at DESC"

            c.execute(query, params)
            rows = c.fetchall()

            signals = []
            for row in rows:
                # Sonuç belirleme
                result_pct = row[7] if row[7] else 0
                if result_pct > 2:
                    outcome = "success"
                elif result_pct < -2:
                    outcome = "failure"
                else:
                    outcome = "neutral"

                signals.append({
                    "coin": row[0],
                    "signal": row[1],
                    "confidence": row[2],
                    "price_at_signal": row[3],
                    "created_at": row[4],
                    "target_price": row[5],
                    "actual_result": row[6],
                    "result_pct": result_pct,
                    "outcome": outcome
                })

            return signals
    except Exception as e:
        print(f"[Backtesting] History fetch error: {e}")
        return []


def calculate_daily_performance(days: int) -> List[dict]:
    """Günlük performans verilerini hesapla"""
    try:
        with get_db() as conn:
            c = conn.cursor()

            c.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN result_pct > 2 THEN 1 ELSE 0 END) as successful,
                    AVG(result_pct) as avg_return
                FROM signals
                WHERE created_at >= datetime('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date
            """, [f'-{days} days'])

            rows = c.fetchall()

            daily = []
            for row in rows:
                total = row[1] or 1
                successful = row[2] or 0
                daily.append({
                    "date": row[0],
                    "total_signals": total,
                    "successful": successful,
                    "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
                    "avg_return": round(row[3] or 0, 2)
                })

            return daily
    except Exception as e:
        print(f"[Backtesting] Daily performance error: {e}")
        return []


def aggregate_to_weekly(daily_data: List[dict]) -> List[dict]:
    """Günlük veriyi haftalık aggrege et"""
    if not daily_data:
        return []

    weekly = defaultdict(lambda: {"total": 0, "successful": 0, "returns": []})

    for day in daily_data:
        # Haftanın başlangıcını bul
        date = datetime.strptime(day['date'], '%Y-%m-%d')
        week_start = date - timedelta(days=date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')

        weekly[week_key]["total"] += day["total_signals"]
        weekly[week_key]["successful"] += day["successful"]
        weekly[week_key]["returns"].append(day["avg_return"])

    result = []
    for week, data in sorted(weekly.items()):
        success_rate = round(data["successful"] / data["total"] * 100, 1) if data["total"] > 0 else 0
        avg_return = round(sum(data["returns"]) / len(data["returns"]), 2) if data["returns"] else 0

        result.append({
            "week_start": week,
            "total_signals": data["total"],
            "successful": data["successful"],
            "success_rate": success_rate,
            "avg_return": avg_return
        })

    return result


def calculate_overall_stats(daily_data: List[dict]) -> dict:
    """Genel istatistikleri hesapla"""
    if not daily_data:
        return {
            "total_signals": 0,
            "successful": 0,
            "success_rate": 0,
            "avg_return": 0,
            "best_day": None,
            "worst_day": None
        }

    total = sum(d["total_signals"] for d in daily_data)
    successful = sum(d["successful"] for d in daily_data)
    avg_return = sum(d["avg_return"] for d in daily_data) / len(daily_data) if daily_data else 0

    best_day = max(daily_data, key=lambda x: x["success_rate"]) if daily_data else None
    worst_day = min(daily_data, key=lambda x: x["success_rate"]) if daily_data else None

    return {
        "total_signals": total,
        "successful": successful,
        "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
        "avg_return": round(avg_return, 2),
        "best_day": best_day,
        "worst_day": worst_day,
        "active_days": len(daily_data)
    }


def analyze_trend(daily_data: List[dict]) -> dict:
    """Trend analizi"""
    if len(daily_data) < 7:
        return {"trend": "insufficient_data", "description": "Yeterli veri yok"}

    # Son 7 gün vs önceki 7 gün
    recent = daily_data[-7:] if len(daily_data) >= 7 else daily_data
    previous = daily_data[-14:-7] if len(daily_data) >= 14 else daily_data[:len(daily_data)//2]

    recent_avg = sum(d["success_rate"] for d in recent) / len(recent) if recent else 0
    previous_avg = sum(d["success_rate"] for d in previous) / len(previous) if previous else 0

    diff = recent_avg - previous_avg

    if diff > 5:
        trend = "improving"
        description = "Performans yükselişte"
    elif diff < -5:
        trend = "declining"
        description = "Performans düşüşte"
    else:
        trend = "stable"
        description = "Performans stabil"

    return {
        "trend": trend,
        "description": description,
        "recent_avg": round(recent_avg, 1),
        "previous_avg": round(previous_avg, 1),
        "change": round(diff, 1)
    }


def format_chart_data(daily_data: List[dict]) -> dict:
    """Grafik için formatlı veri"""
    return {
        "labels": [d["date"] for d in daily_data],
        "success_rate": [d["success_rate"] for d in daily_data],
        "total_signals": [d["total_signals"] for d in daily_data],
        "avg_return": [d["avg_return"] for d in daily_data]
    }


def calculate_coin_performance(days: int) -> dict:
    """Coin bazlı performans"""
    try:
        with get_db() as conn:
            c = conn.cursor()

            c.execute("""
                SELECT
                    UPPER(coin) as coin,
                    COUNT(*) as total,
                    SUM(CASE WHEN result_pct > 2 THEN 1 ELSE 0 END) as successful,
                    AVG(result_pct) as avg_return
                FROM signals
                WHERE created_at >= datetime('now', ?)
                GROUP BY UPPER(coin)
                HAVING COUNT(*) >= 3
            """, [f'-{days} days'])

            rows = c.fetchall()

            coins = {}
            for row in rows:
                total = row[1] or 1
                successful = row[2] or 0
                coins[row[0]] = {
                    "symbol": row[0],
                    "total_signals": total,
                    "successful": successful,
                    "success_rate": round(successful / total * 100, 1),
                    "avg_return": round(row[3] or 0, 2)
                }

            return coins
    except Exception as e:
        print(f"[Backtesting] Coin performance error: {e}")
        return {}


def calculate_signal_type_performance(days: int) -> List[dict]:
    """Sinyal türü bazlı performans"""
    try:
        with get_db() as conn:
            c = conn.cursor()

            c.execute("""
                SELECT
                    signal,
                    COUNT(*) as total,
                    SUM(CASE WHEN result_pct > 2 THEN 1 ELSE 0 END) as successful,
                    AVG(result_pct) as avg_return
                FROM signals
                WHERE created_at >= datetime('now', ?)
                GROUP BY signal
            """, [f'-{days} days'])

            rows = c.fetchall()

            types = []
            for row in rows:
                total = row[1] or 1
                successful = row[2] or 0
                types.append({
                    "signal_type": row[0],
                    "total_signals": total,
                    "successful": successful,
                    "success_rate": round(successful / total * 100, 1),
                    "avg_return": round(row[3] or 0, 2)
                })

            return sorted(types, key=lambda x: x["success_rate"], reverse=True)
    except Exception as e:
        print(f"[Backtesting] Signal type performance error: {e}")
        return []


def run_simulation(signals: List[dict], initial_investment: float, follow_signals: bool) -> dict:
    """Strateji simülasyonu"""
    if not signals:
        return {"error": "No signals to simulate"}

    portfolio_value = initial_investment
    trades = []
    wins = 0
    losses = 0

    for signal in signals:
        result_pct = signal.get("result_pct", 0)

        if follow_signals:
            # Sinyal takip stratejisi
            trade_return = result_pct / 100 * portfolio_value
            portfolio_value += trade_return

            if result_pct > 0:
                wins += 1
            elif result_pct < 0:
                losses += 1

            trades.append({
                "date": signal["created_at"],
                "signal": signal["signal"],
                "return_pct": result_pct,
                "portfolio_value": round(portfolio_value, 2)
            })

    total_return = portfolio_value - initial_investment
    total_return_pct = (total_return / initial_investment) * 100

    return {
        "final_value": round(portfolio_value, 2),
        "total_return": round(total_return, 2),
        "total_return_pct": round(total_return_pct, 2),
        "total_trades": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / len(trades) * 100, 1) if trades else 0,
        "trades_sample": trades[:10]  # İlk 10 trade
    }
