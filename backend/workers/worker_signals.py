#!/usr/bin/env python3
"""
CryptoSignal - Signal Generator Worker v2.0
===========================================
ATR-based Exit Strategy + Signal Tracking entegrasyonu

v2.0 Güncellemeler:
- Exit Strategy hesaplama ve kaydetme
- Signal Tracker entegrasyonu (her 60 saniyede çıkış kontrolü)
- Dinamik SL/TP (ATR bazlı)
- Trailing Stop desteği
- Minimum 1:2 R:R zorunluluğu

v1.6 Özellikler (korundu):
- Multi-factor confidence system
- Quality Gate filtresi
- Stablecoin/Wrapped token filtresi
- Multi-source historical data
"""

import asyncio
import json
import redis
import httpx
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# Parent path ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analysis_service import AnalysisService, get_market_regime
from database import save_signal_track
from config import SKIP_SIGNAL_COINS, STABLECOINS, WRAPPED_TOKENS

# Redis connection
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    password=REDIS_PASSWORD
)

# Config
UPDATE_INTERVAL = 300  # 5 dakika
SIGNAL_CHECK_INTERVAL = 60  # 60 saniye (exit kontrolü)
TIMEFRAMES = ["1d", "1w", "1m", "3m", "6m", "1y"]
TIMEFRAME_LABELS = {
    "1d": "1 Günlük",
    "1w": "1 Haftalık",
    "1m": "1 Aylık",
    "3m": "3 Aylık",
    "6m": "6 Aylık",
    "1y": "1 Yıllık"
}


# Historical data caching
HISTORICAL_CACHE_TTL = 3600  # Cache historical data for 1 hour

# Wrapped token mapping - use underlying asset data
WRAPPED_TOKEN_MAP = {
    # Wrapped BTC variants -> use BTC data
    "WBTC": "BTC", "TBTC": "BTC", "RENBTC": "BTC", "HBTC": "BTC",
    "SBTC": "BTC", "OBTC": "BTC", "PBTC": "BTC", "BTCB": "BTC",
    "CBBTC": "BTC", "LBTC": "BTC", "FBTC": "BTC", "SOLVBTC": "BTC",
    "CLBTC": "BTC",
    # Wrapped ETH variants -> use ETH data
    "WETH": "ETH", "STETH": "ETH", "WSTETH": "ETH", "CBETH": "ETH",
    "RETH": "ETH", "FRXETH": "ETH", "SFRXETH": "ETH", "METH": "ETH",
    "WEETH": "ETH", "EETH": "ETH", "RSETH": "ETH", "EZETH": "ETH",
    "SWETH": "ETH", "OSETH": "ETH", "ANKRETH": "ETH", "BETH": "ETH",
    "WBETH": "ETH",
    # Wrapped BNB variants -> use BNB data
    "WBNB": "BNB", "SBNB": "BNB", "ABNB": "BNB",
    # Wrapped SOL variants -> use SOL data
    "WSOL": "SOL", "MSOL": "SOL", "JITOSOL": "SOL", "BNSOL": "SOL",
    "JSOL": "SOL", "STSOL": "SOL",
    # Wrapped AVAX -> use AVAX data
    "WAVAX": "AVAX", "SAVAX": "AVAX",
    # Wrapped MATIC/POL -> use POL data
    "WMATIC": "POL", "STMATIC": "POL",
    # Wrapped FTM -> use FTM data
    "WFTM": "FTM",
}

# CoinGecko rate limiting
COINGECKO_SEMAPHORE = asyncio.Semaphore(10)  # Increased for better throughput
COINGECKO_BACKOFF = 1.0  # Reduced backoff time

# AI/Yapay Zeka Coinleri - Her zaman işlenecek
AI_COINS = {
    # Büyük AI Projeleri
    "FET", "RNDR", "TAO", "AGIX", "OCEAN", "WLD", "AKT", "ARKM",
    # Orta Ölçekli AI
    "AIOZ", "NMR", "ALI", "RSS3", "CGPT", "PAAL", "OLAS", "0X0",
    # AI Altyapı
    "PRIME", "NEURAL", "MASA", "ATOR", "GPU", "RLC", "PHB", "NFP",
    # AI Gaming/Metaverse
    "MYRIA", "VOXEL", "OORT", "VANAR", "TRAC", "ORAI",
    # Yeni AI Projeleri
    "IO", "ATH", "ZK", "NOS", "VIRTUALS", "SPEC", "GRIFFAIN"
}

# Minimum filtreler
MIN_MARKET_CAP = 10_000_000      # $10M minimum
MIN_VOLUME_24H = 1_000_000       # $1M minimum hacim

# İşlenecek coin limitleri
COIN_PROCESS_LIMIT = 500         # TOP 500 coin
HISTORICAL_DATA_LIMIT = 400      # İlk 400'e historical data (expanded Binance list)

# Analysis Service instance
analysis_service = AnalysisService()

# Quality Gate settings
MIN_CONFIDENCE_FOR_TRADE = 60
MIN_FACTOR_ALIGNMENT = 2
HIGH_RISK_CONFIDENCE_PENALTY = 10

def get_fear_greed_value() -> int:
    """Redis'ten Fear & Greed degerini al"""
    try:
        fg_raw = r.get("fear_greed")
        if fg_raw:
            fg_data = json.loads(fg_raw)
            return fg_data.get("value", 50)
    except:
        pass
    return 50


BUY_SIGNALS = {"BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"}
SELL_SIGNALS = {"SELL", "SAT", "STRONG_SELL", "GÜÇLÜ SAT"}
HOLD_SIGNALS = {"HOLD", "BEKLE"}

# Top 50 signal filter
MAX_ACTIVE_SIGNALS = 50


def filter_top_signals(signals: dict, max_count: int = MAX_ACTIVE_SIGNALS) -> dict:
    """
    En kaliteli sinyalleri filtrele - sadece AL/SAT sinyallerini say
    Sıralama: confidence * (1 + alignment/10) * quality_bonus
    """
    active_signals = []
    hold_signals = []

    for symbol, sig in signals.items():
        signal_type = sig.get("signal", "HOLD")
        if signal_type in BUY_SIGNALS or signal_type in SELL_SIGNALS:
            conf = sig.get("confidence", 0)
            details = sig.get("confidence_details", {})
            alignment = _extract_alignment(details)

            # Quality score hesapla
            quality_bonus = 1.0
            qg = sig.get("quality_gate", {})
            if qg.get("passed"):
                quality_bonus = 1.2

            # R:R bonus
            rr = sig.get("risk_reward_ratio", 0)
            try:
                if rr and float(rr) >= 2.0:
                    quality_bonus *= 1.1
            except (TypeError, ValueError):
                pass

            score = conf * (1 + alignment / 10) * quality_bonus
            active_signals.append((symbol, sig, score))
        else:
            hold_signals.append((symbol, sig))

    # En yüksek skorlu sinyalleri al
    active_signals.sort(key=lambda x: x[2], reverse=True)
    top_active = active_signals[:max_count]

    # Sonucu oluştur
    result = {}
    for symbol, sig, _ in top_active:
        result[symbol] = sig

    # HOLD sinyallerini de ekle (bunlar zaten işlem önermiyor)
    for symbol, sig in hold_signals:
        result[symbol] = sig

    return result


def _norm_risk(risk_level: str) -> str:
    """Risk seviyesini normalize et"""
    if not risk_level:
        return "UNKNOWN"
    r = risk_level.strip().upper()
    if r in {"HIGH", "YÜKSEK"}:
        return "HIGH"
    if r in {"MEDIUM", "ORTA"}:
        return "MEDIUM"
    if r in {"LOW", "DÜŞÜK", "DUSUK"}:
        return "LOW"
    return r


def _extract_alignment(details: dict) -> int:
    """confidence_details içinden factor uyum sayısını çıkarır"""
    if not isinstance(details, dict):
        return 0

    fb = details.get("factors_buy")
    fs = details.get("factors_sell")

    if isinstance(fb, (int, float)) or isinstance(fs, (int, float)):
        try:
            fb = int(fb or 0)
            fs = int(fs or 0)
            return max(fb, fs)
        except Exception:
            return 0

    if isinstance(fb, list) or isinstance(fs, list):
        fb_n = len(fb or [])
        fs_n = len(fs or [])
        return max(fb_n, fs_n)

    return 0


def _has_indicators(technical: dict) -> bool:
    """İndikatör verisi var mı kontrol et"""
    if not technical:
        return False

    rsi = technical.get("rsi")
    has_rsi = rsi is not None and rsi not in ("N/A", "na", "NA", "") and isinstance(rsi, (int, float))

    macd = technical.get("macd")
    if macd is not None:
        if isinstance(macd, dict):
            has_macd = macd.get("histogram") is not None
        elif isinstance(macd, (int, float)):
            has_macd = True
        else:
            has_macd = macd not in ("N/A", "na", "NA", "")
    else:
        has_macd = False

    ma = technical.get("ma")
    if ma is not None and isinstance(ma, dict):
        has_ma = ma.get("ma_20") is not None or ma.get("ma_50") is not None
    else:
        has_ma = False

    return has_rsi or has_macd or has_ma


def should_emit_signal(analysis: dict, risk_level: str, technical: dict = None, market_data: dict = None, futures_data: dict = None) -> tuple:
    """Geliştirilmiş Quality Gate v3 - Market Regime + Crowding Protection"""
    signal = (analysis.get("signal") or "BEKLE").strip()
    confidence = float(analysis.get("confidence") or 0)
    details = analysis.get("confidence_details") or {}

    if signal in HOLD_SIGNALS:
        return "HOLD", confidence, "already_hold"

    if signal not in BUY_SIGNALS and signal not in SELL_SIGNALS:
        return "HOLD", confidence, f"unknown_signal_{signal}"

    if not _has_indicators(technical):
        return "HOLD", confidence, "missing_indicators"

    # MARKET REGIME FILTRESI
    if market_data:
        btc_change = market_data.get("btc_change_24h", 0) or 0
        fear_greed = market_data.get("fear_greed", 50) or 50

        # BTC düşüşteyken AL verme
        if signal in BUY_SIGNALS and btc_change < -3:
            return "HOLD", confidence, f"btc_downtrend_{btc_change:.1f}%"

        # Bear market'te AL için ekstra kontrol
        if signal in BUY_SIGNALS and btc_change < -5 and fear_greed < 30:
            if confidence < 90:
                return "HOLD", confidence, "bear_market_blocks_buy"

    # CROWDING PROTECTION
    if futures_data:
        ls_ratio = futures_data.get("long_short_ratio", 1.0) or 1.0
        funding_rate = futures_data.get("funding_rate", 0.0) or 0.0

        # Herkes long'dayken AL verme
        if signal in BUY_SIGNALS and ls_ratio > 2.5:
            return "HOLD", confidence, f"crowded_long_{ls_ratio:.2f}"

        # Herkes short'dayken SAT verme
        if signal in SELL_SIGNALS and ls_ratio < 0.5:
            return "HOLD", confidence, f"crowded_short_{ls_ratio:.2f}"

        # Yüksek funding rate'de long açma
        if signal in BUY_SIGNALS and funding_rate > 0.1:
            return "HOLD", confidence, f"high_funding_{funding_rate:.4f}"

    # CONFIDENCE THRESHOLD
    risk = _norm_risk(risk_level)
    threshold = MIN_CONFIDENCE_FOR_TRADE + (HIGH_RISK_CONFIDENCE_PENALTY if risk == "HIGH" else 0)

    if confidence < threshold:
        return "HOLD", confidence, f"low_confidence_{confidence:.1f}<{threshold}"

    # FAKTÖR UYUMU
    alignment = _extract_alignment(details)
    if alignment < MIN_FACTOR_ALIGNMENT:
        return "HOLD", confidence, f"low_alignment_{alignment}<{MIN_FACTOR_ALIGNMENT}"

    return signal, confidence, "passed"


print("[Signal Worker v2.0] Starting with ATR-based Exit Strategy...")
print(f"  Update interval: {UPDATE_INTERVAL}s")
print(f"  Signal check interval: {SIGNAL_CHECK_INTERVAL}s")
print(f"  Timeframes: {', '.join(TIMEFRAMES)}")
print(f"  Quality Gate: min_conf={MIN_CONFIDENCE_FOR_TRADE}, min_align={MIN_FACTOR_ALIGNMENT}")
print(f"  Skip filters: {len(SKIP_SIGNAL_COINS)} coins")
print(f"  AI Coins: {len(AI_COINS)} tracked")
print(f"  Limits: TOP {COIN_PROCESS_LIMIT} + Historical {HISTORICAL_DATA_LIMIT}")


# ============================================
# HISTORICAL PRICE FETCHERS
# ============================================

# Expanded Binance symbols list - 240+ coins for better historical data coverage
BINANCE_SYMBOLS = {
    # Top 100 by market cap
    "BTC", "ETH", "BNB", "XRP", "SOL", "ADA", "DOGE", "TRX", "AVAX",
    "DOT", "LINK", "MATIC", "LTC", "BCH", "ATOM", "UNI", "XLM", "ETC",
    "FIL", "APT", "NEAR", "INJ", "OP", "ARB", "SUI", "SEI", "FET",
    "RNDR", "AAVE", "SHIB", "PEPE", "TON", "HBAR", "ICP", "STX", "IMX",
    "TAO", "JUP", "ENA", "WLD", "TIA", "PYTH", "GRT", "ALGO", "VET",
    "FTM", "SAND", "MANA", "AXS", "GALA", "LDO", "MKR", "SNX", "CRV",
    "COMP", "ENJ", "CHZ", "FLOW", "EOS", "XTZ", "NEO", "ZEC", "DASH",
    "IOTA", "THETA", "EGLD", "QNT", "RUNE", "KAVA", "CFX", "APE", "GMX",
    "W", "STRK", "MANTA", "DYDX", "PENDLE", "BLUR", "FLOKI", "BONK",
    "WIF", "MEME", "ORDI", "JTO", "ZK", "POL", "ONDO", "MINA",
    # Additional working Binance symbols (tested)
    "XMR", "NEXO", "CAKE", "TRUMP", "TWT", "BTT", "JST", "SUN", "WIN", "HOT",
    "ROSE", "ONE", "ZIL", "ICX", "ONT", "SC", "RVN", "ZEN", "DCR", "WAVES",
    "BAT", "ENS", "1INCH", "SUSHI", "YFI", "BADGER", "PERP", "REEF", "CELO", "ANKR",
    "STORJ", "SKL", "CTSI", "BAND", "NKN", "CELR", "OGN", "LINA", "ALPHA", "DODO",
    "AUCTION", "MASK", "HIGH", "RARE", "POLS", "SUPER", "TVK", "BURGER", "SFP",
    "ALPACA", "TLM", "SPELL", "CVX", "BICO", "RAD", "BOND", "QUICK", "REQ", "VOXEL",
    "SSV", "LEVER", "AGLD", "GLMR", "MOVR", "ACH", "PLA", "DAR", "FXS", "LQTY",
    "RPL", "MAGIC", "ID", "RDNT", "ARKM", "EDU", "CYBER", "COMBO", "MAV", "BAKE",
    "WING", "FORTH", "ALCX", "FRONT", "POND", "VIDT", "TROY", "HARD", "IRIS", "MDT",
    "STPT", "SXP", "COTI", "OG", "KEY", "DOCK", "DEGO", "DF", "EPS",
    "UNFI", "TKO", "MLN", "FIO", "LSK", "ARDR", "STRAX", "STMX",
    "MTL", "WRX", "IOTX", "DUSK", "PUNDIX", "DGB", "SYS", "XVG", "FLUX", "ERN",
    "REI", "ASTR", "AGIX", "OCEAN", "LOOM", "KMD", "VTHO", "WAN", "NULS",
    "GAS", "POWR", "RLC", "NMR", "ANT", "BAL", "SNT", "LRC", "OMG", "ZRX",
    "AUDIO", "RAY", "PROM", "BETA", "LAZIO", "PORTO", "JOE", "BIFI", "JASMY", "GMT",
    "LUNA", "LUNC"
}

# Extended CoinGecko mapping for 180+ coins (fallback for non-Binance coins)
SYMBOL_TO_COINGECKO = {
    # TOP 50 by Market Cap
    "BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether", "BNB": "binancecoin",
    "XRP": "ripple", "SOL": "solana", "USDC": "usd-coin", "ADA": "cardano",
    "DOGE": "dogecoin", "TRX": "tron", "AVAX": "avalanche-2", "DOT": "polkadot",
    "LINK": "chainlink", "MATIC": "matic-network", "LTC": "litecoin", "BCH": "bitcoin-cash",
    "SHIB": "shiba-inu", "ATOM": "cosmos", "UNI": "uniswap", "XLM": "stellar",
    "ETC": "ethereum-classic", "TON": "the-open-network", "HBAR": "hedera-hashgraph",
    "FIL": "filecoin", "APT": "aptos", "NEAR": "near", "INJ": "injective-protocol",
    "OP": "optimism", "ARB": "arbitrum", "SUI": "sui", "SEI": "sei-network",
    "AAVE": "aave", "GRT": "the-graph", "ALGO": "algorand", "VET": "vechain",
    "FTM": "fantom", "SAND": "the-sandbox", "MANA": "decentraland", "AXS": "axie-infinity",
    "GALA": "gala", "LDO": "lido-dao", "MKR": "maker", "SNX": "havven",
    "CRV": "curve-dao-token", "COMP": "compound-governance-token", "ENJ": "enjincoin",
    "CHZ": "chiliz", "FLOW": "flow", "EOS": "eos", "XTZ": "tezos",
    # Layer 1 & Layer 2
    "NEO": "neo", "ZEC": "zcash", "DASH": "dash", "IOTA": "iota",
    "THETA": "theta-token", "EGLD": "elrond-erd-2", "QNT": "quant-network",
    "RUNE": "thorchain", "KAVA": "kava", "CFX": "conflux-token", "XMR": "monero",
    "KAS": "kaspa", "FLR": "flare-networks", "ROSE": "oasis-network", "ONE": "harmony",
    "ZIL": "zilliqa", "ICX": "icon", "ONT": "ontology", "IOST": "iostoken",
    "GLMR": "moonbeam", "MOVR": "moonriver", "ASTR": "astar", "CELO": "celo",
    "WAVES": "waves", "LSK": "lisk", "ARDR": "ardor", "STRK": "starknet",
    "MANTA": "manta-network", "ZK": "zksync", "SONIC": "sonic-labs", "MOVE": "movement",
    # Exchange Tokens
    "CRO": "crypto-com-chain", "KCS": "kucoin-shares", "OKB": "okb", "LEO": "leo-token",
    "GT": "gatechain-token", "MNT": "mantle", "BGB": "bitget-token", "NEXO": "nexo",
    "HTX": "huobi-token", "WRX": "wazirx",
    # DeFi
    "PENDLE": "pendle", "RDNT": "radiant-capital", "GMX": "gmx", "DYDX": "dydx",
    "SSV": "ssv-network", "RPL": "rocket-pool", "FXS": "frax-share", "LQTY": "liquity",
    "CVX": "convex-finance", "SPELL": "spell-token", "BICO": "biconomy",
    "BAND": "band-protocol", "ALPHA": "alpha-finance", "DODO": "dodo", "REEF": "reef",
    "YFI": "yearn-finance", "SUSHI": "sushi", "1INCH": "1inch", "BAL": "balancer",
    "MORPHO": "morpho", "ETHFI": "ether-fi", "USUAL": "usual",
    # AI & Data
    "FET": "fetch-ai", "RNDR": "render-token", "RENDER": "render-token",
    "AGIX": "singularitynet", "OCEAN": "ocean-protocol", "TAO": "bittensor",
    "ARKM": "arkham", "WLD": "worldcoin-wld", "VIRTUAL": "virtual-protocol",
    "AI16Z": "ai16z", "AIXBT": "aixbt", "GRIFFAIN": "griffain", "ZEREBRO": "zerebro",
    "GOAT": "goatseus-maximus", "ACT": "act-i-the-ai-prophecy",
    # Gaming & Metaverse
    "IMX": "immutable-x", "MAGIC": "magic", "PLA": "playdapp", "PRIME": "echelon-prime",
    "BEAM": "beam-2", "PIXEL": "pixels", "PORTAL": "portal-gaming", "XAI": "xai-blockchain",
    "GODS": "gods-unchained", "ILV": "illuvium", "SUPER": "superfarm",
    "ALICE": "my-neighbor-alice", "WEMIX": "wemix-token", "GMT": "stepn",
    # Meme Coins
    "PEPE": "pepe", "WIF": "dogwifcoin", "BONK": "bonk", "FLOKI": "floki",
    "MEME": "memecoin", "BOME": "book-of-meme", "MEW": "cat-in-a-dogs-world",
    "POPCAT": "popcat", "NEIRO": "neiro-on-eth", "TURBO": "turbo",
    "PNUT": "peanut-the-squirrel", "FARTCOIN": "fartcoin", "SPX": "spx6900",
    "TRUMP": "official-trump", "BRETT": "brett", "MOG": "mog-coin",
    "SLERF": "slerf", "MYRO": "myro", "TOSHI": "toshi",
    # Infrastructure
    "PYTH": "pyth-network", "TIA": "celestia", "DYM": "dymension", "ALT": "altlayer",
    "MAVIA": "heroes-of-mavia", "STORJ": "storj", "ANKR": "ankr", "SKL": "skale",
    "CTSI": "cartesi", "CELR": "celer-network", "NKN": "nkn", "ACH": "alchemy-pay",
    "IOTX": "iotex", "GNO": "gnosis",
    # Solana Ecosystem
    "JUP": "jupiter-exchange-solana", "JTO": "jito-governance-token", "RAY": "raydium",
    "ORCA": "orca", "MNDE": "marinade", "TENSOR": "tensor", "DRIFT": "drift-protocol",
    "KMNO": "kamino", "PARCL": "parcl", "W": "wormhole",
    # RWA
    "ONDO": "ondo-finance", "CFG": "centrifuge", "MPL": "maple", "TRU": "truefi",
    "CPOOL": "clearpool",
    # Privacy
    "ZEN": "horizen", "DCR": "decred", "SC": "siacoin", "FLUX": "zelcash", "AR": "arweave",
    # Others
    "COMBO": "furucombo", "ID": "space-id", "EDU": "open-campus",
    "CYBER": "cyberconnect", "MAV": "maverick-protocol", "MASK": "mask-network",
    "XDC": "xdce-crowd-sale", "CAKE": "pancakeswap-token", "TWT": "trust-wallet-token",
    "BSV": "bitcoin-cash-sv", "BTT": "bittorrent", "JST": "just", "SUN": "sun-token",
    "WIN": "wink", "HOT": "holotoken", "DGB": "digibyte", "RVN": "ravencoin",
    "SYS": "syscoin", "PUNDIX": "pundi-x-2", "ERN": "ethernity-chain",
    "DUSK": "dusk-network", "MTL": "metal", "STMX": "storm",
    "JOE": "joe", "VELO": "velodrome-finance", "AERO": "aerodrome-finance",
    "QUICK": "quickswap", "PERP": "perpetual-protocol",
    "BAT": "basic-attention-token", "ENS": "ethereum-name-service", "SNT": "status",
    "LRC": "loopring", "OMG": "omisego", "ZRX": "0x", "AUDIO": "audius",
    "APE": "apecoin", "LUNA": "terra-luna-2", "LUNC": "terra-luna", "JASMY": "jasmycoin",
    "OGN": "origin-protocol", "STX": "blockstack", "ICP": "internet-computer",
    "ENA": "ethena", "PENGU": "pudgy-penguins", "BIO": "bio-protocol",
    "POL": "polygon-ecosystem-token", "HYPE": "hyperliquid", "WBT": "whitebit",
    "PAXG": "pax-gold", "XAUT": "tether-gold",
}

CMC_API_KEY = os.getenv("CMC_API_KEY", "")


async def fetch_from_binance(symbol: str, days: int) -> List:
    """Binance Klines API"""
    if symbol not in BINANCE_SYMBOLS:
        return []

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
                klines = resp.json()
                prices = [[int(k[0]), float(k[4])] for k in klines]
                return prices
    except Exception as e:
        print(f"[Binance] {symbol} error: {e}")
    return []


async def fetch_from_coingecko(symbol: str, days: int) -> List:
    """CoinGecko API - Son fallback"""
    coin_id = SYMBOL_TO_COINGECKO.get(symbol)
    if not coin_id:
        return []

    try:
        async with COINGECKO_SEMAPHORE:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                    params={
                        "vs_currency": "usd",
                        "days": str(days),
                        "interval": "daily"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("prices", [])
                elif resp.status_code == 429:
                    await asyncio.sleep(COINGECKO_BACKOFF)
    except Exception as e:
        print(f"[CoinGecko] {symbol} error: {e}")
    return []


async def fetch_from_cmc(symbol: str, days: int) -> List:
    """CoinMarketCap API - Third fallback"""
    if not CMC_API_KEY:
        return []

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # First get CMC ID for the symbol
            resp = await client.get(
                "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map",
                headers={"X-CMC_PRO_API_KEY": CMC_API_KEY},
                params={"symbol": symbol, "limit": 1}
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            if not data.get("data"):
                return []

            cmc_id = data["data"][0]["id"]

            # Get historical quotes
            resp = await client.get(
                "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/historical",
                headers={"X-CMC_PRO_API_KEY": CMC_API_KEY},
                params={
                    "id": cmc_id,
                    "interval": "daily",
                    "count": min(days, 90)
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                quotes = data.get("data", {}).get("quotes", [])
                prices = []
                for q in quotes:
                    try:
                        price = q.get("quote", {}).get("USD", {}).get("price")
                        ts = q.get("timestamp", "")
                        if price and ts:
                            from datetime import datetime
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            prices.append([int(dt.timestamp() * 1000), float(price)])
                    except:
                        continue
                return prices
    except Exception as e:
        pass  # Silent fail for CMC
    return []


async def fetch_historical_prices_uncached(symbol: str, days: int = 90) -> List:
    """Multi-source historical price fetcher (uncached)"""
    # 1. Binance (fastest, no rate limits)
    prices = await fetch_from_binance(symbol, days)
    if prices and len(prices) >= 14:
        return prices

    # 2. CoinGecko (good coverage)
    prices = await fetch_from_coingecko(symbol, days)
    if prices and len(prices) >= 14:
        return prices

    # 3. CoinMarketCap (third fallback)
    prices = await fetch_from_cmc(symbol, days)
    if prices and len(prices) >= 14:
        return prices

    return []


async def get_cached_historical(symbol: str, days: int = 90) -> List:
    """Get historical prices from Redis cache or fetch fresh"""
    cache_key = f"hist:{symbol}:{days}"

    try:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    except:
        pass

    # Not in cache, fetch fresh
    prices = await fetch_historical_prices_uncached(symbol, days)

    if prices and len(prices) >= 14:
        try:
            r.setex(cache_key, HISTORICAL_CACHE_TTL, json.dumps(prices))
        except:
            pass

    return prices


async def fetch_historical_prices(symbol: str, days: int = 90) -> List:
    """Multi-source historical price fetcher with caching and wrapped token support"""
    # Check if this is a wrapped token - use underlying asset
    underlying = WRAPPED_TOKEN_MAP.get(symbol)
    if underlying:
        symbol = underlying

    return await get_cached_historical(symbol, days)


def get_news_sentiment_for_coin(symbol: str, news_db: Dict) -> Optional[Dict]:
    """Coin için news sentiment hesapla"""
    if not news_db:
        return None

    cutoff_dt = datetime.utcnow() - timedelta(hours=24)
    relevant_news = []
    
    for news in news_db.values():
        crawled_str = news.get("crawled_at", "")
        if not crawled_str:
            continue
        try:
            crawled_dt = datetime.fromisoformat(crawled_str.replace("Z", "+00:00"))
            if crawled_dt.tzinfo:
                crawled_dt = crawled_dt.replace(tzinfo=None)
            if crawled_dt < cutoff_dt:
                continue
        except (ValueError, TypeError):
            continue

        coins = news.get("coins", [])
        if symbol in coins or "GENERAL" in coins:
            relevant_news.append(news)

    if not relevant_news:
        return None

    total_score = 0
    for news in relevant_news:
        sentiment = news.get("sentiment", "neutral")
        score = news.get("sentiment_score", 0)

        if sentiment == "bullish":
            total_score += abs(score)
        elif sentiment == "bearish":
            total_score -= abs(score)

    avg_score = total_score / len(relevant_news) if relevant_news else 0

    return {
        "score": round(avg_score, 3),
        "news_count": len(relevant_news)
    }


# ============================================
# SIGNAL GENERATION WITH EXIT STRATEGY
# ============================================

def generate_signals_for_coin(
    symbol: str,
    price_data: Dict,
    futures_data: Dict,
    news_sentiment: Optional[Dict],
    historical_prices: List,
    prices_data: Dict = None
) -> Dict:
    """
    Tek coin için tüm timeframe'lerde sinyal üret
    + EXIT STRATEGY HESAPLAMA (v2.0)
    """
    results = {}

    # Technical indicators
    if historical_prices:
        technical = analysis_service.calculate_indicators(historical_prices)
    else:
        technical = {
            "current_price": price_data.get("price", 0),
            "change_24h": price_data.get("change_24h", 0),
            "change_7d": price_data.get("change_7d", 0),
            "rsi": None,
            "macd": None,
            "bollinger": {},
            "ma": {},
            "volatility": {},
            "trend": "NEUTRAL"
        }

    # Futures
    futures = futures_data.get(symbol, {}) if futures_data else None

    # Market Regime hesapla (v3.0)
    btc_7d_change = prices_data.get("BTC", {}).get("change_7d", 0) if prices_data else 0
    fear_greed = get_fear_greed_value()
    market_regime = get_market_regime(btc_7d_change, fear_greed)

    # Sinyal üret
    signal_result = analysis_service.generate_signal(
        technical=technical,
        futures=futures,
        news_sentiment=news_sentiment,
        market_regime=market_regime
    )

    # Risk seviyesi
    risk_result = analysis_service.calculate_risk_level(symbol, technical)

    # Quality Gate
    raw_signal = signal_result["signal"]
    raw_signal_tr = signal_result["signal_tr"]
    risk_level = risk_result["level"]

    # Market Regime data for Quality Gate v3
    market_data = {
        "btc_change_24h": prices_data.get("BTC", {}).get("change_24h", 0) if prices_data else 0,
        "fear_greed": get_fear_greed_value()
    }
    coin_futures = futures_data.get(symbol, {}) if futures_data else None

    final_signal, final_conf, gate_reason = should_emit_signal(signal_result, risk_level, technical, market_data, coin_futures)

    signal_tr_map = {
        "HOLD": "BEKLE",
        "BUY": "AL",
        "STRONG_BUY": "GÜÇLÜ AL",
        "SELL": "SAT",
        "STRONG_SELL": "GÜÇLÜ SAT"
    }
    final_signal_tr = signal_tr_map.get(final_signal, raw_signal_tr)

    # Yetersiz veri kontrolü
    conf_details = signal_result.get("confidence_details", {})
    factors_neutral = conf_details.get("factors_neutral", 0)
    data_quality = conf_details.get("data_quality", 0)
    has_insufficient_data = (
        signal_result["confidence"] <= 45 and
        factors_neutral >= 5 and
        data_quality <= 4
    )

    quality_gate = {
        "passed": gate_reason == "passed",
        "reason": gate_reason,
        "original_signal": raw_signal,
        "min_conf": MIN_CONFIDENCE_FOR_TRADE,
        "min_align": MIN_FACTOR_ALIGNMENT,
        "insufficient_data": has_insufficient_data,
    }

    # ============================================
    # EXIT STRATEGY HESAPLAMA (YENİ v2.0)
    # Her timeframe için AYRI hesapla
    # ============================================
    current_price = price_data.get("price", 0)
    category = risk_result.get("category", "ALT")

    # Sonucu hazırla - BASE (exit_strategy hariç)
    base_result = {
        "symbol": symbol,
        "name": price_data.get("name", symbol),
        "price": current_price,
        "change_24h": price_data.get("change_24h", 0),
        "change_7d": price_data.get("change_7d", 0),
        "change_30d": price_data.get("change_30d", 0),
        "market_cap": price_data.get("market_cap", 0),
        "volume_24h": price_data.get("volume_24h", 0),
        "rank": price_data.get("rank", 999),
        "image": price_data.get("image", ""),
        "source": price_data.get("source", "coingecko"),
        "signal": final_signal,
        "signal_tr": final_signal_tr,
        "signal_raw": raw_signal,
        "quality_gate": quality_gate,
        "score": signal_result["score"],
        "confidence": signal_result["confidence"],
        "confidence_details": signal_result["confidence_details"],
        "reasons": signal_result["reasons"],
        "risk_level": risk_result["level"],
        "risk_score": risk_result["score"],
        "risk_factors": risk_result["factors"],
        "category": risk_result["category"],
        "technical": technical,
        "news_sentiment": news_sentiment,
        "updated_at": datetime.utcnow().isoformat()
    }

    # Her timeframe için AYRI exit strategy
    for tf in TIMEFRAMES:
        tf_result = base_result.copy()
        tf_result["timeframe"] = tf
        tf_result["timeframe_label"] = TIMEFRAME_LABELS.get(tf, tf)
        
        # Bu timeframe için exit strategy hesapla
        exit_strategy = analysis_service.calculate_exit_strategy(
            current_price=current_price,
            signal=final_signal,
            confidence=signal_result["confidence"],
            technical=technical,
            category=category,
            timeframe=tf
        )
        
        tf_result["exit_strategy"] = exit_strategy
        tf_result["stop_loss"] = exit_strategy.get("stop_loss")
        tf_result["take_profit"] = exit_strategy.get("take_profit")
        tf_result["trailing_stop"] = exit_strategy.get("trailing_stop")
        tf_result["risk_reward_ratio"] = exit_strategy.get("risk_reward_ratio")
        tf_result["stop_loss_pct"] = exit_strategy.get("stop_loss_pct")
        tf_result["take_profit_pct"] = exit_strategy.get("take_profit_pct")
        
        results[tf] = tf_result

    return results


async def generate_all_signals():
    """Tüm coinler için sinyal üret"""
    print(f"\n[Signals] Generating at {datetime.utcnow().strftime('%H:%M:%S')}")

    prices_raw = r.get("prices_data")
    futures_raw = r.get("futures_data")
    news_raw = r.get("news_db")

    prices_data = json.loads(prices_raw) if prices_raw else {}
    futures_data = json.loads(futures_raw) if futures_raw else {}
    news_db = json.loads(news_raw) if news_raw else {}

    if not prices_data:
        print("[Signals] No price data available")
        return

    print(f"  Coins: {len(prices_data)} | News: {len(news_db)} | Futures: {len(futures_data)}")

    sorted_coins = sorted(
        prices_data.items(),
        key=lambda x: x[1].get("market_cap", 0) or 0,
        reverse=True
    )

    all_signals = {tf: {"signals": {}, "stats": {}, "risk_stats": {}, "count": 0} for tf in TIMEFRAMES}
    processed = 0
    skipped_coins = {"stablecoin": 0, "wrapped": 0, "other": 0, "low_mcap": 0}
    quality_gate_stats = {"passed": 0, "blocked": 0, "reasons": {}}

    # AI coinlerini + TOP 500'ü birleştir
    coins_to_process = set()

    # 1. TOP 500 coin (market cap sıralı)
    for symbol, _ in sorted_coins[:COIN_PROCESS_LIMIT]:
        coins_to_process.add(symbol)

    # 2. AI coinlerini ekle (market cap'ten bağımsız)
    for symbol, _ in sorted_coins:
        if symbol in AI_COINS:
            coins_to_process.add(symbol)

    # sorted_coins'den işlenecek coinleri filtrele (sırayı koru)
    filtered_coins = [(s, d) for s, d in sorted_coins if s in coins_to_process]

    print(f"  Processing: {len(filtered_coins)} coins (TOP {COIN_PROCESS_LIMIT} + {len(AI_COINS)} AI coins)")

    for symbol, price_data in filtered_coins:
        try:
            if symbol in SKIP_SIGNAL_COINS:
                if symbol in STABLECOINS:
                    skipped_coins["stablecoin"] += 1
                elif symbol in WRAPPED_TOKENS:
                    skipped_coins["wrapped"] += 1
                else:
                    skipped_coins["other"] += 1
                continue

            # Minimum market cap/volume filtresi (AI coinleri hariç)
            if symbol not in AI_COINS:
                mcap = price_data.get("market_cap", 0) or 0
                vol = price_data.get("volume_24h", 0) or 0
                if mcap < MIN_MARKET_CAP or vol < MIN_VOLUME_24H:
                    skipped_coins["low_mcap"] += 1
                    continue

            news_sentiment = get_news_sentiment_for_coin(symbol, news_db)

            historical_prices = []
            if processed < HISTORICAL_DATA_LIMIT:
                historical_prices = await fetch_historical_prices(symbol, days=90)
                if historical_prices and processed % 20 == 0:
                    await asyncio.sleep(0.2)

            coin_signals = generate_signals_for_coin(
                symbol=symbol,
                price_data=price_data,
                futures_data=futures_data,
                news_sentiment=news_sentiment,
                historical_prices=historical_prices,
                prices_data=prices_data
            )

            for tf, signal_data in coin_signals.items():
                all_signals[tf]["signals"][symbol] = signal_data

                sig = signal_data["signal"]
                if sig not in all_signals[tf]["stats"]:
                    all_signals[tf]["stats"][sig] = 0
                all_signals[tf]["stats"][sig] += 1

                risk = signal_data["risk_level"]
                if risk not in all_signals[tf]["risk_stats"]:
                    all_signals[tf]["risk_stats"][risk] = 0
                all_signals[tf]["risk_stats"][risk] += 1

                if tf == "1d":
                    qg = signal_data.get("quality_gate", {})
                    if qg.get("passed"):
                        quality_gate_stats["passed"] += 1
                    elif qg.get("original_signal") in BUY_SIGNALS | SELL_SIGNALS:
                        quality_gate_stats["blocked"] += 1
                        reason = qg.get("reason", "unknown")
                        if reason.startswith("low_confidence"):
                            reason_key = "low_confidence"
                        elif reason.startswith("low_alignment"):
                            reason_key = "low_alignment"
                        else:
                            reason_key = reason
                        quality_gate_stats["reasons"][reason_key] = quality_gate_stats["reasons"].get(reason_key, 0) + 1

            processed += 1

            if processed % 50 == 0:
                print(f"  Processed: {processed}")

        except Exception as e:
            print(f"  Error {symbol}: {e}")
            continue

    # Top 50 sinyal filtreleme - her timeframe için
    for tf in TIMEFRAMES:
        original_count = len(all_signals[tf]["signals"])
        all_signals[tf]["signals"] = filter_top_signals(all_signals[tf]["signals"])
        filtered_count = len([s for s in all_signals[tf]["signals"].values()
                             if s.get("signal") in BUY_SIGNALS or s.get("signal") in SELL_SIGNALS])
        all_signals[tf]["count"] = len(all_signals[tf]["signals"])
        if tf == "1d":
            print(f"  [Filter] Active signals: {original_count} -> Top {filtered_count} (max {MAX_ACTIVE_SIGNALS})")

    r.set("signals_all_timeframes", json.dumps(all_signals))
    r.set("signals_data", json.dumps(all_signals["1d"]["signals"]))
    r.set("signals_stats", json.dumps(all_signals["1d"]["stats"]))
    r.set("signals_risk_stats", json.dumps(all_signals["1d"]["risk_stats"]))
    r.set("signals_updated", datetime.utcnow().isoformat())
    r.set("signals_count", str(processed))

    stats_1d = all_signals["1d"]["stats"]
    buy_count = stats_1d.get("BUY", 0) + stats_1d.get("STRONG_BUY", 0)
    sell_count = stats_1d.get("SELL", 0) + stats_1d.get("STRONG_SELL", 0)
    hold_count = stats_1d.get("HOLD", 0)

    print(f"  Total: {processed} | BUY: {buy_count} | HOLD: {hold_count} | SELL: {sell_count}")

    total_skipped = sum(skipped_coins.values())
    print(f"  [Skipped] Total: {total_skipped} | Stablecoin: {skipped_coins['stablecoin']} | Wrapped: {skipped_coins['wrapped']} | LowMcap: {skipped_coins['low_mcap']}")

    qg_passed = quality_gate_stats["passed"]
    qg_blocked = quality_gate_stats["blocked"]
    print(f"  [QualityGate] Passed: {qg_passed} | Blocked: {qg_blocked}")

    # Signal tracking
    await track_all_signals(all_signals["1d"]["signals"])


async def track_all_signals(signals_1d: Dict):
    """
    Tüm coinler için akıllı sinyal tracking
    + EXIT STRATEGY KAYDETME (v2.0)
    """
    recent_tracks = set()
    try:
        from database import get_db
        with get_db() as conn:
            rows = conn.execute("""
                SELECT symbol, signal FROM signal_tracking
                WHERE created_at >= datetime('now', '-24 hours')
            """).fetchall()
            recent_tracks = {(row["symbol"], row["signal"]) for row in rows}
    except Exception as e:
        print(f"  [Track] Recent check error: {e}")

    tracked = 0
    skipped_hold = 0
    skipped_low_conf = 0
    skipped_duplicate = 0

    for symbol, signal_data in signals_1d.items():
        if not signal_data:
            continue

        signal = signal_data.get("signal", "")
        if signal not in ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]:
            skipped_hold += 1
            continue

        confidence = signal_data.get("confidence", 0)
        if confidence < 30:
            skipped_low_conf += 1
            continue

        if (symbol, signal) in recent_tracks:
            skipped_duplicate += 1
            continue

        try:
            price = signal_data.get("price", 0)
            
            # EXIT STRATEGY'DEN SL/TP AL (v2.0)
            exit_strategy = signal_data.get("exit_strategy", {})
            target_price = exit_strategy.get("take_profit", price * 1.06)
            stop_loss = exit_strategy.get("stop_loss", price * 0.97)
            trailing_stop = exit_strategy.get("trailing_stop")
            trailing_stop_pct = exit_strategy.get("trailing_stop_pct", 2.0)
            risk_reward_ratio = exit_strategy.get("risk_reward_ratio", "1:2.0")
            stop_loss_pct = exit_strategy.get("stop_loss_pct", 3.0)
            take_profit_pct = exit_strategy.get("take_profit_pct", 6.0)

            signal_tr = signal_data.get("signal_tr", signal)

            # DB'ye kaydet (v2.0 - ekstra kolonlar)
            save_signal_track(
                symbol=symbol,
                signal=signal,
                signal_tr=signal_tr,
                confidence=int(confidence),
                entry_price=price,
                target_price=target_price,
                stop_loss=stop_loss,
                timeframe="1d",
                # v2.0 ek parametreler
                trailing_stop=trailing_stop,
                trailing_stop_pct=trailing_stop_pct,
                risk_reward_ratio=risk_reward_ratio,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
            tracked += 1

        except Exception as e:
            print(f"  [Track] Error {symbol}: {e}")
            continue

    print(f"  [Track] Saved: {tracked} | Skip: HOLD={skipped_hold}, LowConf={skipped_low_conf}, Dup={skipped_duplicate}")


# ============================================
# SIGNAL CHECKER INTEGRATION (v2.0)
# ============================================

async def check_exit_conditions():
    """
    Açık pozisyonları kontrol et ve çıkış koşullarını değerlendir
    Her 60 saniyede çalışır
    """
    try:
        from signal_tracker import signal_tracker
        stats = signal_tracker.process_all_signals()
        
        if stats["closed"] > 0:
            print(f"  [Exit Check] Closed: {stats['closed']} | SL: {stats['exits'].get('STOP_LOSS', 0)} | TP: {stats['exits'].get('TAKE_PROFIT', 0)}")
    except ImportError:
        # signal_tracker.py henüz yok, sessizce geç
        pass
    except Exception as e:
        print(f"  [Exit Check] Error: {e}")


async def main():
    """Main loop"""
    print(f"[Signal Worker v2.0] Starting main loop")

    last_signal_gen = 0
    last_exit_check = 0

    while True:
        try:
            now = asyncio.get_event_loop().time()

            # Sinyal üretimi (5 dakikada bir)
            if now - last_signal_gen >= UPDATE_INTERVAL:
                await generate_all_signals()
                last_signal_gen = now

            # Çıkış kontrolü (60 saniyede bir)
            if now - last_exit_check >= SIGNAL_CHECK_INTERVAL:
                await check_exit_conditions()
                last_exit_check = now

            # Kısa uyku
            await asyncio.sleep(10)

        except Exception as e:
            print(f"[Signal Worker] Error: {e}")
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
