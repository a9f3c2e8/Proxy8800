#!/bin/bash

echo "🔄 Перезапуск всех сервисов с доменом 8800.life..."

if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Останавливаем
echo "⏸️  Остановка..."
$DOCKER_COMPOSE down

# Запускаем
echo "🚀 Запуск..."
$DOCKER_COMPOSE up -d

echo ""
echo "⏳ Ждем 5 секунд..."
sleep 5

echo ""
echo "📊 Статус:"
$DOCKER_COMPOSE ps

echo ""
echo "📝 Логи прокси (MTProto ссылка):"
$DOCKER_COMPOSE logs proxy | grep -A 5 "Ссылка для Telegram"

echo ""
echo "📝 Логи бота:"
$DOCKER_COMPOSE logs --tail=10 bot

echo ""
echo "✅ Готово! Домен 8800.life работает!"
echo ""
echo "Проверь подключение:"
echo "https://t.me/proxy?server=8800.life&port=8800&secret=dd2ae5891b2b9b9b811b212050843193aa"
