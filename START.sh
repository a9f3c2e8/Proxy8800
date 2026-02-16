#!/bin/bash

echo "=================================="
echo "  8800.life - ВСЁ В ОДНОМ!"
echo "=================================="
echo ""

# Определяем docker compose
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
else
    DC="docker compose"
fi

echo "🛑 Останавливаем старые контейнеры..."
$DC down

echo ""
echo "🔨 Собираем контейнер..."
$DC build

echo ""
echo "🚀 Запускаем..."
$DC up -d

echo ""
echo "⏳ Ждем 5 секунд..."
sleep 5

echo ""
echo "📊 Статус:"
$DC ps

echo ""
echo "📝 Логи (последние 30 строк):"
$DC logs --tail=30

echo ""
echo "=================================="
echo "  ✅ ГОТОВО!"
echo "=================================="
echo ""
echo "📱 Ссылка для подключения:"
echo "https://t.me/proxy?server=8800.life&port=8800&secret=dd2ae5891b2b9b9b811b212050843193aa"
echo ""
echo "📝 Смотреть логи:"
echo "docker compose logs -f"
echo ""
