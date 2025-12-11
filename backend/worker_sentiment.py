#!/usr/bin/env python3
"""
CryptoSignal - Sentiment Worker v2.0
====================================
Güncellemeler:
- 10 dakika güncelleme (30dk'dan düşürüldü)
- Birden fazla Fear & Greed kaynağı
- Crypto-specific sentiment göstergeleri
- FX rates
- Global market metrics
"""

import asyncio
import json
import redis
import httpx
from datetime import datetime
from typing import Dict, Optional

# Redis
REDIS_PASS = "3f9af2788cb89aa74c06bd48dd290658"
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, password=REDIS_PASS)

# Güncelleme aralığı
UPDATE_INTERVAL = 600  # 10 dakika

print("[Sentiment Worker v2.0] Starting...")


async def fetch_fear_greed(client: httpx.AsyncClient) -> Optional[Dict]:
    """Fear & Greed Index from alternative.me"""
    try:
        resp = await client.get("https://api.alternative.me/fng/?limit=7")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                current = data["data"][0]
                history = data["data"][1:7]
                
                # Calculate trend
                current_val = int(current.get("value", 50))
                prev_val = int(history[0].get("value", 50)) if history else current_val
                trend = "up" if current_val > prev_val else "down" if current_val < prev_val else "stable"
                
                # 7 day average
                avg_7d = sum(int(h.get("value", 50)) for h in data["data"]) / len(data["data"])
                
                return {
                    "value": current_val,
                    "value_classification": current.get("value_classification", "Neutral"),
                    "trend": trend,
                    "change_24h": current_val - prev_val,
                    "avg_7d": round(avg_7d, 1),
                    "timestamp": current.get("timestamp"),
                    "history": [{"value": int(h["value"]), "date": h.get("timestamp")} for h in history]
                }
    except Exception as e:
        print(f"[Fear&Greed] Error: {e}")
    return None


async def fetch_global_metrics(client: httpx.AsyncClient) -> Optional[Dict]:
    """CoinGecko global metrics"""
    try:
        resp = await client.get("https://api.coingecko.com/api/v3/global")
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            
            return {
                "total_market_cap_usd": data.get("total_market_cap", {}).get("usd", 0),
                "total_volume_24h_usd": data.get("total_volume", {}).get("usd", 0),
                "btc_dominance": round(data.get("market_cap_percentage", {}).get("btc", 0), 2),
                "eth_dominance": round(data.get("market_cap_percentage", {}).get("eth", 0), 2),
                "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
                "markets": data.get("markets", 0),
                "market_cap_change_24h": round(data.get("market_cap_change_percentage_24h_usd", 0), 2),
            }
    except Exception as e:
        print(f"[Global] Error: {e}")
    return None


async def fetch_fx_rates(client: httpx.AsyncClient) -> Optional[Dict]:
    """FX rates from exchangerate-api"""
    try:
        resp = await client.get("https://api.exchangerate-api.com/v4/latest/USD")
        if resp.status_code == 200:
            data = resp.json()
            rates = data.get("rates", {})
            
            return {
                "TRY": rates.get("TRY", 34),
                "EUR": rates.get("EUR", 0.92),
                "GBP": rates.get("GBP", 0.79),
                "JPY": rates.get("JPY", 150),
                "CNY": rates.get("CNY", 7.2),
                "KRW": rates.get("KRW", 1350),
                "INR": rates.get("INR", 83),
                "BRL": rates.get("BRL", 5.0),
                "base": "USD",
            }
    except Exception as e:
        print(f"[FX] Error: {e}")
    return None


async def fetch_btc_metrics(client: httpx.AsyncClient) -> Optional[Dict]:
    """Bitcoin specific metrics"""
    try:
        resp = await client.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin",
            params={"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"}
        )
        if resp.status_code == 200:
            data = resp.json()
            market = data.get("market_data", {})
            
            return {
                "price_usd": market.get("current_price", {}).get("usd", 0),
                "ath": market.get("ath", {}).get("usd", 0),
                "ath_change_percentage": round(market.get("ath_change_percentage", {}).get("usd", 0), 2),
                "ath_date": market.get("ath_date", {}).get("usd", ""),
                "market_cap": market.get("market_cap", {}).get("usd", 0),
                "volume_24h": market.get("total_volume", {}).get("usd", 0),
                "circulating_supply": market.get("circulating_supply", 0),
                "max_supply": market.get("max_supply", 21000000),
                "change_24h": round(market.get("price_change_percentage_24h", 0), 2),
                "change_7d": round(market.get("price_change_percentage_7d", 0), 2),
                "change_30d": round(market.get("price_change_percentage_30d", 0), 2),
            }
    except Exception as e:
        print(f"[BTC] Error: {e}")
    return None


def calculate_market_sentiment(fear_greed: Dict, global_metrics: Dict, btc: Dict) -> Dict:
    """Genel piyasa sentiment'ini hesapla"""
    
    score = 50  # Neutral start
    signals = []
    
    # Fear & Greed contribution (40%)
    if fear_greed:
        fg_val = fear_greed.get("value", 50)
        if fg_val < 25:
            score -= 20
            signals.append("Extreme Fear")
        elif fg_val < 40:
            score -= 10
            signals.append("Fear")
        elif fg_val > 75:
            score += 20
            signals.append("Extreme Greed")
        elif fg_val > 60:
            score += 10
            signals.append("Greed")
    
    # Market cap change contribution (30%)
    if global_metrics:
        mc_change = global_metrics.get("market_cap_change_24h", 0)
        if mc_change > 5:
            score += 15
            signals.append(f"Market +{mc_change:.1f}%")
        elif mc_change > 2:
            score += 8
        elif mc_change < -5:
            score -= 15
            signals.append(f"Market {mc_change:.1f}%")
        elif mc_change < -2:
            score -= 8
    
    # BTC performance contribution (30%)
    if btc:
        btc_change = btc.get("change_24h", 0)
        if btc_change > 5:
            score += 15
            signals.append(f"BTC +{btc_change:.1f}%")
        elif btc_change > 2:
            score += 8
        elif btc_change < -5:
            score -= 15
            signals.append(f"BTC {btc_change:.1f}%")
        elif btc_change < -2:
            score -= 8
    
    # Classify
    if score >= 70:
        sentiment = "Very Bullish"
    elif score >= 55:
        sentiment = "Bullish"
    elif score <= 30:
        sentiment = "Very Bearish"
    elif score <= 45:
        sentiment = "Bearish"
    else:
        sentiment = "Neutral"
    
    return {
        "score": score,
        "sentiment": sentiment,
        "signals": signals[:5],
    }


async def fetch_all():
    """Tüm sentiment verilerini topla"""
    async with httpx.AsyncClient(timeout=15) as client:
        # Paralel çağrılar
        fg_task = fetch_fear_greed(client)
        global_task = fetch_global_metrics(client)
        fx_task = fetch_fx_rates(client)
        btc_task = fetch_btc_metrics(client)
        
        fear_greed, global_metrics, fx_rates, btc_metrics = await asyncio.gather(
            fg_task, global_task, fx_task, btc_task
        )
        
        # Calculate overall sentiment
        market_sentiment = calculate_market_sentiment(fear_greed, global_metrics, btc_metrics)
        
        # Save to Redis
        timestamp = datetime.utcnow().isoformat()
        
        if fear_greed:
            fear_greed["updated"] = timestamp
            r.set("fear_greed", json.dumps(fear_greed))
            print(f"[F&G] {fear_greed['value']} - {fear_greed['value_classification']} ({fear_greed['trend']})")
        
        if global_metrics:
            global_metrics["updated"] = timestamp
            r.set("global_metrics", json.dumps(global_metrics))
            mc = global_metrics["total_market_cap_usd"]
            print(f"[Global] MCap: ${mc/1e12:.2f}T | BTC Dom: {global_metrics['btc_dominance']}%")
        
        if fx_rates:
            fx_rates["updated"] = timestamp
            r.set("fx_rates", json.dumps(fx_rates))
            print(f"[FX] USD/TRY: {fx_rates['TRY']:.2f} | USD/EUR: {fx_rates['EUR']:.4f}")
        
        if btc_metrics:
            btc_metrics["updated"] = timestamp
            r.set("btc_metrics", json.dumps(btc_metrics))
        
        # Market sentiment
        market_sentiment["updated"] = timestamp
        r.set("market_sentiment", json.dumps(market_sentiment))
        print(f"[Sentiment] {market_sentiment['sentiment']} ({market_sentiment['score']}/100)")
        
        r.set("sentiment_updated", timestamp)


async def main():
    """10 dakikada bir güncelle"""
    print(f"[Sentiment] Update interval: {UPDATE_INTERVAL}s ({UPDATE_INTERVAL//60} min)")
    
    while True:
        try:
            await fetch_all()
        except Exception as e:
            print(f"[Sentiment] Error: {e}")
        
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())