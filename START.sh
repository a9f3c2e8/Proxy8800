#!/bin/bash

echo "=================================="
echo "  8800.life - ЧИСТЫЙ ЗАПУСК"
echo "=================================="
echo ""

# Определяем docker compose
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
else
    DC="docker compose"
fi

echo "🛑 Удаляем ВСЕ старые контейнеры..."
$DC down --remove-orphans
docker stop 8800-proxy 2>/dev/null || true
docker rm 8800-proxy 2>/dev/null || true

echo ""
echo "🔨 Собираем контейнер заново..."
$DC build --no-cache

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
echo "📝 Логи:"
$DC logs --tail=50

echo ""
echo "=================================="
echo "  ✅ ГОТОВО!"
echo "=================================="
echo ""
echo "📱 Ссылка для подключения:"
echo "https://t.me/proxy?server=8800.life&port=8800&secret=dd2ae5891b2b9b9b811b212050843193aa"
echo ""
echo "📝 Смотреть логи в реальном времени:"
echo "docker compose logs -f"
echo ""
echo "🔍 Проверить что слушает на 8800:"
echo "ss -tlnp | grep 8800"
echo ""
