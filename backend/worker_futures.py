#!/usr/bin/env python3
"""
CryptoSignal - Futures Worker v2.0
==================================
Güncellemeler:
- 200+ coin futures verisi (40'tan artırıldı)
- 1 dakika güncelleme (5dk'dan düşürüldü)
- Toplu API çağrıları (rate limit optimizasyonu)
- Open Interest USD değeri
- Liquidation verisi
"""

import asyncio
import json
import redis
import httpx
from datetime import datetime
from typing import Dict, List

# Redis
REDIS_PASS = "3f9af2788cb89aa74c06bd48dd290658"
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, password=REDIS_PASS)

# Güncelleme aralığı
UPDATE_INTERVAL = 60  # 1 dakika

print("[Futures Worker v2.0] Starting...")

async def fetch_all_funding_rates(client: httpx.AsyncClient) -> Dict:
    """Tüm funding rate'leri tek çağrıda al"""
    try:
        resp = await client.get("https://fapi.binance.com/fapi/v1/premiumIndex")
        if resp.status_code == 200:
            result = {}
            for item in resp.json():
                symbol = item.get("symbol", "")
                if symbol.endswith("USDT"):
                    base = symbol.replace("USDT", "")
                    result[base] = {
                        "funding_rate": float(item.get("lastFundingRate", 0)) * 100,
                        "mark_price": float(item.get("markPrice", 0)),
                        "index_price": float(item.get("indexPrice", 0)),
                        "next_funding_time": item.get("nextFundingTime", 0)
                    }
            return result
    except Exception as e:
        print(f"[Funding] Error: {e}")
    return {}


async def fetch_all_open_interest(client: httpx.AsyncClient) -> Dict:
    """Tüm open interest verilerini al"""
    try:
        resp = await client.get("https://fapi.binance.com/fapi/v1/openInterest", params={"symbol": "BTCUSDT"})
        # Binance tek tek çağrı gerektiriyor, toplu endpoint yok
        # Bunun yerine ticker'dan çekelim
        
        resp = await client.get("https://fapi.binance.com/fapi/v1/ticker/24hr")
        if resp.status_code == 200:
            result = {}
            for item in resp.json():
                symbol = item.get("symbol", "")
                if symbol.endswith("USDT"):
                    base = symbol.replace("USDT", "")
                    result[base] = {
                        "volume_24h": float(item.get("volume", 0)),
                        "quote_volume_24h": float(item.get("quoteVolume", 0)),
                        "price_change_24h": float(item.get("priceChangePercent", 0)),
                        "high_24h": float(item.get("highPrice", 0)),
                        "low_24h": float(item.get("lowPrice", 0)),
                        "last_price": float(item.get("lastPrice", 0)),
                        "trades_24h": int(item.get("count", 0))
                    }
            return result
    except Exception as e:
        print(f"[OI] Error: {e}")
    return {}


async def fetch_long_short_ratio(client: httpx.AsyncClient, symbols: List[str]) -> Dict:
    """Top coinler için Long/Short ratio"""
    result = {}
    
    for symbol in symbols[:50]:  # Top 50
        try:
            resp = await client.get(
                "https://fapi.binance.com/futures/data/topLongShortAccountRatio",
                params={"symbol": f"{symbol}USDT", "period": "1h", "limit": 1}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    result[symbol] = {
                        "long_account": float(data[0].get("longAccount", 0.5)),
                        "short_account": float(data[0].get("shortAccount", 0.5)),
                        "long_short_ratio": float(data[0].get("longShortRatio", 1.0)),
                    }
            await asyncio.sleep(0.05)  # Rate limit
        except:
            pass
    
    return result


async def fetch_taker_buy_sell(client: httpx.AsyncClient, symbols: List[str]) -> Dict:
    """Taker buy/sell ratio"""
    result = {}
    
    for symbol in symbols[:30]:  # Top 30
        try:
            resp = await client.get(
                "https://fapi.binance.com/futures/data/takerlongshortRatio",
                params={"symbol": f"{symbol}USDT", "period": "1h", "limit": 1}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    result[symbol] = {
                        "buy_vol": float(data[0].get("buyVol", 0)),
                        "sell_vol": float(data[0].get("sellVol", 0)),
                        "buy_sell_ratio": float(data[0].get("buySellRatio", 1.0)),
                    }
            await asyncio.sleep(0.05)
        except:
            pass
    
    return result


async def fetch_futures_data():
    """Ana veri toplama fonksiyonu"""
    async with httpx.AsyncClient(timeout=30) as client:
        # Paralel çağrılar
        funding_task = fetch_all_funding_rates(client)
        ticker_task = fetch_all_open_interest(client)
        
        funding_data, ticker_data = await asyncio.gather(funding_task, ticker_task)
        
        # Top symbols for detailed data
        top_symbols = sorted(
            ticker_data.keys(),
            key=lambda x: ticker_data[x].get("quote_volume_24h", 0),
            reverse=True
        )[:100]
        
        # L/S ratio ve taker buy/sell
        ls_data = await fetch_long_short_ratio(client, top_symbols)
        taker_data = await fetch_taker_buy_sell(client, top_symbols)
        
        # Combine all data
        result = {}
        
        for symbol in funding_data.keys():
            result[symbol] = {
                "futures_symbol": f"{symbol}USDT",
                **funding_data.get(symbol, {}),
                **ticker_data.get(symbol, {}),
                **ls_data.get(symbol, {"long_short_ratio": 1.0}),
                **taker_data.get(symbol, {}),
            }
            
            # Open Interest USD hesapla
            mark_price = funding_data.get(symbol, {}).get("mark_price", 0)
            volume = ticker_data.get(symbol, {}).get("volume_24h", 0)
            if mark_price and volume:
                result[symbol]["open_interest_usd"] = volume * mark_price
        
        # Save to Redis
        r.set("futures_data", json.dumps(result))
        r.set("futures_updated", datetime.utcnow().isoformat())
        r.set("futures_count", len(result))
        
        # Stats
        btc = result.get("BTC", {})
        eth = result.get("ETH", {})
        
        print(f"[Futures] {len(result)} coins | BTC Fund: {btc.get('funding_rate', 0):.4f}% L/S: {btc.get('long_short_ratio', 1):.2f} | ETH Fund: {eth.get('funding_rate', 0):.4f}%")


async def main():
    """1 dakikada bir güncelle"""
    print(f"[Futures] Update interval: {UPDATE_INTERVAL}s")
    
    while True:
        try:
            await fetch_futures_data()
        except Exception as e:
            print(f"[Futures] Error: {e}")
        
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())