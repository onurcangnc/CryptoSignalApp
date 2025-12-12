# -*- coding: utf-8 -*-
"""
CryptoSignal - Signal Stats Router
===================================
Sinyal başarı istatistikleri API
"""

from fastapi import APIRouter, Depends
from typing import Optional
import json
from datetime import datetime, timedelta

from dependencies import get_current_user
from database import get_signal_success_rate, redis_client

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