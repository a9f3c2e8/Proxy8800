#!/bin/bash

echo "🚀 Запуск MTProxy на 8800.life"

# Убиваем старый процесс
echo "🔄 Останавливаем старый процесс..."
pkill -f mtprotoproxy || true
sleep 2

# Открываем порты
echo "🔓 Открываем порты..."
iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

# Запускаем mtprotoproxy напрямую (не Docker — Docker игнорирует config.py)
echo "▶️  Запускаем MTProxy..."
cd ~/socks5-proxy
nohup python3 mtprotoproxy.py > /tmp/mtproxy.log 2>&1 &

sleep 3
echo ""
echo "✅ MTProxy запущен!"
echo ""
echo "📱 Ссылка для Telegram:"
echo "https://t.me/proxy?server=8800.life&port=443&secret=ee665192ec740b9064430789980cd72dbe63646e2e636c6f7564666c6172652e636f6d"
echo ""
echo "📋 Логи: tail -f /tmp/mtproxy.log"
