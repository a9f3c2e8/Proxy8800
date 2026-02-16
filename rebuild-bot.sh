#!/bin/bash

echo "🔨 Пересборка бота..."

# Определяем версию docker compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Останавливаем бота
echo "⏸️  Остановка бота..."
$DOCKER_COMPOSE stop bot

# Пересобираем
echo "🔨 Сборка..."
$DOCKER_COMPOSE build bot

# Запускаем
echo "🚀 Запуск..."
$DOCKER_COMPOSE up -d bot

echo ""
echo "✅ Готово! Проверяем логи..."
sleep 2
$DOCKER_COMPOSE logs --tail=20 bot
