# -*- coding: utf-8 -*-
"""
CryptoSignal - Authentication
=============================
JWT token oluşturma ve doğrulama
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional

from config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRY_HOURS


def create_token(user_id: str) -> str:
    """JWT token oluştur"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """JWT token doğrula, user_id döndür"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """JWT token decode et, tüm payload'ı döndür"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except:
        return None
