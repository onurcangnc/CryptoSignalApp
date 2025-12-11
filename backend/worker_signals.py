#!/usr/bin/env python3
"""
CryptoSignal - Signals Worker v7.0
==================================
ChatGPT'nin önerdiği FÜZYON MODELİ:

A) Teknik Analiz (40%)
   - RSI, MACD, Bollinger, EMA, Trend

B) On-chain + Order Book + Funding (30%)
   - L/S Ratio, Funding Rate, Order Book Delta

C) AI Haber Analizi + Sentiment (30%)
   - AI-powered haber sentiment
   - Fear & Greed Index
   - Coin bazlı haber etkisi

Düzeltmeler:
- Daha dengeli AL/SAT dağılımı
- 6 zaman periyodu desteği
- AI haber entegrasyonu
- Gerçekçi risk skorları
"""

import json
import time
import redis
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

# Configuration
REDIS_PASS = "3f9af2788cb89aa74c06bd48dd290658"
r = redis.Redis(host='localhost', port=6379, password=REDIS_PASS, decode_responses=True)

# Ayarlar
MAX_COINS = 500
UPDATE_INTERVAL = 1  # 5 saniye - gerçek zamanlı sinyal güncellemesi
BINANCE_KLINES_COINS = 100

STABLECOINS = {'USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'USDP', 'FRAX', 'PYUSD', 'FDUSD', 'USDD', 'USDS', 'USD1', 'USDE', 'WBETH'}

# Coin kategorileri
MEGA_CAP = {'BTC', 'ETH'}
LARGE_CAP = {'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'LINK', 'TRX', 'TON', 'LTC', 'BCH'}
HIGH_RISK = {'SHIB', 'PEPE', 'FLOKI', 'BONK', 'WIF', 'MEME', 'TURBO', 'LUNC'}

FUTURES_COINS = {
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'DOT', 'LINK',
    'LTC', 'SHIB', 'TRX', 'ATOM', 'UNI', 'ETC', 'XLM', 'NEAR', 'APT', 'OP',
    'ARB', 'SUI', 'FIL', 'AAVE', 'MKR', 'SAND', 'MANA', 'AXS', 'GALA', 'FET',
    'RNDR', 'INJ', 'SEI', 'TIA', 'JUP', 'PYTH', 'WLD', 'STRK', 'PENDLE', 'BCH',
    'ENA', 'PEPE', 'WIF', 'BONK', 'TAO', 'HBAR', 'ICP', 'IMX', 'ORDI'
}

# Zaman periyotları
TIMEFRAMES = {
    '1d': {'interval': '1h', 'limit': 24, 'label': '1 Gün'},
    '1w': {'interval': '4h', 'limit': 42, 'label': '1 Hafta'},
    '1m': {'interval': '1d', 'limit': 30, 'label': '1 Ay'},
    '3m': {'interval': '1d', 'limit': 90, 'label': '3 Ay'},
    '6m': {'interval': '1d', 'limit': 180, 'label': '6 Ay'},
    '1y': {'interval': '1w', 'limit': 52, 'label': '1 Yıl'},
}

# ============ AĞIRLIKLAR (ChatGPT Füzyon Modeli) ============
# A) Teknik: 40% | B) On-chain+OB+Funding: 30% | C) Haber+Sentiment: 30%

def get_weights(symbol: str) -> Dict[str, float]:
    """Coin kategorisine göre ağırlıklar"""
    if symbol in MEGA_CAP:
        return {
            'technical': 0.35,      # RSI, MACD, BB, Trend
            'futures': 0.15,        # L/S Ratio
            'funding': 0.15,        # Funding Rate
            'orderbook': 0.10,      # Order Book Delta
            'ai_news': 0.15,        # AI Haber Sentiment
            'market': 0.05,         # Fear & Greed
            'momentum': 0.05        # 24h Change
        }
    elif symbol in LARGE_CAP:
        return {
            'technical': 0.35,
            'futures': 0.12,
            'funding': 0.12,
            'orderbook': 0.10,
            'ai_news': 0.18,
            'market': 0.05,
            'momentum': 0.08
        }
    elif symbol in HIGH_RISK:
        return {
            'technical': 0.30,
            'futures': 0.10,
            'funding': 0.08,
            'orderbook': 0.08,
            'ai_news': 0.20,        # Meme coin'ler habere duyarlı
            'market': 0.08,
            'momentum': 0.16        # Momentum önemli
        }
    else:
        return {
            'technical': 0.35,
            'futures': 0.12,
            'funding': 0.12,
            'orderbook': 0.08,
            'ai_news': 0.18,
            'market': 0.07,
            'momentum': 0.08
        }


# Cache
klines_cache: Dict[str, Tuple[List, float]] = {}


# =============================================================================
# TECHNICAL INDICATORS
# =============================================================================

def calculate_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_ema(data: List[float], period: int) -> List[float]:
    if len(data) < period:
        return []
    
    multiplier = 2 / (period + 1)
    ema_values = [sum(data[:period]) / period]
    
    for price in data[period:]:
        ema = (price - ema_values[-1]) * multiplier + ema_values[-1]
        ema_values.append(ema)
    
    return ema_values


def calculate_macd(closes: List[float]) -> Tuple[str, float]:
    if len(closes) < 35:
        return 'NEUTRAL', 0
    
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    
    if not ema12 or not ema26:
        return 'NEUTRAL', 0
    
    offset = len(ema12) - len(ema26)
    macd_values = [ema12[i + offset] - ema26[i] for i in range(len(ema26))]
    
    if len(macd_values) < 9:
        return 'NEUTRAL', 0
    
    signal_values = calculate_ema(macd_values, 9)
    if not signal_values:
        return 'NEUTRAL', 0
    
    macd_line = macd_values[-1]
    signal_line = signal_values[-1]
    histogram = macd_line - signal_line
    
    # Crossover detection
    if len(macd_values) >= 2 and len(signal_values) >= 2:
        prev_macd = macd_values[-2]
        prev_signal = signal_values[-2]
        
        if prev_macd <= prev_signal and macd_line > signal_line:
            return 'BULLISH_CROSS', histogram
        elif prev_macd >= prev_signal and macd_line < signal_line:
            return 'BEARISH_CROSS', histogram
    
    return ('BULLISH' if histogram > 0 else 'BEARISH'), histogram


def calculate_bollinger(closes: List[float]) -> float:
    if len(closes) < 20:
        return 0
    
    recent = closes[-20:]
    middle = sum(recent) / 20
    std = math.sqrt(sum((x - middle) ** 2 for x in recent) / 20)
    
    if std == 0:
        return 0
    
    return max(-1, min(1, (closes[-1] - middle) / (2 * std)))


def calculate_trend(closes: List[float]) -> Tuple[str, float]:
    if len(closes) < 50:
        return 'NEUTRAL', 0
    
    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50
    current = closes[-1]
    
    trend_strength = ((sma20 - sma50) / sma50) * 100 if sma50 > 0 else 0
    
    if current > sma20 > sma50:
        return 'STRONG_UP', trend_strength
    elif current > sma20:
        return 'UP', trend_strength
    elif current < sma20 < sma50:
        return 'STRONG_DOWN', trend_strength
    elif current < sma20:
        return 'DOWN', trend_strength
    
    return 'NEUTRAL', trend_strength


def calculate_volatility(closes: List[float]) -> float:
    if len(closes) < 15:
        return 5.0
    
    returns = []
    for i in range(1, min(15, len(closes))):
        if closes[i-1] > 0:
            ret = abs((closes[i] - closes[i-1]) / closes[i-1] * 100)
            returns.append(ret)
    
    return sum(returns) / len(returns) if returns else 5.0


# =============================================================================
# DATA FETCHERS
# =============================================================================

def get_binance_klines(symbol: str, interval: str = '1h', limit: int = 100) -> Optional[List]:
    cache_key = f"{symbol}_{interval}_{limit}"
    now = time.time()
    
    if cache_key in klines_cache:
        data, ts = klines_cache[cache_key]
        if now - ts < 60:
            return data
    
    try:
        resp = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": f"{symbol}USDT", "interval": interval, "limit": limit},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            klines_cache[cache_key] = (data, now)
            return data
    except:
        pass
    
    return klines_cache.get(cache_key, (None,))[0]


def get_all_funding_rates() -> Dict:
    try:
        resp = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=10)
        if resp.status_code == 200:
            result = {}
            for item in resp.json():
                symbol = item['symbol'].replace('USDT', '').replace('PERP', '')
                rate = float(item.get('lastFundingRate', 0)) * 100
                
                if rate >= 0.08:
                    signal, extreme = 'STRONG_BEARISH', True
                elif rate >= 0.04:
                    signal, extreme = 'BEARISH', False
                elif rate <= -0.04:
                    signal, extreme = 'STRONG_BULLISH', True
                elif rate <= -0.02:
                    signal, extreme = 'BULLISH', False
                else:
                    signal, extreme = 'NEUTRAL', False
                
                result[symbol] = {'rate': rate, 'signal': signal, 'extreme': extreme}
            return result
    except:
        pass
    return {}


def get_orderbook(symbol: str) -> Optional[Dict]:
    if symbol not in FUTURES_COINS:
        return None
    
    try:
        resp = requests.get(
            "https://fapi.binance.com/fapi/v1/depth",
            params={"symbol": f"{symbol}USDT", "limit": 20},
            timeout=3
        )
        if resp.status_code == 200:
            data = resp.json()
            bid_vol = sum(float(b[1]) for b in data['bids'][:10])
            ask_vol = sum(float(a[1]) for a in data['asks'][:10])
            
            total = bid_vol + ask_vol
            if total == 0:
                return None
            
            imbalance = (bid_vol - ask_vol) / total * 100
            
            if imbalance > 20:
                signal = 'STRONG_BUY'
            elif imbalance > 8:
                signal = 'BUY'
            elif imbalance < -20:
                signal = 'STRONG_SELL'
            elif imbalance < -8:
                signal = 'SELL'
            else:
                signal = 'NEUTRAL'
            
            return {'imbalance': round(imbalance, 1), 'signal': signal}
    except:
        pass
    return None


def get_ai_news_sentiment(symbol: str) -> Dict:
    """AI haber sentiment'ini Redis'ten al"""
    try:
        ai_sentiments = r.get("ai_coin_sentiments")
        if ai_sentiments:
            data = json.loads(ai_sentiments)
            if symbol in data:
                return data[symbol]
    except:
        pass
    
    # Fallback: Eski keyword-based sistem
    try:
        news_raw = r.get("news_db")
        if news_raw:
            news_list = json.loads(news_raw)
            if isinstance(news_list, dict):
                news_list = list(news_list.values())
            
            relevant = [n for n in news_list if symbol in n.get('coins', []) or symbol.lower() in n.get('title', '').lower()]
            
            if relevant:
                bullish = sum(1 for n in relevant if n.get('sentiment') == 'bullish')
                bearish = sum(1 for n in relevant if n.get('sentiment') == 'bearish')
                total = len(relevant)
                
                if bullish > bearish:
                    sentiment = 'BULLISH'
                    score = bullish / total
                elif bearish > bullish:
                    sentiment = 'BEARISH'
                    score = -bearish / total
                else:
                    sentiment = 'NEUTRAL'
                    score = 0
                
                return {
                    'sentiment': sentiment,
                    'avg_score': score,
                    'count': total,
                    'bullish': bullish,
                    'bearish': bearish
                }
    except:
        pass
    
    return {'sentiment': 'NEUTRAL', 'avg_score': 0, 'count': 0}


# =============================================================================
# RISK CALCULATION
# =============================================================================

def calculate_risk(symbol: str, volatility: float, market_cap: float, 
                   change_24h: float, funding: Optional[Dict]) -> Tuple[str, int, List[str]]:
    risk_score = 0
    factors = []
    
    # Volatility (0-30)
    if volatility > 12:
        risk_score += 30
        factors.append(f"Yüksek volatilite ({volatility:.1f}%)")
    elif volatility > 7:
        risk_score += 15
    elif volatility > 4:
        risk_score += 5
    
    # Market cap (0-30)
    if market_cap < 50_000_000:
        risk_score += 30
        factors.append("Çok düşük market cap")
    elif market_cap < 200_000_000:
        risk_score += 22
        factors.append("Düşük market cap")
    elif market_cap < 1_000_000_000:
        risk_score += 12
    elif market_cap < 10_000_000_000:
        risk_score += 5
    
    # High risk coin (0-20)
    if symbol in HIGH_RISK:
        risk_score += 20
        factors.append("Memecoin / Yüksek risk")
    
    # Price shock (0-15)
    if abs(change_24h) > 20:
        risk_score += 15
        factors.append(f"Ani fiyat hareketi ({change_24h:+.1f}%)")
    elif abs(change_24h) > 12:
        risk_score += 8
    
    # Extreme funding (0-10)
    if funding and funding.get('extreme'):
        risk_score += 10
        factors.append(f"Ekstrem funding ({funding.get('rate', 0):+.3f}%)")
    
    # Risk level
    if risk_score >= 55:
        level = "HIGH"
    elif risk_score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"
    
    return level, risk_score, factors[:4]


# =============================================================================
# SIGNAL GENERATION
# =============================================================================

def generate_signal(symbol: str, coin_data: Dict, futures: Dict, 
                    fear_greed: Dict, funding_rates: Dict, timeframe: str = '1d') -> Dict:
    """Ana sinyal üretici"""
    
    price = coin_data.get('price', 0)
    change_24h = coin_data.get('change_24h', 0)
    change_7d = coin_data.get('change_7d', 0)
    market_cap = coin_data.get('market_cap', 0) or 0
    volume = coin_data.get('volume_24h', 0) or coin_data.get('volume', 0) or 0
    
    weights = get_weights(symbol)
    scores = {k: 0 for k in weights}
    reasons = []
    data_quality = 0
    
    tf_config = TIMEFRAMES.get(timeframe, TIMEFRAMES['1d'])
    
    # ============ A) TEKNİK ANALİZ (40%) ============
    rsi = 50
    macd_signal = 'NEUTRAL'
    bb_position = 0
    trend = 'NEUTRAL'
    volatility = 5.0
    
    klines = None
    if symbol in FUTURES_COINS or symbol in MEGA_CAP or symbol in LARGE_CAP:
        klines = get_binance_klines(symbol, tf_config['interval'], tf_config['limit'])
    
    if klines and len(klines) >= 20:
        closes = [float(k[4]) for k in klines]
        data_quality += 40
        
        # RSI
        rsi = calculate_rsi(closes)
        if rsi < 30:
            scores['technical'] += 40
            reasons.append(f"RSI aşırı satım ({rsi:.0f})")
        elif rsi < 38:
            scores['technical'] += 20
            reasons.append(f"RSI düşük ({rsi:.0f})")
        elif rsi > 70:
            scores['technical'] -= 40
            reasons.append(f"RSI aşırı alım ({rsi:.0f})")
        elif rsi > 62:
            scores['technical'] -= 20
            reasons.append(f"RSI yüksek ({rsi:.0f})")
        
        # MACD
        macd_signal, histogram = calculate_macd(closes)
        if macd_signal == 'BULLISH_CROSS':
            scores['technical'] += 30
            reasons.append("MACD bullish cross")
        elif macd_signal == 'BEARISH_CROSS':
            scores['technical'] -= 30
            reasons.append("MACD bearish cross")
        elif macd_signal == 'BULLISH':
            scores['technical'] += 12
        elif macd_signal == 'BEARISH':
            scores['technical'] -= 12
        
        # Bollinger
        bb_position = calculate_bollinger(closes)
        if bb_position < -0.75:
            scores['technical'] += 25
            reasons.append("BB alt bandında")
        elif bb_position > 0.75:
            scores['technical'] -= 25
            reasons.append("BB üst bandında")
        
        # Trend
        trend, trend_str = calculate_trend(closes)
        if trend == 'STRONG_UP':
            scores['technical'] += 20
            reasons.append("Güçlü yükseliş trendi")
        elif trend == 'UP':
            scores['technical'] += 10
        elif trend == 'STRONG_DOWN':
            scores['technical'] -= 20
            reasons.append("Güçlü düşüş trendi")
        elif trend == 'DOWN':
            scores['technical'] -= 10
        
        volatility = calculate_volatility(closes)
    
    # ============ B) ON-CHAIN + OB + FUNDING (30%) ============
    
    # Futures L/S Ratio
    coin_futures = futures.get(symbol, {})
    ls_ratio = coin_futures.get('long_short_ratio', 1.0)
    
    if ls_ratio and ls_ratio != 1.0:
        data_quality += 15
        if ls_ratio > 2.5:
            scores['futures'] -= 35
            reasons.append(f"Aşırı long (L/S: {ls_ratio:.1f})")
        elif ls_ratio > 1.8:
            scores['futures'] -= 18
        elif ls_ratio < 0.5:
            scores['futures'] += 35
            reasons.append(f"Short squeeze (L/S: {ls_ratio:.1f})")
        elif ls_ratio < 0.7:
            scores['futures'] += 18
    
    # Funding Rate
    funding = funding_rates.get(symbol)
    if funding:
        data_quality += 12
        f_signal = funding.get('signal', 'NEUTRAL')
        f_rate = funding.get('rate', 0)
        
        if f_signal == 'STRONG_BULLISH':
            scores['funding'] += 40
            reasons.append(f"Negatif funding ({f_rate:+.3f}%)")
        elif f_signal == 'BULLISH':
            scores['funding'] += 20
        elif f_signal == 'STRONG_BEARISH':
            scores['funding'] -= 40
            reasons.append(f"Yüksek funding ({f_rate:+.3f}%)")
        elif f_signal == 'BEARISH':
            scores['funding'] -= 20
    
    # Order Book
    orderbook = get_orderbook(symbol)
    if orderbook:
        data_quality += 10
        ob_signal = orderbook.get('signal', 'NEUTRAL')
        imb = orderbook.get('imbalance', 0)
        
        if ob_signal == 'STRONG_BUY':
            scores['orderbook'] += 35
            reasons.append(f"Güçlü alım (OB: +{imb:.0f}%)")
        elif ob_signal == 'BUY':
            scores['orderbook'] += 18
        elif ob_signal == 'STRONG_SELL':
            scores['orderbook'] -= 35
            reasons.append(f"Güçlü satış (OB: {imb:.0f}%)")
        elif ob_signal == 'SELL':
            scores['orderbook'] -= 18
    
    # ============ C) HABER + SENTIMENT (30%) ============
    
    # AI News Sentiment
    news_data = get_ai_news_sentiment(symbol)
    if news_data.get('count', 0) > 0:
        data_quality += 15
        n_sentiment = news_data.get('sentiment', 'NEUTRAL')
        n_score = news_data.get('avg_score', 0)
        n_count = news_data.get('count', 0)
        
        if n_sentiment == 'BULLISH':
            scores['ai_news'] += min(40, 20 + n_count * 5)
            reasons.append(f"Olumlu haberler ({news_data.get('bullish', 0)}/{n_count})")
        elif n_sentiment == 'BEARISH':
            scores['ai_news'] -= min(40, 20 + n_count * 5)
            reasons.append(f"Olumsuz haberler ({news_data.get('bearish', 0)}/{n_count})")
    
    # Market Sentiment (Fear & Greed)
    fg_value = fear_greed.get('value', 50) if fear_greed else 50
    data_quality += 5
    
    if fg_value < 25:
        scores['market'] += 30
        reasons.append(f"Extreme Fear ({fg_value})")
    elif fg_value < 40:
        scores['market'] += 15
    elif fg_value > 75:
        scores['market'] -= 30
        reasons.append(f"Extreme Greed ({fg_value})")
    elif fg_value > 60:
        scores['market'] -= 15
    
    # Momentum
    if change_24h < -12:
        scores['momentum'] += 30
        reasons.append(f"Sert düşüş ({change_24h:.1f}%)")
    elif change_24h < -6:
        scores['momentum'] += 15
    elif change_24h > 15:
        scores['momentum'] -= 30
        reasons.append(f"Aşırı yükseliş ({change_24h:.1f}%)")
    elif change_24h > 8:
        scores['momentum'] -= 15
    
    # ============ FINAL SKOR ============
    weighted_score = sum(scores[k] * weights[k] for k in scores)
    normalized = max(-100, min(100, weighted_score))
    
    # ============ SİNYAL (Düşürülmüş threshold'lar) ============
    if normalized >= 20:
        signal, signal_tr = "STRONG_BUY", "GÜÇLÜ AL"
    elif normalized >= 8:
        signal, signal_tr = "BUY", "AL"
    elif normalized <= -20:
        signal, signal_tr = "STRONG_SELL", "GÜÇLÜ SAT"
    elif normalized <= -8:
        signal, signal_tr = "SELL", "SAT"
    else:
        signal, signal_tr = "HOLD", "BEKLE"
    
    # Reason yoksa ekle
    if not reasons:
        if normalized > 3:
            reasons.append("Hafif pozitif momentum")
        elif normalized < -3:
            reasons.append("Hafif negatif momentum")
        else:
            reasons.append("Nötr piyasa koşulları")
    
    # Risk
    risk_level, risk_score, risk_factors = calculate_risk(
        symbol, volatility, market_cap, change_24h, funding
    )
    
    # Confidence
    base_conf = min(92, max(45, 50 + data_quality * 0.5))
    strength_bonus = min(15, abs(normalized) * 0.25)
    confidence = min(92, base_conf + strength_bonus)
    
    if risk_level == "HIGH":
        confidence = min(confidence, 65)
    elif risk_level == "MEDIUM":
        confidence = min(confidence, 78)
    
    # Category
    category = 'MEGA_CAP' if symbol in MEGA_CAP else \
               'LARGE_CAP' if symbol in LARGE_CAP else \
               'MEME' if symbol in HIGH_RISK else 'ALT'
    
    return {
        'symbol': symbol,
        'signal': signal,
        'signal_tr': signal_tr,
        'confidence': round(confidence),
        'score': round(normalized, 1),
        'simple_reason': reasons[0] if reasons else "Nötr piyasa",
        'reasons': reasons[:5],
        'category': category,
        'timeframe': timeframe,
        
        'risk_level': risk_level,
        'risk_score': risk_score,
        'risk_factors': risk_factors,
        
        'technical': {
            'rsi': round(rsi, 1),
            'macd_signal': macd_signal,
            'bb_position': round(bb_position, 2),
            'trend': trend,
            'volatility': round(volatility, 2)
        },
        
        'futures': {'long_short_ratio': ls_ratio},
        'funding': funding or {'rate': 0, 'signal': 'UNKNOWN'},
        'orderbook': orderbook or {'imbalance': 0, 'signal': 'UNKNOWN'},
        'news_sentiment': news_data,
        'market_sentiment': {'fear_greed': fg_value},
        
        'price': price,
        'change_24h': change_24h,
        'change_7d': change_7d,
        'market_cap': market_cap,
        'volume_24h': volume,
        
        'weights_used': weights,
        'data_quality': data_quality,
        'generated_at': datetime.utcnow().isoformat() + 'Z'
    }


# =============================================================================
# MAIN
# =============================================================================

def run():
    print("=" * 70)
    print("CryptoSignal - Signals Worker v7.0 (FUSION MODEL)")
    print("=" * 70)
    print("ChatGPT Füzyon Modeli:")
    print("  A) Teknik Analiz: 40% (RSI, MACD, BB, Trend)")
    print("  B) On-chain + OB + Funding: 30%")
    print("  C) AI Haber + Sentiment: 30%")
    print("=" * 70)
    print(f"  📊 Max coins: {MAX_COINS}")
    print(f"  ⏱️  Update: {UPDATE_INTERVAL}s")
    print(f"  📈 Timeframes: {', '.join(TIMEFRAMES.keys())}")
    print("=" * 70)
    
    while True:
        try:
            start = time.time()
            print(f"\n{datetime.now().strftime('%H:%M:%S')} - Generating signals...")
            
            # Load data
            prices_raw = r.get("prices_data")
            if not prices_raw:
                print("⚠️ No prices data")
                time.sleep(30)
                continue
            
            prices = json.loads(prices_raw)
            futures = json.loads(r.get("futures_data") or "{}")
            fear_greed = json.loads(r.get("fear_greed") or "{}")
            
            # Funding rates
            funding_rates = get_all_funding_rates()
            print(f"  📊 Funding: {len(funding_rates)} coins")
            
            # Filter coins
            coins = []
            for symbol, data in prices.items():
                if symbol not in STABLECOINS and data.get('price', 0) > 0:
                    coins.append({'symbol': symbol, **data})
            
            coins = sorted(coins, key=lambda x: x.get('market_cap', 0) or 0, reverse=True)[:MAX_COINS]
            print(f"  📊 Processing {len(coins)} coins...")
            
            # Generate for all timeframes
            all_signals = {}
            
            for tf in TIMEFRAMES.keys():
                signals = {}
                stats = {'STRONG_BUY': 0, 'BUY': 0, 'HOLD': 0, 'SELL': 0, 'STRONG_SELL': 0}
                risk_stats = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
                
                for i, coin in enumerate(coins):
                    sym = coin.get('symbol', '')
                    
                    if i % 100 == 0 and i > 0:
                        print(f"     [{tf}] {i}/{len(coins)}...")
                    
                    sig = generate_signal(sym, coin, futures, fear_greed, funding_rates, tf)
                    signals[sym] = sig
                    stats[sig['signal']] += 1
                    risk_stats[sig['risk_level']] += 1
                    
                    if i < BINANCE_KLINES_COINS:
                        time.sleep(0.015)
                
                all_signals[tf] = {
                    'signals': signals,
                    'stats': stats,
                    'risk_stats': risk_stats,
                    'count': len(signals)
                }
                
                # Stats
                buy = stats['STRONG_BUY'] + stats['BUY']
                sell = stats['STRONG_SELL'] + stats['SELL']
                print(f"     [{tf}] 🟢 {buy} | 🟡 {stats['HOLD']} | 🔴 {sell}")
            
            # Save to Redis
            r.set("signals_data", json.dumps(all_signals['1d']['signals']))
            r.set("signals_stats", json.dumps(all_signals['1d']['stats']))
            r.set("signals_risk_stats", json.dumps(all_signals['1d']['risk_stats']))
            r.set("signals_all_timeframes", json.dumps(all_signals))
            r.set("signals_updated", datetime.utcnow().isoformat())
            r.set("signals_count", len(coins))
            r.set("funding_rates", json.dumps(funding_rates))
            
            # Summary
            elapsed = time.time() - start
            print(f"\n{'='*55}")
            print(f"✅ COMPLETED in {elapsed:.1f}s")
            
            for sym in ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE']:
                if sym in all_signals['1d']['signals']:
                    s = all_signals['1d']['signals'][sym]
                    print(f"   {sym:5s}: {s['signal_tr']:8s} ({s['confidence']}%) - {s['simple_reason'][:40]}")
            
            wait = max(1, UPDATE_INTERVAL - elapsed)
            print(f"\n⏳ Next in {wait:.0f}s...")
            time.sleep(wait)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(30)


if __name__ == "__main__":
    run()