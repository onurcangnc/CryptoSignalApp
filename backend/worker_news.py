#!/usr/bin/env python3
"""
News Worker v4 - Memory Buffer + Hourly Redis Flush
====================================================
- 100+ haber kaynağı
- 1 dakikada bir crawl
- Memory'de biriktir (news_buffer)
- Saat başı Redis'e toplu yaz (news_db)
- Flush sonrası buffer sıfırla
- Duplicate kontrolü (hash set)
- 72 saat sonra eski haberler silinir
"""

import asyncio
import json
import redis
import httpx
import re
import hashlib
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import Dict, Set, List
import time

# Redis connection
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    password=REDIS_PASSWORD
)

# =============================================================================
# CONFIGURATION
# =============================================================================

CRAWL_INTERVAL = 60              # 1 dakikada bir crawl
FLUSH_INTERVAL = 1800            # 30 dakikada bir Redis'e flush
NEWS_RETENTION_HOURS = 72        # 72 saat tut
MAX_CONCURRENT = 20              # Eşzamanlı request
REQUEST_TIMEOUT = 15

# =============================================================================
# 100+ NEWS SOURCES
# =============================================================================

RSS_SOURCES = [
    # ===== TIER 1 - Major (7) =====
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "tier": 1},
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss", "tier": 1},
    {"name": "TheBlock", "url": "https://www.theblock.co/rss.xml", "tier": 1},
    {"name": "Decrypt", "url": "https://decrypt.co/feed", "tier": 1},
    {"name": "CryptoSlate", "url": "https://cryptoslate.com/feed/", "tier": 1},
    {"name": "BitcoinMagazine", "url": "https://bitcoinmagazine.com/feed", "tier": 1},
    {"name": "Blockworks", "url": "https://blockworks.co/feed", "tier": 1},

    # ===== TIER 2 - Quality (13) =====
    {"name": "CryptoNews", "url": "https://cryptonews.com/news/feed/", "tier": 2},
    {"name": "CryptoPotato", "url": "https://cryptopotato.com/feed/", "tier": 2},
    {"name": "UToday", "url": "https://u.today/rss", "tier": 2},
    {"name": "DailyHodl", "url": "https://dailyhodl.com/feed/", "tier": 2},
    {"name": "NewsBTC", "url": "https://www.newsbtc.com/feed/", "tier": 2},
    {"name": "AMBCrypto", "url": "https://ambcrypto.com/feed/", "tier": 2},
    {"name": "Bitcoinist", "url": "https://bitcoinist.com/feed/", "tier": 2},
    {"name": "CoinGape", "url": "https://coingape.com/feed/", "tier": 2},
    {"name": "ZyCrypto", "url": "https://zycrypto.com/feed/", "tier": 2},
    {"name": "CryptoGlobe", "url": "https://www.cryptoglobe.com/feed/", "tier": 2},
    {"name": "Coinpedia", "url": "https://coinpedia.org/feed/", "tier": 2},
    {"name": "CoinEdition", "url": "https://coinedition.com/feed/", "tier": 2},
    {"name": "CryptoDaily", "url": "https://cryptodaily.co.uk/feed", "tier": 2},

    # ===== TIER 3 - Regional & Niche (20) =====
    {"name": "BeInCrypto", "url": "https://beincrypto.com/feed/", "tier": 3},
    {"name": "CoinJournal", "url": "https://coinjournal.net/feed/", "tier": 3},
    {"name": "CryptoNinjas", "url": "https://www.cryptoninjas.net/feed/", "tier": 3},
    {"name": "CoinSpeaker", "url": "https://www.coinspeaker.com/feed/", "tier": 3},
    {"name": "CryptoBriefing", "url": "https://cryptobriefing.com/feed/", "tier": 3},
    {"name": "Blockonomi", "url": "https://blockonomi.com/feed/", "tier": 3},
    {"name": "TronWeekly", "url": "https://www.tronweekly.com/feed/", "tier": 3},
    {"name": "EthereumWorldNews", "url": "https://en.ethereumworldnews.com/feed/", "tier": 3},
    {"name": "CryptoMode", "url": "https://cryptomode.com/feed/", "tier": 3},
    {"name": "InsideBitcoins", "url": "https://insidebitcoins.com/feed", "tier": 3},
    {"name": "CoinCodex", "url": "https://coincodex.com/feed/", "tier": 3},
    {"name": "Cryptopolitan", "url": "https://www.cryptopolitan.com/feed/", "tier": 3},
    {"name": "UseTheBitcoin", "url": "https://usethebitcoin.com/feed/", "tier": 3},
    {"name": "CoinQuora", "url": "https://coinquora.com/feed/", "tier": 3},
    {"name": "TokenPost", "url": "https://tokenpost.com/rss/news/", "tier": 3},
    {"name": "CryptoTicker", "url": "https://cryptoticker.io/en/feed/", "tier": 3},
    {"name": "Finbold", "url": "https://finbold.com/feed/", "tier": 3},
    {"name": "CoinCu", "url": "https://coincu.com/feed/", "tier": 3},
    {"name": "Watcher.Guru", "url": "https://watcher.guru/news/feed", "tier": 3},
    {"name": "CryptoNewsZ", "url": "https://www.cryptonewsz.com/feed/", "tier": 3},

    # ===== TIER 4 - DeFi (7) =====
    {"name": "DeFiPrime", "url": "https://defiprime.com/feed.xml", "tier": 4},
    {"name": "TheDeFiant", "url": "https://thedefiant.io/feed", "tier": 4},
    {"name": "DeFiRate", "url": "https://defirate.com/feed/", "tier": 4},
    {"name": "RektNews", "url": "https://rekt.news/feed.xml", "tier": 4},
    {"name": "WeekInEthereum", "url": "https://weekinethereumnews.com/feed/", "tier": 4},
    {"name": "Bankless", "url": "https://www.bankless.com/rss/", "tier": 4},
    {"name": "DeFiLlama", "url": "https://defillama.com/feed", "tier": 4},

    # ===== TIER 5 - NFT & Gaming (6) =====
    {"name": "NFTNow", "url": "https://nftnow.com/feed/", "tier": 5},
    {"name": "NFTEvening", "url": "https://nftevening.com/feed/", "tier": 5},
    {"name": "PlayToEarn", "url": "https://playtoearn.net/feed", "tier": 5},
    {"name": "NFTPlazas", "url": "https://nftplazas.com/feed/", "tier": 5},
    {"name": "NFTCulture", "url": "https://www.nftculture.com/feed/", "tier": 5},
    {"name": "CryptoGames", "url": "https://cryptogames.net/feed/", "tier": 5},

    # ===== TIER 6 - Mainstream Tech (8) =====
    {"name": "Wired-Crypto", "url": "https://www.wired.com/feed/tag/cryptocurrency/latest/rss", "tier": 6},
    {"name": "TechCrunch-Crypto", "url": "https://techcrunch.com/tag/cryptocurrency/feed/", "tier": 6},
    {"name": "Forbes-Crypto", "url": "https://www.forbes.com/crypto-blockchain/feed/", "tier": 6},
    {"name": "CNBC-Crypto", "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html", "tier": 6},
    {"name": "Cointelegraph-TR", "url": "https://tr.cointelegraph.com/rss", "tier": 6},
    {"name": "Investing-Crypto", "url": "https://www.investing.com/rss/news_301.rss", "tier": 6},
    {"name": "Benzinga-Crypto", "url": "https://www.benzinga.com/feed/crypto", "tier": 6},
    {"name": "Seeking-Crypto", "url": "https://seekingalpha.com/tag/cryptocurrency.xml", "tier": 6},

    # ===== TIER 7 - International (12) =====
    {"name": "CoinPost-JP", "url": "https://coinpost.jp/?feed=rss2", "tier": 7},
    {"name": "BlockMedia-KR", "url": "https://www.blockmedia.co.kr/feed/", "tier": 7},
    {"name": "CryptoActu-FR", "url": "https://cryptoactu.com/feed/", "tier": 7},
    {"name": "CoinTribune-FR", "url": "https://www.cointribune.com/feed/", "tier": 7},
    {"name": "BTC-Echo-DE", "url": "https://www.btc-echo.de/feed/", "tier": 7},
    {"name": "CryptoNews-RU", "url": "https://ru.cryptonews.com/news/feed/", "tier": 7},
    {"name": "CriptoNoticias-ES", "url": "https://www.criptonoticias.com/feed/", "tier": 7},
    {"name": "Livecoins-BR", "url": "https://livecoins.com.br/feed/", "tier": 7},
    {"name": "CoinTurk", "url": "https://coin-turk.com/feed", "tier": 7},
    {"name": "KriptoKoin-TR", "url": "https://kriptokoin.com/feed/", "tier": 7},
    {"name": "BitcoinSistemi-TR", "url": "https://www.bitcoinsistemi.com/feed/", "tier": 7},
    {"name": "Kripto-TR", "url": "https://kripto.istanbul/feed/", "tier": 7},

    # ===== TIER 8 - Exchange Blogs (10) =====
    {"name": "Binance-Blog", "url": "https://www.binance.com/en/blog/rss", "tier": 8},
    {"name": "Coinbase-Blog", "url": "https://www.coinbase.com/blog/rss", "tier": 8},
    {"name": "Kraken-Blog", "url": "https://blog.kraken.com/feed/", "tier": 8},
    {"name": "OKX-Blog", "url": "https://www.okx.com/academy/en/feed", "tier": 8},
    {"name": "Bybit-Blog", "url": "https://blog.bybit.com/feed/", "tier": 8},
    {"name": "KuCoin-Blog", "url": "https://www.kucoin.com/blog/rss", "tier": 8},
    {"name": "Gate-Blog", "url": "https://www.gate.io/blog/feed", "tier": 8},
    {"name": "Bitfinex-Blog", "url": "https://blog.bitfinex.com/feed/", "tier": 8},
    {"name": "Gemini-Blog", "url": "https://www.gemini.com/blog/feed", "tier": 8},
    {"name": "Bitstamp-Blog", "url": "https://blog.bitstamp.net/feed/", "tier": 8},

    # ===== TIER 9 - Project Blogs (12) =====
    {"name": "Ethereum-Blog", "url": "https://blog.ethereum.org/feed.xml", "tier": 9},
    {"name": "Solana-News", "url": "https://solana.com/news/rss.xml", "tier": 9},
    {"name": "Chainlink-Blog", "url": "https://blog.chain.link/rss/", "tier": 9},
    {"name": "Polygon-Blog", "url": "https://polygon.technology/blog/rss.xml", "tier": 9},
    {"name": "Avalanche-Medium", "url": "https://medium.com/feed/avalancheavax", "tier": 9},
    {"name": "Arbitrum-Medium", "url": "https://medium.com/feed/offchainlabs", "tier": 9},
    {"name": "Uniswap-Blog", "url": "https://uniswap.org/rss.xml", "tier": 9},
    {"name": "Aave-Medium", "url": "https://medium.com/feed/aave", "tier": 9},
    {"name": "MakerDAO-Blog", "url": "https://blog.makerdao.com/feed/", "tier": 9},
    {"name": "Compound-Medium", "url": "https://medium.com/feed/compound-finance", "tier": 9},
    {"name": "Lido-Blog", "url": "https://blog.lido.fi/rss/", "tier": 9},
    {"name": "Curve-Medium", "url": "https://medium.com/feed/@curvefinance", "tier": 9},

    # ===== TIER 10 - Research (6) =====
    {"name": "Messari", "url": "https://messari.io/rss", "tier": 10},
    {"name": "GlassnodeInsights", "url": "https://insights.glassnode.com/rss/", "tier": 10},
    {"name": "Chainalysis-Blog", "url": "https://blog.chainalysis.com/feed/", "tier": 10},
    {"name": "Nansen-Research", "url": "https://research.nansen.ai/feed", "tier": 10},
    {"name": "IntoTheBlock", "url": "https://medium.com/feed/intotheblock", "tier": 10},
    {"name": "TokenTerminal", "url": "https://tokenterminal.substack.com/feed", "tier": 10},

    # ===== TIER 11 - Security (4) =====
    {"name": "SlowMist", "url": "https://slowmist.medium.com/feed", "tier": 11},
    {"name": "PeckShield", "url": "https://peckshield.medium.com/feed", "tier": 11},
    {"name": "CertiK-Blog", "url": "https://www.certik.com/resources/blog/rss.xml", "tier": 11},
    {"name": "Immunefi", "url": "https://medium.com/feed/immunefi", "tier": 11},

    # ===== TIER 12 - Reddit (5) =====
    {"name": "Reddit-CC", "url": "https://www.reddit.com/r/CryptoCurrency/.rss", "tier": 12},
    {"name": "Reddit-Bitcoin", "url": "https://www.reddit.com/r/Bitcoin/.rss", "tier": 12},
    {"name": "Reddit-Ethereum", "url": "https://www.reddit.com/r/ethereum/.rss", "tier": 12},
    {"name": "Reddit-Solana", "url": "https://www.reddit.com/r/solana/.rss", "tier": 12},
    {"name": "Reddit-DeFi", "url": "https://www.reddit.com/r/defi/.rss", "tier": 12},
]

# =============================================================================
# SENTIMENT KEYWORDS
# =============================================================================

BULLISH_KEYWORDS = {
    "rally": 0.5, "surge": 0.5, "soar": 0.5, "breakout": 0.5, "moon": 0.6,
    "all-time high": 0.7, "ath": 0.6, "pump": 0.4, "skyrocket": 0.6,
    "bullish": 0.4, "gain": 0.25, "rise": 0.25, "jump": 0.3, "spike": 0.3,
    "growth": 0.25, "recover": 0.3, "rebound": 0.35, "climb": 0.25,
    "adoption": 0.45, "partnership": 0.4, "etf approved": 0.7, "etf": 0.3,
    "institutional": 0.4, "accumulate": 0.4, "whale buy": 0.5,
    "upgrade": 0.3, "launch": 0.25, "mainnet": 0.35, "approval": 0.45,
    "outperform": 0.3, "record": 0.3, "milestone": 0.3,
}

BEARISH_KEYWORDS = {
    "crash": 0.6, "dump": 0.5, "plunge": 0.55, "collapse": 0.6, "tank": 0.45,
    "hack": 0.7, "hacked": 0.7, "exploit": 0.65, "rug": 0.7, "scam": 0.7,
    "fraud": 0.65, "stolen": 0.6, "vulnerability": 0.5,
    "bearish": 0.4, "drop": 0.3, "fall": 0.25, "decline": 0.25,
    "sell-off": 0.45, "selloff": 0.45, "fear": 0.3, "panic": 0.45,
    "sec lawsuit": 0.55, "lawsuit": 0.45, "ban": 0.5, "crackdown": 0.45,
    "bankruptcy": 0.65, "liquidation": 0.5, "layoff": 0.35,
    "reject": 0.4, "delay": 0.2, "warning": 0.3,
}

# =============================================================================
# COIN MAPPING (200+)
# =============================================================================

COIN_NAMES = {
    "bitcoin": "BTC", "btc": "BTC", "ethereum": "ETH", "eth": "ETH",
    "solana": "SOL", "sol": "SOL", "xrp": "XRP", "ripple": "XRP",
    "cardano": "ADA", "ada": "ADA", "dogecoin": "DOGE", "doge": "DOGE",
    "polkadot": "DOT", "dot": "DOT", "avalanche": "AVAX", "avax": "AVAX",
    "chainlink": "LINK", "link": "LINK", "polygon": "POL", "matic": "POL",
    "litecoin": "LTC", "ltc": "LTC", "uniswap": "UNI", "uni": "UNI",
    "cosmos": "ATOM", "atom": "ATOM", "stellar": "XLM", "xlm": "XLM",
    "tron": "TRX", "trx": "TRX", "bnb": "BNB", "binance": "BNB",
    "toncoin": "TON", "ton": "TON", "shiba": "SHIB", "shib": "SHIB",
    "pepe": "PEPE", "bonk": "BONK", "sui": "SUI", "sei": "SEI",
    "aptos": "APT", "apt": "APT", "arbitrum": "ARB", "arb": "ARB",
    "optimism": "OP", "near": "NEAR", "injective": "INJ", "inj": "INJ",
    "render": "RNDR", "rndr": "RNDR", "fetch": "FET", "fet": "FET",
    "hedera": "HBAR", "hbar": "HBAR", "filecoin": "FIL", "fil": "FIL",
    "aave": "AAVE", "maker": "MKR", "mkr": "MKR", "the graph": "GRT",
    "stacks": "STX", "stx": "STX", "immutable": "IMX", "imx": "IMX",
    "kaspa": "KAS", "kas": "KAS", "ondo": "ONDO", "jupiter": "JUP",
    "worldcoin": "WLD", "wld": "WLD", "celestia": "TIA", "tia": "TIA",
    "pyth": "PYTH", "monero": "XMR", "xmr": "XMR", "bitcoin cash": "BCH",
    "ethereum classic": "ETC", "etc": "ETC", "algorand": "ALGO",
    "vechain": "VET", "vet": "VET", "theta": "THETA", "sandbox": "SAND",
    "decentraland": "MANA", "axie": "AXS", "gala": "GALA", "flow": "FLOW",
    "mantra": "OM", "floki": "FLOKI", "dogwifhat": "WIF", "wif": "WIF",
    "bittensor": "TAO", "tao": "TAO", "fantom": "FTM", "ftm": "FTM",
    "internet computer": "ICP", "icp": "ICP", "cronos": "CRO",
    "eigenlayer": "EIGEN", "blur": "BLUR", "pendle": "PENDLE",
    "ethena": "ENA", "starknet": "STRK", "zksync": "ZK", "layerzero": "ZRO",
    "notcoin": "NOT", "io.net": "IO", "jito": "JTO", "wormhole": "W",
}

TICKER_SYMBOLS = list(set(COIN_NAMES.values()))

# =============================================================================
# STATE
# =============================================================================

# Memory buffer - crawl edilen haberler burada birikir
news_buffer: Dict[str, dict] = {}

# Hash set - duplicate kontrolü için (memory'de kalır)
seen_hashes: Set[str] = set()

# Son flush zamanı
last_flush = datetime.utcnow()

# İstatistikler
stats = {
    "crawled_this_hour": 0,
    "duplicates_skipped": 0,
    "total_flushed": 0,
    "errors": 0
}

print(f"[NewsWorker v4] Starting - Memory Buffer Mode")
print(f"  Sources: {len(RSS_SOURCES)}")
print(f"  Crawl: {CRAWL_INTERVAL}s | Flush: {FLUSH_INTERVAL}s")

# =============================================================================
# HELPERS
# =============================================================================

def generate_hash(url: str, title: str) -> str:
    """URL + title hash"""
    combined = f"{url}|{title.lower().strip()}"
    return hashlib.md5(combined.encode()).hexdigest()[:20]

def analyze_sentiment(title: str, content: str) -> dict:
    """Sentiment analizi"""
    text = f"{title} {content}".lower()

    bull_score = sum(w for k, w in BULLISH_KEYWORDS.items() if k in text)
    bear_score = sum(w for k, w in BEARISH_KEYWORDS.items() if k in text)
    net = bull_score - bear_score

    if net > 0.4:
        return {"sentiment": "bullish", "score": min(net, 1.0)}
    elif net < -0.4:
        return {"sentiment": "bearish", "score": max(-1.0, -net)}
    elif net > 0.15:
        return {"sentiment": "bullish", "score": net}
    elif net < -0.15:
        return {"sentiment": "bearish", "score": net}
    return {"sentiment": "neutral", "score": 0.0}

def extract_coins(title: str, content: str) -> List[str]:
    """Coin çıkarma"""
    text = f"{title} {content}".lower()
    found = set()

    for name, symbol in COIN_NAMES.items():
        if len(name) >= 3 and re.search(r'\b' + re.escape(name) + r'\b', text):
            found.add(symbol)

    for ticker in TICKER_SYMBOLS:
        if len(ticker) >= 3 and re.search(r'\b' + ticker + r'\b', f"{title} {content}"):
            found.add(ticker)

    found -= {"THE", "FOR", "AND", "NOT", "ALL", "NEW", "ONE", "NOW", "TOP"}
    return list(found)[:15] if found else ["GENERAL"]

def to_toml(news: dict) -> str:
    """TOML format for LLM"""
    coins = ", ".join(f'"{c}"' for c in news.get("coins", []))
    return f'''[[news]]
id = "{news.get('id', '')}"
title = """{news.get('title', '')}"""
source = "{news.get('source', '')}"
sentiment = "{news.get('sentiment', 'neutral')}"
score = {news.get('sentiment_score', 0)}
coins = [{coins}]
time = "{news.get('published_at', '')}"
'''

# =============================================================================
# CRAWLING
# =============================================================================

async def crawl_source(client: httpx.AsyncClient, source: dict) -> int:
    """Tek kaynak crawl"""
    name = source["name"]
    url = source["url"]
    tier = source.get("tier", 5)
    new_count = 0

    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code != 200:
            return 0

        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item") or soup.find_all("entry")

        for item in items[:100]:
            try:
                title = item.find("title")
                title = title.text.strip() if title else ""

                link = item.find("link")
                link = (link.get("href") or link.text or "").strip() if link else ""

                if not title or not link:
                    continue

                # Duplicate check
                news_hash = generate_hash(link, title)
                if news_hash in seen_hashes:
                    stats["duplicates_skipped"] += 1
                    continue

                # Date
                pub_date = ""
                for tag in ["pubDate", "published", "updated"]:
                    el = item.find(tag)
                    if el:
                        pub_date = el.text.strip()
                        break

                # Content
                content = ""
                for tag in ["description", "content:encoded", "content", "summary"]:
                    el = item.find(tag)
                    if el:
                        content = BeautifulSoup(el.text, "html.parser").get_text()
                        content = " ".join(content.split())[:1500]
                        break

                # Analyze
                sent = analyze_sentiment(title, content)
                coins = extract_coins(title, content)

                # Add to buffer (memory)
                news_buffer[news_hash] = {
                    "id": news_hash,
                    "title": title[:400],
                    "content": content[:1000],
                    "source": name,
                    "source_url": link,
                    "published_at": pub_date,
                    "crawled_at": datetime.utcnow().isoformat(),
                    "sentiment": sent["sentiment"],
                    "sentiment_score": round(sent["score"], 3),
                    "coins": coins,
                    "tier": tier
                }

                seen_hashes.add(news_hash)
                new_count += 1

            except:
                continue

        return new_count
    except Exception as e:
        stats["errors"] += 1
        return 0

async def crawl_all():
    """Tüm kaynakları crawl et"""
    start = time.time()
    total_new = 0

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        limits=httpx.Limits(max_connections=MAX_CONCURRENT)
    ) as client:
        # Batch crawl
        for i in range(0, len(RSS_SOURCES), MAX_CONCURRENT):
            batch = RSS_SOURCES[i:i + MAX_CONCURRENT]
            tasks = [crawl_source(client, src) for src in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, int):
                    total_new += result

            if i + MAX_CONCURRENT < len(RSS_SOURCES):
                await asyncio.sleep(0.3)

    stats["crawled_this_hour"] += total_new

    # Sadece count güncelle (data değil)
    r.set("news_buffer_count", str(len(news_buffer)))
    r.set("news_last_crawl", datetime.utcnow().isoformat())

    duration = time.time() - start
    bulls = sum(1 for n in news_buffer.values() if n["sentiment"] == "bullish")
    bears = sum(1 for n in news_buffer.values() if n["sentiment"] == "bearish")

    print(f"  Buffer: {len(news_buffer)} | +{total_new} | 🟢{bulls} 🔴{bears} | {duration:.1f}s")

def flush_to_redis():
    """Buffer'ı Redis'e flush et ve sıfırla"""
    global news_buffer, seen_hashes, last_flush

    if not news_buffer:
        print("[Flush] Buffer empty, skipping")
        return

    # Mevcut Redis verisini al
    existing = {}
    try:
        cached = r.get("news_db")
        if cached:
            existing = json.loads(cached)
    except:
        pass

    # Eski haberleri temizle (72 saatten eski)
    cutoff = (datetime.utcnow() - timedelta(hours=NEWS_RETENTION_HOURS)).isoformat()
    existing = {k: v for k, v in existing.items() if v.get("crawled_at", "") > cutoff}

    # Buffer'ı ekle
    existing.update(news_buffer)

    # Redis'e yaz
    r.set("news_db", json.dumps(existing))
    r.set("news_count", str(len(existing)))
    r.set("news_updated", datetime.utcnow().isoformat())

    # Stats
    flushed = len(news_buffer)
    stats["total_flushed"] += flushed

    print(f"[Flush] {flushed} news -> Redis | Total: {len(existing)} | Duplicates: {stats['duplicates_skipped']}")

    # Buffer'ı sıfırla (seen_hashes kalır - duplicate için)
    news_buffer.clear()
    stats["crawled_this_hour"] = 0
    stats["duplicates_skipped"] = 0
    last_flush = datetime.utcnow()

    # Seen hashes'i de trim et (çok büyürse)
    if len(seen_hashes) > 50000:
        # Son 30000'i tut
        seen_hashes.clear()
        for news_id in existing.keys():
            seen_hashes.add(news_id)
        print(f"[Cleanup] Trimmed seen_hashes to {len(seen_hashes)}")

def export_buffer_toml(limit: int = 100) -> str:
    """Buffer'ı TOML olarak export et"""
    sorted_news = sorted(
        news_buffer.values(),
        key=lambda x: x.get("crawled_at", ""),
        reverse=True
    )[:limit]

    parts = ["# News Buffer Export\n"]
    for news in sorted_news:
        parts.append(to_toml(news))
    return "\n".join(parts)

# =============================================================================
# MAIN LOOP
# =============================================================================

async def main():
    global last_flush

    # Load seen_hashes from existing Redis data
    try:
        cached = r.get("news_db")
        if cached:
            existing = json.loads(cached)
            for news_id, news in existing.items():
                h = generate_hash(news.get("source_url", ""), news.get("title", ""))
                seen_hashes.add(h)
            print(f"[Init] Loaded {len(seen_hashes)} hashes from Redis")
    except:
        pass

    crawl_count = 0

    while True:
        crawl_count += 1
        ts = datetime.utcnow().strftime('%H:%M:%S')
        print(f"\n[Crawl #{crawl_count}] {ts}")

        try:
            await crawl_all()
        except Exception as e:
            print(f"[Error] {e}")
            stats["errors"] += 1

        # Saat başı flush
        elapsed = (datetime.utcnow() - last_flush).total_seconds()
        if elapsed >= FLUSH_INTERVAL:
            print(f"\n{'='*50}")
            flush_to_redis()
            print(f"{'='*50}")
        else:
            remaining = int((FLUSH_INTERVAL - elapsed) / 60)
            print(f"  Next flush in {remaining} min")

        await asyncio.sleep(CRAWL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())