# -*- coding: utf-8 -*-
"""
CryptoSignal - Signal Stats Router v2.1
=========================================
Sinyal başarı istatistikleri API + Exit Analysis

v2.1 Yeni endpointler:
- /api/exit-analysis - Exit reason bazlı performans
- /api/exit-timeline - Günlük exit timeline
"""

from fastapi import APIRouter, Depends
from typing import Optional
import json
from datetime import datetime, timedelta

from dependencies import get_current_user
from database import get_db, get_signal_success_rate, redis_client

router = APIRouter(prefix="/api", tags=["signals"])


@router.get("/signal-stats")
async def get_signal_stats(
    days: int = 30,
    symbol: Optional[str] = None,
    user=Depends(get_current_user)
):
    """
    Sinyal başarı istatistiklerini getir

    Args:
        days: Son X günün istatistikleri (7, 30, 90)
        symbol: Belirli bir coin için (opsiyonel)
    """
    # Redis cache'den al
    cache_key = f"signal_stats_{days}d"
    if symbol:
        cache_key += f"_{symbol}"

    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    # Veritabanından hesapla
    stats = get_signal_success_rate(days=days, symbol=symbol)

    # Cache'e kaydet (10 dakika)
    redis_client.setex(cache_key, 600, json.dumps(stats))

    return stats


@router.get("/signal-performance")
async def get_signal_performance(user=Depends(get_current_user)):
    """
    Genel sinyal performansı özeti
    Her zaman dilimi için toplam istatistikler
    """
    stats_7d = get_signal_success_rate(days=7)
    stats_30d = get_signal_success_rate(days=30)
    stats_90d = get_signal_success_rate(days=90)

    return {
        "overview": {
            "7_days": {
                "success_rate": stats_7d["success_rate"],
                "total_signals": stats_7d["total_signals"],
                "successful": stats_7d["successful_signals"]
            },
            "30_days": {
                "success_rate": stats_30d["success_rate"],
                "total_signals": stats_30d["total_signals"],
                "successful": stats_30d["successful_signals"]
            },
            "90_days": {
                "success_rate": stats_90d["success_rate"],
                "total_signals": stats_90d["total_signals"],
                "successful": stats_90d["successful_signals"]
            }
        },
        "by_signal_type": stats_30d["by_signal"],
        "message": f"Son 30 günde sinyallerimizin %{stats_30d['success_rate']:.1f}'i kârlı oldu"
    }


@router.get("/coin-signal-history/{symbol}")
async def get_coin_signal_history(
    symbol: str,
    user=Depends(get_current_user)
):
    """Belirli bir coin için sinyal geçmişi ve performansı"""
    stats = get_signal_success_rate(days=90, symbol=symbol)

    return {
        "symbol": symbol,
        "stats": stats,
        "recommendation": (
            f"{symbol} için son 90 günde {stats['total_signals']} sinyal verdik. "
            f"%{stats['success_rate']:.1f} başarı oranına sahibiz."
        )
    }


@router.get("/signal-accuracy-by-confidence")
async def get_accuracy_by_confidence(user=Depends(get_current_user)):
    """
    Confidence seviyesine göre sinyal accuracy istatistikleri

    Kalibrasyon verisi - confidence ile gerçek accuracy korelasyonu
    """
    # Redis'ten pre-computed stats al
    cached = redis_client.get("signal_accuracy_stats")
    if cached:
        try:
            stats = json.loads(cached)
            return {
                "status": "ok",
                "data": stats,
                "calibration_note": (
                    "Bu veriler sinyal güven skorlarının gerçek sonuçlarla "
                    "ne kadar örtüştüğünü gösterir. İdeal durumda yüksek güven "
                    "sinyalleri daha yüksek accuracy'ye sahip olmalıdır."
                )
            }
        except json.JSONDecodeError:
            pass

    # Cache yoksa direkt hesapla
    from database import get_db

    with get_db() as conn:
        # Confidence aralıklarına göre (low: <40, medium: 40-70, high: >70)
        confidence_stats = {}
        for level, (min_conf, max_conf) in [
            ("low", (0, 40)),
            ("medium", (40, 70)),
            ("high", (70, 101))
        ]:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_successful = 1 THEN 1 ELSE 0 END) as successful,
                    AVG(profit_loss_pct) as avg_pnl
                FROM signal_tracking
                WHERE result IS NOT NULL
                AND confidence >= ? AND confidence < ?
            """, (min_conf, max_conf)).fetchone()

            total = row["total"] or 0
            successful = row["successful"] or 0
            avg_pnl = row["avg_pnl"] or 0

            confidence_stats[level] = {
                "total": total,
                "successful": successful,
                "accuracy": round((successful / total * 100), 1) if total >= 10 else None,
                "avg_profit_loss": round(avg_pnl, 2),
                "confidence_range": f"{min_conf}-{max_conf}%"
            }

        # Genel istatistik
        general = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_successful = 1 THEN 1 ELSE 0 END) as successful,
                AVG(profit_loss_pct) as avg_pnl
            FROM signal_tracking
            WHERE result IS NOT NULL
        """).fetchone()

    total = general["total"] or 0
    successful = general["successful"] or 0

    return {
        "status": "ok",
        "data": {
            "general": {
                "total_signals": total,
                "successful": successful,
                "accuracy": round((successful / total * 100), 1) if total >= 10 else None,
                "avg_profit_loss": round(general["avg_pnl"] or 0, 2)
            },
            "by_confidence": confidence_stats,
            "updated_at": datetime.utcnow().isoformat()
        },
        "calibration_note": (
            "Bu veriler sinyal güven skorlarının gerçek sonuçlarla "
            "ne kadar örtüştüğünü gösterir."
        )
    }


# =============================================================================
# v2.1 YENİ ENDPOINT: EXIT ANALYSIS
# =============================================================================

@router.get("/exit-analysis")
async def get_exit_analysis(
    days: int = 30,
    user=Depends(get_current_user)
):
    """
    Exit reason bazlı performans analizi (v2.1)

    Hangi exit reason ile çıkıldı:
    - STOP_LOSS: Zarar kes ile kapanan
    - TAKE_PROFIT: Kâr al ile kapanan
    - TRAILING_STOP: Trailing stop ile kapanan
    - TIME_EXPIRED: Süre dolduğu için kapanan
    """
    cache_key = f"exit_analysis_{days}d"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

    with get_db() as conn:
        # Exit reason bazlı istatistikler
        rows = conn.execute("""
            SELECT
                exit_reason,
                COUNT(*) as total,
                SUM(CASE WHEN is_successful = 1 THEN 1 ELSE 0 END) as successful,
                AVG(profit_loss_pct) as avg_pnl,
                AVG(CASE WHEN is_successful = 1 THEN profit_loss_pct ELSE NULL END) as avg_win,
                AVG(CASE WHEN is_successful = 0 THEN profit_loss_pct ELSE NULL END) as avg_loss
            FROM signal_tracking
            WHERE exit_reason IS NOT NULL
            AND closed_at >= ?
            GROUP BY exit_reason
        """, (cutoff_date,)).fetchall()

        exit_stats = {}

        for row in rows:
            reason = row["exit_reason"]
            total = row["total"] or 0
            successful = row["successful"] or 0
            avg_pnl = row["avg_pnl"] or 0
            avg_win = row["avg_win"] or 0
            avg_loss = row["avg_loss"] or 0

            exit_stats[reason] = {
                "total": total,
                "successful": successful,
                "success_rate": round((successful / total * 100), 1) if total > 0 else 0,
                "avg_profit_loss": round(avg_pnl, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2)
            }

        # Genel özet
        overall = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_successful = 1 THEN 1 ELSE 0 END) as successful,
                AVG(profit_loss_pct) as avg_pnl
            FROM signal_tracking
            WHERE exit_reason IS NOT NULL
            AND closed_at >= ?
        """, (cutoff_date,)).fetchone()

    result = {
        "period_days": days,
        "total_closed": overall["total"] or 0,
        "total_successful": overall["successful"] or 0,
        "overall_success_rate": round(
            ((overall["successful"] or 0) / (overall["total"] or 1)) * 100, 1
        ),
        "overall_avg_pnl": round(overall["avg_pnl"] or 0, 2),
        "by_exit_reason": exit_stats,
        "updated_at": datetime.utcnow().isoformat()
    }

    # Cache'e kaydet (5 dakika)
    redis_client.setex(cache_key, 300, json.dumps(result))

    return result


@router.get("/exit-timeline")
async def get_exit_timeline(
    days: int = 30,
    user=Depends(get_current_user)
):
    """
    Günlük exit istatistikleri timeline (v2.1)

    Son N günün her günü için kapanış istatistikleri
    """
    cache_key = f"exit_timeline_{days}d"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                DATE(closed_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN is_successful = 1 THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN exit_reason = 'STOP_LOSS' THEN 1 ELSE 0 END) as stop_loss,
                SUM(CASE WHEN exit_reason = 'TAKE_PROFIT' THEN 1 ELSE 0 END) as take_profit,
                SUM(CASE WHEN exit_reason = 'TRAILING_STOP' THEN 1 ELSE 0 END) as trailing_stop,
                AVG(profit_loss_pct) as avg_pnl
            FROM signal_tracking
            WHERE exit_reason IS NOT NULL
            AND closed_at >= ?
            GROUP BY DATE(closed_at)
            ORDER BY date DESC
        """, (cutoff_date,)).fetchall()

        timeline = []
        for row in rows:
            total = row["total"] or 0
            successful = row["successful"] or 0
            timeline.append({
                "date": row["date"],
                "total": total,
                "successful": successful,
                "success_rate": round((successful / total * 100), 1) if total > 0 else 0,
                "exits": {
                    "STOP_LOSS": row["stop_loss"] or 0,
                    "TAKE_PROFIT": row["take_profit"] or 0,
                    "TRAILING_STOP": row["trailing_stop"] or 0
                },
                "avg_pnl": round(row["avg_pnl"] or 0, 2)
            })

    result = {
        "period_days": days,
        "timeline": timeline,
        "updated_at": datetime.utcnow().isoformat()
    }

    # Cache'e kaydet (5 dakika)
    redis_client.setex(cache_key, 300, json.dumps(result))

    return result