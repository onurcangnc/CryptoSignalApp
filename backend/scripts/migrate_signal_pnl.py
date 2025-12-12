#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal P/L Migration Script
============================
Mevcut signal_tracking verilerindeki profit_loss_pct değerlerini
sinyal yönüne göre yeniden hesaplar.

Sorun: Önceki kod tüm sinyalleri BUY gibi hesaplıyordu.
       SELL sinyallerinde fiyat düşüşü = kar olmalı.

Kullanım:
    python3 scripts/migrate_signal_pnl.py

Sunucuda:
    cd /opt/cryptosignal-app/backend
    source venv/bin/activate
    python3 scripts/migrate_signal_pnl.py
"""

import sqlite3
import os
import sys

# Backend path'i ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH


def migrate_signal_pnl():
    """Signal tracking P/L değerlerini düzelt"""

    print("=" * 60)
    print("Signal P/L Migration Script")
    print("=" * 60)
    print(f"\nDatabase: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Tüm tamamlanmış sinyalleri al
    c.execute("""
        SELECT id, symbol, signal, entry_price, actual_price, profit_loss_pct, result
        FROM signal_tracking
        WHERE result IS NOT NULL AND actual_price IS NOT NULL
    """)

    rows = c.fetchall()
    print(f"\nToplam {len(rows)} sinyal bulundu.\n")

    if not rows:
        print("Düzeltilecek sinyal yok.")
        conn.close()
        return

    # İstatistikler
    stats = {
        "total": len(rows),
        "buy_signals": 0,
        "sell_signals": 0,
        "hold_signals": 0,
        "updated": 0,
        "old_total_pnl": 0,
        "new_total_pnl": 0
    }

    updates = []

    for row in rows:
        signal_id = row["id"]
        signal = row["signal"]
        entry_price = row["entry_price"] or 0
        actual_price = row["actual_price"] or 0
        old_pnl = row["profit_loss_pct"] or 0

        # Ham fiyat değişimi
        if entry_price > 0:
            raw_price_change_pct = ((actual_price - entry_price) / entry_price * 100)
        else:
            raw_price_change_pct = 0

        # Sinyal türüne göre doğru P/L hesapla
        if signal in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]:
            new_pnl = raw_price_change_pct
            stats["buy_signals"] += 1
        elif signal in ["SELL", "SAT", "STRONG_SELL", "GÜÇLÜ SAT"]:
            new_pnl = -raw_price_change_pct  # Ters çevir
            stats["sell_signals"] += 1
        else:  # HOLD, BEKLE
            new_pnl = 0  # BEKLE = pozisyon yok = P/L yok
            stats["hold_signals"] += 1

        stats["old_total_pnl"] += old_pnl
        stats["new_total_pnl"] += new_pnl

        # Değişiklik varsa kaydet
        if abs(old_pnl - new_pnl) > 0.01:
            updates.append({
                "id": signal_id,
                "symbol": row["symbol"],
                "signal": signal,
                "old_pnl": round(old_pnl, 2),
                "new_pnl": round(new_pnl, 2),
                "diff": round(new_pnl - old_pnl, 2)
            })

    # Değişiklikleri göster
    print("Sinyal Dağılımı:")
    print(f"  AL/BUY sinyalleri:   {stats['buy_signals']}")
    print(f"  SAT/SELL sinyalleri: {stats['sell_signals']}")
    print(f"  BEKLE/HOLD sinyalleri: {stats['hold_signals']}")

    print(f"\nDeğişecek kayıt sayısı: {len(updates)}")
    print(f"\nEski toplam P/L: {stats['old_total_pnl']:.2f}%")
    print(f"Yeni toplam P/L: {stats['new_total_pnl']:.2f}%")
    print(f"Fark: {stats['new_total_pnl'] - stats['old_total_pnl']:.2f}%")

    if not updates:
        print("\nDeğişiklik gerekmiyor.")
        conn.close()
        return

    # Örnek değişiklikler göster
    print("\nÖrnek değişiklikler (ilk 10):")
    print("-" * 70)
    print(f"{'Symbol':<10} {'Sinyal':<12} {'Eski P/L':>10} {'Yeni P/L':>10} {'Fark':>10}")
    print("-" * 70)

    for u in updates[:10]:
        print(f"{u['symbol']:<10} {u['signal']:<12} {u['old_pnl']:>10.2f}% {u['new_pnl']:>10.2f}% {u['diff']:>+10.2f}%")

    if len(updates) > 10:
        print(f"... ve {len(updates) - 10} kayıt daha")

    # Onay al
    print("\n" + "=" * 60)
    response = input("Bu değişiklikleri uygulamak istiyor musunuz? (evet/hayır): ").strip().lower()

    if response not in ["evet", "e", "yes", "y"]:
        print("İptal edildi.")
        conn.close()
        return

    # Değişiklikleri uygula
    print("\nDeğişiklikler uygulanıyor...")

    for u in updates:
        c.execute(
            "UPDATE signal_tracking SET profit_loss_pct = ? WHERE id = ?",
            (u["new_pnl"], u["id"])
        )
        stats["updated"] += 1

    conn.commit()
    conn.close()

    print(f"\n✅ {stats['updated']} kayıt güncellendi!")
    print("\nÖnemli: Redis cache'i temizlemek için backend'i restart edin:")
    print("  sudo systemctl restart cryptosignal-backend")


if __name__ == "__main__":
    migrate_signal_pnl()