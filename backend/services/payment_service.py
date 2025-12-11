# -*- coding: utf-8 -*-
"""
CryptoSignal - Payment Service
===============================
NOWPayments crypto ödeme entegrasyonu
"""

import os
import hmac
import hashlib
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta

# NOWPayments API
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"

# Fiyatlandırma
PRICING = {
    "pro": {
        "monthly": 9.99,
        "display_name": "Pro Plan",
        "daily_analyses": 30
    },
    "premium": {
        "monthly": 19.99,
        "display_name": "Premium Plan",
        "daily_analyses": 100
    }
}


class PaymentService:
    """Crypto ödeme servisi"""

    def __init__(self):
        self.api_key = NOWPAYMENTS_API_KEY
        self.ipn_secret = NOWPAYMENTS_IPN_SECRET
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def get_available_currencies(self) -> list:
        """Kabul edilen kripto paralar"""
        try:
            r = requests.get(
                f"{NOWPAYMENTS_API_URL}/currencies",
                headers=self.headers,
                timeout=10
            )
            if r.status_code == 200:
                currencies = r.json().get("currencies", [])
                # Öncelikli olanları filtrele
                priority = ["usdttrc20", "usdt", "btc", "eth", "bnbbsc"]
                return [c for c in priority if c in currencies] + currencies
            return []
        except Exception as e:
            print(f"[Payment] Currency list error: {e}")
            return ["usdttrc20", "btc", "eth"]  # Fallback

    def create_payment(
        self,
        user_id: str,
        email: str,
        tier: str,
        duration_months: int = 1,
        currency: str = "usdttrc20"
    ) -> Optional[Dict]:
        """
        Ödeme oluştur

        Args:
            user_id: Kullanıcı ID
            email: Kullanıcı email
            tier: pro veya premium
            duration_months: Ay sayısı (1, 3, 12)
            currency: Ödeme yapılacak kripto (usdttrc20, btc, eth)

        Returns:
            Payment detayları veya None
        """
        if tier not in PRICING:
            return None

        # Fiyat hesapla
        price_usd = PRICING[tier]["monthly"] * duration_months

        # İndirim uygula (3 ay: %10, 12 ay: %20)
        if duration_months == 3:
            price_usd *= 0.9  # %10 indirim
        elif duration_months == 12:
            price_usd *= 0.8  # %20 indirim

        price_usd = round(price_usd, 2)

        # Order ID oluştur
        order_id = f"sub_{user_id}_{tier}_{int(datetime.utcnow().timestamp())}"

        try:
            # NOWPayments invoice oluştur
            payload = {
                "price_amount": price_usd,
                "price_currency": "usd",
                "pay_currency": currency,
                "order_id": order_id,
                "order_description": f"{PRICING[tier]['display_name']} - {duration_months} ay",
                "ipn_callback_url": f"{os.getenv('API_BASE_URL', 'https://api.cryptosignal.ai')}/api/webhook/payment",
                "success_url": f"{os.getenv('FRONTEND_URL', 'https://cryptosignal.ai')}/payment/success",
                "cancel_url": f"{os.getenv('FRONTEND_URL', 'https://cryptosignal.ai')}/payment/cancel",
                "is_fixed_rate": False,
                "is_fee_paid_by_user": True
            }

            r = requests.post(
                f"{NOWPAYMENTS_API_URL}/invoice",
                headers=self.headers,
                json=payload,
                timeout=15
            )

            if r.status_code == 200:
                data = r.json()

                return {
                    "payment_id": data.get("id"),
                    "order_id": order_id,
                    "invoice_url": data.get("invoice_url"),
                    "pay_address": data.get("pay_address"),
                    "pay_amount": data.get("pay_amount"),
                    "pay_currency": currency.upper(),
                    "price_usd": price_usd,
                    "tier": tier,
                    "duration_months": duration_months,
                    "expires_at": data.get("created_at")  # 1 saat geçerli
                }
            else:
                print(f"[Payment] Create error: {r.status_code} - {r.text}")
                return None

        except Exception as e:
            print(f"[Payment] Exception: {e}")
            return None

    def verify_ipn_signature(self, payload: str, signature: str) -> bool:
        """IPN webhook imzasını doğrula"""
        if not self.ipn_secret:
            return False

        calculated = hmac.new(
            self.ipn_secret.encode(),
            payload.encode(),
            hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(calculated, signature)

    def get_payment_status(self, payment_id: str) -> Optional[Dict]:
        """Ödeme durumunu kontrol et"""
        try:
            r = requests.get(
                f"{NOWPAYMENTS_API_URL}/payment/{payment_id}",
                headers=self.headers,
                timeout=10
            )

            if r.status_code == 200:
                return r.json()
            return None

        except Exception as e:
            print(f"[Payment] Status error: {e}")
            return None

    def calculate_expiry_date(self, duration_months: int) -> str:
        """Abonelik bitiş tarihini hesapla"""
        expiry = datetime.utcnow() + timedelta(days=30 * duration_months)
        return expiry.isoformat()


# Singleton
payment_service = PaymentService()