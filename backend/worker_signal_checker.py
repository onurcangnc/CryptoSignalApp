#!/usr/bin/env python3
"""
CryptoSignal - Signal Checker Worker
=====================================
Sinyal doğruluk oranını otomatik kontrol eder
Her saat çalışır ve vadesi gelen sinyalleri değerlendirir
"""

import time
import json
import redis
from datetime import datetime
from typing import Dict
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    check_signal_results,
    update_signal_result,
    get_signal_success_rate
)

# Redis
REDIS_PASS = "3f9af2788cb89aa74c06bd48dd290658"
r = redis.Redis(host='localhost', port=6379, password=REDIS_PASS, decode_responses=True)


def check_and_update_signals():
    """Vadesi gelen sinyalleri kontrol et ve güncelle"""
    print(f"\n[Signal Checker] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

    # Kontrol edilecek sinyaller
    pending_signals = check_signal_results()

    if not pending_signals:
        print("[Signal Checker] Kontrol edilecek sinyal yok")
        return

    print(f"[Signal Checker] {len(pending_signals)} sinyal kontrol ediliyor...")

    # Güncel fiyatları al
    prices_data = json.loads(r.get("prices_data") or "{}")

    checked = 0
    for signal in pending_signals:
        symbol = signal["symbol"]
        signal_id = signal["id"]

        # Güncel fiyatı bul
        coin_data = prices_data.get(symbol, {})
        current_price = coin_data.get("price", 0)

        if current_price > 0:
            # Sinyal sonucunu güncelle
            update_signal_result(signal_id, current_price)
            checked += 1
            print(f"  ✓ {symbol}: {signal['signal']} @ ${signal['entry_price']:.2f} → ${current_price:.2f}")
        else:
            print(f"  ⚠ {symbol}: Fiyat bulunamadı")

    print(f"[Signal Checker] {checked}/{len(pending_signals)} sinyal güncellendi")

    # Başarı oranlarını hesapla ve Redis'e kaydet
    update_success_stats()


def update_success_stats():
    """Başarı istatistiklerini güncelle"""
    # Son 7 gün
    stats_7d = get_signal_success_rate(days=7)
    r.set("signal_stats_7d", json.dumps(stats_7d))

    # Son 30 gün
    stats_30d = get_signal_success_rate(days=30)
    r.set("signal_stats_30d", json.dumps(stats_30d))

    # Son 90 gün
    stats_90d = get_signal_success_rate(days=90)
    r.set("signal_stats_90d", json.dumps(stats_90d))

    print(f"\n[Stats] Son 30 gün: {stats_30d['successful_signals']}/{stats_30d['total_signals']} (%{stats_30d['success_rate']:.1f})")

    # Her sinyal tipi için
    for sig in stats_30d["by_signal"]:
        print(f"  • {sig['signal']}: %{sig['success_rate']:.1f} (Ort. P/L: %{sig['avg_pnl']:+.2f})")


def main():
    """Ana döngü"""
    print("="*60)
    print("CryptoSignal - Signal Checker Worker")
    print("="*60)

    print("\nHer saat başı sinyal sonuçlarını kontrol eder")
    print("Başarı oranlarını otomatik hesaplar\n")

    # İlk çalıştırma
    check_and_update_signals()

    # Her saat çalış
    while True:
        print(f"\n[Signal Checker] Sonraki kontrol: 1 saat sonra")
        time.sleep(3600)  # 1 saat

        try:
            check_and_update_signals()
        except Exception as e:
            print(f"[Signal Checker] HATA: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
