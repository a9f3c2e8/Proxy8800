#!/bin/bash

echo "=================================="
echo "  Проверка конфигурации 8800.life"
echo "=================================="
echo ""

# Получаем IP сервера
SERVER_IP=$(curl -s ifconfig.me)
echo "🌐 IP сервера: $SERVER_IP"
echo ""

# Проверяем .env
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

echo "📝 Текущая конфигурация .env:"
echo "---"
grep -E "^(BOT_TOKEN|PROXY_DOMAIN|MTPROTO_SECRET|API_KEY)=" .env
echo "---"
echo ""

# Проверяем PROXY_DOMAIN
PROXY_DOMAIN=$(grep "^PROXY_DOMAIN=" .env | cut -d'=' -f2)
if [ "$PROXY_DOMAIN" != "$SERVER_IP" ]; then
    echo "⚠️  PROXY_DOMAIN ($PROXY_DOMAIN) не совпадает с IP сервера ($SERVER_IP)"
    echo "   Клиенты не смогут подключиться к прокси!"
    echo ""
fi

# Проверяем MTProto секрет
MTPROTO_SECRET=$(grep "^MTPROTO_SECRET=" .env | cut -d'=' -f2)
if [[ ! $MTPROTO_SECRET =~ ^dd[0-9a-f]{32}$ ]]; then
    echo "⚠️  MTPROTO_SECRET должен начинаться с 'dd' и содержать 32 hex символа"
    echo "   Текущий: $MTPROTO_SECRET"
    echo ""
fi

# Проверяем API_KEY
API_KEY=$(grep "^API_KEY=" .env | cut -d'=' -f2)
if [ "$API_KEY" == "your-secret-api-key-change-me" ] || [ "$API_KEY" == "8800life-secret-key-change-in-production" ]; then
    echo "⚠️  API_KEY не изменен! Используется значение по умолчанию"
    echo "   Измените его для безопасности"
    echo ""
fi

# Проверяем BOT_TOKEN
BOT_TOKEN=$(grep "^BOT_TOKEN=" .env | cut -d'=' -f2)
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не установлен!"
    echo ""
fi

# Проверяем порты
echo "🔍 Проверка портов:"
if netstat -tulpn 2>/dev/null | grep -q ":8800 "; then
    echo "✅ Порт 8800 (MTProto) открыт"
else
    echo "❌ Порт 8800 не открыт"
fi

if netstat -tulpn 2>/dev/null | grep -q ":8801 "; then
    echo "✅ Порт 8801 (API) открыт"
else
    echo "❌ Порт 8801 не открыт"
fi
echo ""

# Проверяем Docker
echo "🐳 Проверка Docker:"
if docker ps | grep -q "8800-proxy"; then
    echo "✅ Контейнер 8800-proxy запущен"
    PROXY_STATUS="running"
else
    echo "❌ Контейнер 8800-proxy не запущен"
    PROXY_STATUS="stopped"
fi

if docker ps | grep -q "8800-telegram-bot"; then
    echo "✅ Контейнер 8800-telegram-bot запущен"
    BOT_STATUS="running"
else
    echo "❌ Контейнер 8800-telegram-bot не запущен"
    BOT_STATUS="stopped"
fi
echo ""

# Если контейнеры запущены, показываем ссылку
if [ "$PROXY_STATUS" == "running" ]; then
    echo "📱 MTProto прокси ссылка:"
    echo "   https://t.me/proxy?server=$SERVER_IP&port=8800&secret=$MTPROTO_SECRET"
    echo ""
    echo "   Или прямая ссылка:"
    echo "   tg://proxy?server=$SERVER_IP&port=8800&secret=$MTPROTO_SECRET"
    echo ""
fi

# Проверяем API
if [ "$PROXY_STATUS" == "running" ]; then
    echo "🔧 Проверка API:"
    API_RESPONSE=$(curl -s http://localhost:8801/api/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ API отвечает: $API_RESPONSE"
    else
        echo "❌ API не отвечает"
    fi
    echo ""
fi

echo "=================================="
echo "  Проверка завершена"
echo "=================================="
