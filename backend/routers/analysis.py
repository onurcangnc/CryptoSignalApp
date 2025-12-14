# -*- coding: utf-8 -*-
"""
CryptoSignal - Analysis Router
==============================
/api/analyze, /api/digest endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import json

from database import redis_client, increment_llm_usage, today_str
from dependencies import get_current_user, require_llm_quota, check_llm_quota
from config import LLM_LIMITS

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.get("/analyze/{symbol}")
async def analyze_coin(
    symbol: str,
    timeframe: str = Query(default="1d", pattern="^(1d|1w|1m|3m|6m|1y)$"),
    user: dict = Depends(get_current_user)
):
    """
    Coin analizi - sinyal verilerini döndürür
    Not: Bu endpoint LLM kullanmıyor, sadece mevcut verileri döndürüyor
    """
    symbol = symbol.upper()
    
    try:
        # Fiyat verisi
        prices_raw = redis_client.get("prices_data")
        prices = json.loads(prices_raw) if prices_raw else {}
        price_data = prices.get(symbol, {})
        
        # Sinyal verisi
        signals_raw = redis_client.get("signals_data")
        signals = json.loads(signals_raw) if signals_raw else {}
        signal_data = signals.get(symbol, {})
        
        # Futures verisi
        futures_raw = redis_client.get("futures_data")
        futures = json.loads(futures_raw) if futures_raw else {}
        futures_data = futures.get(symbol, {})
        
        if not price_data and not signal_data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        return {
            "success": True,
            "symbol": symbol,
            "price": price_data.get("price", 0),
            "change_24h": price_data.get("change_24h", 0),
            "change_7d": price_data.get("change_7d", 0),
            "market_cap": price_data.get("market_cap", 0),
            "volume_24h": price_data.get("volume_24h", 0),
            "signal": signal_data,
            "futures": futures_data,
            "recommendation": signal_data.get("signal_tr", signal_data.get("signal", "BEKLE")),
            "confidence": signal_data.get("confidence", 50),
            "risk_level": signal_data.get("risk_level", "MEDIUM"),
            "reasons": signal_data.get("reasons", []),
            "technical": signal_data.get("technical", {})
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digest")
async def get_market_digest(user: dict = Depends(require_llm_quota)):
    """
    AI Market Özeti - LLM kullanır
    Not: Bu basit bir placeholder, gerçek implementasyon services/llm_service.py'da
    """
    # LLM kotasını kontrol et
    can_use, used, limit, remaining = check_llm_quota(user)
    
    if not can_use:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI limit reached ({used}/{limit})"
        )
    
    # LLM kullanımını kaydet
    increment_llm_usage(user['id'], today_str())
    
    # Basit özet (gerçek LLM implementasyonu ayrı serviste)
    try:
        # Market verileri
        fear_greed = json.loads(redis_client.get("fear_greed") or "{}")
        signals_stats = json.loads(redis_client.get("signals_stats") or "{}")
        
        fg_value = fear_greed.get("value", 50)
        fg_class = fear_greed.get("classification", "Neutral")
        
        buy_count = signals_stats.get("STRONG_BUY", 0) + signals_stats.get("BUY", 0)
        sell_count = signals_stats.get("STRONG_SELL", 0) + signals_stats.get("SELL", 0)
        
        # Basit özet metni
        if fg_value < 30:
            market_mood = "korku hakim"
        elif fg_value > 70:
            market_mood = "açgözlülük hakim"
        else:
            market_mood = "nötr"
        
        digest = f"""📊 Piyasa Özeti

Fear & Greed: {fg_value} ({fg_class})
Piyasada {market_mood}.

Sinyal Dağılımı:
🟢 AL: {buy_count}
🔴 SAT: {sell_count}

Bu özet otomatik oluşturulmuştur. Detaylı analiz için AI Digest özelliğini kullanın.
"""
        
        return {
            "success": True,
            "digest": digest,
            "generated_at": today_str(),
            "remaining_quota": remaining - 1
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prices")
async def get_prices():
    """Tüm fiyatları getir"""
    try:
        prices_raw = redis_client.get("prices_data")
        prices = json.loads(prices_raw) if prices_raw else {}
        
        fx_raw = redis_client.get("fx_rates")
        fx = json.loads(fx_raw) if fx_raw else {"USD": 1, "TRY": 34.5, "EUR": 0.92}
        
        return {
            "prices": prices,
            "count": len(prices),
            "fx": fx,
            "updated_at": redis_client.get("prices_updated")
        }
    except Exception as e:
        return {"prices": {}, "error": str(e)}


@router.get("/coins")
async def get_coins(limit: int = 500, search: str = None):
    """
    Coin listesi - portföy ve diğer seçiciler için

    Args:
        limit: Maksimum coin sayısı (default 500, max 1000)
        search: Arama filtresi (symbol veya name içinde arar)
    """
    try:
        prices_raw = redis_client.get("prices_data")
        prices = json.loads(prices_raw) if prices_raw else {}

        # Market cap'e göre sırala
        coins = sorted(
            prices.keys(),
            key=lambda x: prices[x].get("market_cap", 0) or 0,
            reverse=True
        )

        # Arama filtresi uygula
        if search:
            search_lower = search.lower()
            coins = [
                c for c in coins
                if search_lower in c.lower() or
                   search_lower in (prices[c].get("name", "") or "").lower()
            ]

        # Limit uygula (max 1000)
        limit = min(limit, 1000)
        coins = coins[:limit]

        details = []
        for symbol in coins:
            data = prices[symbol]
            details.append({
                "symbol": symbol,
                "name": data.get("name", symbol),
                "price": data.get("price", 0),
                "change_24h": data.get("change_24h", 0),
                "change_7d": data.get("change_7d", 0),
                "market_cap": data.get("market_cap", 0),
                "volume": data.get("volume_24h", 0),
                "rank": data.get("rank", 0),
                "image": data.get("image", "")
            })

        return {
            "coins": coins,
            "details": details,
            "count": len(coins),
            "total_available": len(prices)
        }
    except Exception as e:
        return {"coins": [], "error": str(e)}


@router.get("/fear-greed")
async def get_fear_greed():
    """Fear & Greed Index"""
    try:
        fg_raw = redis_client.get("fear_greed")
        if fg_raw:
            return json.loads(fg_raw)
        return {"value": 50, "classification": "Neutral"}
    except:
        return {"value": 50, "classification": "Neutral"}
