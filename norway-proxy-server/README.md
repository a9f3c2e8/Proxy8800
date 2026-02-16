# 8800.life Proxy Server

Полноценная система управления SOCKS5 прокси с API и базой данных.

## Особенности

- ✅ SOCKS5 прокси с аутентификацией
- ✅ API для управления пользователями
- ✅ База данных SQLite для хранения данных
- ✅ Статистика подключений и трафика
- ✅ Контроль сроков действия и лимитов
- ✅ Минимальное логирование (без спама)
- ✅ Все данные внутри системы (без раскрытия IP)

## Быстрый старт

```bash
# Установить API ключ
export API_KEY="your-secret-key-here"

# Запустить
docker-compose up --build -d

# Проверить логи
docker-compose logs -f
```

## Порты

- `8800` - SOCKS5 прокси
- `8801` - API управления

## API Endpoints

### Создать пользователя
```bash
curl -X POST http://localhost:8801/api/user/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_user_id": 123456,
    "username": "user8800",
    "password": "pass8800",
    "days": 30
  }'
```

### Получить информацию о пользователе
```bash
curl http://localhost:8801/api/user/123456 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Получить статистику
```bash
curl http://localhost:8801/api/user/123456/stats \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Продлить подписку
```bash
curl -X POST http://localhost:8801/api/user/user8800/extend \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

### Список всех пользователей
```bash
curl http://localhost:8801/api/users \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Использование прокси

После создания пользователя через API:

```
Тип: SOCKS5
Хост: your-server.com
Порт: 8800
Логин: user8800
Пароль: pass8800
```

## Переменные окружения

- `REQUIRE_AUTH` - требовать аутентификацию (default: true)
- `MAX_CONNECTIONS` - максимум соединений (default: 1000)
- `DB_PATH` - путь к базе данных (default: /data/proxy.db)
- `API_KEY` - ключ для API (обязательно!)

## База данных

Все данные хранятся в SQLite:
- Пользователи прокси
- Статистика подключений
- История использования
- Лимиты трафика

## Безопасность

- API защищен Bearer токеном
- Пароли не логируются
- IP адреса хранятся только для статистики
- Минимальное логирование

## Мониторинг

Проверить статус:
```bash
curl http://localhost:8801/api/health
```

Открыть веб-панель:
```
http://localhost:8801/
```
