# -*- coding: utf-8 -*-
"""
CryptoSignal - Futures Service
==============================
Binance Futures API entegrasyonu
"""

import httpx
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from database import redis_client

# Binance Futures symbol mapping
FUTURES_SYMBOLS = {
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT", "XRP": "XRPUSDT",
    "DOGE": "DOGEUSDT", "ADA": "ADAUSDT", "AVAX": "AVAXUSDT", "DOT": "DOTUSDT",
    "LINK": "LINKUSDT", "MATIC": "MATICUSDT", "POL": "MATICUSDT", "UNI": "UNIUSDT",
    "LTC": "LTCUSDT", "BCH": "BCHUSDT", "ATOM": "ATOMUSDT", "FIL": "FILUSDT",
    "APT": "APTUSDT", "ARB": "ARBUSDT", "OP": "OPUSDT", "INJ": "INJUSDT",
    "SUI": "SUIUSDT", "SEI": "SEIUSDT", "TIA": "TIAUSDT", "NEAR": "NEARUSDT",
    "PEPE": "PEPEUSDT", "SHIB": "SHIBUSDT", "BONK": "BONKUSDT", "WIF": "WIFUSDT",
    "FET": "FETUSDT", "RNDR": "RNDRUSDT", "GRT": "GRTUSDT", "AAVE": "AAVEUSDT",
    "MKR": "MKRUSDT", "SNX": "SNXUSDT", "CRV": "CRVUSDT", "LDO": "LDOUSDT",
    "BNB": "BNBUSDT", "TRX": "TRXUSDT", "ETC": "ETCUSDT", "XLM": "XLMUSDT",
}

# Cache
futures_cache: Dict[str, dict] = {}
futures_cache_time: datetime = None


class FuturesService:
    """Binance Futures veri servisi"""
    
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self.cache_duration = 300  # 5 dakika
    
    async def fetch_all(self) -> Dict[str, Dict]:
        """
        Tüm futures verilerini çek
        
        Returns:
            Symbol -> futures data mapping
        """
        global futures_cache, futures_cache_time
        
        # Cache kontrolü
        if futures_cache_time:
            cache_age = (datetime.utcnow() - futures_cache_time).total_seconds()
            if cache_age < self.cache_duration:
                return futures_cache
        
        result = {}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Funding rates
                funding_data = await self._fetch_funding_rates(client)
                
                # Open interest
                oi_data = await self._fetch_open_interest(client)
                
                # Long/Short ratio
                ls_data = await self._fetch_long_short_ratio(client)
                
                # Combine data
                for symbol, futures_symbol in FUTURES_SYMBOLS.items():
                    result[symbol] = {
                        "funding_rate": funding_data.get(futures_symbol, 0),
                        "open_interest": oi_data.get(futures_symbol, 0),
                        "open_interest_value": oi_data.get(f"{futures_symbol}_value", 0),
                        "long_short_ratio": ls_data.get(futures_symbol, 1.0),
                        "long_account": ls_data.get(f"{futures_symbol}_long", 50),
                        "short_account": ls_data.get(f"{futures_symbol}_short", 50),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                
                # Cache güncelle
                futures_cache = result
                futures_cache_time = datetime.utcnow()
                
                # Redis'e kaydet
                redis_client.set("futures_data", str(result).replace("'", '"'))
                redis_client.set("futures_updated", datetime.utcnow().isoformat())
                
                print(f"[Futures] Updated {len(result)} symbols")
                
                return result
        
        except Exception as e:
            print(f"[Futures] Error: {e}")
            return futures_cache or {}
    
    async def _fetch_funding_rates(self, client: httpx.AsyncClient) -> Dict:
        """Funding rate'leri çek"""
        try:
            r = await client.get(f"{self.base_url}/fapi/v1/premiumIndex")
            if r.status_code == 200:
                data = r.json()
                return {
                    item["symbol"]: float(item.get("lastFundingRate", 0)) * 100
                    for item in data
                }
        except Exception as e:
            print(f"[Futures] Funding rate error: {e}")
        return {}
    
    async def _fetch_open_interest(self, client: httpx.AsyncClient) -> Dict:
        """Open interest verilerini çek"""
        result = {}
        try:
            r = await client.get(f"{self.base_url}/fapi/v1/openInterest", params={"symbol": "BTCUSDT"})
            # Bulk endpoint yok, tek tek çekmek gerekiyor
            # Şimdilik sadece cache'den döndür
            pass
        except Exception as e:
            print(f"[Futures] Open interest error: {e}")
        return result
    
    async def _fetch_long_short_ratio(self, client: httpx.AsyncClient) -> Dict:
        """Long/Short ratio verilerini çek"""
        result = {}
        try:
            # Top trader L/S ratio
            for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
                r = await client.get(
                    f"{self.base_url}/futures/data/topLongShortAccountRatio",
                    params={"symbol": symbol, "period": "1h", "limit": 1}
                )
                if r.status_code == 200:
                    data = r.json()
                    if data:
                        ls = data[0]
                        result[symbol] = float(ls.get("longShortRatio", 1.0))
                        result[f"{symbol}_long"] = float(ls.get("longAccount", 50))
                        result[f"{symbol}_short"] = float(ls.get("shortAccount", 50))
                
                await asyncio.sleep(0.1)  # Rate limit
        except Exception as e:
            print(f"[Futures] L/S ratio error: {e}")
        return result
    
    async def get_symbol_data(self, symbol: str) -> Optional[Dict]:
        """Tek sembol için futures verisi"""
        # Önce cache'den dene
        if symbol in futures_cache:
            return futures_cache[symbol]
        
        # Redis'den dene
        try:
            futures_raw = redis_client.get("futures_data")
            if futures_raw:
                import json
                all_futures = json.loads(futures_raw)
                return all_futures.get(symbol)
        except:
            pass
        
        return None
    
    def analyze_futures_signal(self, data: Dict) -> Dict:
        """
        Futures verilerinden sinyal üret
        
        TRADING SIGNALS:
        - Funding > 0.1% = Too many longs, expect correction
        - Funding < -0.1% = Too many shorts, expect bounce
        - L/S Ratio > 2 = Retail is very long, be cautious
        - L/S Ratio < 0.5 = Retail is very short, potential reversal
        """
        funding = data.get("funding_rate", 0)
        ls_ratio = data.get("long_short_ratio", 1)
        
        signal = "NEUTRAL"
        score = 0
        reasons = []
        
        # Funding rate analizi
        if funding > 0.1:
            signal = "BEARISH"
            score -= 20
            reasons.append(f"Extreme positive funding ({funding:.3f}%)")
        elif funding > 0.05:
            score -= 10
            reasons.append(f"High positive funding ({funding:.3f}%)")
        elif funding < -0.1:
            signal = "BULLISH"
            score += 20
            reasons.append(f"Extreme negative funding ({funding:.3f}%)")
        elif funding < -0.05:
            score += 10
            reasons.append(f"Negative funding ({funding:.3f}%)")
        
        # Long/Short ratio analizi
        if ls_ratio > 2:
            signal = "BEARISH"
            score -= 15
            reasons.append(f"Too many longs ({ls_ratio:.2f})")
        elif ls_ratio > 1.5:
            score -= 8
            reasons.append(f"More longs ({ls_ratio:.2f})")
        elif ls_ratio < 0.5:
            signal = "BULLISH"
            score += 15
            reasons.append(f"Too many shorts ({ls_ratio:.2f})")
        elif ls_ratio < 0.7:
            score += 8
            reasons.append(f"More shorts ({ls_ratio:.2f})")
        
        return {
            "signal": signal,
            "score": score,
            "reasons": reasons,
            "funding_rate": funding,
            "long_short_ratio": ls_ratio
        }


# Singleton instance
futures_service = FuturesService()
