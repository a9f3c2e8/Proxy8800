# 8800.life Telegram Bot + Proxy Server

## Структура

```
Proxy8800/
├── handlers/              # Обработчики бота
├── keyboards/             # Клавиатуры
├── services/              # Сервисы
├── utils/                 # Утилиты
├── main.py               # Главный файл бота
├── config.py             # Конфигурация
├── database.py           # База данных
├── Dockerfile            # Docker для бота
├── docker-compose.yml    # Docker Compose для бота
│
└── norway-proxy-server/  # Прокси-сервер для 104.233.9.112
    ├── proxy_server.py
    ├── Dockerfile
    ├── docker-compose.yml
    └── .env
```

## Быстрый старт

### 1. Запуск бота (194.87.102.170)

```bash
# Загрузи проект на сервер
scp -r Proxy8800 root@194.87.102.170:/root/

# Подключись
ssh root@194.87.102.170

# Перейди в папку
cd /root/Proxy8800

# Настрой .env (токен бота)
nano .env

# Запусти Docker
docker-compose up -d

# Проверь логи
docker-compose logs -f
```

### 2. Запуск прокси-сервера (104.233.9.112)

```bash
# Загрузи папку на сервер
scp -r Proxy8800/norway-proxy-server root@104.233.9.112:/root/

# Подключись
ssh root@104.233.9.112

# Перейди в папку
cd /root/norway-proxy-server

# Запусти Docker
docker-compose up -d

# Проверь логи
docker-compose logs -f
```

### 3. Настрой DNS

В панели 8800.life:
```
Тип: A
Имя: *
Значение: 104.233.9.112
```

## Управление

### Бот (194.87.102.170)

```bash
# Логи
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление
git pull  # или загрузи новые файлы
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Прокси (104.233.9.112)

```bash
# Логи
docker-compose logs -f

# Перезапуск
docker-compose restart

# Активные подключения
netstat -an | grep :1080 | grep ESTABLISHED | wc -l
```

## Тестирование

```bash
# Проверка DNS
nslookup test.8800.life

# Проверка прокси
curl --socks5 test1234:pass5678@104.233.9.112:1080 https://api.ipify.org

# Проверка через Telegram
# 1. Купи прокси в боте
# 2. Нажми "Подключиться к Telegram"
# 3. Готово!
```

## Готово!

✅ Бот на 194.87.102.170  
✅ Прокси на 104.233.9.112  
✅ Все в Docker  
✅ Автоперезапуск  
✅ Работает!
