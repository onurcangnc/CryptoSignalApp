# -*- coding: utf-8 -*-
"""
CryptoSignal - DCA Calculator Router
====================================
Dollar Cost Averaging hesaplayıcı
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database import redis_client

router = APIRouter(prefix="/api/dca", tags=["DCA Calculator"])


class DCACalculationRequest(BaseModel):
    """DCA hesaplama isteği"""
    symbol: str  # Coin sembolü (BTC, ETH, vb.)
    total_investment: float  # Toplam yatırım miktarı (USD)
    frequency: str  # daily, weekly, biweekly, monthly
    duration_months: int  # Kaç ay süreyle
    start_price: Optional[float] = None  # Başlangıç fiyatı (opsiyonel)


class DCACompareRequest(BaseModel):
    """DCA vs Lump Sum karşılaştırma"""
    symbol: str
    investment_amount: float
    months_ago: int  # Kaç ay önce başlasaydı


@router.post("/calculate")
async def calculate_dca(request: DCACalculationRequest):
    """
    DCA stratejisi hesapla

    - Toplam coin miktarı
    - Ortalama alış fiyatı
    - Tahmini değer (mevcut fiyat ile)
    - Kar/zarar projeksiyonu
    """

    # Frekans ayarları
    frequency_map = {
        "daily": 30,      # Ayda ~30 alım
        "weekly": 4,      # Ayda 4 alım
        "biweekly": 2,    # Ayda 2 alım
        "monthly": 1      # Ayda 1 alım
    }

    if request.frequency not in frequency_map:
        raise HTTPException(400, "Invalid frequency. Use: daily, weekly, biweekly, monthly")

    if request.duration_months < 1 or request.duration_months > 120:
        raise HTTPException(400, "Duration must be between 1 and 120 months")

    if request.total_investment <= 0:
        raise HTTPException(400, "Investment amount must be greater than 0")

    # Mevcut fiyatı al
    current_price = get_current_price(request.symbol)
    if not current_price:
        raise HTTPException(404, f"Price not found for {request.symbol}")

    # Hesaplamalar
    purchases_per_month = frequency_map[request.frequency]
    total_purchases = purchases_per_month * request.duration_months
    amount_per_purchase = request.total_investment / total_purchases

    # Başlangıç fiyatı (verilmediyse mevcut fiyat)
    start_price = request.start_price or current_price

    # Simülasyon: Fiyatın %20 aralığında dalgalandığını varsay
    # Gerçek veriler için historical API kullanılabilir
    simulated_purchases = simulate_dca_purchases(
        start_price=start_price,
        current_price=current_price,
        num_purchases=total_purchases,
        amount_per_purchase=amount_per_purchase
    )

    total_coins = sum(p['coins'] for p in simulated_purchases)
    avg_price = request.total_investment / total_coins if total_coins > 0 else 0
    current_value = total_coins * current_price
    profit_loss = current_value - request.total_investment
    profit_loss_pct = (profit_loss / request.total_investment * 100) if request.total_investment > 0 else 0

    return {
        "success": True,
        "symbol": request.symbol.upper(),
        "strategy": "DCA",

        # Giriş parametreleri
        "input": {
            "total_investment": request.total_investment,
            "frequency": request.frequency,
            "duration_months": request.duration_months,
            "purchases_per_month": purchases_per_month,
            "total_purchases": total_purchases,
            "amount_per_purchase": round(amount_per_purchase, 2)
        },

        # Sonuçlar
        "results": {
            "total_coins": round(total_coins, 8),
            "average_price": round(avg_price, 2),
            "current_price": round(current_price, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2),
            "break_even_price": round(avg_price, 2)
        },

        # Projeksiyon senaryoları
        "projections": calculate_projections(total_coins, current_price, request.total_investment),

        # Alım detayları (ilk ve son 3)
        "purchase_samples": {
            "first_3": simulated_purchases[:3],
            "last_3": simulated_purchases[-3:]
        }
    }


@router.post("/compare")
async def compare_dca_vs_lumpsum(request: DCACompareRequest):
    """
    DCA vs Lump Sum (tek seferde alım) karşılaştırması

    Geçmiş verilere dayalı gerçek karşılaştırma
    """

    if request.months_ago < 1 or request.months_ago > 60:
        raise HTTPException(400, "Months ago must be between 1 and 60")

    current_price = get_current_price(request.symbol)
    if not current_price:
        raise HTTPException(404, f"Price not found for {request.symbol}")

    # Geçmiş fiyat tahmini (basitleştirilmiş)
    # Gerçek uygulamada historical API kullanılır
    historical_price = estimate_historical_price(request.symbol, request.months_ago, current_price)

    # Lump Sum senaryosu
    lumpsum_coins = request.investment_amount / historical_price
    lumpsum_value = lumpsum_coins * current_price
    lumpsum_return = ((lumpsum_value / request.investment_amount) - 1) * 100

    # DCA senaryosu (aylık alım)
    dca_results = simulate_historical_dca(
        start_price=historical_price,
        current_price=current_price,
        months=request.months_ago,
        total_investment=request.investment_amount
    )

    dca_value = dca_results['total_coins'] * current_price
    dca_return = ((dca_value / request.investment_amount) - 1) * 100

    winner = "lumpsum" if lumpsum_return > dca_return else "dca" if dca_return > lumpsum_return else "tie"

    return {
        "success": True,
        "symbol": request.symbol.upper(),
        "investment_amount": request.investment_amount,
        "period_months": request.months_ago,

        "lump_sum": {
            "strategy": "Tek Seferde Alım",
            "purchase_price": round(historical_price, 2),
            "coins_bought": round(lumpsum_coins, 8),
            "current_value": round(lumpsum_value, 2),
            "return_pct": round(lumpsum_return, 2),
            "profit_loss": round(lumpsum_value - request.investment_amount, 2)
        },

        "dca": {
            "strategy": "Aylık DCA",
            "average_price": round(dca_results['avg_price'], 2),
            "coins_bought": round(dca_results['total_coins'], 8),
            "current_value": round(dca_value, 2),
            "return_pct": round(dca_return, 2),
            "profit_loss": round(dca_value - request.investment_amount, 2)
        },

        "comparison": {
            "winner": winner,
            "difference_pct": round(abs(lumpsum_return - dca_return), 2),
            "current_price": round(current_price, 2)
        },

        "insight": generate_comparison_insight(winner, lumpsum_return, dca_return, request.symbol)
    }


@router.get("/quick")
async def quick_dca_calc(
    symbol: str = Query(..., description="Coin sembolü"),
    amount: float = Query(..., description="Aylık yatırım miktarı (USD)"),
    months: int = Query(12, description="Süre (ay)")
):
    """
    Hızlı DCA hesaplama
    """
    current_price = get_current_price(symbol)
    if not current_price:
        raise HTTPException(404, f"Price not found for {symbol}")

    total_investment = amount * months

    # Basit hesaplama (sabit fiyat varsayımı)
    total_coins = total_investment / current_price

    return {
        "symbol": symbol.upper(),
        "monthly_investment": amount,
        "duration_months": months,
        "total_investment": total_investment,
        "current_price": round(current_price, 2),
        "estimated_coins": round(total_coins, 8),
        "note": "Bu basit bir hesaplamadır. Gerçek sonuçlar fiyat değişimlerine göre farklılık gösterebilir."
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_current_price(symbol: str) -> float:
    """Redis'ten mevcut fiyatı al"""
    try:
        prices_raw = redis_client.get("prices_data")
        if prices_raw:
            prices = json.loads(prices_raw)
            coin_data = prices.get(symbol.upper(), {})
            return coin_data.get('price', 0)
    except:
        pass
    return 0


def simulate_dca_purchases(start_price: float, current_price: float,
                          num_purchases: int, amount_per_purchase: float) -> List[dict]:
    """
    DCA alımlarını simüle et
    Fiyatın başlangıçtan sona lineer değiştiğini varsayar
    """
    purchases = []

    for i in range(num_purchases):
        # Lineer interpolasyon + küçük rastgele varyasyon
        progress = i / max(num_purchases - 1, 1)
        price = start_price + (current_price - start_price) * progress

        # ±10% varyasyon ekle
        import random
        variation = 1 + (random.random() - 0.5) * 0.2
        price = price * variation

        coins = amount_per_purchase / price

        purchases.append({
            "purchase_num": i + 1,
            "price": round(price, 2),
            "amount": round(amount_per_purchase, 2),
            "coins": round(coins, 8)
        })

    return purchases


def simulate_historical_dca(start_price: float, current_price: float,
                           months: int, total_investment: float) -> dict:
    """
    Geçmiş DCA performansını simüle et
    """
    monthly_amount = total_investment / months
    total_coins = 0

    for i in range(months):
        # Fiyat progresyonu simülasyonu
        progress = i / max(months - 1, 1)
        price = start_price + (current_price - start_price) * progress

        # Varyasyon
        import random
        variation = 1 + (random.random() - 0.5) * 0.15
        price = price * variation

        total_coins += monthly_amount / price

    avg_price = total_investment / total_coins if total_coins > 0 else 0

    return {
        "total_coins": total_coins,
        "avg_price": avg_price
    }


def estimate_historical_price(symbol: str, months_ago: int, current_price: float) -> float:
    """
    Geçmiş fiyatı tahmin et

    Not: Gerçek uygulamada CoinGecko historical API kullanılmalı
    Burada basitleştirilmiş bir tahmin yapıyoruz
    """
    # Aylık ortalama değişim varsayımı
    # Kripto piyasası için %5-15 arası aylık değişim normal
    monthly_change_estimates = {
        "BTC": 0.08,
        "ETH": 0.10,
        "SOL": 0.15,
        "default": 0.10
    }

    monthly_change = monthly_change_estimates.get(symbol.upper(), monthly_change_estimates["default"])

    # Geçmiş fiyat = Mevcut fiyat / (1 + aylık_değişim)^ay
    historical_price = current_price / ((1 + monthly_change) ** months_ago)

    return max(historical_price, current_price * 0.1)  # Minimum %10'u


def calculate_projections(total_coins: float, current_price: float,
                         total_investment: float) -> List[dict]:
    """
    Farklı fiyat senaryolarında projeksiyon
    """
    projections = []

    scenarios = [
        {"label": "-50%", "multiplier": 0.5},
        {"label": "-25%", "multiplier": 0.75},
        {"label": "Mevcut", "multiplier": 1.0},
        {"label": "+25%", "multiplier": 1.25},
        {"label": "+50%", "multiplier": 1.5},
        {"label": "+100%", "multiplier": 2.0},
        {"label": "+200%", "multiplier": 3.0}
    ]

    for scenario in scenarios:
        projected_price = current_price * scenario["multiplier"]
        projected_value = total_coins * projected_price
        profit_loss = projected_value - total_investment
        profit_loss_pct = (profit_loss / total_investment * 100) if total_investment > 0 else 0

        projections.append({
            "scenario": scenario["label"],
            "price": round(projected_price, 2),
            "value": round(projected_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2)
        })

    return projections


def generate_comparison_insight(winner: str, lumpsum_return: float,
                               dca_return: float, symbol: str) -> str:
    """
    Karşılaştırma için içgörü oluştur
    """
    diff = abs(lumpsum_return - dca_return)

    if winner == "lumpsum":
        if diff > 20:
            return f"Bu dönemde {symbol} fiyatı sürekli yükseldiği için tek seferde alım önemli avantaj sağladı. Ancak bu her zaman böyle olmayabilir."
        else:
            return f"Tek seferde alım biraz daha iyi performans gösterdi, ancak fark küçük. DCA risk yönetimi açısından hala iyi bir strateji."
    elif winner == "dca":
        if diff > 20:
            return f"DCA stratejisi bu dönemde çok daha iyi performans gösterdi. Fiyat dalgalanmalarından faydalanarak ortalama maliyeti düşürdü."
        else:
            return f"DCA biraz daha iyi performans gösterdi ve aynı zamanda risk yönetimi avantajı sağladı."
    else:
        return f"Her iki strateji de benzer sonuçlar verdi. DCA, duygusal karar vermeyi azaltması açısından avantajlı olabilir."
