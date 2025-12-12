# -*- coding: utf-8 -*-
"""
CryptoSignal - LLM Service
==========================
OpenAI API ile AI özellikleri
"""

import os
import json
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import OPENAI_API_KEY
from database import save_llm_analytics

# OpenAI client
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("[LLM Service] OpenAI initialized")
    except Exception as e:
        print(f"[LLM Service] OpenAI init failed: {e}")

# Stats tracking
llm_stats = {
    "digest": 0,
    "forecast": 0,
    "analysis": 0,
    "news_analysis": 0,
    "tokens_in": 0,
    "tokens_out": 0
}


class LLMService:
    """OpenAI API servisi"""

    # Cost per 1M tokens for gpt-4o-mini (approximate)
    COST_PER_1M_INPUT = 0.15  # $0.15 per 1M input tokens
    COST_PER_1M_OUTPUT = 0.60  # $0.60 per 1M output tokens

    def __init__(self):
        self.client = openai_client
        self.model = "gpt-4o-mini"
        self.enabled = openai_client is not None

    def is_available(self) -> bool:
        """LLM kullanılabilir mi?"""
        return self.enabled

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Token maliyetini hesapla"""
        input_cost = (input_tokens / 1_000_000) * self.COST_PER_1M_INPUT
        output_cost = (output_tokens / 1_000_000) * self.COST_PER_1M_OUTPUT
        return input_cost + output_cost

    def _track_usage(self, user_id: str, feature: str, input_tokens: int,
                     output_tokens: int, response_time_ms: int):
        """LLM kullanımını veritabanına kaydet"""
        try:
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)
            save_llm_analytics(
                user_id=user_id,
                feature=feature,
                tokens_used=total_tokens,
                cost_usd=cost,
                model=self.model,
                response_time_ms=response_time_ms
            )
        except Exception as e:
            print(f"[LLM Analytics Error] {e}")
    
    async def generate_digest(self, news: List[Dict], coins: List[str], user_id: str = None) -> Optional[str]:
        """
        AI Market Özeti oluştur

        Args:
            news: Haber listesi
            coins: Kullanıcının takip ettiği coinler
            user_id: Kullanıcı ID (analytics için)

        Returns:
            Özet metni veya None
        """
        if not self.client or not news:
            return None

        start_time = time.time()

        try:
            news_text = "\n".join([
                f"[{n.get('sentiment', 'neutral').upper()}] {n.get('title', '')}"
                for n in news[:15]
            ])

            prompt = f"""You are a crypto analyst. Analyze these news for someone holding {', '.join(coins)}.

News:
{news_text}

Provide a concise 2-3 sentence actionable summary in Turkish. Focus on:
- Key market movements
- Risks to watch
- Opportunities

Be direct and practical. Start with the most important insight."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.5
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            llm_stats["digest"] += 1
            llm_stats["tokens_in"] += response.usage.prompt_tokens
            llm_stats["tokens_out"] += response.usage.completion_tokens

            # Track analytics
            if user_id:
                self._track_usage(
                    user_id=user_id,
                    feature="news_digest",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    response_time_ms=response_time_ms
                )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[LLM Digest Error] {e}")
            return None
    
    async def analyze_portfolio(self, holdings: List[Dict], market_data: Dict, user_id: str = None) -> Optional[Dict]:
        """
        Portföy AI analizi

        Args:
            holdings: Kullanıcının varlıkları
            market_data: Piyasa verileri
            user_id: Kullanıcı ID (analytics için)

        Returns:
            Analiz sonucu
        """
        if not self.client or not holdings:
            return None

        start_time = time.time()

        try:
            # Portföy özeti oluştur
            portfolio_text = ""
            total_value = 0
            total_pnl = 0

            for h in holdings:
                coin = h.get("coin", "")
                value = h.get("current_value_usd", 0)
                pnl = h.get("profit_loss_usd", 0)
                pnl_pct = h.get("profit_loss_pct", 0)
                total_value += value
                total_pnl += pnl

                portfolio_text += f"- {coin}: ${value:.2f} ({pnl_pct:+.1f}%)\n"

            prompt = f"""Analyze this crypto portfolio and provide advice in Turkish.

Portfolio (Total: ${total_value:.2f}, P/L: ${total_pnl:.2f}):
{portfolio_text}

Market Context:
- Fear & Greed: {market_data.get('fear_greed', 50)}

Provide:
1. Risk score (1-10)
2. Brief assessment (1 sentence per coin)
3. 2-3 actionable recommendations

Format as JSON:
{{
  "risk_score": 7,
  "risk_level": "riskli|orta|güvenli",
  "assessment": "Overall assessment...",
  "coins": [
    {{"symbol": "BTC", "action": "TUT|AL|SAT", "reason": "..."}},
  ],
  "recommendations": ["...", "..."]
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            llm_stats["analysis"] += 1
            llm_stats["tokens_in"] += response.usage.prompt_tokens
            llm_stats["tokens_out"] += response.usage.completion_tokens

            # Track analytics
            if user_id:
                self._track_usage(
                    user_id=user_id,
                    feature="portfolio_analysis",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    response_time_ms=response_time_ms
                )

            result = json.loads(response.choices[0].message.content)
            result["generated_at"] = datetime.utcnow().isoformat()

            return result

        except Exception as e:
            print(f"[LLM Portfolio Analysis Error] {e}")
            return None
    
    async def analyze_news_batch(
        self,
        news_list: List[Dict],
        target_coins: List[str] = None,
        user_id: str = None
    ) -> List[Dict]:
        """
        Haber batch analizi

        Args:
            news_list: Analiz edilecek haberler
            target_coins: Hedef coinler
            user_id: Kullanıcı ID (analytics için)

        Returns:
            Analiz edilmiş haberler
        """
        if not self.client or not news_list:
            return news_list

        start_time = time.time()

        try:
            # Build news text
            news_text = ""
            for idx, n in enumerate(news_list[:15]):
                title = n.get("title", "")[:100]
                content = n.get("content", "")[:200]
                news_text += f"\n[{idx+1}] {title}\n    {content}\n"

            coins_str = ', '.join(target_coins) if target_coins else 'general market'

            prompt = f"""Analyze these crypto news items for {coins_str}.

For EACH news item, determine:
1. SENTIMENT: BULLISH / BEARISH / NEUTRAL
2. IMPACT: HIGH / MEDIUM / LOW
3. CONFIDENCE: 0-100
4. KEY_INSIGHT: One sentence (max 15 words)

NEWS ITEMS:
{news_text}

Respond ONLY in JSON:
{{
  "analyses": [
    {{"idx": 1, "sentiment": "BULLISH", "impact": "HIGH", "confidence": 85, "insight": "..."}},
    ...
  ]
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            llm_stats["news_analysis"] += 1
            llm_stats["tokens_in"] += response.usage.prompt_tokens
            llm_stats["tokens_out"] += response.usage.completion_tokens

            # Track analytics
            if user_id:
                self._track_usage(
                    user_id=user_id,
                    feature="news_analysis",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    response_time_ms=response_time_ms
                )

            result = json.loads(response.choices[0].message.content)
            analyses = result.get("analyses", [])

            # Merge analyses back into news
            for analysis in analyses:
                idx = analysis.get("idx", 0) - 1
                if 0 <= idx < len(news_list):
                    news_list[idx]["llm_sentiment"] = analysis.get("sentiment", "NEUTRAL")
                    news_list[idx]["llm_impact"] = analysis.get("impact", "LOW")
                    news_list[idx]["llm_confidence"] = analysis.get("confidence", 50)
                    news_list[idx]["llm_insight"] = analysis.get("insight", "")

            return news_list

        except Exception as e:
            print(f"[LLM News Analysis Error] {e}")
            return news_list
    
    async def generate_coin_analysis(self, symbol: str, data: Dict, user_id: str = None) -> Optional[Dict]:
        """
        Tek coin için detaylı AI analizi

        Args:
            symbol: Coin sembolü
            data: Teknik ve piyasa verileri
            user_id: Kullanıcı ID (analytics için)

        Returns:
            AI analiz sonucu
        """
        if not self.client:
            return None

        start_time = time.time()

        try:
            prompt = f"""Analyze {symbol} and provide trading recommendation in Turkish.

Data:
- Price: ${data.get('price', 0):.2f}
- 24h Change: {data.get('change_24h', 0):.2f}%
- RSI: {data.get('rsi', 50):.1f}
- MACD: {data.get('macd', 'N/A')}
- Funding Rate: {data.get('funding_rate', 0):.4f}%
- Long/Short Ratio: {data.get('long_short_ratio', 1):.2f}

Provide JSON response:
{{
  "signal": "AL|SAT|TUT",
  "confidence": 75,
  "summary": "Brief Turkish summary...",
  "key_levels": {{
    "support": 0,
    "resistance": 0
  }},
  "risks": ["risk1", "risk2"],
  "timeframe": "short|medium|long"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            llm_stats["analysis"] += 1
            llm_stats["tokens_in"] += response.usage.prompt_tokens
            llm_stats["tokens_out"] += response.usage.completion_tokens

            # Track analytics
            if user_id:
                self._track_usage(
                    user_id=user_id,
                    feature="coin_analysis",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    response_time_ms=response_time_ms
                )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"[LLM Coin Analysis Error] {e}")
            return None
    
    def get_stats(self) -> Dict:
        """LLM kullanım istatistikleri"""
        return {
            **llm_stats,
            "enabled": self.enabled,
            "model": self.model
        }


# Singleton instance
llm_service = LLMService()
