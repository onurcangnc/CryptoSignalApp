#!/bin/bash
# CryptoSignal - Stop All Services
# Usage: sudo ./stop.sh

echo "🛑 Stopping CryptoSignal Services..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

stop_service() {
    local svc=$1
    echo -n "Stopping $svc... "
    if systemctl stop $svc 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

# Stop in reverse order (applications first, core last)
echo "🌐 Application:"
stop_service cryptosignal-frontend
stop_service cryptosignal-backend

echo ""
echo "⚙️ Workers:"
stop_service cryptosignal-telegram
stop_service cryptosignal-signal-checker
stop_service cryptosignal-ai-analyst
stop_service cryptosignal-sentiment
stop_service cryptosignal-news
stop_service cryptosignal-futures
stop_service cryptosignal-prices

echo ""
echo "📦 Core Services:"
stop_service redis-server

echo ""
echo "✅ All services stopped"
