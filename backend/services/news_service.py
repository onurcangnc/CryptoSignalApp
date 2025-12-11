# -*- coding: utf-8 -*-
"""
CryptoSignal - News Service
===========================
Haber analizi ve sentiment
"""

import json
import re
from typing import Optional, Dict, List
from datetime import datetime

from database import redis_client
from config import BULLISH_KEYWORDS, BEARISH_KEYWORDS, COIN_SYMBOLS


class NewsService:
    """Haber analizi servisi"""
    
    def __init__(self):
        self.bullish_keywords = BULLISH_KEYWORDS
        self.bearish_keywords = BEARISH_KEYWORDS
        self.coin_symbols = COIN_SYMBOLS
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Keyword-based sentiment analizi (ücretsiz)
        
        Args:
            text: Analiz edilecek metin
            
        Returns:
            sentiment, score, confidence
        """
        text_lower = text.lower()
        
        bullish_score = 0
        bearish_score = 0
        bullish_matches = []
        bearish_matches = []
        
        # Bullish keywords
        for keyword, weight in self.bullish_keywords.items():
            if keyword in text_lower:
                bullish_score += weight
                bullish_matches.append(keyword)
        
        # Bearish keywords
        for keyword, weight in self.bearish_keywords.items():
            if keyword in text_lower:
                bearish_score += abs(weight)
                bearish_matches.append(keyword)
        
        # Net score
        net_score = bullish_score - bearish_score
        
        # Sentiment belirleme
        if net_score > 0.15:
            sentiment = "bullish"
        elif net_score < -0.15:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        # Confidence (match sayısına göre)
        total_matches = len(bullish_matches) + len(bearish_matches)
        confidence = min(90, 30 + (total_matches * 15))
        
        return {
            "sentiment": sentiment,
            "score": round(net_score, 3),
            "confidence": confidence,
            "bullish_keywords": bullish_matches[:5],
            "bearish_keywords": bearish_matches[:5]
        }
    
    def extract_coins(self, text: str) -> List[str]:
        """
        Metinden coin sembollerini çıkar
        
        Args:
            text: Analiz edilecek metin
            
        Returns:
            Coin sembol listesi
        """
        text_lower = text.lower()
        found_coins = set()
        
        # Coin names mapping
        for name, symbol in self.coin_symbols.items():
            # Word boundary ile ara
            pattern = r'\b' + re.escape(name) + r'\b'
            if re.search(pattern, text_lower):
                found_coins.add(symbol)
        
        # Direct symbol search (BTC, ETH, etc.)
        symbols = re.findall(r'\b([A-Z]{2,6})\b', text)
        for s in symbols:
            if s in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'BNB', 'AVAX', 
                     'DOT', 'LINK', 'UNI', 'LTC', 'BCH', 'SHIB', 'PEPE', 'ARB',
                     'OP', 'APT', 'SUI', 'NEAR', 'FET', 'RNDR', 'INJ', 'TIA']:
                found_coins.add(s)
        
        return list(found_coins)[:10]  # Max 10 coin
    
    def get_news_from_redis(self, limit: int = 100) -> List[Dict]:
        """Redis'den haberleri getir"""
        try:
            news_raw = redis_client.get("news_db")
            if not news_raw:
                return []
            
            news_dict = json.loads(news_raw)
            news_list = list(news_dict.values())
            
            # Sort by date
            news_list.sort(
                key=lambda x: x.get('crawled_at', x.get('published_at', '')),
                reverse=True
            )
            
            return news_list[:limit]
        except Exception as e:
            print(f"[News Service] Error: {e}")
            return []
    
    def get_coin_news(self, symbol: str, limit: int = 20) -> List[Dict]:
        """Belirli bir coin için haberleri getir"""
        all_news = self.get_news_from_redis(500)
        
        coin_news = [
            n for n in all_news 
            if symbol.upper() in (n.get('coins') or [])
        ]
        
        return coin_news[:limit]
    
    def get_market_sentiment(self) -> Dict:
        """Genel piyasa sentiment'i"""
        news = self.get_news_from_redis(100)
        
        if not news:
            return {
                "sentiment": "neutral",
                "score": 0,
                "news_count": 0,
                "bullish": 0,
                "bearish": 0,
                "neutral": 0
            }
        
        bullish = sum(1 for n in news if n.get('sentiment') == 'bullish')
        bearish = sum(1 for n in news if n.get('sentiment') == 'bearish')
        neutral = len(news) - bullish - bearish
        
        score = (bullish - bearish) / len(news) if news else 0
        
        if score > 0.2:
            sentiment = "bullish"
        elif score < -0.2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": round(score, 3),
            "news_count": len(news),
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral
        }
    
    def get_coin_sentiment(self, symbol: str) -> Dict:
        """Belirli bir coin için sentiment"""
        news = self.get_coin_news(symbol, 50)
        
        if not news:
            return {
                "symbol": symbol,
                "sentiment": "neutral",
                "score": 0,
                "news_count": 0
            }
        
        bullish = sum(1 for n in news if n.get('sentiment') == 'bullish')
        bearish = sum(1 for n in news if n.get('sentiment') == 'bearish')
        
        score = (bullish - bearish) / len(news)
        
        if score > 0.2:
            sentiment = "bullish"
        elif score < -0.2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "score": round(score, 3),
            "news_count": len(news),
            "bullish": bullish,
            "bearish": bearish,
            "recent_headlines": [n.get('title', '')[:100] for n in news[:5]]
        }
    
    def get_trending_coins(self, limit: int = 10) -> List[Dict]:
        """Haberlerde en çok geçen coinler"""
        news = self.get_news_from_redis(200)
        
        coin_counts = {}
        coin_sentiment = {}
        
        for n in news:
            coins = n.get('coins', [])
            sentiment = n.get('sentiment', 'neutral')
            
            for coin in coins:
                if coin and coin not in ['GENERAL', 'USDT', 'USDC']:
                    coin_counts[coin] = coin_counts.get(coin, 0) + 1
                    
                    if coin not in coin_sentiment:
                        coin_sentiment[coin] = {'bullish': 0, 'bearish': 0, 'neutral': 0}
                    coin_sentiment[coin][sentiment] = coin_sentiment[coin].get(sentiment, 0) + 1
        
        # Sort by count
        sorted_coins = sorted(coin_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for coin, count in sorted_coins[:limit]:
            sentiment = coin_sentiment.get(coin, {})
            bullish = sentiment.get('bullish', 0)
            bearish = sentiment.get('bearish', 0)
            
            if bullish > bearish:
                mood = "bullish"
            elif bearish > bullish:
                mood = "bearish"
            else:
                mood = "neutral"
            
            result.append({
                "symbol": coin,
                "news_count": count,
                "sentiment": mood,
                "bullish": bullish,
                "bearish": bearish
            })
        
        return result


# Singleton instance
news_service = NewsService()
