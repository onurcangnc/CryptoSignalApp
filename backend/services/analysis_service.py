# -*- coding: utf-8 -*-
"""
CryptoSignal - Analysis Service v2.0
====================================
Teknik analiz ve sinyal üretimi

Güncellemeler:
- Multi-factor confidence system (faktör uyumu bazlı)
- ATR-based volatility risk scoring
- News sentiment integration
- Gerçek belirsizliği yansıtan confidence
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
    
    def calculate_indicators(self, prices: List, volumes: List = None) -> Dict:
        """
        Public wrapper for technical indicator calculation.

        Args:
            prices: List of [timestamp, price] pairs
            volumes: List of [timestamp, volume] pairs (optional)

        Returns:
            Dict with RSI, MACD, Bollinger, MA, volatility, trend
        """
        return self._calculate_indicators(prices, volumes or [])

    def _calculate_indicators(self, prices: List, volumes: List) -> Dict:
        """Teknik indikatörleri hesapla (internal)"""
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
    
    def generate_signal(self, technical: Dict, futures: Dict = None, news_sentiment: Dict = None) -> Dict:
        """
        Sinyal üret - Multi-Factor Confidence System v2.0

        Args:
            technical: Teknik analiz verileri
            futures: Futures verileri (opsiyonel)
            news_sentiment: Haber sentiment verileri (opsiyonel)

        Returns:
            Sinyal, güven skoru ve faktör detayları
        """
        score = 0
        reasons = []

        # Faktör yönleri - confidence hesaplaması için
        factor_directions = []  # "BUY", "SELL", "NEUTRAL"

        # ============================================
        # 1. RSI ANALİZİ (ağırlık: 25)
        # ============================================
        rsi = technical.get("rsi")
        rsi_direction = "NEUTRAL"
        if rsi:
            if rsi < 30:
                score += 25
                reasons.append(f"RSI aşırı satım ({rsi:.0f})")
                rsi_direction = "BUY"
            elif rsi > 70:
                score -= 25
                reasons.append(f"RSI aşırı alım ({rsi:.0f})")
                rsi_direction = "SELL"
            elif rsi < 45:
                score += 10
                rsi_direction = "BUY"
            elif rsi > 55:
                score -= 10
                rsi_direction = "SELL"
        factor_directions.append(rsi_direction)

        # ============================================
        # 2. TREND ANALİZİ (ağırlık: 20)
        # ============================================
        trend = technical.get("trend")
        trend_direction = "NEUTRAL"
        if trend == "BULLISH":
            score += 20
            reasons.append("Yükseliş trendi")
            trend_direction = "BUY"
        elif trend == "BEARISH":
            score -= 20
            reasons.append("Düşüş trendi")
            trend_direction = "SELL"
        factor_directions.append(trend_direction)

        # ============================================
        # 3. BOLLİNGER ANALİZİ (ağırlık: 15)
        # ============================================
        bb_position = technical.get("bollinger", {}).get("position")
        bb_direction = "NEUTRAL"
        if bb_position is not None:
            if bb_position < 20:
                score += 15
                reasons.append("Bollinger alt bandında")
                bb_direction = "BUY"
            elif bb_position > 80:
                score -= 15
                reasons.append("Bollinger üst bandında")
                bb_direction = "SELL"
        factor_directions.append(bb_direction)

        # ============================================
        # 4. MACD ANALİZİ (ağırlık: 10)
        # ============================================
        macd = technical.get("macd")
        macd_direction = "NEUTRAL"
        if macd is not None:
            if macd > 0:
                score += 10
                macd_direction = "BUY"
            else:
                score -= 10
                macd_direction = "SELL"
        factor_directions.append(macd_direction)

        # ============================================
        # 5. FUTURES ANALİZİ (ağırlık: 20)
        # ============================================
        futures_direction = "NEUTRAL"
        if futures:
            funding = futures.get("funding_rate", 0)
            ls_ratio = futures.get("long_short_ratio", 1)

            # Funding rate
            if funding > 0.05:
                score -= 15
                reasons.append(f"Yüksek funding ({funding:.3f}%)")
                futures_direction = "SELL"
            elif funding < -0.05:
                score += 15
                reasons.append(f"Negatif funding ({funding:.3f}%)")
                futures_direction = "BUY"

            # Long/Short ratio
            if ls_ratio > 2:
                score -= 10
                reasons.append(f"Çok fazla long ({ls_ratio:.2f})")
                if futures_direction == "NEUTRAL":
                    futures_direction = "SELL"
            elif ls_ratio < 0.5:
                score += 10
                reasons.append(f"Çok fazla short ({ls_ratio:.2f})")
                if futures_direction == "NEUTRAL":
                    futures_direction = "BUY"
        factor_directions.append(futures_direction)

        # ============================================
        # 6. HABER SENTİMENT ANALİZİ (ağırlık: 10) - YENİ!
        # ============================================
        news_direction = "NEUTRAL"
        if news_sentiment:
            ns_score = news_sentiment.get("score", 0)
            news_count = news_sentiment.get("news_count", 0)

            # En az 3 haber varsa dikkate al
            if news_count >= 3:
                if ns_score > 0.2:
                    score += 10
                    news_direction = "BUY"
                    reasons.append(f"Haberler olumlu ({news_count} haber)")
                elif ns_score < -0.2:
                    score -= 10
                    news_direction = "SELL"
                    reasons.append(f"Haberler olumsuz ({news_count} haber)")
        factor_directions.append(news_direction)

        # ============================================
        # SİNYAL BELİRLEME (v2.1 - Daha dengeli eşikler)
        # ============================================
        # Eski eşikler çok yüksekti, neredeyse hiç BUY üretmiyordu
        if score >= 25:
            signal = "STRONG_BUY"
            signal_tr = "GÜÇLÜ AL"
        elif score >= 5:
            signal = "BUY"
            signal_tr = "AL"
        elif score <= -25:
            signal = "STRONG_SELL"
            signal_tr = "GÜÇLÜ SAT"
        elif score <= -5:
            signal = "SELL"
            signal_tr = "SAT"
        else:
            signal = "HOLD"
            signal_tr = "BEKLE"

        # ============================================
        # MULTİ-FACTOR CONFIDENCE HESAPLAMA (YENİ!)
        # ============================================
        confidence, confidence_details = self._calculate_multi_factor_confidence(
            factor_directions=factor_directions,
            technical=technical,
            score=score
        )

        return {
            "signal": signal,
            "signal_tr": signal_tr,
            "score": score,
            "confidence": confidence,
            "confidence_details": confidence_details,
            "reasons": reasons,
            "technical": technical
        }

    def _calculate_multi_factor_confidence(
        self,
        factor_directions: List[str],
        technical: Dict,
        score: int
    ) -> tuple:
        """
        Multi-factor confidence hesaplama

        Faktörler:
        1. Faktör Uyumu (30%) - Kaç faktör aynı yönü gösteriyor?
        2. Veri Kalitesi (20%) - Kaç indikatör hesaplanabildi?
        3. Volatilite Cezası (15%) - Yüksek volatilite = düşük confidence
        4. Sinyal Gücü (20%) - Skor büyüklüğü
        5. Trend Netliği (15%) - Trend ne kadar net?

        Returns:
            (confidence_score, details_dict)
        """

        # 1. Faktör Uyumu (max 30 puan)
        non_neutral = [d for d in factor_directions if d != "NEUTRAL"]
        if non_neutral:
            buy_count = sum(1 for d in non_neutral if d == "BUY")
            sell_count = sum(1 for d in non_neutral if d == "SELL")
            dominant_count = max(buy_count, sell_count)
            alignment_ratio = dominant_count / len(non_neutral)
            alignment_score = alignment_ratio * 30
        else:
            alignment_score = 15  # Tüm faktörler neutral
            alignment_ratio = 0.5

        # 2. Veri Kalitesi (max 20 puan)
        indicators = [
            technical.get("rsi"),
            technical.get("macd"),
            technical.get("bollinger", {}).get("position"),
            technical.get("ma", {}).get("ma_20"),
            technical.get("ma", {}).get("ma_50"),
        ]
        available_count = sum(1 for i in indicators if i is not None)
        data_quality_score = (available_count / len(indicators)) * 20

        # 3. Volatilite Cezası (max -15 puan)
        vol_7d = technical.get("volatility", {}).get("7d", 0) or 0
        if vol_7d > 8:
            volatility_penalty = -15
        elif vol_7d > 5:
            volatility_penalty = -10
        elif vol_7d > 3:
            volatility_penalty = -5
        else:
            volatility_penalty = 0

        # 4. Sinyal Gücü (max 20 puan)
        abs_score = abs(score)
        if abs_score >= 40:
            signal_strength_score = 20
        elif abs_score >= 30:
            signal_strength_score = 15
        elif abs_score >= 20:
            signal_strength_score = 10
        elif abs_score >= 10:
            signal_strength_score = 5
        else:
            signal_strength_score = 0

        # 5. Trend Netliği (max 15 puan)
        trend = technical.get("trend", "NEUTRAL")
        ma_20 = technical.get("ma", {}).get("ma_20")
        ma_50 = technical.get("ma", {}).get("ma_50")
        current_price = technical.get("current_price", 0)

        if trend != "NEUTRAL" and ma_20 and ma_50 and current_price:
            # MA'lar arasındaki mesafe yüzdesi
            ma_spread = abs(ma_20 - ma_50) / ma_50 * 100 if ma_50 > 0 else 0
            if ma_spread > 5:
                trend_clarity_score = 15
            elif ma_spread > 2:
                trend_clarity_score = 10
            else:
                trend_clarity_score = 5
        else:
            trend_clarity_score = 0

        # Toplam confidence (base: 30)
        base_confidence = 30
        total_confidence = (
            base_confidence +
            alignment_score +
            data_quality_score +
            volatility_penalty +
            signal_strength_score +
            trend_clarity_score
        )

        # 0-100 arasında sınırla
        confidence = max(0, min(100, round(total_confidence)))

        details = {
            "alignment": round(alignment_score, 1),
            "alignment_ratio": round(alignment_ratio * 100, 0),
            "data_quality": round(data_quality_score, 1),
            "volatility_penalty": volatility_penalty,
            "signal_strength": signal_strength_score,
            "trend_clarity": trend_clarity_score,
            "factors_buy": sum(1 for d in factor_directions if d == "BUY"),
            "factors_sell": sum(1 for d in factor_directions if d == "SELL"),
            "factors_neutral": sum(1 for d in factor_directions if d == "NEUTRAL"),
        }

        return confidence, details
    
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
    
    def calculate_risk_level(self, symbol: str, technical: Dict) -> Dict:
        """
        Risk seviyesi hesapla - ATR/Volatilite bazlı v2.0

        Daha agresif eşikler:
        - HIGH_RISK coinler (SHIB, PEPE vb.) otomatik HIGH
        - 7 günlük volatilite daha önemli (kısa vadeli risk)
        - RSI extreme değerleri riski artırır

        Returns:
            Dict with level, score, and breakdown
        """
        risk_score = 0
        risk_factors = []

        # ============================================
        # 1. VOLATİLİTE ANALİZİ (max 40 puan) - Daha hassas
        # ============================================
        vol_7d = technical.get("volatility", {}).get("7d", 0) or 0
        vol_30d = technical.get("volatility", {}).get("30d", 0) or 0

        # 7 günlük volatilite (kısa vadeli risk) - Daha önemli
        if vol_7d > 10:
            risk_score += 30
            risk_factors.append(f"Çok yüksek 7g volatilite ({vol_7d:.1f}%)")
        elif vol_7d > 7:
            risk_score += 25
            risk_factors.append(f"Yüksek 7g volatilite ({vol_7d:.1f}%)")
        elif vol_7d > 5:
            risk_score += 18
            risk_factors.append(f"Orta 7g volatilite ({vol_7d:.1f}%)")
        elif vol_7d > 3:
            risk_score += 10
        # 7g vol < 3% = düşük volatilite, puan eklenmez

        # 30 günlük volatilite (trend riski)
        if vol_30d > 8:
            risk_score += 10
        elif vol_30d > 5:
            risk_score += 5

        # ============================================
        # 2. KATEGORİ RİSKİ (max 40 puan) - Daha agresif
        # ============================================
        category = self.get_coin_category(symbol)
        if category == "HIGH_RISK":
            risk_score += 40  # Eskiden 30
            risk_factors.append("Yüksek riskli coin kategorisi")
        elif category == "ALT":
            risk_score += 25  # Eskiden 20
            risk_factors.append("Altcoin kategorisi")
        elif category == "LARGE_CAP":
            risk_score += 10
        elif category == "MEGA_CAP":
            risk_score += 5  # BTC, ETH bile minimal risk taşır
        # STABLECOIN = 0 puan

        # ============================================
        # 3. RSI EXTREME (max 15 puan)
        # ============================================
        rsi = technical.get("rsi", 50) or 50
        if rsi < 20 or rsi > 80:
            risk_score += 15
            risk_factors.append(f"RSI aşırı bölgede ({rsi:.0f})")
        elif rsi < 25 or rsi > 75:
            risk_score += 8

        # ============================================
        # 4. FİYAT DEĞİŞİM ANOMALİSİ (max 10 puan)
        # ============================================
        change_24h = technical.get("change_24h", 0) or 0
        if abs(change_24h) > 15:
            risk_score += 10
            risk_factors.append(f"24s aşırı hareket ({change_24h:+.1f}%)")
        elif abs(change_24h) > 10:
            risk_score += 5

        # ============================================
        # RİSK SEVİYESİ BELİRLEME (Daha düşük eşikler)
        # ============================================
        if risk_score >= 40:  # Eskiden 50
            level = "HIGH"
        elif risk_score >= 20:  # Eskiden 25
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "level": level,
            "score": risk_score,
            "factors": risk_factors,
            "category": category,
            "volatility_7d": vol_7d,
            "volatility_30d": vol_30d
        }


# Singleton instance
analysis_service = AnalysisService()
