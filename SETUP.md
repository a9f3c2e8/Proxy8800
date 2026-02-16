# 🚀 Установка 8800.life - 2 сервера

## Архитектура

```
Клиент → 8800.life:8800 → 104.233.9.112 (Норвегия) → MTProto → Telegram
                                ↓
                         Бот на 194.87.102.170
```

## Сервер 1: БОТ (194.87.102.170)

```bash
# На сервере с ботом
cd /root/Proxy8800

# Остановить всё
docker compose down --remove-orphans

# Пересобрать
docker compose build

# Запустить
docker compose up -d

# Проверить
docker compose logs -f
```

## Сервер 2: ПРОКСИ (104.233.9.112 - Норвегия)

```bash
# Подключиться к серверу Норвегия
ssh root@104.233.9.112

# Создать директорию
mkdir -p /root/mtproto-proxy
cd /root/mtproto-proxy

# Скопировать файлы из norway-proxy/
# (Dockerfile, docker-compose.yml, proxy_mtproto.py, START.sh)

# Запустить
chmod +x START.sh
./START.sh
```

## Копирование файлов на Норвегию

**С локального компьютера:**

```bash
scp norway-proxy/* root@104.233.9.112:/root/mtproto-proxy/
```

**Или вручную создать на Норвегии:**

1. Создай `/root/mtproto-proxy/Dockerfile`
2. Создай `/root/mtproto-proxy/docker-compose.yml`
3. Создай `/root/mtproto-proxy/proxy_mtproto.py`
4. Создай `/root/mtproto-proxy/START.sh`

Все файлы в папке `norway-proxy/`

## Проверка

**На Норвегии (104.233.9.112):**
```bash
ss -tlnp | grep 8800
docker compose logs -f
```

**Подключение из Telegram:**
```
https://t.me/proxy?server=8800.life&port=8800&secret=dd2ae5891b2b9b9b811b212050843193aa
```

## Firewall на Норвегии

```bash
# Открыть порт 8800
iptables -I INPUT -p tcp --dport 8800 -j ACCEPT
iptables-save
```

## Итог

- ✅ Бот работает на 194.87.102.170
- ✅ MTProto прокси на 104.233.9.112 (Норвегия)
- ✅ Домен 8800.life → 104.233.9.112
- ✅ Клиенты подкл