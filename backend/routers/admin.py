# -*- coding: utf-8 -*-
"""
CryptoSignal - Admin Router (Enhanced with LLM Analytics)
==========================================================
/api/admin/* endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
import json
import secrets
from datetime import datetime, timedelta

from database import (
    redis_client, get_db, get_all_users, get_all_invites,
    create_invite, get_llm_usage, get_llm_analytics,
    get_llm_stats_by_feature, get_llm_stats_by_user,
    save_portfolio_simulation, get_portfolio, today_str
)
from dependencies import get_admin_user, get_current_user
from models import CreateInviteRequest

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# =============================================================================
# ADMIN STATS (Enhanced)
# =============================================================================

@router.get("/stats")
async def get_admin_stats(user: dict = Depends(get_admin_user)):
    """Enhanced admin dashboard istatistikleri"""

    # Kullanıcı sayısı ve tier dağılımı
    users = get_all_users()
    user_count = len(users)

    tier_counts = {}
    for u in users:
        tier = u.get("tier", "free")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    # LLM Usage - Bugün
    today = today_str()
    llm_calls_today = 0
    for u in users:
        llm_calls_today += get_llm_usage(u["id"], today)

    # LLM Usage - Bu Ay (yaklaşık)
    try:
        analytics = get_llm_analytics()
        this_month = datetime.utcnow().replace(day=1).isoformat()
        monthly_analytics = [a for a in analytics if a.get("created_at", "") >= this_month]
        llm_cost_month = sum(a.get("cost_usd", 0) for a in monthly_analytics)
    except:
        llm_cost_month = 0

    # MRR Calculation
    pro_users = tier_counts.get("pro", 0)
    premium_users = tier_counts.get("premium", 0)
    mrr = (pro_users * 9.99) + (premium_users * 29.99)

    # Profit Margin
    profit_margin = ((mrr - llm_cost_month) / mrr * 100) if mrr > 0 else 0

    # Redis'den worker durumları
    # fear_greed is a JSON object, get updated timestamp from sentiment_updated
    workers = {
        "prices": redis_client.get("prices_updated"),
        "futures": redis_client.get("futures_updated"),
        "news": redis_client.get("news_updated"),
        "signals": redis_client.get("signals_updated"),
        "fear_greed": redis_client.get("sentiment_updated")
    }

    # Coin ve sinyal sayıları
    coins_count = redis_client.get("prices_count") or "0"
    signals_count = redis_client.get("signals_count") or "0"
    news_count = redis_client.get("news_count") or "0"

    return {
        "users": user_count,
        "tier_distribution": tier_counts,
        "coins": int(coins_count),
        "signals": int(signals_count),
        "news": int(news_count),
        "workers": workers,

        # Enhanced metrics
        "llm_calls_today": llm_calls_today,
        "llm_cost_month": round(llm_cost_month, 2),
        "mrr": round(mrr, 2),
        "profit_margin": round(profit_margin, 2)
    }


# =============================================================================
# LLM ANALYTICS
# =============================================================================

@router.get("/llm-analytics")
async def get_llm_analytics_stats(user: dict = Depends(get_admin_user)):
    """LLM kullanım ve maliyet analizi"""

    try:
        # Tüm analytics verilerini al
        all_analytics = get_llm_analytics()

        # Tarih bazlı filtreleme
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0).isoformat()
        week_start = (now - timedelta(days=7)).isoformat()
        month_start = now.replace(day=1, hour=0, minute=0, second=0).isoformat()

        today_data = [a for a in all_analytics if a.get("created_at", "") >= today_start]
        week_data = [a for a in all_analytics if a.get("created_at", "") >= week_start]
        month_data = [a for a in all_analytics if a.get("created_at", "") >= month_start]

        # Calculate stats
        def calc_stats(data):
            return {
                "calls": len(data),
                "cost": sum(a.get("cost_usd", 0) for a in data),
                "tokens": sum(a.get("tokens_used", 0) for a in data)
            }

        # Feature breakdown (bu ay)
        feature_stats = {}
        for a in month_data:
            feature = a.get("feature", "other")
            if feature not in feature_stats:
                feature_stats[feature] = {"calls": 0, "cost": 0}
            feature_stats[feature]["calls"] += 1
            feature_stats[feature]["cost"] += a.get("cost_usd", 0)

        # Tier breakdown
        users = get_all_users()
        user_tier_map = {u["id"]: u.get("tier", "free") for u in users}

        tier_stats = {"free": {"users": 0, "calls": 0, "cost": 0},
                     "pro": {"users": 0, "calls": 0, "cost": 0},
                     "premium": {"users": 0, "calls": 0, "cost": 0}}

        for a in month_data:
            uid = a.get("user_id")
            tier = user_tier_map.get(uid, "free")
            tier_stats[tier]["calls"] += 1
            tier_stats[tier]["cost"] += a.get("cost_usd", 0)

        # Count users per tier
        for tier in tier_stats:
            tier_stats[tier]["users"] = sum(1 for u in users if u.get("tier") == tier)

        # Top users
        top_users_data = get_llm_stats_by_user(limit=10)

        # Average cost per call
        total_calls = sum(calc_stats(month_data)["calls"] for _ in [month_data])
        total_cost = sum(calc_stats(month_data)["cost"] for _ in [month_data])
        avg_cost = (total_cost / len(month_data)) if month_data else 0.0025
        avg_tokens = (sum(a.get("tokens_used", 0) for a in month_data) / len(month_data)) if month_data else 9500

        return {
            "today": calc_stats(today_data),
            "week": calc_stats(week_data),
            "month": calc_stats(month_data),
            "average_cost_per_call": round(avg_cost, 6),
            "avg_tokens": int(avg_tokens),
            "by_feature": feature_stats,
            "by_tier": tier_stats,
            "top_users": top_users_data
        }
    except Exception as e:
        # Fallback data if analytics table doesn't exist yet
        return {
            "today": {"calls": 0, "cost": 0, "tokens": 0},
            "week": {"calls": 0, "cost": 0, "tokens": 0},
            "month": {"calls": 0, "cost": 0, "tokens": 0},
            "average_cost_per_call": 0.0025,
            "avg_tokens": 9500,
            "by_feature": {},
            "by_tier": {
                "free": {"users": 0, "calls": 0, "cost": 0},
                "pro": {"users": 0, "calls": 0, "cost": 0},
                "premium": {"users": 0, "calls": 0, "cost": 0}
            },
            "top_users": []
        }


# =============================================================================
# PORTFOLIO SIMULATOR
# =============================================================================

@router.post("/simulator/run")
async def run_portfolio_simulation(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Portfolio simülasyonu çalıştır"""

    scenario_type = request.get("scenario_type", "market_drop")
    parameters = request.get("parameters", {})

    # Portfolio verilerini al
    portfolio = get_portfolio(user["id"])
    holdings = portfolio.get("holdings", [])

    if not holdings:
        raise HTTPException(status_code=400, detail="Portfolio is empty")

    # Fiyat verilerini al
    try:
        prices_raw = redis_client.get("prices_data")
        prices = json.loads(prices_raw) if prices_raw else {}
    except:
        prices = {}

    # Simülasyon çalıştır
    if scenario_type == "market_drop":
        drop_pct = parameters.get("drop_percentage", 20)
        results = simulate_market_drop(holdings, prices, drop_pct)

    elif scenario_type == "sell_position":
        coin = parameters.get("coin", "")
        sell_pct = parameters.get("sell_percentage", 100)
        results = simulate_sell_position(holdings, prices, coin, sell_pct)

    elif scenario_type == "add_funds":
        amount = parameters.get("amount", 1000)
        coin = parameters.get("coin", "BTC")
        results = simulate_add_funds(holdings, prices, coin, amount)

    elif scenario_type == "rebalance":
        target_allocation = parameters.get("target_allocation", {})
        results = simulate_rebalance(holdings, prices, target_allocation)

    elif scenario_type == "monte_carlo":
        iterations = parameters.get("iterations", 1000)
        days = parameters.get("days", 30)
        results = simulate_monte_carlo(holdings, prices, iterations, days)

    else:
        raise HTTPException(status_code=400, detail="Unknown scenario type")

    # Kaydet
    sim_id = save_portfolio_simulation(user["id"], scenario_type, parameters, results)

    return {"success": True, "simulation_id": sim_id, **results}


# =============================================================================
# SIMULATION HELPERS
# =============================================================================

def simulate_market_drop(holdings, prices, drop_pct):
    """Piyasa düşüşü simülasyonu"""
    import random

    current_value = 0
    new_value = 0

    for h in holdings:
        coin = h.get("coin", "")
        quantity = h.get("quantity", 0) or 0
        price = prices.get(coin, {}).get("price", 0)

        current_value += quantity * price

        # Her coin için rastgele düşüş (±20% varyans)
        coin_drop = drop_pct + random.uniform(-5, 5)
        new_price = price * (1 - coin_drop / 100)
        new_value += quantity * new_price

    loss = current_value - new_value
    loss_pct = (loss / current_value * 100) if current_value > 0 else 0

    return {
        "scenario": f"Market drops {drop_pct}%",
        "current_value": round(current_value, 2),
        "new_value": round(new_value, 2),
        "loss": round(loss, 2),
        "loss_pct": round(loss_pct, 2)
    }


def simulate_sell_position(holdings, prices, coin, sell_pct):
    """Pozisyon satışı simülasyonu"""
    current_value = sum((h.get("quantity", 0) or 0) * prices.get(h.get("coin", ""), {}).get("price", 0) for h in holdings)

    target_holding = next((h for h in holdings if h.get("coin") == coin), None)
    if not target_holding:
        raise HTTPException(status_code=404, detail=f"Coin {coin} not found in portfolio")

    quantity = target_holding.get("quantity", 0) or 0
    price = prices.get(coin, {}).get("price", 0)
    position_value = quantity * price

    sell_amount = position_value * (sell_pct / 100)
    new_value = current_value - sell_amount

    return {
        "scenario": f"Sell {sell_pct}% of {coin}",
        "current_value": round(current_value, 2),
        "sell_amount": round(sell_amount, 2),
        "new_value": round(new_value, 2),
        "cash_generated": round(sell_amount, 2)
    }


def simulate_add_funds(holdings, prices, coin, amount):
    """Fon ekleme simülasyonu"""
    current_value = sum((h.get("quantity", 0) or 0) * prices.get(h.get("coin", ""), {}).get("price", 0) for h in holdings)

    price = prices.get(coin, {}).get("price", 0)
    if price == 0:
        raise HTTPException(status_code=400, detail=f"Price for {coin} not available")

    new_quantity = amount / price
    new_value = current_value + amount

    return {
        "scenario": f"Add ${amount} in {coin}",
        "current_value": round(current_value, 2),
        "added_amount": round(amount, 2),
        "new_value": round(new_value, 2),
        "coin_quantity": round(new_quantity, 8)
    }


def simulate_rebalance(holdings, prices, target_allocation):
    """Rebalancing simülasyonu"""
    current_value = sum((h.get("quantity", 0) or 0) * prices.get(h.get("coin", ""), {}).get("price", 0) for h in holdings)

    trades = []
    for coin, target_pct in target_allocation.items():
        price = prices.get(coin, {}).get("price", 0)
        if price == 0:
            continue

        current_holding = next((h for h in holdings if h.get("coin") == coin), None)
        current_quantity = current_holding.get("quantity", 0) if current_holding else 0
        current_position_value = current_quantity * price

        target_value = current_value * (target_pct / 100)
        diff = target_value - current_position_value

        if abs(diff) > 10:  # Only trade if difference > $10
            action = "BUY" if diff > 0 else "SELL"
            trades.append({
                "coin": coin,
                "action": action,
                "amount": abs(diff),
                "current_pct": round((current_position_value / current_value * 100), 2) if current_value > 0 else 0,
                "target_pct": target_pct
            })

    return {
        "scenario": "Rebalance portfolio",
        "current_value": round(current_value, 2),
        "trades": trades,
        "total_trades": len(trades)
    }


def simulate_monte_carlo(holdings, prices, iterations, days):
    """Monte Carlo simülasyonu"""
    import random

    current_value = sum((h.get("quantity", 0) or 0) * prices.get(h.get("coin", ""), {}).get("price", 0) for h in holdings)

    results = []

    for _ in range(iterations):
        value = current_value

        # Her gün için rastgele değişim
        for day in range(days):
            daily_change = random.gauss(0, 3)  # μ=0%, σ=3%
            value *= (1 + daily_change / 100)

        results.append(value)

    results.sort()

    return {
        "scenario": f"Monte Carlo ({iterations} simulations, {days} days)",
        "current_value": round(current_value, 2),
        "best_case": round(results[-1], 2),
        "worst_case": round(results[0], 2),
        "average": round(sum(results) / len(results), 2),
        "median": round(results[len(results) // 2], 2),
        "percentile_10": round(results[int(len(results) * 0.1)], 2),
        "percentile_90": round(results[int(len(results) * 0.9)], 2)
    }


# =============================================================================
# USER MANAGEMENT
# =============================================================================

@router.get("/users")
async def get_users(user: dict = Depends(get_admin_user)):
    """Tüm kullanıcıları listele"""
    users = get_all_users()
    return {"users": users, "count": len(users)}


@router.get("/invites")
async def get_invites(user: dict = Depends(get_admin_user)):
    """Tüm davet kodlarını listele"""
    invites = get_all_invites()
    return {"invites": invites, "count": len(invites)}


@router.post("/invites")
async def create_new_invite(
    data: CreateInviteRequest,
    user: dict = Depends(get_admin_user)
):
    """Yeni davet kodu oluştur"""
    token = f"{data.tier.upper()}-{secrets.token_hex(4).upper()}"
    create_invite(token, data.tier, data.note or "")

    return {
        "success": True,
        "invite": {
            "token": token,
            "tier": data.tier,
            "note": data.note
        }
    }


@router.post("/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    tier: str,
    admin: dict = Depends(get_admin_user)
):
    """Kullanıcı tier'ını güncelle"""
    if tier not in ["free", "pro", "premium", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid tier")

    with get_db() as conn:
        result = conn.execute(
            "UPDATE users SET tier = ? WHERE id = ?",
            (tier, user_id)
        )
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "message": f"User tier updated to {tier}"}


# =============================================================================
# SYSTEM HEALTH
# =============================================================================

@router.get("/system/health")
async def get_system_health(user: dict = Depends(get_admin_user)):
    """Enhanced sistem sağlık kontrolü"""

    health = {
        "database": "ok",
        "redis": "ok",
        "workers": {},
        "overall": "healthy"
    }

    # Redis kontrolü
    try:
        redis_client.ping()
        redis_info = redis_client.info()
        health["redis_info"] = {
            "memory_used": redis_info.get("used_memory_human", "N/A"),
            "connected_clients": redis_info.get("connected_clients", 0)
        }
    except:
        health["redis"] = "error"
        health["overall"] = "critical"

    # Worker kontrolları
    now = datetime.utcnow()

    worker_keys = {
        "prices": "prices_updated",
        "futures": "futures_updated",
        "news": "news_updated",
        "signals": "signals_updated",
        "sentiment": "sentiment_updated"
    }

    for name, key in worker_keys.items():
        updated = redis_client.get(key)
        if updated:
            try:
                update_time = datetime.fromisoformat(updated.replace('Z', ''))
                age = (now - update_time).total_seconds()

                if age < 120:  # 2 dakika
                    status = "healthy"
                elif age < 600:  # 10 dakika
                    status = "warning"
                    if health["overall"] == "healthy":
                        health["overall"] = "warning"
                else:
                    status = "stale"
                    if health["overall"] in ["healthy", "warning"]:
                        health["overall"] = "degraded"

                health["workers"][name] = {
                    "status": status,
                    "last_update": updated,
                    "age_seconds": int(age)
                }
            except:
                health["workers"][name] = {"status": "unknown"}
        else:
            health["workers"][name] = {"status": "not_running"}
            if health["overall"] in ["healthy", "warning"]:
                health["overall"] = "degraded"

    return health
