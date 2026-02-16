#!/bin/bash

echo "=================================="
echo "  MTProto Proxy - Норвегия"
echo "  8800.life:8800"
echo "=================================="
echo ""

if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
else
    DC="docker compose"
fi

echo "🛑 Останавливаем старый прокси..."
$DC down

echo ""
echo "🔨 Собираем..."
$DC build

echo ""
echo "🚀 Запускаем..."
$DC up -d

echo ""
sleep 3

echo "📊 Статус:"
$DC ps

echo ""
echo "📝 Логи:"
$DC logs --tail=30

echo ""
echo "=================================="
echo "  ✅ MTProto прокси запущен!"
echo "=================================="
echo ""
echo "📱 Ссылка для подключения:"
echo "https://t.me/proxy?server=8800.life&port=8800&secret=dd2ae5891b2b9b9b811b212050843193aa"
echo ""
echo "📝 Логи в реальном времени:"
echo "docker compose logs -f"
echo ""
echo "🔍 Проверить порт:"
echo "ss -tlnp | grep 8800"
echo ""
