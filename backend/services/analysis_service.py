# -*- coding: utf-8 -*-
"""
CryptoSignal - Analysis Service
===============================
Teknik analiz ve sinyal üretimi
"""

import json
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from database import redis_client
from config import STABLECOINS, MEGA_CAP_COINS, LARGE_CAP_COINS, HIGH_RISK_COINS

# CoinGecko ID mapping
COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple",
    "ADA": "cardano", "DOGE": "dogecoin", "DOT": "polkadot", "AVAX": "avalanche-2",
    "LINK": "chainlink", "LTC": "litecoin", "UNI": "uniswap", "ATOM": "cosmos",
    "XLM": "stellar", "ALGO": "algorand", "VET": "vechain", "FIL": "filecoin",
    "HBAR": "hedera-hashgraph", "NEAR": "near", "APT": "aptos", "ARB": "arbitrum",
    "OP": "optimism", "INJ": "injective-protocol", "SUI": "sui", "SEI": "sei-network",
    "TIA": "celestia", "RNDR": "render-token", "FET": "fetch-ai", "TAO": "bittensor",
    "PEPE": "pepe", "SHIB": "shiba-inu", "BONK": "bonk", "WIF": "dogwifcoin",
    "TON": "the-open-network", "TRX": "tron", "BCH": "bitcoin-cash", "ETC": "ethereum-classic",
    "BNB": "binancecoin", "MATIC": "matic-network", "POL": "matic-network",
}

# Cache
historical_cache: Dict[str, dict] = {}
historical_cache_time: Dict[str, datetime] = {}


class AnalysisService:
    """Teknik analiz servisi"""
    
    def __init__(self):
        self.cache_duration = 3600  # 1 saat
    
    async def fetch_historical_data(self, symbol: str) -> Optional[Dict]:
        """CoinGecko'dan tarihsel veri çek"""
        global historical_cache, historical_cache_time
        
        # Cache kontrolü
        if symbol in historical_cache:
            cache_age = (datetime.utcnow() - historical_cache_time.get(symbol, datetime.min)).total_seconds()
            if cache_age < self.cache_duration:
                return historical_cache[symbol]
        
        coin_id = COINGECKO_IDS.get(symbol)
        if not coin_id:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                    params={"vs_currency": "usd", "days": 365, "interval": "daily"}
                )
                
                if r.status_code != 200:
                    return None
                
                data = r.json()
                prices = data.get("prices", [])
                volumes = data.get("total_volumes", [])
                
                if len(prices) < 30:
                    return None
                
                result = self._calculate_indicators(prices, volumes)
                
                # Cache'e kaydet
                historical_cache[symbol] = result
                historical_cache_time[symbol] = datetime.utcnow()
                
                return result
        
        except Exception as e:
            print(f"[Analysis] Historical data error for {symbol}: {e}")
            return None
    
    def _calculate_indicators(self, prices: List, volumes: List) -> Dict:
        """Teknik indikatörleri hesapla"""
        current_price = prices[-1][1] if prices else 0
        
        def get_change(days_ago):
            if len(prices) > days_ago:
                old = prices[-(days_ago+1)][1]
                return ((current_price - old) / old * 100) if old > 0 else 0
            return None
        
        def calc_rsi(period=14):
            if len(prices) < period + 1:
                return None
            gains, losses = [], []
            for i in range(-period, 0):
                change = prices[i][1] - prices[i-1][1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            if avg_loss == 0:
                return 100
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        
        def calc_ma(period):
            if len(prices) < period:
                return None
            return sum(p[1] for p in prices[-period:]) / period
        
        def calc_ema(period):
            if len(prices) < period:
                return None
            price_list = [p[1] for p in prices]
            multiplier = 2 / (period + 1)
            ema = price_list[0]
            for price in price_list[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            return ema
        
        def calc_macd():
            ema_12 = calc_ema(12)
            ema_26 = calc_ema(26)
            if not ema_12 or not ema_26:
                return None, None, None
            macd_line = ema_12 - ema_26
            return macd_line, None, None
        
        def calc_bollinger(period=20, num_std=2):
            if len(prices) < period:
                return None, None, None, None
            recent_prices = [p[1] for p in prices[-period:]]
            sma = sum(recent_prices) / period
            variance = sum((p - sma) ** 2 for p in recent_prices) / period
            std_dev = variance ** 0.5
            upper = sma + (num_std * std_dev)
            lower = sma - (num_std * std_dev)
            if upper - lower > 0:
                position = (current_price - lower) / (upper - lower) * 100
            else:
                position = 50
            return upper, sma, lower, position
        
        def calc_volatility(days):
            if len(prices) < days:
                return None
            recent = prices[-days:]
            returns = []
            for i in range(1, len(recent)):
                if recent[i-1][1] > 0:
                    ret = (recent[i][1] - recent[i-1][1]) / recent[i-1][1] * 100
                    returns.append(ret)
            if returns:
                avg = sum(returns) / len(returns)
                variance = sum((r - avg) ** 2 for r in returns) / len(returns)
                return variance ** 0.5
            return None
        
        # Calculate all indicators
        rsi = calc_rsi()
        macd_line, macd_signal, macd_hist = calc_macd()
        bb_upper, bb_middle, bb_lower, bb_position = calc_bollinger()
        ma_20 = calc_ma(20)
        ma_50 = calc_ma(50)
        ma_200 = calc_ma(200)
        volatility_7d = calc_volatility(7)
        volatility_30d = calc_volatility(30)
        
        return {
            "current_price": current_price,
            "change_24h": get_change(1),
            "change_7d": get_change(7),
            "change_30d": get_change(30),
            "change_90d": get_change(90),
            "change_365d": get_change(365),
            "rsi": round(rsi, 2) if rsi else None,
            "macd": round(macd_line, 6) if macd_line else None,
            "bollinger": {
                "upper": round(bb_upper, 2) if bb_upper else None,
                "middle": round(bb_middle, 2) if bb_middle else None,
                "lower": round(bb_lower, 2) if bb_lower else None,
                "position": round(bb_position, 2) if bb_position else None
            },
            "ma": {
                "ma_20": round(ma_20, 2) if ma_20 else None,
                "ma_50": round(ma_50, 2) if ma_50 else None,
                "ma_200": round(ma_200, 2) if ma_200 else None
            },
            "volatility": {
                "7d": round(volatility_7d, 2) if volatility_7d else None,
                "30d": round(volatility_30d, 2) if volatility_30d else None
            },
            "trend": self._determine_trend(current_price, ma_20, ma_50, ma_200)
        }
    
    def _determine_trend(self, price, ma_20, ma_50, ma_200) -> str:
        """Trend belirleme"""
        if not all([ma_20, ma_50]):
            return "NEUTRAL"
        
        if price > ma_20 > ma_50:
            return "BULLISH"
        elif price < ma_20 < ma_50:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def generate_signal(self, technical: Dict, futures: Dict = None) -> Dict:
        """
        Sinyal üret
        
        Args:
            technical: Teknik analiz verileri
            futures: Futures verileri (opsiyonel)
            
        Returns:
            Sinyal ve güven skoru
        """
        score = 0
        reasons = []
        
        # RSI analizi (ağırlık: 25)
        rsi = technical.get("rsi")
        if rsi:
            if rsi < 30:
                score += 25
                reasons.append(f"RSI aşırı satım ({rsi:.0f})")
            elif rsi > 70:
                score -= 25
                reasons.append(f"RSI aşırı alım ({rsi:.0f})")
            elif rsi < 45:
                score += 10
            elif rsi > 55:
                score -= 10
        
        # Trend analizi (ağırlık: 20)
        trend = technical.get("trend")
        if trend == "BULLISH":
            score += 20
            reasons.append("Yükseliş trendi")
        elif trend == "BEARISH":
            score -= 20
            reasons.append("Düşüş trendi")
        
        # Bollinger analizi (ağırlık: 15)
        bb_position = technical.get("bollinger", {}).get("position")
        if bb_position is not None:
            if bb_position < 20:
                score += 15
                reasons.append("Bollinger alt bandında")
            elif bb_position > 80:
                score -= 15
                reasons.append("Bollinger üst bandında")
        
        # MACD analizi (ağırlık: 15)
        macd = technical.get("macd")
        if macd is not None:
            if macd > 0:
                score += 10
            else:
                score -= 10
        
        # Futures analizi (ağırlık: 25)
        if futures:
            funding = futures.get("funding_rate", 0)
            ls_ratio = futures.get("long_short_ratio", 1)
            
            # Funding rate
            if funding > 0.05:
                score -= 15
                reasons.append(f"Yüksek funding ({funding:.3f}%)")
            elif funding < -0.05:
                score += 15
                reasons.append(f"Negatif funding ({funding:.3f}%)")
            
            # Long/Short ratio
            if ls_ratio > 2:
                score -= 10
                reasons.append(f"Çok fazla long ({ls_ratio:.2f})")
            elif ls_ratio < 0.5:
                score += 10
                reasons.append(f"Çok fazla short ({ls_ratio:.2f})")
        
        # Sinyal belirleme
        if score >= 30:
            signal = "STRONG_BUY"
            signal_tr = "GÜÇLÜ AL"
        elif score >= 10:
            signal = "BUY"
            signal_tr = "AL"
        elif score <= -30:
            signal = "STRONG_SELL"
            signal_tr = "GÜÇLÜ SAT"
        elif score <= -10:
            signal = "SELL"
            signal_tr = "SAT"
        else:
            signal = "HOLD"
            signal_tr = "BEKLE"
        
        # Güven skoru (0-100)
        confidence = min(100, max(0, 50 + abs(score)))
        
        return {
            "signal": signal,
            "signal_tr": signal_tr,
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
            "technical": technical
        }
    
    def get_coin_category(self, symbol: str) -> str:
        """Coin kategorisini belirle"""
        if symbol in STABLECOINS:
            return "STABLECOIN"
        elif symbol in MEGA_CAP_COINS:
            return "MEGA_CAP"
        elif symbol in LARGE_CAP_COINS:
            return "LARGE_CAP"
        elif symbol in HIGH_RISK_COINS:
            return "HIGH_RISK"
        else:
            return "ALT"
    
    def calculate_risk_level(self, symbol: str, technical: Dict) -> str:
        """Risk seviyesi hesapla"""
        risk_score = 0
        
        # Volatilite
        vol_30d = technical.get("volatility", {}).get("30d", 0)
        if vol_30d:
            if vol_30d > 10:
                risk_score += 30
            elif vol_30d > 5:
                risk_score += 15
        
        # Kategori riski
        category = self.get_coin_category(symbol)
        if category == "HIGH_RISK":
            risk_score += 30
        elif category == "ALT":
            risk_score += 20
        elif category == "LARGE_CAP":
            risk_score += 10
        
        # RSI extreme
        rsi = technical.get("rsi", 50)
        if rsi < 20 or rsi > 80:
            risk_score += 15
        
        if risk_score >= 50:
            return "HIGH"
        elif risk_score >= 25:
            return "MEDIUM"
        else:
            return "LOW"


# Singleton instance
analysis_service = AnalysisService()
