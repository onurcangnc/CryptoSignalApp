# -*- coding: utf-8 -*-
"""
CryptoSignal - Analysis Service v3.0
====================================
Major Fixes:
- TRUE ATR calculation with OHLCV data
- Market Regime aware signal generation
- Dynamic RSI thresholds based on market conditions
- Trend override rules to prevent counter-trend signals
- Lowered base confidence for better accuracy

v3.0 Changes:
- Fixed ATR: Now uses proper High/Low/Close data
- Market Regime: BULL/BEAR/NEUTRAL detection
- Dynamic thresholds: RSI adapts to market conditions
- Trend Override: Don't SELL in bull market just because RSI > 70
"""

import json
import httpx
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta

from database import redis_client
from config import STABLECOINS, MEGA_CAP_COINS, LARGE_CAP_COINS, HIGH_RISK_COINS


# ============================================
# SHARED MULTIPLIER FUNCTIONS (Used by backtest too)
# ============================================

def get_confidence_multipliers(confidence: int) -> Tuple[float, float]:
    """
    Get SL/TP multipliers based on confidence level.
    SHARED between analysis_service and backtest_engine.
    """
    if confidence >= 80:
        return 1.8, 2.5  # High confidence: wider SL, closer TP
    elif confidence >= 60:
        return 2.0, 2.2
    elif confidence >= 40:
        return 2.5, 2.0
    else:
        return 2.5, 2.0


def get_category_adjustments(category: str) -> Tuple[float, float]:
    """
    Get category-based SL/TP adjustment multipliers.
    SHARED between analysis_service and backtest_engine.
    """
    if category == "MEGA_CAP":
        return 0.8, 0.9  # Tighter for stable coins
    elif category == "HIGH_RISK":
        return 1.3, 1.2  # Wider for volatile coins
    return 1.0, 1.0


def get_timeframe_multipliers(timeframe: str) -> Tuple[float, float, str]:
    """
    Get timeframe-based multipliers.
    SHARED between analysis_service and backtest_engine.
    """
    multipliers = {
        "1d": (1.0, 1.0, "1 Günlük"),
        "1w": (1.8, 1.8, "1 Haftalık"),
        "1m": (3.0, 3.0, "1 Aylık"),
        "3m": (4.5, 4.5, "3 Aylık"),
        "6m": (6.0, 6.0, "6 Aylık"),
        "1y": (8.0, 8.0, "1 Yıllık"),
    }
    return multipliers.get(timeframe, (1.0, 1.0, "1 Günlük"))


# ============================================
# MARKET REGIME DETECTION
# ============================================

def get_market_regime(btc_change_7d: float = 0, fear_greed: int = 50) -> str:
    """
    Detect current market regime based on BTC performance and Fear & Greed.

    Returns:
        "BULL" - Strong uptrend, RSI can stay elevated
        "BEAR" - Strong downtrend, RSI can stay depressed
        "NEUTRAL" - Ranging market, use standard thresholds
    """
    if btc_change_7d > 5 and fear_greed > 40:
        return "BULL"
    elif btc_change_7d < -5 and fear_greed < 40:
        return "BEAR"
    return "NEUTRAL"


def get_dynamic_rsi_thresholds(market_regime: str) -> Dict[str, int]:
    """
    Get RSI thresholds adjusted for market regime.

    In BULL markets: RSI can stay 70-85 for weeks, don't sell early
    In BEAR markets: RSI can stay 15-30 for weeks, don't buy early
    """
    if market_regime == "BULL":
        return {
            "extreme_overbought": 85,  # Only sell above 85
            "overbought": 80,          # Mild sell signal
            "neutral_high": 65,        # No signal
            "neutral_low": 40,         # No signal
            "oversold": 35,            # Mild buy signal
            "extreme_oversold": 25     # Strong buy signal
        }
    elif market_regime == "BEAR":
        return {
            "extreme_overbought": 65,  # Sell above 65 in bear market
            "overbought": 55,          # Mild sell signal
            "neutral_high": 45,        # No signal
            "neutral_low": 30,         # No signal
            "oversold": 25,            # Mild buy signal
            "extreme_oversold": 15     # Strong buy signal
        }
    else:  # NEUTRAL
        return {
            "extreme_overbought": 75,
            "overbought": 70,
            "neutral_high": 55,
            "neutral_low": 45,
            "oversold": 30,
            "extreme_oversold": 25
        }

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
    """Teknik analiz servisi - v3.0"""

    def __init__(self):
        self.cache_duration = 3600  # 1 saat
        self.ohlcv_cache: Dict[str, List[Dict]] = {}
        self.ohlcv_cache_time: Dict[str, datetime] = {}

    # ============================================
    # OHLCV DATA FETCHING (NEW in v3.0)
    # ============================================

    async def fetch_ohlcv_data(self, symbol: str, days: int = 90) -> List[Dict]:
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) data from Binance.
        Required for accurate ATR calculation.
        """
        cache_key = f"{symbol}_{days}"
        if cache_key in self.ohlcv_cache:
            cache_age = (datetime.utcnow() - self.ohlcv_cache_time.get(cache_key, datetime.min)).total_seconds()
            if cache_age < self.cache_duration:
                return self.ohlcv_cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.binance.com/api/v3/klines",
                    params={
                        "symbol": f"{symbol}USDT",
                        "interval": "1d",
                        "limit": min(days, 365)
                    }
                )
                if resp.status_code == 200:
                    raw_klines = resp.json()
                    ohlcv = [
                        {
                            "timestamp": k[0],
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": float(k[5])
                        }
                        for k in raw_klines
                    ]
                    self.ohlcv_cache[cache_key] = ohlcv
                    self.ohlcv_cache_time[cache_key] = datetime.utcnow()
                    return ohlcv
        except Exception as e:
            print(f"[Analysis] OHLCV fetch error for {symbol}: {e}")

        return []

    def calc_true_atr(self, ohlcv: List[Dict], period: int = 14) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate TRUE ATR using High/Low/Close data.

        True Range = max(
            High - Low,
            |High - Previous Close|,
            |Low - Previous Close|
        )
        ATR = SMA of True Range over 'period' days
        """
        if len(ohlcv) < period + 1:
            return None, None

        true_ranges = []
        for i in range(1, len(ohlcv)):
            high = ohlcv[i]["high"]
            low = ohlcv[i]["low"]
            prev_close = ohlcv[i-1]["close"]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        if len(true_ranges) < period:
            return None, None

        # SMA of last 'period' true ranges
        atr = sum(true_ranges[-period:]) / period
        current_price = ohlcv[-1]["close"]
        atr_percent = (atr / current_price * 100) if current_price > 0 else 0

        return round(atr, 6), round(atr_percent, 2)

    def calculate_indicators_with_ohlcv(self, ohlcv: List[Dict]) -> Dict:
        """
        Calculate technical indicators using OHLCV data for accurate ATR.
        """
        if not ohlcv or len(ohlcv) < 30:
            return {}

        # Convert to prices list for existing indicator functions
        prices = [[candle["timestamp"], candle["close"]] for candle in ohlcv]

        # Calculate standard indicators
        result = self._calculate_indicators(prices, [])

        # Override ATR with TRUE ATR calculation
        true_atr, true_atr_pct = self.calc_true_atr(ohlcv)
        if true_atr is not None:
            result["volatility"]["atr"] = true_atr
            result["volatility"]["atr_percent"] = true_atr_pct

        return result
    
    async def fetch_historical_data(self, symbol: str) -> Optional[Dict]:
        """CoinGecko'dan tarihsel veri çek"""
        global historical_cache, historical_cache_time
        
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
                
                historical_cache[symbol] = result
                historical_cache_time[symbol] = datetime.utcnow()
                
                return result
        
        except Exception as e:
            print(f"[Analysis] Historical data error for {symbol}: {e}")
            return None
    
    def calculate_indicators(self, prices: List, volumes: List = None) -> Dict:
        """Public wrapper for technical indicator calculation."""
        return self._calculate_indicators(prices, volumes or [])

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
        
        # ============================================
        # ATR HESAPLAMA - v3.0 (FIXED!)
        # ============================================
        def calc_atr(period=14):
            """
            Average True Range calculation.

            NOTE: This version works with close-only data by estimating
            the true range. For accurate ATR, use calc_true_atr() with OHLCV data.

            Estimation method: Use price changes with volatility adjustment
            """
            if len(prices) < period + 1:
                return None, None

            # Calculate daily returns for volatility estimation
            returns = []
            for i in range(-period - 5, 0):
                if i - 1 >= -len(prices):
                    prev_price = prices[i-1][1]
                    curr_price = prices[i][1]
                    if prev_price > 0:
                        daily_return = abs(curr_price - prev_price) / prev_price
                        returns.append(daily_return)

            if not returns:
                return None, None

            # Use average daily range as ATR proxy
            avg_daily_range = sum(returns) / len(returns)

            # ATR = average daily range * current price
            atr = avg_daily_range * current_price
            atr_percent = avg_daily_range * 100

            return atr, atr_percent
        
        # Calculate all indicators
        rsi = calc_rsi()
        macd_line, macd_signal, macd_hist = calc_macd()
        bb_upper, bb_middle, bb_lower, bb_position = calc_bollinger()
        ma_20 = calc_ma(20)
        ma_50 = calc_ma(50)
        ma_200 = calc_ma(200)
        volatility_7d = calc_volatility(7)
        volatility_30d = calc_volatility(30)
        atr, atr_percent = calc_atr(14)
        
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
                "30d": round(volatility_30d, 2) if volatility_30d else None,
                "atr": round(atr, 4) if atr else None,
                "atr_percent": round(atr_percent, 2) if atr_percent else None
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
    
    # ============================================
    # EXIT STRATEGY HESAPLAMA (YENİ!) - v2.1
    # ============================================
    
    # Timeframe bazlı çarpanlar
    TIMEFRAME_MULTIPLIERS = {
        "1d": {"sl": 1.0, "tp": 1.0, "label": "1 Günlük"},
        "1w": {"sl": 1.8, "tp": 1.8, "label": "1 Haftalık"},
        "1m": {"sl": 3.0, "tp": 3.0, "label": "1 Aylık"},
        "3m": {"sl": 4.5, "tp": 4.5, "label": "3 Aylık"},
        "6m": {"sl": 6.0, "tp": 6.0, "label": "6 Aylık"},
        "1y": {"sl": 8.0, "tp": 8.0, "label": "1 Yıllık"},
    }
    
    def calculate_exit_strategy(
        self,
        current_price: float,
        signal: str,
        confidence: int,
        technical: Dict,
        category: str = "ALT",
        timeframe: str = "1d"
    ) -> Dict:
        """
        ATR-based Stop-Loss ve Take-Profit hesapla
        
        Args:
            current_price: Mevcut fiyat
            signal: Sinyal yönü (BUY/SELL)
            confidence: Güven skoru (0-100)
            technical: Teknik analiz verileri
            category: Coin kategorisi
            timeframe: Zaman dilimi (1d, 1w, 1m, 3m, 6m, 1y)
        
        Returns:
            Dict with stop_loss, take_profit, trailing_stop, risk_reward_ratio
        """
        if current_price <= 0:
            return self._default_exit_strategy(current_price, timeframe)
        
        volatility = technical.get("volatility", {})
        atr_percent = volatility.get("atr_percent")
        
        if not atr_percent:
            vol_7d = volatility.get("7d", 3.0) or 3.0
            atr_percent = vol_7d
        
        atr_percent = max(1.5, min(atr_percent, 10.0))
        
        # TIMEFRAME ÇARPANLARI (YENİ!)
        tf_mult = self.TIMEFRAME_MULTIPLIERS.get(timeframe, {"sl": 1.0, "tp": 1.0, "label": "1 Günlük"})
        tf_sl_mult = tf_mult["sl"]
        tf_tp_mult = tf_mult["tp"]
        timeframe_label = tf_mult["label"]
        
        # CONFIDENCE-BASED MULTIPLIERS (Optimized for better TP/SL ratio)
        if confidence >= 80:
            sl_multiplier = 1.8  # Wider SL (was 1.2)
            tp_multiplier = 2.5  # Closer TP (was 3.5)
        elif confidence >= 60:
            sl_multiplier = 2.0  # (was 1.5)
            tp_multiplier = 2.2  # (was 3.0)
        elif confidence >= 40:
            sl_multiplier = 2.5  # (was 2.0)
            tp_multiplier = 2.0  # (was 2.5)
        else:
            sl_multiplier = 2.5
            tp_multiplier = 2.0
        
        # CATEGORY-BASED ADJUSTMENTS
        if category == "MEGA_CAP":
            sl_multiplier *= 0.8
            tp_multiplier *= 0.9
        elif category == "HIGH_RISK":
            sl_multiplier *= 1.3
            tp_multiplier *= 1.2
        
        # TIMEFRAME UYGULAMASI (YENİ!)
        sl_multiplier *= tf_sl_mult
        tp_multiplier *= tf_tp_mult
        
        # HESAPLAMA
        stop_loss_pct = atr_percent * sl_multiplier
        take_profit_pct = atr_percent * tp_multiplier
        
        # Timeframe bazlı min/max sınırlar (YENİ!)
        if timeframe == "1d":
            stop_loss_pct = max(1.0, min(stop_loss_pct, 8.0))
            take_profit_pct = max(2.0, min(take_profit_pct, 20.0))
        elif timeframe == "1w":
            stop_loss_pct = max(3.0, min(stop_loss_pct, 15.0))
            take_profit_pct = max(6.0, min(take_profit_pct, 35.0))
        elif timeframe == "1m":
            stop_loss_pct = max(5.0, min(stop_loss_pct, 25.0))
            take_profit_pct = max(10.0, min(take_profit_pct, 50.0))
        elif timeframe == "3m":
            stop_loss_pct = max(8.0, min(stop_loss_pct, 35.0))
            take_profit_pct = max(16.0, min(take_profit_pct, 70.0))
        elif timeframe == "6m":
            stop_loss_pct = max(10.0, min(stop_loss_pct, 45.0))
            take_profit_pct = max(20.0, min(take_profit_pct, 90.0))
        elif timeframe == "1y":
            stop_loss_pct = max(15.0, min(stop_loss_pct, 60.0))
            take_profit_pct = max(30.0, min(take_profit_pct, 120.0))
        else:
            stop_loss_pct = max(1.0, min(stop_loss_pct, 8.0))
            take_profit_pct = max(2.0, min(take_profit_pct, 20.0))
        
        # R:R RATIO KONTROLÜ (Minimum 1:2)
        risk_reward_ratio = take_profit_pct / stop_loss_pct
        
        if risk_reward_ratio < 2.0:
            take_profit_pct = stop_loss_pct * 2.0
            risk_reward_ratio = 2.0
        
        is_long = signal in ["BUY", "STRONG_BUY", "AL", "GÜÇLÜ AL"]
        
        if is_long:
            stop_loss = current_price * (1 - stop_loss_pct / 100)
            take_profit = current_price * (1 + take_profit_pct / 100)
            trailing_stop_pct = stop_loss_pct * 0.8
            trailing_stop = current_price * (1 - trailing_stop_pct / 100)
        else:
            stop_loss = current_price * (1 + stop_loss_pct / 100)
            take_profit = current_price * (1 - take_profit_pct / 100)
            trailing_stop_pct = stop_loss_pct * 0.8
            trailing_stop = current_price * (1 + trailing_stop_pct / 100)
        
        return {
            "entry_price": round(current_price, 6),
            "stop_loss": round(stop_loss, 6),
            "take_profit": round(take_profit, 6),
            "trailing_stop": round(trailing_stop, 6),
            "stop_loss_pct": round(stop_loss_pct, 2),
            "take_profit_pct": round(take_profit_pct, 2),
            "trailing_stop_pct": round(trailing_stop_pct, 2),
            "risk_reward_ratio": f"1:{risk_reward_ratio:.1f}",
            "atr_percent": round(atr_percent, 2),
            "direction": "LONG" if is_long else "SHORT",
            "confidence_tier": "high" if confidence >= 60 else "medium" if confidence >= 40 else "low",
            "timeframe": timeframe,
            "timeframe_label": timeframe_label
        }
    
    def _default_exit_strategy(self, current_price: float, timeframe: str = "1d") -> Dict:
        """Varsayılan exit strategy"""
        tf_mult = self.TIMEFRAME_MULTIPLIERS.get(timeframe, {"sl": 1.0, "tp": 1.0, "label": "1 Günlük"})
        sl_pct = 3.0 * tf_mult["sl"]
        tp_pct = 6.0 * tf_mult["tp"]
        
        return {
            "entry_price": current_price,
            "stop_loss": current_price * (1 - sl_pct / 100),
            "take_profit": current_price * (1 + tp_pct / 100),
            "trailing_stop": current_price * (1 - sl_pct * 0.8 / 100),
            "stop_loss_pct": sl_pct,
            "take_profit_pct": tp_pct,
            "trailing_stop_pct": sl_pct * 0.8,
            "risk_reward_ratio": "1:2.0",
            "atr_percent": 3.0,
            "direction": "LONG",
            "confidence_tier": "low",
            "timeframe": timeframe,
            "timeframe_label": tf_mult["label"]
        }
    
    def generate_signal(
        self,
        technical: Dict,
        futures: Dict = None,
        news_sentiment: Dict = None,
        market_regime: str = "NEUTRAL"
    ) -> Dict:
        """
        Generate trading signal with Market Regime awareness.

        v3.0 Changes:
        - Dynamic RSI thresholds based on market regime
        - Trend override rule: Don't SELL in bull market just because RSI > 70
        - Better factor weighting
        """
        score = 0
        reasons = []
        factor_directions = []

        # Get dynamic RSI thresholds based on market regime
        rsi_thresholds = get_dynamic_rsi_thresholds(market_regime)
        trend = technical.get("trend", "NEUTRAL")

        # 1. RSI ANALİZİ - WITH DYNAMIC THRESHOLDS
        rsi = technical.get("rsi")
        rsi_direction = "NEUTRAL"
        if rsi:
            # TREND OVERRIDE RULE (v3.0)
            # In bull market with bullish trend, don't sell just because RSI > 70
            if market_regime == "BULL" and trend == "BULLISH" and 70 < rsi < 85:
                # RSI is elevated but trend is strong - HOLD, don't SELL
                rsi_direction = "NEUTRAL"
                reasons.append(f"RSI yüksek ({rsi:.0f}) ama trend güçlü")
            elif market_regime == "BEAR" and trend == "BEARISH" and 15 < rsi < 30:
                # RSI is low but trend is bearish - HOLD, don't BUY
                rsi_direction = "NEUTRAL"
                reasons.append(f"RSI düşük ({rsi:.0f}) ama trend zayıf")
            elif rsi <= rsi_thresholds["extreme_oversold"]:
                score += 25
                reasons.append(f"RSI aşırı satım ({rsi:.0f})")
                rsi_direction = "BUY"
            elif rsi <= rsi_thresholds["oversold"]:
                score += 15
                rsi_direction = "BUY"
            elif rsi >= rsi_thresholds["extreme_overbought"]:
                score -= 25
                reasons.append(f"RSI aşırı alım ({rsi:.0f})")
                rsi_direction = "SELL"
            elif rsi >= rsi_thresholds["overbought"]:
                score -= 15
                rsi_direction = "SELL"
            elif rsi < rsi_thresholds["neutral_low"]:
                score += 8
                rsi_direction = "BUY"
            elif rsi > rsi_thresholds["neutral_high"]:
                score -= 8
                rsi_direction = "SELL"
        factor_directions.append(rsi_direction)

        # 2. TREND ANALİZİ - INCREASED WEIGHT IN v3.0
        trend_direction = "NEUTRAL"
        trend_weight = 25 if market_regime != "NEUTRAL" else 20  # More weight in trending markets
        if trend == "BULLISH":
            score += trend_weight
            reasons.append("Yükseliş trendi")
            trend_direction = "BUY"
        elif trend == "BEARISH":
            score -= trend_weight
            reasons.append("Düşüş trendi")
            trend_direction = "SELL"
        factor_directions.append(trend_direction)

        # 3. BOLLİNGER ANALİZİ
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

        # 4. MACD ANALİZİ
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

        # 5. FUTURES ANALİZİ
        futures_direction = "NEUTRAL"
        if futures:
            funding = futures.get("funding_rate", 0)
            ls_ratio = futures.get("long_short_ratio", 1)

            if funding > 0.05:
                score -= 15
                reasons.append(f"Yüksek funding ({funding:.3f}%)")
                futures_direction = "SELL"
            elif funding < -0.05:
                score += 15
                reasons.append(f"Negatif funding ({funding:.3f}%)")
                futures_direction = "BUY"

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

        # 6. HABER SENTİMENT ANALİZİ
        news_direction = "NEUTRAL"
        if news_sentiment:
            ns_score = news_sentiment.get("score", 0)
            news_count = news_sentiment.get("news_count", 0)

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

        # SİNYAL BELİRLEME - WITH TREND CONFIRMATION (v3.0)
        # Require higher score in counter-trend situations
        min_score_for_buy = 5
        min_score_for_sell = -5

        # Counter-trend signals need higher conviction
        if market_regime == "BEAR" and score > 0:
            min_score_for_buy = 15  # Need stronger signal to buy in bear market
        if market_regime == "BULL" and score < 0:
            min_score_for_sell = -15  # Need stronger signal to sell in bull market

        if score >= 30:
            signal = "STRONG_BUY"
            signal_tr = "GÜÇLÜ AL"
        elif score >= min_score_for_buy:
            signal = "BUY"
            signal_tr = "AL"
        elif score <= -30:
            signal = "STRONG_SELL"
            signal_tr = "GÜÇLÜ SAT"
        elif score <= min_score_for_sell:
            signal = "SELL"
            signal_tr = "SAT"
        else:
            signal = "HOLD"
            signal_tr = "BEKLE"

        confidence, confidence_details = self._calculate_multi_factor_confidence(
            factor_directions=factor_directions,
            technical=technical,
            score=score
        )

        # Add market regime to details
        confidence_details["market_regime"] = market_regime

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
        Multi-factor confidence calculation - v3.0

        Changes:
        - Lowered base confidence from 30 to 10
        - Return 0 confidence if insufficient data (< 3 indicators)
        - More weight on data quality
        """
        non_neutral = [d for d in factor_directions if d != "NEUTRAL"]
        if non_neutral:
            buy_count = sum(1 for d in non_neutral if d == "BUY")
            sell_count = sum(1 for d in non_neutral if d == "SELL")
            dominant_count = max(buy_count, sell_count)
            alignment_ratio = dominant_count / len(non_neutral)
            alignment_score = alignment_ratio * 30
        else:
            alignment_score = 0  # Changed from 15 - no alignment if all neutral
            alignment_ratio = 0

        indicators = [
            technical.get("rsi"),
            technical.get("macd"),
            technical.get("bollinger", {}).get("position"),
            technical.get("ma", {}).get("ma_20"),
            technical.get("ma", {}).get("ma_50"),
        ]
        available_count = sum(1 for i in indicators if i is not None)

        # CRITICAL: Return 0 confidence if insufficient data
        if available_count < 3:
            return 0, {
                "alignment": 0,
                "alignment_ratio": 0,
                "data_quality": 0,
                "volatility_penalty": 0,
                "signal_strength": 0,
                "trend_clarity": 0,
                "factors_buy": sum(1 for d in factor_directions if d == "BUY"),
                "factors_sell": sum(1 for d in factor_directions if d == "SELL"),
                "factors_neutral": sum(1 for d in factor_directions if d == "NEUTRAL"),
                "insufficient_data": True
            }

        # Increased data quality weight (was 20, now 25)
        data_quality_score = (available_count / len(indicators)) * 25

        vol_7d = technical.get("volatility", {}).get("7d", 0) or 0
        if vol_7d > 8:
            volatility_penalty = -15
        elif vol_7d > 5:
            volatility_penalty = -10
        elif vol_7d > 3:
            volatility_penalty = -5
        else:
            volatility_penalty = 0

        abs_score = abs(score)
        if abs_score >= 40:
            signal_strength_score = 25  # Increased from 20
        elif abs_score >= 30:
            signal_strength_score = 20  # Increased from 15
        elif abs_score >= 20:
            signal_strength_score = 12
        elif abs_score >= 10:
            signal_strength_score = 5
        else:
            signal_strength_score = 0

        trend = technical.get("trend", "NEUTRAL")
        ma_20 = technical.get("ma", {}).get("ma_20")
        ma_50 = technical.get("ma", {}).get("ma_50")
        current_price = technical.get("current_price", 0)

        if trend != "NEUTRAL" and ma_20 and ma_50 and current_price:
            ma_spread = abs(ma_20 - ma_50) / ma_50 * 100 if ma_50 > 0 else 0
            if ma_spread > 5:
                trend_clarity_score = 15
            elif ma_spread > 2:
                trend_clarity_score = 10
            else:
                trend_clarity_score = 5
        else:
            trend_clarity_score = 0

        # LOWERED BASE CONFIDENCE (was 30, now 10)
        base_confidence = 10
        total_confidence = (
            base_confidence +
            alignment_score +
            data_quality_score +
            volatility_penalty +
            signal_strength_score +
            trend_clarity_score
        )

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
            "insufficient_data": False
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
        """Risk seviyesi hesapla"""
        risk_score = 0
        risk_factors = []

        vol_7d = technical.get("volatility", {}).get("7d", 0) or 0
        vol_30d = technical.get("volatility", {}).get("30d", 0) or 0

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

        if vol_30d > 8:
            risk_score += 10
        elif vol_30d > 5:
            risk_score += 5

        category = self.get_coin_category(symbol)
        if category == "HIGH_RISK":
            risk_score += 40
            risk_factors.append("Yüksek riskli coin kategorisi")
        elif category == "ALT":
            risk_score += 25
            risk_factors.append("Altcoin kategorisi")
        elif category == "LARGE_CAP":
            risk_score += 10
        elif category == "MEGA_CAP":
            risk_score += 5

        rsi = technical.get("rsi", 50) or 50
        if rsi < 20 or rsi > 80:
            risk_score += 15
            risk_factors.append(f"RSI aşırı bölgede ({rsi:.0f})")
        elif rsi < 25 or rsi > 75:
            risk_score += 8

        change_24h = technical.get("change_24h", 0) or 0
        if abs(change_24h) > 15:
            risk_score += 10
            risk_factors.append(f"24s aşırı hareket ({change_24h:+.1f}%)")
        elif abs(change_24h) > 10:
            risk_score += 5

        if risk_score >= 40:
            level = "HIGH"
        elif risk_score >= 20:
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
