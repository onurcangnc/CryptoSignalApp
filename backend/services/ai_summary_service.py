# -*- coding: utf-8 -*-
"""
CryptoSignal - AI Summary Service
=================================
Piyasa verilerini birleştirip kapsamlı AI analizi oluşturur

Bileşenler:
1. Özet (Herkes için) - Basit dil, 2-3 cümle
2. Teknik Analiz (Detaylı) - RSI, MACD, MA'lar
3. Basit Analiz (Yeni başlayanlar) - Jargonsuz açıklama
4. Haber Analizi (Portföy bazlı) - Kullanıcının coinleri için
"""

import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from database import redis_client
from config import OPENAI_API_KEY

# OpenAI client
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except:
        pass

# Stats
ai_summary_stats = {
    "summaries_generated": 0,
    "portfolio_analyses": 0,
    "tokens_used": 0,
    "cache_hits": 0
}


@dataclass
class MarketContext:
    """Piyasa verilerini tutan yapı"""
    # Fiyat verileri
    btc_price: float = 0
    btc_change_24h: float = 0
    btc_change_7d: float = 0
    eth_price: float = 0
    eth_change_24h: float = 0
    total_market_cap: str = ""
    btc_dominance: float = 0
    
    # Fear & Greed
    fear_greed_value: int = 50
    fear_greed_label: str = "Neutral"
    
    # Teknik göstergeler (BTC)
    btc_rsi: float = 50
    btc_macd: str = "neutral"
    btc_trend: str = "NEUTRAL"
    btc_ma50: float = 0
    btc_ma200: float = 0
    btc_bb_position: float = 50
    
    # Futures
    btc_funding_rate: float = 0
    btc_long_short_ratio: float = 1
    btc_open_interest: str = ""
    
    # Haber sentiment
    news_bullish_pct: int = 0
    news_bearish_pct: int = 0
    news_neutral_pct: int = 0
    top_news_topics: List[str] = None
    
    def to_toml(self) -> str:
        """TOML formatına çevir"""
        topics = self.top_news_topics or []
        topics_str = ", ".join(f'"{t}"' for t in topics[:5])
        
        return f'''[market]
btc_price = {self.btc_price}
btc_change_24h = {self.btc_change_24h}
btc_change_7d = {self.btc_change_7d}
eth_price = {self.eth_price}
eth_change_24h = {self.eth_change_24h}
total_market_cap = "{self.total_market_cap}"
btc_dominance = {self.btc_dominance}

[sentiment]
fear_greed_value = {self.fear_greed_value}
fear_greed_label = "{self.fear_greed_label}"

[technical]
btc_rsi = {self.btc_rsi}
btc_macd = "{self.btc_macd}"
btc_trend = "{self.btc_trend}"
btc_ma50 = {self.btc_ma50}
btc_ma200 = {self.btc_ma200}
btc_bb_position = {self.btc_bb_position}

[futures]
funding_rate = {self.btc_funding_rate}
long_short_ratio = {self.btc_long_short_ratio}
open_interest = "{self.btc_open_interest}"

[news]
bullish_pct = {self.news_bullish_pct}
bearish_pct = {self.news_bearish_pct}
neutral_pct = {self.news_neutral_pct}
top_topics = [{topics_str}]
'''


class AISummaryService:
    """AI Piyasa Özeti Servisi"""
    
    def __init__(self):
        self.client = openai_client
        self.model = "gpt-4o-mini"
        self.cache_duration = 1800  # 30 dakika cache
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def get_market_context(self) -> MarketContext:
        """Redis'ten tüm piyasa verilerini topla"""
        ctx = MarketContext()
        
        try:
            # Fiyat verileri
            prices_raw = redis_client.get("prices")
            if prices_raw:
                prices = json.loads(prices_raw)
                btc = prices.get("BTC", {})
                eth = prices.get("ETH", {})
                ctx.btc_price = btc.get("price", 0)
                ctx.btc_change_24h = btc.get("change_24h", 0)
                ctx.btc_change_7d = btc.get("change_7d", 0)
                ctx.eth_price = eth.get("price", 0)
                ctx.eth_change_24h = eth.get("change_24h", 0)
            
            # Market cap
            market_raw = redis_client.get("market_data")
            if market_raw:
                market = json.loads(market_raw)
                cap = market.get("total_market_cap", 0)
                if cap >= 1e12:
                    ctx.total_market_cap = f"${cap/1e12:.2f}T"
                else:
                    ctx.total_market_cap = f"${cap/1e9:.0f}B"
                ctx.btc_dominance = market.get("btc_dominance", 0)
            
            # Fear & Greed
            fg_raw = redis_client.get("fear_greed")
            if fg_raw:
                fg = json.loads(fg_raw)
                ctx.fear_greed_value = int(fg.get("value", 50))
                ctx.fear_greed_label = fg.get("classification", "Neutral")
            
            # Teknik analiz (BTC)
            tech_raw = redis_client.get("technical_btc")
            if tech_raw:
                tech = json.loads(tech_raw)
                ctx.btc_rsi = tech.get("rsi", 50)
                ctx.btc_trend = tech.get("trend", "NEUTRAL")
                ctx.btc_ma50 = tech.get("ma", {}).get("ma_50", 0)
                ctx.btc_ma200 = tech.get("ma", {}).get("ma_200", 0)
                ctx.btc_bb_position = tech.get("bollinger", {}).get("position", 50)
                macd = tech.get("macd", 0)
                ctx.btc_macd = "positive" if macd and macd > 0 else "negative" if macd else "neutral"
            
            # Futures
            futures_raw = redis_client.get("futures_data")
            if futures_raw:
                futures = json.loads(futures_raw)
                btc_fut = futures.get("BTCUSDT", {})
                ctx.btc_funding_rate = btc_fut.get("funding_rate", 0)
                ctx.btc_long_short_ratio = btc_fut.get("long_short_ratio", 1)
                oi = btc_fut.get("open_interest", 0)
                ctx.btc_open_interest = f"${oi/1e9:.1f}B" if oi else ""
            
            # Haber sentiment
            news_raw = redis_client.get("news_db")
            if news_raw:
                news = json.loads(news_raw)
                news_list = list(news.values())
                total = len(news_list) or 1
                bullish = sum(1 for n in news_list if n.get("sentiment") == "bullish")
                bearish = sum(1 for n in news_list if n.get("sentiment") == "bearish")
                ctx.news_bullish_pct = int(bullish / total * 100)
                ctx.news_bearish_pct = int(bearish / total * 100)
                ctx.news_neutral_pct = 100 - ctx.news_bullish_pct - ctx.news_bearish_pct
                
                # Top topics (en çok geçen coinler)
                coin_counts = {}
                for n in news_list[:100]:
                    for c in n.get("coins", []):
                        if c != "GENERAL":
                            coin_counts[c] = coin_counts.get(c, 0) + 1
                ctx.top_news_topics = sorted(coin_counts, key=coin_counts.get, reverse=True)[:5]
        
        except Exception as e:
            print(f"[AI Summary] Context error: {e}")
        
        return ctx
    
    async def generate_full_summary(self, user_coins: List[str] = None) -> Dict:
        """
        Tam AI özeti oluştur
        
        Args:
            user_coins: Kullanıcının portföyündeki coinler (opsiyonel)
        
        Returns:
            {
                "simple_summary": "...",
                "technical_analysis": {...},
                "beginner_analysis": "...",
                "portfolio_news": [...],
                "charts_data": {...},
                "generated_at": "..."
            }
        """
        # Cache kontrolü
        cache_key = f"ai_summary:{','.join(sorted(user_coins or ['general']))}"
        cached = redis_client.get(cache_key)
        if cached:
            ai_summary_stats["cache_hits"] += 1
            return json.loads(cached)
        
        # Market context al
        ctx = await self.get_market_context()
        
        # Sonuç objesi
        result = {
            "market_overview": {
                "btc_price": ctx.btc_price,
                "btc_change_24h": ctx.btc_change_24h,
                "btc_change_7d": ctx.btc_change_7d,
                "eth_price": ctx.eth_price,
                "eth_change_24h": ctx.eth_change_24h,
                "total_market_cap": ctx.total_market_cap,
                "btc_dominance": ctx.btc_dominance,
                "fear_greed": {
                    "value": ctx.fear_greed_value,
                    "label": ctx.fear_greed_label
                }
            },
            "technical": {
                "rsi": ctx.btc_rsi,
                "rsi_status": self._get_rsi_status(ctx.btc_rsi),
                "macd": ctx.btc_macd,
                "trend": ctx.btc_trend,
                "ma50": ctx.btc_ma50,
                "ma200": ctx.btc_ma200,
                "ma50_status": "above" if ctx.btc_price > ctx.btc_ma50 else "below",
                "ma200_status": "above" if ctx.btc_price > ctx.btc_ma200 else "below",
                "bb_position": ctx.btc_bb_position,
                "bb_status": self._get_bb_status(ctx.btc_bb_position)
            },
            "futures": {
                "funding_rate": ctx.btc_funding_rate,
                "funding_status": self._get_funding_status(ctx.btc_funding_rate),
                "long_short_ratio": ctx.btc_long_short_ratio,
                "ls_status": self._get_ls_status(ctx.btc_long_short_ratio),
                "open_interest": ctx.btc_open_interest
            },
            "news_sentiment": {
                "bullish": ctx.news_bullish_pct,
                "bearish": ctx.news_bearish_pct,
                "neutral": ctx.news_neutral_pct,
                "trending_coins": ctx.top_news_topics or []
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # LLM ile özetler oluştur
        if self.client:
            try:
                llm_result = await self._generate_llm_analysis(ctx, user_coins)
                result["simple_summary"] = llm_result.get("simple_summary", "")
                result["beginner_analysis"] = llm_result.get("beginner_analysis", {})
                result["recommendation"] = llm_result.get("recommendation", "")
                
                ai_summary_stats["summaries_generated"] += 1
                ai_summary_stats["tokens_used"] += llm_result.get("tokens_used", 0)
            except Exception as e:
                print(f"[AI Summary] LLM error: {e}")
                result["simple_summary"] = self._generate_fallback_summary(ctx)
                result["beginner_analysis"] = self._generate_fallback_beginner(ctx)
        else:
            result["simple_summary"] = self._generate_fallback_summary(ctx)
            result["beginner_analysis"] = self._generate_fallback_beginner(ctx)
        
        # Portföy haberleri
        if user_coins:
            result["portfolio_news"] = await self._get_portfolio_news(user_coins)
        
        # Cache'e kaydet
        redis_client.setex(cache_key, self.cache_duration, json.dumps(result))
        
        return result
    
    async def _generate_llm_analysis(self, ctx: MarketContext, user_coins: List[str] = None) -> Dict:
        """LLM ile analiz oluştur"""
        coins_str = ", ".join(user_coins) if user_coins else "genel piyasa"
        
        prompt = f'''Sen bir kripto analisti. Aşağıdaki piyasa verilerini analiz et.

{ctx.to_toml()}

[user_context]
portfolio_coins = "{coins_str}"

ÜÇ FARKLI ANALİZ OLUŞTUR:

1. SIMPLE_SUMMARY (2-3 cümle, herkes anlasın):
- Piyasa ne durumda?
- Ne beklenebilir?

2. BEGINNER_ANALYSIS (yeni başlayanlar için, jargonsuz):
- overall_status: "iyi" | "kötü" | "karışık"
- explanation: 2-3 madde, basit dille
- what_to_do: 1 cümle öneri
- risk_warning: 1 cümle risk

3. RECOMMENDATION (tek kelime):
- "AL" | "SAT" | "BEKLE"

JSON formatında yanıt ver:
{{
  "simple_summary": "...",
  "beginner_analysis": {{
    "overall_status": "iyi",
    "explanation": ["...", "..."],
    "what_to_do": "...",
    "risk_warning": "..."
  }},
  "recommendation": "BEKLE"
}}'''

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["tokens_used"] = response.usage.total_tokens
        
        return result
    
    async def _get_portfolio_news(self, coins: List[str]) -> List[Dict]:
        """Portföy coinleri için haber analizi"""
        try:
            news_raw = redis_client.get("news_db")
            if not news_raw:
                return []
            
            news_dict = json.loads(news_raw)
            news_list = list(news_dict.values())
            
            portfolio_news = []
            for coin in coins[:10]:  # Max 10 coin
                coin_news = [n for n in news_list if coin in (n.get("coins") or [])]
                if coin_news:
                    bullish = sum(1 for n in coin_news if n.get("sentiment") == "bullish")
                    bearish = sum(1 for n in coin_news if n.get("sentiment") == "bearish")
                    total = len(coin_news)
                    
                    if bullish > bearish:
                        sentiment = "bullish"
                    elif bearish > bullish:
                        sentiment = "bearish"
                    else:
                        sentiment = "neutral"
                    
                    # En son 3 haber başlığı
                    recent = sorted(coin_news, key=lambda x: x.get("crawled_at", ""), reverse=True)[:3]
                    headlines = [n.get("title", "")[:100] for n in recent]
                    
                    portfolio_news.append({
                        "coin": coin,
                        "news_count": total,
                        "sentiment": sentiment,
                        "bullish_count": bullish,
                        "bearish_count": bearish,
                        "headlines": headlines
                    })
            
            return portfolio_news
        
        except Exception as e:
            print(f"[AI Summary] Portfolio news error: {e}")
            return []
    
    async def analyze_portfolio_news_llm(self, coins: List[str]) -> Optional[Dict]:
        """Portföy haberleri için LLM analizi (ayrı endpoint)"""
        if not self.client or not coins:
            return None
        
        # Cache kontrolü
        cache_key = f"portfolio_news_llm:{','.join(sorted(coins))}"
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        try:
            news_raw = redis_client.get("news_db")
            if not news_raw:
                return None
            
            news_dict = json.loads(news_raw)
            news_list = list(news_dict.values())
            
            # Portföy coinleriyle ilgili haberleri topla
            relevant_news = []
            for n in news_list:
                news_coins = n.get("coins", [])
                if any(c in news_coins for c in coins):
                    relevant_news.append({
                        "title": n.get("title", "")[:150],
                        "sentiment": n.get("sentiment", "neutral"),
                        "coins": [c for c in news_coins if c in coins]
                    })
            
            if not relevant_news:
                return None
            
            # Max 30 haber
            relevant_news = relevant_news[:30]
            
            # TOML format
            news_toml = ""
            for i, n in enumerate(relevant_news):
                coins_str = ", ".join(f'"{c}"' for c in n["coins"])
                news_toml += f'''
[[news]]
title = """{n["title"]}"""
sentiment = "{n["sentiment"]}"
coins = [{coins_str}]
'''
            
            prompt = f'''Kullanıcının portföyündeki coinler: {", ".join(coins)}

Bu coinlerle ilgili haberler:
{news_toml}

Her coin için Türkçe analiz yap:
1. Genel sentiment (olumlu/olumsuz/karışık)
2. Öne çıkan 2 konu
3. Risk/fırsat

JSON formatında:
{{
  "analyses": [
    {{
      "coin": "BTC",
      "sentiment": "olumlu",
      "sentiment_emoji": "🟢",
      "highlights": ["ETF onayları devam ediyor", "Kurumsal alımlar artıyor"],
      "risk_opportunity": "Kısa vadede düzeltme riski var ama uzun vade olumlu"
    }}
  ],
  "overall": "Portföyünüz için haberler genel olarak olumlu."
}}'''

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["generated_at"] = datetime.utcnow().isoformat()
            
            ai_summary_stats["portfolio_analyses"] += 1
            ai_summary_stats["tokens_used"] += response.usage.total_tokens
            
            # 1 saat cache
            redis_client.setex(cache_key, 3600, json.dumps(result))
            
            return result
        
        except Exception as e:
            print(f"[AI Summary] Portfolio LLM error: {e}")
            return None
    
    def _get_rsi_status(self, rsi: float) -> str:
        if rsi >= 70:
            return "overbought"
        elif rsi <= 30:
            return "oversold"
        elif rsi >= 60:
            return "high"
        elif rsi <= 40:
            return "low"
        return "neutral"
    
    def _get_bb_status(self, position: float) -> str:
        if position >= 80:
            return "upper"
        elif position <= 20:
            return "lower"
        return "middle"
    
    def _get_funding_status(self, rate: float) -> str:
        if rate > 0.05:
            return "high_long"
        elif rate < -0.05:
            return "high_short"
        return "neutral"
    
    def _get_ls_status(self, ratio: float) -> str:
        if ratio > 1.5:
            return "long_heavy"
        elif ratio < 0.7:
            return "short_heavy"
        return "balanced"
    
    def _generate_fallback_summary(self, ctx: MarketContext) -> str:
        """LLM olmadan basit özet"""
        parts = []
        
        # Fiyat değişimi
        if ctx.btc_change_24h > 3:
            parts.append(f"Bitcoin son 24 saatte %{ctx.btc_change_24h:.1f} yükseldi.")
        elif ctx.btc_change_24h < -3:
            parts.append(f"Bitcoin son 24 saatte %{abs(ctx.btc_change_24h):.1f} düştü.")
        else:
            parts.append(f"Bitcoin son 24 saatte %{ctx.btc_change_24h:.1f} değişim gösterdi.")
        
        # Fear & Greed
        if ctx.fear_greed_value >= 70:
            parts.append("Piyasada aşırı açgözlülük var, dikkatli olun.")
        elif ctx.fear_greed_value <= 30:
            parts.append("Piyasada korku hakim, fırsatlar olabilir.")
        else:
            parts.append("Piyasa nötr seviyelerde.")
        
        return " ".join(parts)
    
    def _generate_fallback_beginner(self, ctx: MarketContext) -> Dict:
        """LLM olmadan basit analiz"""
        if ctx.btc_change_24h > 2 and ctx.fear_greed_value > 50:
            status = "iyi"
            explanation = [
                "Bitcoin yükselişte",
                "Yatırımcılar iyimser"
            ]
            what_to_do = "Elindekini tut, yeni alım için bekle"
        elif ctx.btc_change_24h < -2 and ctx.fear_greed_value < 50:
            status = "kötü"
            explanation = [
                "Bitcoin düşüşte",
                "Piyasada korku var"
            ]
            what_to_do = "Panik satışı yapma, sabırlı ol"
        else:
            status = "karışık"
            explanation = [
                "Piyasa yatay hareket ediyor",
                "Belirgin bir yön yok"
            ]
            what_to_do = "Bekle ve izle"
        
        return {
            "overall_status": status,
            "explanation": explanation,
            "what_to_do": what_to_do,
            "risk_warning": "Kripto yatırımı risklidir, kaybetmeyi göze alabileceğin kadar yatır."
        }
    
    def get_stats(self) -> Dict:
        return ai_summary_stats


# Singleton
ai_summary_service = AISummaryService()