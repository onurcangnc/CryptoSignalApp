# -*- coding: utf-8 -*-
"""
CryptoSignal - AI Summary Router (Enhanced)
==========================================
Portfolio Intelligence + Predictions + Risk Analysis
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict
import json
from datetime import datetime, timedelta

from database import (
    redis_client, get_portfolio, get_db,
    increment_llm_usage, today_str
)
from dependencies import get_current_user, check_llm_quota
from services.llm_service import llm_service

router = APIRouter(prefix="/api/ai-summary", tags=["AI Summary"])


# =============================================================================
# PORTFOLIO AI SUMMARY (Cached)
# =============================================================================

@router.get("/portfolio")
async def get_portfolio_summary(user: dict = Depends(get_current_user)):
    """
    Kullanıcının portföyü için AI özeti getir (cache'den)
    - LLM kullanmaz
    - Herkes erişebilir
    """
    # Cache'den al
    cache_key = f"ai_summary:portfolio:{user['id']}"
    cached = redis_client.get(cache_key)
    
    if cached:
        try:
            return json.loads(cached)
        except:
            pass
    
    # Cache yoksa temel özet döndür
    return await generate_basic_summary(user)


@router.post("/analyze")
async def analyze_portfolio(user: dict = Depends(get_current_user)):
    """
    Yeni AI analizi oluştur
    - LLM kullanır (1 quota)
    - Rate limited
    """
    # Quota kontrolü
    can_use, used, limit, remaining = check_llm_quota(user)
    
    if not can_use:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI limit reached ({used}/{limit})",
            headers={"X-Reset-Time": "00:00 UTC"}
        )
    
    # LLM kullanımını kaydet
    increment_llm_usage(user['id'], today_str())
    
    # Analiz oluştur
    result = await generate_full_analysis(user)
    
    # Cache'e kaydet (1 saat)
    cache_key = f"ai_summary:portfolio:{user['id']}"
    redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return result


# =============================================================================
# ANALYSIS GENERATORS
# =============================================================================

async def generate_basic_summary(user: dict) -> dict:
    """Temel özet (LLM kullanmadan)"""
    # Portfolio verilerini al
    portfolio = get_portfolio(user['id'])
    holdings = portfolio.get('holdings', [])
    
    if not holdings:
        return {
            "success": False,
            "error": "Portfolio is empty",
            "message": "Please add assets to your portfolio first"
        }
    
    # Fiyat verilerini al
    try:
        prices_raw = redis_client.get("prices_data")
        prices = json.loads(prices_raw) if prices_raw else {}
    except:
        prices = {}
    
    # Temel hesaplamalar
    total_value = 0
    total_invested = 0
    total_pnl = 0
    
    holdings_data = []
    
    for h in holdings:
        coin = h.get('coin', '')
        quantity = h.get('quantity', 0) or 0
        invested_usd = h.get('invested_usd', 0) or 0
        
        price_data = prices.get(coin, {})
        current_price = price_data.get('price', 0)
        current_value = quantity * current_price
        
        pnl = current_value - invested_usd if invested_usd > 0 else 0
        pnl_pct = (pnl / invested_usd * 100) if invested_usd > 0 else 0
        
        total_value += current_value
        total_invested += invested_usd
        total_pnl += pnl
        
        holdings_data.append({
            'symbol': coin,
            'value': current_value,
            'invested': invested_usd,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'change_24h': price_data.get('change_24h', 0),
            'allocation': (current_value / total_value * 100) if total_value > 0 else 0
        })
    
    # Sort by value
    holdings_data.sort(key=lambda x: x['value'], reverse=True)
    
    # Health score calculation
    health_score = calculate_health_score(
        total_value, total_pnl, len(holdings), holdings_data
    )
    
    # Diversification score
    diversification_score = calculate_diversification(holdings_data)
    
    # Risk level
    risk_level = calculate_risk_level(holdings, holdings_data)
    
    # Market context
    try:
        fg_raw = redis_client.get("fear_greed")
        fear_greed = json.loads(fg_raw) if fg_raw else {}
    except:
        fear_greed = {}
    
    return {
        "success": True,
        "generated_at": datetime.utcnow().isoformat(),
        "type": "basic",
        
        # Overview
        "total_value": round(total_value, 2),
        "total_invested": round(total_invested, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round((total_pnl / total_invested * 100) if total_invested > 0 else 0, 2),
        "total_change_24h": calculate_weighted_change(holdings_data),
        
        # Scores
        "portfolio_health": {
            "score": health_score,
            "summary": generate_health_summary(health_score)
        },
        "diversification_score": diversification_score,
        "risk_score": risk_level['score'],
        "risk_level": risk_level['level'],
        "risk_level_tr": risk_level['level_tr'],
        
        # Holdings
        "top_holdings": holdings_data[:5],
        
        # Market context
        "market_context": {
            "fear_greed": fear_greed.get('value', 50),
            "fear_greed_label": fear_greed.get('value_classification', 'Neutral')
        },
        
        # Placeholders for AI features
        "predictions": [],
        "personalized_news": [],
        "action_items": [],
        "risk_factors": [],
        
        "message": "Generate fresh AI analysis for detailed insights"
    }


async def generate_full_analysis(user: dict) -> dict:
    """Tam AI analizi (LLM ile)"""
    # Önce temel özeti al
    basic = await generate_basic_summary(user)

    if not basic['success']:
        return basic

    if not llm_service.is_available():
        # LLM yoksa temel özeti döndür
        return basic

    # Portfolio data
    portfolio = get_portfolio(user['id'])
    holdings = portfolio.get('holdings', [])
    coins = [h.get('coin') for h in holdings if h.get('coin')]

    # Market data
    try:
        prices_raw = redis_client.get("prices_data")
        prices = json.loads(prices_raw) if prices_raw else {}

        signals_raw = redis_client.get("signals_data")
        signals = json.loads(signals_raw) if signals_raw else {}

        news_raw = redis_client.get("news_db")
        news_dict = json.loads(news_raw) if news_raw else {}
        all_news = list(news_dict.values())
    except:
        prices = {}
        signals = {}
        all_news = []

    # Filter news for user's coins
    relevant_news = [
        n for n in all_news
        if any(coin in (n.get('coins') or []) for coin in coins)
    ][:20]

    # Generate AI components (existing)
    predictions = await generate_predictions(coins, prices, signals)
    news_analysis = await analyze_news(relevant_news, coins)
    action_items = await generate_actions(basic, signals, coins)
    risk_analysis = await analyze_risks(basic, holdings, prices)

    # Generate NEW AI components (Critical 4 Features)
    trading_signals = await generate_trading_signals(coins, prices, signals)
    portfolio_forecast = await generate_portfolio_forecast(basic, holdings, prices)
    smart_alerts = await generate_smart_alerts(basic, holdings, prices, signals)
    technical_analysis = await generate_technical_analysis(coins, prices, signals)

    # Merge with basic summary
    result = {
        **basic,
        "type": "full",
        "ai_generated": True,

        # AI-enhanced components (existing)
        "predictions": predictions,
        "personalized_news": news_analysis.get('news_items', []),
        "news_summary": news_analysis.get('summary', ''),
        "action_items": action_items,
        "risk_factors": risk_analysis.get('factors', []),
        "asset_allocation": calculate_asset_allocation(holdings, prices),
        "high_volatility_assets": find_high_volatility(holdings, prices),

        # NEW: Critical 4 Features
        "trading_signals": trading_signals,
        "portfolio_forecast": portfolio_forecast,
        "smart_alerts": smart_alerts,
        "technical_analysis": technical_analysis,

        # Enhanced portfolio health
        "portfolio_health": {
            **basic['portfolio_health'],
            "ai_summary": await generate_portfolio_summary_llm(basic, coins)
        }
    }

    return result


# =============================================================================
# AI GENERATORS (LLM)
# =============================================================================

async def generate_predictions(coins: List[str], prices: dict, signals: dict) -> List[dict]:
    """Generate AI predictions for portfolio coins"""
    if not llm_service.is_available() or not coins:
        return []
    
    predictions = []
    
    # Predict for top 5 coins
    for coin in coins[:5]:
        price_data = prices.get(coin, {})
        signal_data = signals.get(coin, {})
        
        current_price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)
        rsi = signal_data.get('technical', {}).get('rsi', 50)
        
        # AI prediction
        prompt = f"""Analyze {coin} and provide a 7-day price prediction.

Current data:
- Price: ${current_price}
- 24h Change: {change_24h}%
- RSI: {rsi}

Respond in JSON:
{{
  "target_price": 50000,
  "potential_gain": 5.2,
  "direction": "bullish|bearish|neutral",
  "confidence": 75,
  "reasoning": "Brief explanation...",
  "key_factors": ["factor1", "factor2"]
}}"""
        
        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            pred = json.loads(response.choices[0].message.content)
            
            predictions.append({
                "symbol": coin,
                "current_price": current_price,
                "timeframe": "7 days",
                **pred
            })
        except:
            continue
    
    return predictions


async def analyze_news(news_list: List[dict], coins: List[str]) -> dict:
    """Analyze news for portfolio"""
    if not llm_service.is_available() or not news_list:
        return {"news_items": [], "summary": ""}
    
    # Build news text
    news_text = ""
    for idx, n in enumerate(news_list[:10]):
        title = n.get('title', '')[:100]
        news_text += f"\n[{idx+1}] {title}"
    
    prompt = f"""Analyze these news items for a portfolio holding {', '.join(coins)}.

NEWS:
{news_text}

Provide:
1. Overall sentiment summary (2-3 sentences in Turkish)
2. For each news item, provide:
   - AI insight (actionable, 1 sentence)
   - Relevance score (0-100)
   - Affected coins from portfolio

Respond in JSON:
{{
  "summary": "Overall summary in Turkish...",
  "items": [
    {{"idx": 1, "insight": "...", "relevance": 85, "affected_coins": ["BTC"]}}
  ]
}}"""
    
    try:
        response = llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Merge with original news
        news_items = []
        for item in result.get('items', []):
            idx = item.get('idx', 0) - 1
            if 0 <= idx < len(news_list):
                news_items.append({
                    **news_list[idx],
                    "ai_insight": item.get('insight', ''),
                    "relevance_score": item.get('relevance', 50),
                    "affected_coins": item.get('affected_coins', [])
                })
        
        return {
            "summary": result.get('summary', ''),
            "news_items": news_items
        }
    except:
        return {"news_items": news_list[:5], "summary": ""}


async def generate_actions(summary: dict, signals: dict, coins: List[str]) -> List[dict]:
    """Generate actionable recommendations"""
    if not llm_service.is_available():
        return []
    
    # Build portfolio context
    holdings_text = ""
    for h in summary.get('top_holdings', [])[:5]:
        holdings_text += f"\n- {h['symbol']}: ${h['value']:.0f} ({h['pnl_pct']:+.1f}%)"
    
    prompt = f"""Analyze this portfolio and provide 3-5 actionable recommendations.

PORTFOLIO:
{holdings_text}

Health Score: {summary.get('portfolio_health', {}).get('score', 50)}/100
Risk Level: {summary.get('risk_level', 'medium')}

Provide specific, actionable items in JSON:
{{
  "actions": [
    {{
      "title": "Action title",
      "symbol": "BTC",
      "type": "buy|sell|hold|rebalance|alert",
      "priority": "high|medium|low",
      "description": "What to do...",
      "reasoning": "Why...",
      "expected_impact": "+5% return potential",
      "impact_direction": "positive|negative",
      "timeframe": "This week|This month|Long-term"
    }}
  ]
}}"""
    
    try:
        response = llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('actions', [])
    except:
        return []


async def analyze_risks(summary: dict, holdings: List[dict], prices: dict) -> dict:
    """Risk analysis"""
    factors = []
    
    # Concentration risk
    top_allocation = max((h.get('allocation', 0) for h in summary.get('top_holdings', [])), default=0)
    if top_allocation > 50:
        factors.append({
            "title": "High Concentration Risk",
            "title_tr": "Yüksek Konsantrasyon Riski",
            "severity": "high",
            "description": f"Your largest holding is {top_allocation:.1f}% of portfolio. Consider diversifying.",
            "description_tr": f"En büyük pozisyonunuz portföyün {top_allocation:.1f}%'sini oluşturuyor. Çeşitlendirmeyi düşünün.",
            "mitigation": "Reduce position to <40% and allocate to other assets"
        })
    
    # Portfolio size risk
    if len(holdings) < 3:
        factors.append({
            "title": "Low Diversification",
            "title_tr": "Düşük Çeşitlendirme",
            "severity": "medium",
            "description": "Portfolio has too few assets. Add 3-5 more for better risk management.",
            "description_tr": "Portföyde çok az varlık var. Risk yönetimi için 3-5 varlık daha ekleyin.",
            "mitigation": "Add uncorrelated assets from different sectors"
        })
    
    # Negative performance risk
    if summary.get('total_pnl', 0) < -20:
        factors.append({
            "title": "Significant Losses",
            "title_tr": "Önemli Kayıplar",
            "severity": "high",
            "description": f"Portfolio is down {summary.get('total_pnl_pct', 0):.1f}%. Review stop-loss levels.",
            "description_tr": f"Portföy {summary.get('total_pnl_pct', 0):.1f}% düştü. Stop-loss seviyelerini gözden geçirin.",
            "mitigation": "Set stop-loss at -25% to limit further downside"
        })
    
    return {"factors": factors}


async def generate_portfolio_summary_llm(summary: dict, coins: List[str]) -> str:
    """Generate AI summary of portfolio health"""
    if not llm_service.is_available():
        return ""
    
    prompt = f"""Summarize this portfolio health in 2-3 sentences (Turkish).

Health Score: {summary.get('portfolio_health', {}).get('score', 50)}/100
Total Value: ${summary.get('total_value', 0):.0f}
P/L: {summary.get('total_pnl_pct', 0):+.1f}%
Holdings: {', '.join(coins)}

Be direct and actionable."""
    
    try:
        response = llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except:
        return ""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_health_score(total_value: float, total_pnl: float, 
                           num_holdings: int, holdings_data: List[dict]) -> int:
    """Calculate portfolio health score (0-100)"""
    score = 50  # Start neutral
    
    # Profitability (±30 points)
    if total_value > 0:
        pnl_pct = (total_pnl / total_value) * 100
        if pnl_pct > 50:
            score += 30
        elif pnl_pct > 20:
            score += 20
        elif pnl_pct > 0:
            score += 10
        elif pnl_pct > -20:
            score -= 10
        elif pnl_pct > -50:
            score -= 20
        else:
            score -= 30
    
    # Diversification (±20 points)
    if num_holdings >= 10:
        score += 20
    elif num_holdings >= 5:
        score += 10
    elif num_holdings >= 3:
        score += 5
    elif num_holdings == 1:
        score -= 20
    
    # Concentration risk (-15 points)
    if holdings_data:
        top_allocation = max(h['allocation'] for h in holdings_data)
        if top_allocation > 70:
            score -= 15
        elif top_allocation > 50:
            score -= 10
    
    return min(100, max(0, score))


def generate_health_summary(score: int) -> str:
    """Generate health summary text"""
    if score >= 80:
        return "Portföyünüz mükemmel durumda. Mevcut stratejinizi sürdürün."
    elif score >= 60:
        return "Portföyünüz iyi durumda. Küçük iyileştirmeler yapabilirsiniz."
    elif score >= 40:
        return "Portföyünüzde bazı iyileştirmeler gerekiyor. Risk yönetimine odaklanın."
    else:
        return "Portföyünüz risk altında. Acil aksiyonlar gerekebilir."


def calculate_diversification(holdings_data: List[dict]) -> int:
    """Calculate diversification score"""
    if not holdings_data:
        return 0
    
    # Herfindahl index
    allocations = [h['allocation'] for h in holdings_data]
    hhi = sum(a ** 2 for a in allocations) / 100
    
    # Convert to 0-100 scale (lower HHI = better diversification)
    score = int((1 - hhi / 100) * 100)
    
    return min(100, max(0, score))


def calculate_risk_level(holdings: List[dict], holdings_data: List[dict]) -> dict:
    """Calculate overall risk level"""
    risk_score = 5  # Neutral
    
    # Concentration
    if holdings_data:
        top_allocation = max(h['allocation'] for h in holdings_data)
        if top_allocation > 70:
            risk_score += 2
        elif top_allocation > 50:
            risk_score += 1
    
    # Diversification
    if len(holdings) < 3:
        risk_score += 2
    elif len(holdings) < 5:
        risk_score += 1
    
    # Volatility (simplified)
    if holdings_data:
        avg_change = sum(abs(h.get('change_24h', 0)) for h in holdings_data) / len(holdings_data)
        if avg_change > 10:
            risk_score += 2
        elif avg_change > 5:
            risk_score += 1
    
    risk_score = min(10, max(1, risk_score))
    
    if risk_score >= 8:
        level = "high"
        level_tr = "Yüksek"
    elif risk_score >= 5:
        level = "medium"
        level_tr = "Orta"
    else:
        level = "low"
        level_tr = "Düşük"
    
    return {"score": risk_score, "level": level, "level_tr": level_tr}


def calculate_weighted_change(holdings_data: List[dict]) -> float:
    """Calculate portfolio weighted 24h change"""
    if not holdings_data:
        return 0
    
    total_change = sum(
        h.get('change_24h', 0) * h.get('allocation', 0) / 100
        for h in holdings_data
    )
    
    return round(total_change, 2)


def calculate_asset_allocation(holdings: List[dict], prices: dict) -> dict:
    """Calculate asset type allocation"""
    from config import MEGA_CAP_COINS, LARGE_CAP_COINS, HIGH_RISK_COINS
    
    allocation = {
        "Mega Cap": 0,
        "Large Cap": 0,
        "Mid Cap": 0,
        "High Risk": 0
    }
    
    total_value = 0
    values = {}
    
    for h in holdings:
        coin = h.get('coin', '')
        quantity = h.get('quantity', 0) or 0
        price = prices.get(coin, {}).get('price', 0)
        value = quantity * price
        total_value += value
        values[coin] = value
    
    for coin, value in values.items():
        pct = (value / total_value * 100) if total_value > 0 else 0
        
        if coin in MEGA_CAP_COINS:
            allocation["Mega Cap"] += pct
        elif coin in LARGE_CAP_COINS:
            allocation["Large Cap"] += pct
        elif coin in HIGH_RISK_COINS:
            allocation["High Risk"] += pct
        else:
            allocation["Mid Cap"] += pct
    
    return {k: round(v, 1) for k, v in allocation.items()}


def find_high_volatility(holdings: List[dict], prices: dict) -> List[str]:
    """Find high volatility assets"""
    high_vol = []

    for h in holdings:
        coin = h.get('coin', '')
        change_24h = abs(prices.get(coin, {}).get('change_24h', 0))

        if change_24h > 10:  # >10% daily change
            high_vol.append(coin)

    return high_vol


# =============================================================================
# NEW CRITICAL FEATURES (4)
# =============================================================================

async def generate_trading_signals(coins: List[str], prices: dict, signals: dict) -> List[dict]:
    """
    🎯 AI Trading Signals - CRITICAL FEATURE #1
    Generate BUY/SELL/HOLD signals with entry/exit points
    """
    if not llm_service.is_available() or not coins:
        return []

    trading_signals = []

    # Generate signals for top 5 coins
    for coin in coins[:5]:
        price_data = prices.get(coin, {})
        signal_data = signals.get(coin, {})

        current_price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)
        change_7d = price_data.get('change_7d', 0)

        technical = signal_data.get('technical', {})
        rsi = technical.get('rsi', 50)
        macd = technical.get('macd', 0)

        # AI signal generation
        prompt = f"""Analyze {coin} and provide a detailed trading signal.

CURRENT DATA:
- Price: ${current_price}
- 24h Change: {change_24h}%
- 7d Change: {change_7d}%
- RSI: {rsi}
- MACD: {macd}

Generate a trading signal with:
1. Signal type (BUY/SELL/HOLD/ACCUMULATE)
2. Strength (1-10)
3. Entry range (if BUY/ACCUMULATE)
4. Target prices (3 levels)
5. Stop loss
6. Risk/Reward ratio
7. Timeframe (Day/Swing/Long)
8. Confidence (%)

Respond in JSON:
{{
  "signal": "BUY|SELL|HOLD|ACCUMULATE",
  "strength": 8.5,
  "entry_range": [43000, 44500],
  "targets": [48000, 52000, 58000],
  "stop_loss": 41000,
  "risk_reward": 3.2,
  "timeframe": "Swing (7-14 days)",
  "confidence": 78,
  "reasoning": "Brief explanation...",
  "key_indicators": ["RSI oversold", "MACD bullish cross"]
}}"""

        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=350,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            signal = json.loads(response.choices[0].message.content)

            trading_signals.append({
                "coin": coin,
                "current_price": current_price,
                "timestamp": datetime.utcnow().isoformat(),
                **signal
            })
        except Exception as e:
            print(f"Error generating signal for {coin}: {e}")
            continue

    return trading_signals


async def generate_portfolio_forecast(summary: dict, holdings: List[dict], prices: dict) -> dict:
    """
    📊 Portfolio Forecasting - CRITICAL FEATURE #2
    7-day and 30-day portfolio value forecasts
    """
    if not llm_service.is_available():
        return {
            "next_7_days": {},
            "next_30_days": {},
            "scenarios": []
        }

    total_value = summary.get('total_value', 0)
    total_pnl_pct = summary.get('total_pnl_pct', 0)

    # Build holdings summary
    holdings_summary = []
    for h in summary.get('top_holdings', [])[:5]:
        holdings_summary.append({
            "coin": h['symbol'],
            "allocation": h.get('allocation', 0),
            "pnl": h.get('pnl_pct', 0)
        })

    prompt = f"""Forecast this crypto portfolio's performance.

PORTFOLIO:
Total Value: ${total_value}
Current P/L: {total_pnl_pct:+.1f}%

Holdings:
{json.dumps(holdings_summary, indent=2)}

Provide forecasts for:
1. Next 7 days (expected, best case, worst case)
2. Next 30 days (expected return, risk-adjusted return, Sharpe ratio estimate)
3. Three scenarios (conservative, moderate, optimistic) with probabilities

Respond in JSON:
{{
  "next_7_days": {{
    "expected_value": 12500,
    "best_case": 13800,
    "worst_case": 11200,
    "confidence_interval": "80%",
    "expected_change_pct": 5.2
  }},
  "next_30_days": {{
    "expected_return_pct": 8.5,
    "risk_adjusted_return_pct": 6.2,
    "sharpe_ratio": 1.4,
    "volatility_estimate": 15.3
  }},
  "scenarios": [
    {{
      "name": "Conservative",
      "return_pct": 3.5,
      "probability": 70,
      "description": "Brief description..."
    }},
    {{
      "name": "Moderate",
      "return_pct": 8.5,
      "probability": 50,
      "description": "Brief description..."
    }},
    {{
      "name": "Optimistic",
      "return_pct": 15.0,
      "probability": 30,
      "description": "Brief description..."
    }}
  ],
  "key_assumptions": ["Bitcoin stability", "Market sentiment neutral"]
}}"""

    try:
        response = llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        forecast = json.loads(response.choices[0].message.content)
        forecast["generated_at"] = datetime.utcnow().isoformat()

        return forecast
    except Exception as e:
        print(f"Error generating forecast: {e}")
        return {
            "next_7_days": {},
            "next_30_days": {},
            "scenarios": []
        }


async def generate_smart_alerts(summary: dict, holdings: List[dict],
                                prices: dict, signals: dict) -> List[dict]:
    """
    🔔 Smart Alerts - CRITICAL FEATURE #3
    Intelligent, actionable alerts based on portfolio conditions
    """
    if not llm_service.is_available():
        return []

    # Build context
    alerts_context = {
        "total_value": summary.get('total_value', 0),
        "health_score": summary.get('portfolio_health', {}).get('score', 50),
        "risk_level": summary.get('risk_level', 'medium'),
        "holdings": []
    }

    for h in summary.get('top_holdings', [])[:5]:
        coin = h['symbol']
        price_data = prices.get(coin, {})
        signal_data = signals.get(coin, {})

        alerts_context['holdings'].append({
            "coin": coin,
            "allocation": h.get('allocation', 0),
            "pnl_pct": h.get('pnl_pct', 0),
            "change_24h": price_data.get('change_24h', 0),
            "rsi": signal_data.get('technical', {}).get('rsi', 50)
        })

    prompt = f"""Generate smart alerts for this portfolio.

PORTFOLIO CONTEXT:
{json.dumps(alerts_context, indent=2)}

Identify 3-5 actionable alerts:
- Price targets reached
- Volatility spikes
- Risk threshold breached
- Opportunity alerts
- Rebalancing needed

Each alert should include:
- Type (price_target, volatility, risk, opportunity, rebalance)
- Severity (low, medium, high, critical)
- Coin affected (if applicable)
- Trigger condition
- Recommended action
- Reasoning

Respond in JSON:
{{
  "alerts": [
    {{
      "type": "price_target",
      "severity": "medium",
      "coin": "BTC",
      "title": "BTC approaching resistance",
      "trigger": "Price >= $45,000",
      "action": "Consider taking 25% profit",
      "reasoning": "Historical resistance at $45,500",
      "auto_action": "Set trailing stop at -5%"
    }}
  ]
}}"""

    try:
        response = llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        alerts = result.get('alerts', [])

        # Add timestamp
        for alert in alerts:
            alert['timestamp'] = datetime.utcnow().isoformat()

        return alerts
    except Exception as e:
        print(f"Error generating alerts: {e}")
        return []


async def generate_technical_analysis(coins: List[str], prices: dict, signals: dict) -> List[dict]:
    """
    📈 Technical Analysis Dashboard - CRITICAL FEATURE #4
    Comprehensive technical analysis for each coin
    """
    if not llm_service.is_available() or not coins:
        return []

    technical_analyses = []

    # Analyze top 5 coins
    for coin in coins[:5]:
        price_data = prices.get(coin, {})
        signal_data = signals.get(coin, {})

        current_price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)

        technical = signal_data.get('technical', {})
        rsi = technical.get('rsi', 50)
        macd = technical.get('macd', 0)

        prompt = f"""Provide technical analysis for {coin}.

CURRENT DATA:
- Price: ${current_price}
- 24h Change: {change_24h}%
- RSI: {rsi}
- MACD: {macd}

Analyze:
1. Trend (bullish/bearish/neutral)
2. Support levels (3 levels)
3. Resistance levels (3 levels)
4. Key indicators interpretation
5. Chart patterns (if any)
6. Volume analysis
7. Overall technical score (0-100)

Respond in JSON:
{{
  "trend": "bullish",
  "trend_strength": 7.5,
  "support_levels": [42000, 40000, 38000],
  "resistance_levels": [48000, 52000, 58000],
  "indicators": {{
    "rsi": {{"value": 35, "signal": "oversold", "interpretation": "Potential reversal"}},
    "macd": {{"signal": "bullish_cross", "interpretation": "Buy signal"}},
    "moving_averages": {{"signal": "golden_cross", "interpretation": "Strong uptrend"}}
  }},
  "patterns": ["Falling wedge (bullish)", "RSI divergence"],
  "volume_analysis": "Above average, confirms trend",
  "technical_score": 72,
  "recommendation": "BUY on dips near support",
  "confidence": 75
}}"""

        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)

            technical_analyses.append({
                "coin": coin,
                "current_price": current_price,
                "timeframe": "4h",
                "timestamp": datetime.utcnow().isoformat(),
                **analysis
            })
        except Exception as e:
            print(f"Error analyzing {coin}: {e}")
            continue

    return technical_analyses