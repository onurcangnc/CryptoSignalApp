#!/bin/bash
# CryptoSignal - Stop All Services
# Usage: sudo ./stop_all.sh

echo "🛑 Stopping CryptoSignal Services..."

systemctl stop cryptosignal-frontend
systemctl stop cryptosignal-backend
systemctl stop cryptosignal-prices
systemctl stop cryptosignal-futures
systemctl stop cryptosignal-news
systemctl stop cryptosignal-sentiment
systemctl stop redis-server

echo "✅ All services stopped"
