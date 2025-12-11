#!/usr/bin/env python3
"""
CryptoSignal - AI News Analyzer v1.0
====================================
Haberleri OpenAI/Claude ile analiz edip sinyal sistemine entegre eder.

Özellikler:
- Her haber için AI sentiment analizi
- Coin bazlı etki skoru
- Regülasyon/hack/partnership kategorileri
- Sinyal worker'a veri sağlar
"""

import json
import time
import redis
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Configuration
REDIS_PASS = "3f9af2788cb89aa74c06bd48dd290658"
r = redis.Redis(host='localhost', port=6379, password=REDIS_PASS, decode_responses=True)

# API Keys - Environment'tan al
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Ayarlar
UPDATE_INTERVAL = 3600  # 1 saat (optimize edilmiş - haberler yavaş değişir)
MAX_NEWS_TO_ANALYZE = 30  # Her döngüde max analiz edilecek haber (sadece önemliler)
ANALYSIS_CACHE_HOURS = 12  # Analiz cache süresi (artırıldı)

print("[AI News Analyzer v1.0] Starting...")


# =============================================================================
# AI ANALYSIS PROMPTS
# =============================================================================

NEWS_ANALYSIS_PROMPT = """Analyze this cryptocurrency news and provide a structured assessment.

NEWS TITLE: {title}
NEWS CONTENT: {content}
SOURCE: {source}

Respond ONLY in this exact JSON format:
{{
    "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
    "sentiment_score": -1.0 to 1.0,
    "impact_level": "HIGH" | "MEDIUM" | "LOW",
    "category": "REGULATION" | "PARTNERSHIP" | "HACK" | "ADOPTION" | "TECHNICAL" | "MARKET" | "OTHER",
    "affected_coins": ["BTC", "ETH", ...],
    "price_prediction": "UP" | "DOWN" | "STABLE",
    "confidence": 0.0 to 1.0,
    "key_points": ["point1", "point2"],
    "risk_factors": ["risk1", "risk2"],
    "time_horizon": "SHORT" | "MEDIUM" | "LONG",
    "summary_tr": "Türkçe özet (max 100 karakter)"
}}

Rules:
- sentiment_score: -1.0 (very bearish) to 1.0 (very bullish)
- Be objective, don't exaggerate
- If uncertain, use NEUTRAL and low confidence
- affected_coins should only include coins DIRECTLY mentioned or affected
- HIGH impact = price move >5% expected, MEDIUM = 2-5%, LOW = <2%
"""

BATCH_ANALYSIS_PROMPT = """Analyze these cryptocurrency news items and provide market sentiment.

NEWS ITEMS:
{news_items}

Provide analysis in this JSON format:
{{
    "overall_market_sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
    "overall_score": -1.0 to 1.0,
    "dominant_themes": ["theme1", "theme2"],
    "high_impact_news": [
        {{"title": "...", "coin": "BTC", "impact": "HIGH", "direction": "UP"}}
    ],
    "risk_alerts": ["alert1", "alert2"],
    "coin_sentiments": {{
        "BTC": {{"sentiment": "BULLISH", "score": 0.6, "news_count": 5}},
        "ETH": {{"sentiment": "NEUTRAL", "score": 0.1, "news_count": 3}}
    }},
    "market_summary_tr": "Türkçe piyasa özeti (max 200 karakter)"
}}
"""


# =============================================================================
# AI API CALLS
# =============================================================================

async def analyze_with_openai(prompt: str) -> Optional[Dict]:
    """OpenAI API ile analiz"""
    if not OPENAI_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # Maliyet optimize
                    "messages": [
                        {"role": "system", "content": "You are a cryptocurrency market analyst. Always respond in valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data['choices'][0]['message']['content']
                # JSON parse
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content)
    except Exception as e:
        print(f"[OpenAI] Error: {e}")
    
    return None


async def analyze_with_claude(prompt: str) -> Optional[Dict]:
    """Claude API ile analiz"""
    if not ANTHROPIC_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",  # Maliyet optimize
                    "max_tokens": 1000,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data['content'][0]['text']
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content)
    except Exception as e:
        print(f"[Claude] Error: {e}")
    
    return None


async def analyze_news_item(news: Dict) -> Optional[Dict]:
    """Tek bir haberi analiz et"""
    title = news.get('title', '')
    content = news.get('content', '')[:500]
    source = news.get('source', '')
    
    prompt = NEWS_ANALYSIS_PROMPT.format(
        title=title,
        content=content,
        source=source
    )
    
    # Önce OpenAI dene, yoksa Claude
    result = await analyze_with_openai(prompt)
    if not result:
        result = await analyze_with_claude(prompt)
    
    return result


async def analyze_news_batch(news_list: List[Dict]) -> Optional[Dict]:
    """Toplu haber analizi - genel piyasa sentiment'i"""
    if not news_list:
        return None
    
    # News items formatla
    items_text = ""
    for i, news in enumerate(news_list[:20], 1):
        items_text += f"{i}. [{news.get('source', '')}] {news.get('title', '')}\n"
    
    prompt = BATCH_ANALYSIS_PROMPT.format(news_items=items_text)
    
    result = await analyze_with_openai(prompt)
    if not result:
        result = await analyze_with_claude(prompt)
    
    return result


# =============================================================================
# IMPORTANT NEWS FILTER (Optimize LLM costs)
# =============================================================================

def is_important_news(news: Dict) -> bool:
    """
    Haber önemli mi kontrol et - sadece yüksek etkili haberleri LLM'e gönder
    Bu %60-70 maliyet azalması sağlar ve kaliteyi artırır
    """
    title = news.get('title', '').lower()
    content = news.get('content', '').lower()
    source = news.get('source', '').lower()

    # Yüksek etkili kaynaklar
    important_sources = [
        'coindesk', 'cointelegraph', 'bloomberg', 'reuters',
        'wsj', 'financial times', 'cnbc', 'decrypt', 'theblock'
    ]

    # Yüksek etkili kelimeler (regülasyon, güvenlik, büyük ortaklıklar)
    important_keywords = [
        'sec', 'etf', 'approved', 'ban', 'regulation', 'lawsuit',
        'hack', 'exploit', 'vulnerability', 'breach',
        'partnership', 'acquisition', 'merger', 'integration',
        'btc', 'bitcoin', 'ethereum', 'binance', 'coinbase',
        'fed', 'government', 'congress', 'senate',
        'billion', 'institutional', 'blackrock', 'fidelity'
    ]

    # Kaynak önemli mi?
    if any(src in source for src in important_sources):
        return True

    # Kritik keyword var mı (title veya content)?
    text = title + ' ' + content[:200]  # İlk 200 char yeterli
    if any(kw in text for kw in important_keywords):
        return True

    return False


# =============================================================================
# FALLBACK - KEYWORD ANALYSIS (API yoksa)
# =============================================================================

BULLISH_KEYWORDS = {
    'surge': 0.3, 'rally': 0.3, 'breakout': 0.25, 'bullish': 0.3,
    'soar': 0.3, 'jump': 0.2, 'gain': 0.15, 'rise': 0.15,
    'partnership': 0.25, 'adoption': 0.3, 'etf': 0.35, 'approved': 0.35,
    'institutional': 0.3, 'accumulate': 0.25, 'upgrade': 0.2,
    'launch': 0.2, 'integrate': 0.2, 'milestone': 0.2
}

BEARISH_KEYWORDS = {
    'crash': -0.4, 'dump': -0.35, 'plunge': -0.35, 'bearish': -0.3,
    'fall': -0.2, 'decline': -0.2, 'drop': -0.2, 'sell': -0.15,
    'hack': -0.5, 'exploit': -0.45, 'scam': -0.5, 'fraud': -0.45,
    'lawsuit': -0.35, 'sec': -0.3, 'ban': -0.4, 'regulation': -0.2,
    'liquidation': -0.3, 'bankruptcy': -0.5, 'delay': -0.15
}

def analyze_with_keywords(news: Dict) -> Dict:
    """Fallback: Keyword tabanlı analiz"""
    text = (news.get('title', '') + ' ' + news.get('content', '')).lower()
    
    score = 0
    matched_bull = []
    matched_bear = []
    
    for word, weight in BULLISH_KEYWORDS.items():
        if word in text:
            score += weight
            matched_bull.append(word)
    
    for word, weight in BEARISH_KEYWORDS.items():
        if word in text:
            score += weight  # weight zaten negatif
            matched_bear.append(word)
    
    # Normalize score to -1 to 1
    score = max(-1, min(1, score))
    
    if score > 0.2:
        sentiment = "BULLISH"
    elif score < -0.2:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"
    
    # Impact estimation
    impact = "HIGH" if abs(score) > 0.4 else "MEDIUM" if abs(score) > 0.2 else "LOW"
    
    return {
        "sentiment": sentiment,
        "sentiment_score": round(score, 2),
        "impact_level": impact,
        "category": "OTHER",
        "affected_coins": news.get('coins', []),
        "confidence": min(0.7, 0.3 + len(matched_bull + matched_bear) * 0.1),
        "key_points": matched_bull[:3] if matched_bull else matched_bear[:3],
        "analyzed_by": "keyword_fallback"
    }


# =============================================================================
# TWO-STAGE SMART ANALYSIS (Optimize LLM costs)
# =============================================================================

async def analyze_news_smart(news: Dict) -> Dict:
    """
    İki aşamalı akıllı analiz:
    1. Önce keyword analizi yap (ücretsiz)
    2. Confidence düşükse LLM kullan (ücretli)

    Bu %70-80 maliyet azalması sağlar
    """
    # Aşama 1: Keyword analizi
    keyword_result = analyze_with_keywords(news)

    # Aşama 2: Confidence düşükse veya karmaşık ise LLM kullan
    if keyword_result['confidence'] < 0.6:
        # LLM ile analiz et
        llm_result = await analyze_news_item(news)
        if llm_result:
            llm_result['analyzed_by'] = 'ai_llm'
            return llm_result

    # Keyword sonucu yeterli
    keyword_result['analyzed_by'] = 'keyword_only'
    return keyword_result


# =============================================================================
# MAIN ANALYSIS LOOP
# =============================================================================

async def process_news():
    """Ana haber işleme döngüsü"""
    
    # Haberleri Redis'ten al
    news_raw = r.get("news_db")
    if not news_raw:
        print("[AI News] No news data found")
        return
    
    news_db = json.loads(news_raw)
    if isinstance(news_db, dict):
        news_list = list(news_db.values())
    else:
        news_list = news_db
    
    # Sadece son 24 saatin haberlerini al
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    recent_news = [n for n in news_list if n.get('crawled_at', '') > cutoff]
    
    print(f"[AI News] Processing {len(recent_news)} recent news...")
    
    # Daha önce analiz edilmemiş haberleri bul
    analyzed_cache = json.loads(r.get("ai_news_analyzed") or "{}")
    to_analyze = []
    
    for news in recent_news:
        news_id = news.get('id', '')
        cached = analyzed_cache.get(news_id)
        
        # Cache'de yoksa veya çok eskiyse analiz et
        if not cached:
            to_analyze.append(news)
        elif cached.get('analyzed_at', '') < (datetime.utcnow() - timedelta(hours=ANALYSIS_CACHE_HOURS)).isoformat():
            to_analyze.append(news)
    
    print(f"[AI News] {len(to_analyze)} news need analysis")

    # 🔥 OPTİMİZASYON: Sadece önemli haberleri filtrele
    important_news = [n for n in to_analyze if is_important_news(n)]
    print(f"[AI News] {len(important_news)} important news filtered from {len(to_analyze)}")

    # Analiz et (max limit)
    analyzed_count = 0
    llm_used_count = 0
    keyword_only_count = 0
    api_available = bool(OPENAI_API_KEY or ANTHROPIC_API_KEY)

    for news in important_news[:MAX_NEWS_TO_ANALYZE]:
        news_id = news.get('id', '')

        if api_available:
            # 🔥 OPTİMİZASYON: İki aşamalı akıllı analiz
            analysis = await analyze_news_smart(news)

            # İstatistik tut
            if analysis.get('analyzed_by') == 'ai_llm':
                llm_used_count += 1
            else:
                keyword_only_count += 1
        else:
            analysis = analyze_with_keywords(news)

        analysis['analyzed_at'] = datetime.utcnow().isoformat()
        analyzed_cache[news_id] = analysis
        analyzed_count += 1

        # Rate limit
        if api_available and analysis.get('analyzed_by') == 'ai_llm':
            await asyncio.sleep(0.5)
    
    print(f"[AI News] ✅ Analyzed {analyzed_count} news items (LLM: {llm_used_count}, Keyword: {keyword_only_count})")
    print(f"[AI News] 💰 Cost optimization: {(keyword_only_count / max(analyzed_count, 1) * 100):.1f}% saved by keyword-only analysis")

    # Batch analiz - genel piyasa sentiment'i
    market_analysis = None
    if api_available and len(recent_news) >= 5:
        print("[AI News] Running batch market analysis...")
        market_analysis = await analyze_news_batch(recent_news[:20])
    
    # Coin bazlı sentiment hesapla
    coin_sentiments = {}
    
    for news in recent_news:
        news_id = news.get('id', '')
        analysis = analyzed_cache.get(news_id, {})
        
        affected_coins = analysis.get('affected_coins', news.get('coins', []))
        sentiment_score = analysis.get('sentiment_score', 0)
        impact = analysis.get('impact_level', 'LOW')
        
        # Impact multiplier
        impact_mult = {'HIGH': 2.0, 'MEDIUM': 1.0, 'LOW': 0.5}.get(impact, 0.5)
        weighted_score = sentiment_score * impact_mult
        
        for coin in affected_coins:
            if coin == 'GENERAL':
                continue
            
            if coin not in coin_sentiments:
                coin_sentiments[coin] = {
                    'total_score': 0,
                    'count': 0,
                    'bullish': 0,
                    'bearish': 0,
                    'high_impact': []
                }
            
            coin_sentiments[coin]['total_score'] += weighted_score
            coin_sentiments[coin]['count'] += 1
            
            if sentiment_score > 0.2:
                coin_sentiments[coin]['bullish'] += 1
            elif sentiment_score < -0.2:
                coin_sentiments[coin]['bearish'] += 1
            
            if impact == 'HIGH':
                coin_sentiments[coin]['high_impact'].append({
                    'title': news.get('title', '')[:100],
                    'sentiment': analysis.get('sentiment', 'NEUTRAL'),
                    'score': sentiment_score
                })
    
    # Final sentiment hesapla
    for coin, data in coin_sentiments.items():
        if data['count'] > 0:
            avg_score = data['total_score'] / data['count']
            
            if avg_score > 0.15:
                sentiment = 'BULLISH'
            elif avg_score < -0.15:
                sentiment = 'BEARISH'
            else:
                sentiment = 'NEUTRAL'
            
            data['sentiment'] = sentiment
            data['avg_score'] = round(avg_score, 3)
            data['high_impact'] = data['high_impact'][:3]  # Max 3
    
    # Redis'e kaydet
    r.set("ai_news_analyzed", json.dumps(analyzed_cache))
    r.set("ai_coin_sentiments", json.dumps(coin_sentiments))
    r.set("ai_news_updated", datetime.utcnow().isoformat())
    
    if market_analysis:
        r.set("ai_market_analysis", json.dumps(market_analysis))
    
    # Stats
    total_analyzed = len([a for a in analyzed_cache.values() if a.get('analyzed_by') == 'ai'])
    fallback_count = len([a for a in analyzed_cache.values() if a.get('analyzed_by') == 'keyword_fallback'])
    
    print(f"[AI News] Complete!")
    print(f"   AI analyzed: {total_analyzed}")
    print(f"   Keyword fallback: {fallback_count}")
    print(f"   Coins with sentiment: {len(coin_sentiments)}")
    
    # Sample output
    for coin in ['BTC', 'ETH', 'SOL']:
        if coin in coin_sentiments:
            cs = coin_sentiments[coin]
            print(f"   {coin}: {cs.get('sentiment', 'N/A')} (score: {cs.get('avg_score', 0):.2f}, news: {cs.get('count', 0)})")


async def main():
    """30 dakikada bir çalıştır"""
    
    if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        print("[AI News] ⚠️ No API key found! Using keyword fallback only.")
        print("[AI News] Set OPENAI_API_KEY or ANTHROPIC_API_KEY for AI analysis.")
    else:
        print(f"[AI News] ✅ Using {'OpenAI' if OPENAI_API_KEY else 'Claude'} for analysis")
    
    print(f"[AI News] Update interval: {UPDATE_INTERVAL}s ({UPDATE_INTERVAL//60} min)")
    
    while True:
        try:
            await process_news()
        except Exception as e:
            print(f"[AI News] Error: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())