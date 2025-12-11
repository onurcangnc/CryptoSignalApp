# -*- coding: utf-8 -*-
"""
CryptoSignal - Configuration
============================
Tüm konfigürasyon ve sabitler burada
"""

import os
import secrets

# =============================================================================
# ENVIRONMENT
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "/opt/cryptosignal-app/backend/cryptosignal.db")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# =============================================================================
# APP SETTINGS
# =============================================================================

APP_NAME = "CryptoSignal AI"
APP_VERSION = "6.0"

# JWT Token
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72

# =============================================================================
# LLM LIMITS
# =============================================================================

LLM_LIMITS = {
    "free": 3,
    "pro": 20,
    "admin": 999999
}

# =============================================================================
# TIMEFRAME LABELS
# =============================================================================

TIMEFRAME_LABELS = {
    '1d': '1 Gün',
    '1w': '1 Hafta', 
    '1m': '1 Ay',
    '3m': '3 Ay',
    '6m': '6 Ay',
    '1y': '1 Yıl'
}

# =============================================================================
# COIN LISTS
# =============================================================================

STABLECOINS = {
    'USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'USDP', 'FRAX', 
    'PYUSD', 'FDUSD', 'USDD', 'USDS', 'USD1', 'USDE', 'WBETH'
}

MEGA_CAP_COINS = {'BTC', 'ETH'}

LARGE_CAP_COINS = {
    'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'LINK', 
    'TRX', 'TON', 'SHIB', 'LTC', 'BCH', 'NEAR', 'UNI', 'APT'
}

HIGH_RISK_COINS = {
    'SHIB', 'PEPE', 'FLOKI', 'BONK', 'WIF', 'MEME', 'BOME', 
    'LUNC', 'TURBO', 'LADYS', 'AIDOGE', 'DOGE'
}

FUTURES_COINS = {
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'DOT', 'LINK',
    'MATIC', 'LTC', 'SHIB', 'TRX', 'ATOM', 'UNI', 'ETC', 'XLM', 'NEAR', 'APT',
    'OP', 'ARB', 'SUI', 'FIL', 'AAVE', 'MKR', 'SAND', 'MANA', 'AXS', 'GALA',
    'FET', 'RNDR', 'INJ', 'SEI', 'TIA', 'JUP', 'PYTH', 'WLD', 'STRK', 'PENDLE',
    'BCH', 'ENA', 'PEPE', 'WIF', 'BONK', 'ORDI', 'TAO', 'HBAR', 'ICP', 'IMX'
}

# =============================================================================
# NEWS SOURCES
# =============================================================================

NEWS_FEEDS = [
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss"},
    {"name": "Decrypt", "url": "https://decrypt.co/feed"},
    {"name": "CryptoNews", "url": "https://cryptonews.com/news/feed/"},
    {"name": "BitcoinMagazine", "url": "https://bitcoinmagazine.com/feed"},
    {"name": "TheBlock", "url": "https://www.theblock.co/rss.xml"},
    {"name": "CryptoPotato", "url": "https://cryptopotato.com/feed/"},
    {"name": "UToday", "url": "https://u.today/rss"},
]

# =============================================================================
# SENTIMENT KEYWORDS
# =============================================================================

BULLISH_KEYWORDS = {
    'surge': 0.3, 'rally': 0.3, 'breakout': 0.25, 'bullish': 0.3,
    'soar': 0.3, 'jump': 0.2, 'gain': 0.15, 'rise': 0.15,
    'partnership': 0.25, 'adoption': 0.3, 'etf': 0.35, 'approved': 0.35,
    'institutional': 0.3, 'accumulate': 0.25, 'upgrade': 0.2,
    'launch': 0.2, 'integrate': 0.2, 'milestone': 0.2,
    'all-time high': 0.4, 'ath': 0.35, 'moon': 0.25
}

BEARISH_KEYWORDS = {
    'crash': -0.4, 'dump': -0.35, 'plunge': -0.35, 'bearish': -0.3,
    'fall': -0.2, 'decline': -0.2, 'drop': -0.2, 'sell': -0.15,
    'hack': -0.5, 'exploit': -0.45, 'scam': -0.5, 'fraud': -0.45,
    'lawsuit': -0.35, 'sec': -0.3, 'ban': -0.4, 'regulation': -0.2,
    'liquidation': -0.3, 'bankruptcy': -0.5, 'delay': -0.15,
    'fud': -0.25, 'rug': -0.5, 'ponzi': -0.5
}

# =============================================================================
# COIN SYMBOL MAPPING
# =============================================================================

COIN_SYMBOLS = {
    'bitcoin': 'BTC', 'btc': 'BTC',
    'ethereum': 'ETH', 'eth': 'ETH', 'ether': 'ETH',
    'solana': 'SOL', 'sol': 'SOL',
    'ripple': 'XRP', 'xrp': 'XRP',
    'cardano': 'ADA', 'ada': 'ADA',
    'dogecoin': 'DOGE', 'doge': 'DOGE',
    'bnb': 'BNB', 'binance': 'BNB',
    'polkadot': 'DOT', 'dot': 'DOT',
    'chainlink': 'LINK', 'link': 'LINK',
    'avalanche': 'AVAX', 'avax': 'AVAX',
    'polygon': 'MATIC', 'matic': 'MATIC',
    'litecoin': 'LTC', 'ltc': 'LTC',
    'shiba': 'SHIB', 'shib': 'SHIB',
    'tron': 'TRX', 'trx': 'TRX',
    'cosmos': 'ATOM', 'atom': 'ATOM',
    'uniswap': 'UNI', 'uni': 'UNI',
    'arbitrum': 'ARB', 'arb': 'ARB',
    'optimism': 'OP', 'op': 'OP',
    'near': 'NEAR', 'sui': 'SUI',
    'pepe': 'PEPE', 'bonk': 'BONK',
    'render': 'RNDR', 'rndr': 'RNDR',
    'filecoin': 'FIL', 'fil': 'FIL',
    'aave': 'AAVE', 'maker': 'MKR',
}
