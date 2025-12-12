#!/bin/bash
# CryptoSignal - Restart All Services
# Usage: sudo ./restart_all.sh

echo "🔄 CryptoSignal Services Restart"
echo "================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

restart_service() {
    local svc=$1
    echo -n "Restarting $svc... "
    if systemctl restart $svc 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

# Restart in correct order
echo ""
echo "📦 Core Services:"
restart_service redis-server

echo ""
echo "⚙️ Workers:"
restart_service cryptosignal-prices
restart_service cryptosignal-futures
restart_service cryptosignal-news
restart_service cryptosignal-sentiment
restart_service cryptosignal-ai-analyst
restart_service cryptosignal-signals
restart_service cryptosignal-signal-checker
restart_service cryptosignal-price-alerts
restart_service cryptosignal-telegram
restart_service cryptosignal-telegram-admin

echo ""
echo "🌐 Application:"
restart_service cryptosignal-backend
echo -n "Reloading nginx... "
if systemctl reload nginx 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Wait a moment for services to start
sleep 2

# Status check
echo ""
echo "================================="
echo "📊 Status Check:"
echo ""

for svc in redis-server \
           cryptosignal-backend \
           nginx \
           cryptosignal-prices \
           cryptosignal-futures \
           cryptosignal-news \
           cryptosignal-sentiment \
           cryptosignal-ai-analyst \
           cryptosignal-signals \
           cryptosignal-signal-checker \
           cryptosignal-price-alerts \
           cryptosignal-telegram \
           cryptosignal-telegram-admin; do
    status=$(systemctl is-active $svc 2>/dev/null)
    if [ "$status" = "active" ]; then
        echo -e "  ${GREEN}✅${NC} $svc"
    else
        echo -e "  ${RED}❌${NC} $svc ($status)"
    fi
done

# Redis check
echo ""
echo "📊 Redis Data:"
redis-cli -a "3f9af2788cb89aa74c06bd48dd290658" DBSIZE 2>/dev/null || echo "  Redis not responding"

echo ""
echo "🎉 Done!"
