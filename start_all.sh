#!/bin/sh
set -e

echo "Запуск MTProto прокси в фоне..."
python proxy_mtproto.py &

echo "Ждем 2 секунды..."
sleep 2

echo "Запуск Telegram бота..."
exec python -u main.py
