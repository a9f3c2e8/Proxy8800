#!/bin/bash

echo "🚀 Запуск MTProxy на 8800.life"

# Открываем порты
echo "🔓 Открываем порты..."
iptables -I INPUT -p tcp --dport 8800 -j ACCEPT
iptables -I INPUT -p tcp --dport 443 -j ACCEPT

# Запускаем
echo "▶️  Запускаем MTProxy..."
docker compose down
docker compose up -d --build

echo ""
echo "✅ MTProxy запущен!"
echo ""
echo "📱 Ссылка для Telegram:"
echo "https://t.me/proxy?server=8800.life&port=8800&secret=dd7f8a9b2c3d4e5f6789abcdef012345"
echo ""
echo "📋 Команды:"
echo "  Логи:       docker compose logs -f"
echo "  Остановить: docker compose down"
echo "  Статус:     docker compose ps"
