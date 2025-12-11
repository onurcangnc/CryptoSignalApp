# -*- coding: utf-8 -*-
"""
CryptoSignal - Portfolio Router
===============================
/api/portfolio endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
import json
from datetime import datetime

from models import PortfolioUpdate
from database import redis_client, get_portfolio, save_portfolio, get_db
from dependencies import get_current_user, require_llm_quota, check_llm_quota
from config import LLM_LIMITS

router = APIRouter(prefix="/api", tags=["Portfolio"])


# Global state (worker'lardan güncellenir)
prices_data = {}
fx_rates = {"USD": 1, "TRY": 34.5, "EUR": 0.92, "GBP": 0.79}


def load_prices():
    """Redis'den fiyatları yükle"""
    global prices_data, fx_rates
    try:
        prices_raw = redis_client.get("prices_data")
        if prices_raw:
            prices_data = json.loads(prices_raw)
        
        fx_raw = redis_client.get("fx_rates")
        if fx_raw:
            fx_rates = json.loads(fx_raw)
    except:
        pass


@router.get("/portfolio")
async def get_user_portfolio(user: dict = Depends(get_current_user)):
    """Kullanıcı portföyünü getir"""
    load_prices()
    
    portfolio = get_portfolio(user["id"])
    max_coins = 100 if user["tier"] == "admin" else 10
    
    holdings = []
    total_value = 0
    total_invested = 0
    
    for h in portfolio.get("holdings", []):
        coin = h["coin"]
        price_data = prices_data.get(coin, {"price": 0, "change_24h": 0})
        
        quantity = h.get("quantity", 0) or 0
        invested_usd = h.get("invested_usd", 0) or 0
        current_price = price_data.get("price", 0)
        current_value = quantity * current_price
        
        profit_loss = current_value - invested_usd if invested_usd > 0 else 0
        profit_loss_pct = (profit_loss / invested_usd * 100) if invested_usd > 0 else 0
        
        total_value += current_value
        total_invested += invested_usd
        
        holdings.append({
            "coin": coin,
            "weight": h.get("weight", 0),
            "quantity": round(quantity, 8),
            "invested_amount": h.get("invested_amount"),
            "invested_currency": h.get("invested_currency", "USD"),
            "invested_usd": round(invested_usd, 2),
            "input_mode": h.get("input_mode", "fiat"),
            "current_price_usd": current_price,
            "current_value_usd": round(current_value, 2),
            "profit_loss_usd": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2),
            "change_24h": price_data.get("change_24h", 0)
        })
    
    total_pnl = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    return {
        "holdings": holdings,
        "total_value_usd": round(total_value, 2),
        "total_invested_usd": round(total_invested, 2),
        "total_profit_loss_usd": round(total_pnl, 2),
        "total_profit_loss_pct": round(total_pnl_pct, 2),
        "budget": portfolio.get("budget"),
        "budget_currency": portfolio.get("budget_currency", "USD"),
        "max_coins": max_coins,
        "tier": user["tier"],
        "fx": fx_rates
    }


@router.put("/portfolio")
async def update_portfolio(data: PortfolioUpdate, user: dict = Depends(get_current_user)):
    """Portföyü güncelle"""
    max_coins = 100 if user["tier"] == "admin" else 10
    
    if len(data.holdings) > max_coins:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_coins} coins allowed for {user['tier']} tier"
        )
    
    holdings = []
    for h in data.holdings:
        holdings.append({
            "coin": h.coin.upper(),
            "weight": h.weight or 0,
            "quantity": h.quantity or 0,
            "invested_amount": h.invested_amount,
            "invested_currency": h.invested_currency or "USD",
            "invested_usd": h.invested_usd or 0,
            "input_mode": h.input_mode or "fiat"
        })
    
    save_portfolio(
        user["id"],
        holdings,
        data.budget,
        data.budget_currency or "USD"
    )
    
    return {"success": True, "message": "Portfolio updated"}


@router.delete("/portfolio/{coin}")
async def remove_coin(coin: str, user: dict = Depends(get_current_user)):
    """Portföyden coin sil"""
    portfolio = get_portfolio(user["id"])
    holdings = [h for h in portfolio.get("holdings", []) if h["coin"] != coin.upper()]
    
    save_portfolio(
        user["id"],
        holdings,
        portfolio.get("budget"),
        portfolio.get("budget_currency", "USD")
    )
    
    return {"success": True, "message": f"{coin} removed from portfolio"}


# =============================================================================
# PORTFOLIO AI ANALYSIS
# =============================================================================

@router.get("/portfolio/ai-analysis")
async def get_portfolio_ai_analysis(user: dict = Depends(get_current_user)):
    """Mevcut AI analizini getir (cache'den)"""
    try:
        # Redis'den cache'lenmiş analizi al
        cache_key = f"portfolio_analysis_{user['id']}"
        cached = redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        return {"error": "No analysis available. Click 'Analyze' to generate."}
    except Exception as e:
        return {"error": str(e)}


@router.post("/portfolio/analyze")
async def analyze_portfolio(user: dict = Depends(require_llm_quota)):
    """
    AI ile portföy analizi yap
    LLM kotası kullanır
    """
    from database import increment_llm_usage, today_str
    
    load_prices()
    
    portfolio = get_portfolio(user["id"])
    holdings = portfolio.get("holdings", [])
    
    if not holdings:
        raise HTTPException(status_code=400, detail="Portfolio is empty")
    
    # Portföy verilerini hazırla
    portfolio_data = []
    total_value = 0
    total_invested = 0
    
    for h in holdings:
        coin = h["coin"]
        price_data = prices_data.get(coin, {"price": 0, "change_24h": 0})
        
        quantity = h.get("quantity", 0) or 0
        invested_usd = h.get("invested_usd", 0) or 0
        current_price = price_data.get("price", 0)
        current_value = quantity * current_price
        
        profit_loss = current_value - invested_usd if invested_usd > 0 else 0
        profit_loss_pct = (profit_loss / invested_usd * 100) if invested_usd > 0 else 0
        
        total_value += current_value
        total_invested += invested_usd
        
        portfolio_data.append({
            "coin": coin,
            "current_value_usd": current_value,
            "invested_usd": invested_usd,
            "profit_loss_usd": profit_loss,
            "profit_loss_pct": profit_loss_pct,
            "change_24h": price_data.get("change_24h", 0)
        })
    
    # Fear & Greed
    try:
        fg_raw = redis_client.get("fear_greed")
        fear_greed = json.loads(fg_raw).get("value", 50) if fg_raw else 50
    except:
        fear_greed = 50
    
    # LLM ile analiz
    try:
        from services.llm_service import llm_service
        
        if not llm_service.is_available():
            # Fallback: Basit analiz
            analysis = generate_simple_analysis(portfolio_data, total_value, total_invested, fear_greed)
        else:
            analysis = await llm_service.analyze_portfolio(
                portfolio_data,
                {"fear_greed": fear_greed}
            )
            
            if not analysis:
                analysis = generate_simple_analysis(portfolio_data, total_value, total_invested, fear_greed)
        
        # LLM kullanımını kaydet
        increment_llm_usage(user['id'], today_str())
        
        # Cache'e kaydet (1 saat)
        cache_key = f"portfolio_analysis_{user['id']}"
        redis_client.setex(cache_key, 3600, json.dumps(analysis))
        
        return analysis
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_simple_analysis(holdings: list, total_value: float, total_invested: float, fear_greed: int) -> dict:
    """LLM olmadan basit analiz"""
    total_pnl = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    # Risk skoru hesapla
    risk_score = 5
    
    if total_pnl_pct < -20:
        risk_score += 2
    elif total_pnl_pct < -10:
        risk_score += 1
    elif total_pnl_pct > 50:
        risk_score -= 1
    
    if fear_greed < 30:
        risk_score += 1
    elif fear_greed > 70:
        risk_score += 1
    
    # Coin analizleri
    coin_analyses = []
    for h in holdings:
        pnl_pct = h.get("profit_loss_pct", 0)
        
        if pnl_pct > 20:
            action = "TUT"
            reason = "İyi performans gösteriyor"
        elif pnl_pct < -30:
            action = "SAT"
            reason = "Ciddi kayıp, çıkış değerlendirilmeli"
        elif pnl_pct < -10:
            action = "TUT"
            reason = "Kayıpları izleyin"
        else:
            action = "TUT"
            reason = "Stabil seyrediyor"
        
        coin_analyses.append({
            "symbol": h["coin"],
            "action": action,
            "reason": reason
        })
    
    # Risk seviyesi
    if risk_score >= 7:
        risk_level = "riskli"
    elif risk_score >= 5:
        risk_level = "orta"
    else:
        risk_level = "güvenli"
    
    # Özet
    if total_pnl_pct > 20:
        assessment = "Portföyünüz iyi performans gösteriyor. Kar realizasyonu düşünülebilir."
    elif total_pnl_pct < -20:
        assessment = "Portföyünüz ciddi kayıp yaşıyor. Stop-loss seviyeleri değerlendirilmeli."
    else:
        assessment = "Portföyünüz stabil seyrediyor. Piyasa koşullarını takip edin."
    
    recommendations = []
    if total_pnl_pct < -10:
        recommendations.append("Zarar eden pozisyonları değerlendirin")
    if fear_greed < 30:
        recommendations.append("Piyasada korku hakim, alım fırsatları olabilir")
    elif fear_greed > 70:
        recommendations.append("Piyasada açgözlülük var, dikkatli olun")
    if len(holdings) < 3:
        recommendations.append("Portföyünüzü çeşitlendirmeyi düşünün")
    
    return {
        "risk_score": min(10, max(1, risk_score)),
        "risk_level": risk_level,
        "assessment": assessment,
        "coins": coin_analyses,
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat()
    }
