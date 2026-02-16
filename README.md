# 🔒 8800.life Proxy Server

Telegram бот для продажи прокси с интегрированным MTProto прокси-сервером.

## 🚀 Быстрый старт

### 1. Установка на сервере

```bash
# Клонировать проект
cd /root
git clone <your-repo> Proxy8800
cd Proxy8800

# Сделать скрипт исполняемым
chmod +x deploy.sh

# Запустить развертывание
./deploy.sh
```

Скрипт автоматически:
- Проверит наличие Docker и Docker Compose
- Предложит настроить IP адрес
- Соберет и запустит все сервисы

### 2. Ручная установка

```bash
# Установить Docker
curl -fsSL https://get.docker.com | sh

# Установить Docker Compose (новая версия)
apt install docker-compose-plugin -y

# Настроить .env
nano .env

# Запустить
make build
make up
```

## ⚙️ Конфигурация

Отредактируйте файл `.env`:

```env
# Telegram Bot
BOT_TOKEN=ваш_токен_от_BotFather

# IP адрес или домен вашего сервера
PROXY_DOMAIN=104.233.9.112

# MTProto секрет (dd префикс обязателен)
MTPROTO_SECRET=dd2ae5891b2b9b9b811b212050843193aa

# API ключ (измените на свой)
API_KEY=ваш-секретный-ключ
```

## 📋 Команды управления

```bash
make build      # Собрать контейнеры
make up         # Запустить все сервисы
make down       # Остановить все
make restart    # Перезапустить
make logs       # Посмотреть логи всех сервисов
make logs-bot   # Логи только бота
make logs-proxy # Логи только прокси
make status     # Статус сервисов
make update     # Обновить и перезапустить
```

## 🔍 Проверка работы

### Проверить MTProto прокси

После запуска найдите в логах ссылку:
```bash
make logs-proxy | grep "t.me/proxy"
```

Откройте ссылку в Telegram и подключитесь.

### Проверить API

```bash
curl http://localhost:8801/api/health
```

### Проверить бота

Напишите боту `/start` в Telegram.

## 🌐 Открытие портов

```bash
# UFW
ufw allow 8800/tcp
ufw allow 8801/tcp

# iptables
iptables -A INPUT -p tcp --dport 8800 -j ACCEPT
iptables -A INPUT -p tcp --dport 8801 -j ACCEPT
iptables-save > /etc/iptables/rules.v4
```

## 📁 Структура проекта

```
.
├── docker-compose.yml          # Конфигурация Docker
├── .env                        # Переменные окружения
├── Makefile                    # Команды управления
├── deploy.sh                   # Скрипт развертывания
├── main.py                     # Telegram бот
├── handlers/                   # Обработчики команд
├── services/                   # API клиенты
├── core/                       # Конфигурация и БД
├── norway-proxy-server/        # Прокси-сервер
│   ├── api_server.py          # API управления
│   ├── mtproto_server.py      # MTProto прокси
│   └── proxy_server.py        # SOCKS5 прокси
└── data/                       # База данных
```

## 🔧 Решение проблем

### Прокси не подключается

1. Проверьте порт:
```bash
netstat -tulpn | grep 8800
```

2. Проверьте логи:
```bash
make logs-proxy
```

3. Убедитесь, что PROXY_DOMAIN в .env правильный

### Бот не отвечает

1. Проверьте BOT_TOKEN в .env
2. Проверьте логи:
```bash
make logs-bot
```

### Контейнеры не запускаются

```bash
# Пересоздать с нуля
make down
docker system prune -f
make build
make up
```

## 📊 Мониторинг

```bash
# Использование ресурсов
docker stats

# Активные подключения к прокси
docker exec 8800-proxy netstat -an | grep 8800 | wc -l

# Логи в реальном времени
make logs
```

## 🔐 Безопасность

1. Измените `API_KEY` в .env на случайную строку
2. Не открывайте порт 8801 наружу (только для внутренней связи)
3. Регулярно обновляйте систему:
```bash
apt update && apt upgrade -y
```

## 📝 API Endpoints

API доступен на порту 8801 (только внутри Docker сети):

- `GET /api/health` - Проверка работоспособности
- `POST /api/user/create` - Создать пользователя
- `GET /api/user/{telegram_id}` - Получить пользователя
- `POST /api/mtproto/create` - Создать MTProto секрет
- `GET /api/mtproto/{telegram_id}` - Получить MTProto

Все запросы требуют заголовок:
```
Authorization: Bearer YOUR_API_KEY
```

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи: `make logs`
2. Проверьте статус: `make status`
3. Перезапустите: `make restart`

## 📄 Лицензия

Proprietary - 8800.life
