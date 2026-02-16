#!/bin/bash
# Быстрый перезапуск бота без пересборки

if command -v docker-compose &> /dev/null; then
    docker-compose restart bot
else
    docker compose restart bot
fi

echo "Ждем 3 секунды..."
sleep 3

echo "Логи бота:"
if command -v docker-compose &> /dev/null; then
    docker-compose logs --tail=30 bot
else
    docker compose logs --tail=30 bot
fi
