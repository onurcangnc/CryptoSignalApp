#!/bin/bash
# CryptoSignal - Check Status
# Usage: ./status.sh

echo "📊 CryptoSignal Services Status"
echo "================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local svc=$1
    local status=$(systemctl is-active $svc 2>/dev/null)
    local memory=$(systemctl show $svc --property=MemoryCurrent 2>/dev/null | cut -d= -f2)
    
    if [ "$status" = "active" ]; then
        # Convert memory to MB
        if [ "$memory" != "" ] && [ "$memory" != "[not set]" ]; then
            mem_mb=$((memory / 1024 / 1024))
            echo -e "  ${GREEN}✅${NC} $svc ${YELLOW}(${mem_mb}MB)${NC}"
        else
            echo -e "  ${GREEN}✅${NC} $svc"
        fi
    else
        echo -e "  ${RED}❌${NC} $svc ($status)"
    fi
}

echo "📦 Core:"
check_service redis-server

echo ""
echo "⚙️ Workers:"
check_service cryptosignal-prices
check_service cryptosignal-futures
check_service cryptosignal-news
check_service cryptosignal-sentiment
check_service cryptosignal-ai-analyst
check_service cryptosignal-signal-checker
check_service cryptosignal-telegram
check_service cryptosignal-telegram-admin

echo ""
echo "🌐 Application:"
check_service cryptosignal-backend
check_service cryptosignal-frontend

# Redis stats
echo ""
echo "================================"
echo "📊 Redis Stats:"
REDIS_PASS="3f9af2788cb89aa74c06bd48dd290658"
if redis-cli -a $REDIS_PASS ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}Connected${NC}"
    echo "  Keys: $(redis-cli -a $REDIS_PASS DBSIZE 2>/dev/null | cut -d: -f2)"
    echo "  Memory: $(redis-cli -a $REDIS_PASS INFO memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d '\r')"
    
    # Check key ages
    echo ""
    echo "📅 Data Freshness:"
    for key in prices_updated futures_updated news_updated; do
        val=$(redis-cli -a $REDIS_PASS GET $key 2>/dev/null)
        if [ "$val" != "" ]; then
            echo "  $key: $val"
        fi
    done
else
    echo -e "  ${RED}Not connected${NC}"
fi

echo ""
echo "================================"
echo "🔗 Endpoints:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
