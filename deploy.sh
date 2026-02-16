#!/bin/bash

echo "=================================="
echo "  8800.life Proxy Deployment"
echo "=================================="
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Проверка Docker Compose (новая или старая версия)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose не установлен!"
    echo "Установите: apt install docker-compose-plugin -y"
    exit 1
fi

echo "✅ Docker и Docker Compose установлены ($DOCKER_COMPOSE)"
echo ""

# Проверка .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте файл .env с необходимыми параметрами"
    exit 1
fi

echo "✅ Файл .env найден"
echo ""

# Получаем IP сервера
SERVER_IP=$(curl -s ifconfig.me)
echo "🌐 IP сервера: $SERVER_IP"
echo ""

# Проверяем PROXY_DOMAIN в .env
if grep -q "PROXY_DOMAIN=8800.life" .env; then
    echo "⚠️  PROXY_DOMAIN установлен как 8800.life"
    echo "   Рекомендуется изменить на IP сервера: $SERVER_IP"
    echo ""
    read -p "Изменить PROXY_DOMAIN на $SERVER_IP? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i "s/PROXY_DOMAIN=.*/PROXY_DOMAIN=$SERVER_IP/" .env
        echo "✅ PROXY_DOMAIN обновлен"
    fi
fi

echo ""
echo "🔨 Сборка контейнеров..."
$DOCKER_COMPOSE build

if [ $? -ne 0 ]; then
    echo "❌ Ошибка сборки!"
    exit 1
fi

echo ""
echo "🚀 Запуск сервисов..."
$DOCKER_COMPOSE up -d

if [ $? -ne 0 ]; then
    echo "❌ Ошибка запуска!"
    exit 1
fi

echo ""
echo "⏳ Ожидание запуска сервисов..."
sleep 5

echo ""
echo "📊 Статус сервисов:"
$DOCKER_COMPOSE ps

echo ""
echo "=================================="
echo "  ✅ Развертывание завершено!"
echo "=================================="
echo ""
echo "📱 MTProto прокси будет доступен на:"
echo "   https://t.me/proxy?server=$SERVER_IP&port=8800&secret=<ваш_секрет>"
echo ""
echo "🔧 Управление:"
echo "   make logs       - Посмотреть логи"
echo "   make status     - Статус сервисов"
echo "   make restart    - Перезапустить"
echo "   make down       - Остановить"
echo ""
echo "📝 Логи прокси-сервера:"
$DOCKER_COMPOSE logs --tail=20 proxy
echo ""
