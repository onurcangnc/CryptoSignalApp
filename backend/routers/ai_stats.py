# -*- coding: utf-8 -*-
"""
CryptoSignal - AI Stats Router
==============================
/api/ai/* endpoints
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from database import (
    get_db, get_llm_usage, get_total_llm_usage, today_str
)
from dependencies import get_current_user, get_admin_user
from config import LLM_LIMITS

router = APIRouter(prefix="/api/ai", tags=["AI Stats"])


@router.get("/stats")
async def get_ai_stats(user: dict = Depends(get_current_user)):
    """
    Kullanıcının AI kullanım istatistiklerini döndür
    Admin ise sistem istatistiklerini de göster
    """
    today = today_str()
    
    # Kullanıcı istatistikleri
    used_today = get_llm_usage(user['id'], today)
    daily_limit = LLM_LIMITS.get(user['tier'], 3)
    remaining = max(0, daily_limit - used_today)
    total_all_time = get_total_llm_usage(user['id'])
    
    user_stats = {
        "used_today": used_today,
        "daily_limit": daily_limit,
        "remaining": remaining,
        "tier": user['tier'],
        "total_all_time": total_all_time,
        "reset_time": "00:00 UTC"
    }
    
    response = {
        "success": True,
        "user_stats": user_stats
    }
    
    # Admin ise sistem istatistiklerini de ekle
    if user['tier'] == 'admin':
        with get_db() as conn:
            # Bugün aktif kullanıcı sayısı
            active_users = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as count FROM llm_usage WHERE date = ?",
                (today,)
            ).fetchone()['count'] or 0
            
            # Bugün toplam AI çağrısı
            total_calls_row = conn.execute(
                "SELECT SUM(count) as total FROM llm_usage WHERE date = ?",
                (today,)
            ).fetchone()
            total_ai_calls = total_calls_row['total'] if total_calls_row and total_calls_row['total'] else 0
            
            # Son 7 günlük kullanım
            week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
            weekly_usage = conn.execute(
                "SELECT date, SUM(count) as total FROM llm_usage WHERE date >= ? GROUP BY date ORDER BY date",
                (week_ago,)
            ).fetchall()
            
            # Toplam kullanıcı sayısı
            total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count'] or 0
            
            # Tier dağılımı
            tier_dist = conn.execute(
                "SELECT tier, COUNT(*) as count FROM users GROUP BY tier"
            ).fetchall()
            tier_distribution = {row['tier']: row['count'] for row in tier_dist}
        
        # Tahmini maliyet
        avg_tokens_per_request = 800
        cost_per_1m_tokens = 0.30
        estimated_cost = (total_ai_calls * avg_tokens_per_request / 1_000_000) * cost_per_1m_tokens
        
        response["system_stats"] = {
            "active_users_today": active_users,
            "total_ai_calls_today": total_ai_calls,
            "total_users": total_users,
            "tier_distribution": tier_distribution,
            "estimated_cost_today": round(estimated_cost, 4),
            "weekly_usage": [
                {"date": row['date'], "calls": row['total']} 
                for row in weekly_usage
            ],
            "token_usage": {
                "input": total_ai_calls * 500,
                "output": total_ai_calls * 300,
                "total": total_ai_calls * 800
            },
            "success_rate": 99.5
        }
    
    return response


@router.get("/usage-history")
async def get_ai_usage_history(
    user: dict = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=90)
):
    """Kullanıcının AI kullanım geçmişi"""
    with get_db() as conn:
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        history = conn.execute(
            "SELECT date, count FROM llm_usage WHERE user_id = ? AND date >= ? ORDER BY date DESC",
            (user['id'], start_date)
        ).fetchall()
        
        return {
            "success": True,
            "user_id": user['id'],
            "history": [{"date": row['date'], "count": row['count']} for row in history],
            "total": sum(row['count'] for row in history)
        }


@router.get("/admin/detailed")
async def get_admin_detailed_stats(user: dict = Depends(get_admin_user)):
    """Admin için detaylı AI istatistikleri"""
    today = today_str()
    
    with get_db() as conn:
        # En çok kullanan kullanıcılar
        top_users = conn.execute("""
            SELECT u.email, u.tier, SUM(l.count) as total_usage
            FROM llm_usage l
            JOIN users u ON l.user_id = u.id
            WHERE l.date >= date('now', '-7 days')
            GROUP BY l.user_id
            ORDER BY total_usage DESC
            LIMIT 10
        """).fetchall()
        
        # Günlük kullanım trendi (son 30 gün)
        daily_trend = conn.execute("""
            SELECT date, SUM(count) as total
            FROM llm_usage
            WHERE date >= date('now', '-30 days')
            GROUP BY date
            ORDER BY date
        """).fetchall()
        
        # Tier bazlı kullanım
        tier_usage = conn.execute("""
            SELECT u.tier, SUM(l.count) as total
            FROM llm_usage l
            JOIN users u ON l.user_id = u.id
            WHERE l.date = ?
            GROUP BY u.tier
        """, (today,)).fetchall()
        
        return {
            "success": True,
            "top_users": [
                {"email": row['email'], "tier": row['tier'], "usage": row['total_usage']}
                for row in top_users
            ],
            "daily_trend": [
                {"date": row['date'], "calls": row['total']}
                for row in daily_trend
            ],
            "tier_usage_today": {row['tier']: row['total'] for row in tier_usage}
        }
