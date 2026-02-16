# 🚀 Развертывание 8800.life Proxy

## Быстрый старт

### 1. Подготовка сервера

```bash
# Обновить систему
apt update && apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установить Docker Compose
apt install docker-compose -y
```

### 2. Настройка проекта

```bash
# Клонировать или загрузить проект
cd /root/Proxy8800

# Отредактировать .env файл
nano .env
```

Важные параметры в `.env`:
```env
# IP адрес или домен вашего сервера
PROXY_DOMAIN=104.233.9.112

# MTProto секрет (можно оставить как есть или сгенерировать новый)
MTPROTO_SECRET=dd2ae5891b2b9b9b811b212050843193aa

# API ключ для внутренней связи (измените на свой)
API_KEY=ваш-секретный-ключ
```

### 3. Запуск

```bash
# Собрать контейнеры
make build

# Запустить все сервисы
make up

# Проверить статус
make status

# Посмотреть логи
make logs
```

## Проверка работы

### Проверить MTProto прокси

После запуска в логах будет ссылка вида:
```
https://t.me/proxy?server=104.233.9.112&port=8800&secret=dd2ae5891b2b9b9b811b212050843193aa
```

Откройте эту ссылку в Telegram и нажмите "Подключить прокси".

### Проверить API

```bash
curl http://localhost:8801/api/health
```

Должен вернуть:
```json
{"status": "ok", "service": "8800.life Proxy API", "version": "1.0.0"}
```

## Управление

```bash
# Посмотреть логи бота
make logs-bot

# Посмотреть логи прокси
make logs-proxy

# Перезапустить сервисы
make restart

# Остановить все
make down

# Обновить и перезапустить
make update
```

## Открытие портов

Убедитесь, что порты открыты в файрволе:

```bash
# UFW
ufw allow 8800/tcp
ufw allow 8801/tcp

# iptables
iptables -A INPUT -p tcp --dport 8800 -j ACCEPT
iptables -A INPUT -p tcp --dport 8801 -j ACCEPT
```

## Структура проекта

```
.
├── docker-compose.yml          # Главный файл конфигурации
├── .env                        # Переменные окружения
├── Makefile                    # Команды управления
├── main.py                     # Telegram бот
├── handlers/                   # Обработчики команд бота
├── services/                   # Сервисы (API клиенты)
├── norway-proxy-server/        # Прокси-сервер
│   ├── api_server.py          # API управления
│   ├── mtproto_server.py      # MTProto прокси
│   ├── proxy_server.py        # SOCKS5 прокси
│   └── Dockerfile
└── data/                       # База данных (создается автоматически)
```

## Решение проблем

### Прокси не подключается

1. Проверьте, что порт 8800 открыт:
```bash
netstat -tulpn | grep 8800
```

2. Проверьте логи:
```bash
make logs-proxy
```

3. Проверьте PROXY_DOMAIN в .env - должен быть IP или домен вашего сервера

### Бот не отвечает

1. Проверьте BOT_TOKEN в .env
2. Проверьте логи бота:
```bash
make logs-bot
```

### База данных не создается

```bash
# Создать директорию вручную
mkdir -p data
chmod 777 data

# Перезапустить
make restart
```

## Безопасность

1. Измените API_KEY в .env на случайную строку
2. Не открывайте порт 8801 наружу (только для внутренней связи)
3. Регулярно обновляйте систему и Docker

## Мониторинг

```bash
# Использование ресурсов
docker stats

# Активные подключения
docker exec 8800-proxy netstat -an | grep 8800 | wc -l
```
