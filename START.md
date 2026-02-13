# 🚀 Запуск за 3 команды

## 1️⃣ Бот (194.87.102.170)

```bash
# Загрузи проект
scp -r Proxy8800 root@194.87.102.170:/root/

# Запусти
ssh root@194.87.102.170
cd /root/Proxy8800
docker-compose up -d
docker-compose logs -f
```

## 2️⃣ Прокси (104.233.9.112)

```bash
# Загрузи прокси-сервер
scp -r Proxy8800/norway-proxy-server root@104.233.9.112:/root/

# Запусти
ssh root@104.233.9.112
cd /root/norway-proxy-server
docker-compose up -d
docker-compose logs -f
```

## 3️⃣ DNS

Панель 8800.life:
```
A * 104.233.9.112
```

## ✅ Готово!

Проверь:
```bash
nslookup test.8800.life
curl --socks5 test:test@104.233.9.112:1080 https://api.ipify.org
```

Купи прокси в боте → Нажми "Подключиться" → Работает!
