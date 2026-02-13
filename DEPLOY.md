# Развертывание SOCKS5 прокси-сервера 8800.life

## Подготовка VPS

### 1. Подключение к серверу
```bash
ssh root@104.233.9.112
```

### 2. Установка Python 3 (если не установлен)
```bash
apt update
apt install -y python3 python3-pip
```

### 3. Создание директории проекта
```bash
mkdir -p /root/proxy8800
cd /root/proxy8800
```

## Загрузка файлов на сервер

### Способ 1: Через SCP (с локального компьютера)
```bash
scp proxy_server.py root@104.233.9.112:/root/proxy8800/
scp proxy_auth.py root@104.233.9.112:/root/proxy8800/
scp start_proxy.py root@104.233.9.112:/root/proxy8800/
```

### Способ 2: Создать файлы вручную на сервере
```bash
# На сервере создайте файлы и скопируйте содержимое
nano /root/proxy8800/proxy_server.py
nano /root/proxy8800/proxy_auth.py
nano /root/proxy8800/start_proxy.py
```

## Настройка DNS

### В панели управления доменом 8800.life:
1. Добавьте A-запись:
   - Тип: A
   - Имя: *
   - Значение: 104.233.9.112
   - TTL: 300

2. Проверьте DNS (через 5-10 минут):
```bash
nslookup test.8800.life
# Должен вернуть: 104.233.9.112
```

## Настройка Firewall

### Открытие порта 1080
```bash
# Для UFW
ufw allow 1080/tcp
ufw status

# Для iptables
iptables -A INPUT -p tcp --dport 1080 -j ACCEPT
iptables-save > /etc/iptables/rules.v4
```

## Установка systemd сервиса

### 1. Создание файла сервиса
```bash
nano /etc/systemd/system/proxy8800.service
```

Вставьте содержимое из файла `proxy8800.service`

### 2. Установка прав
```bash
chmod +x /root/proxy8800/start_proxy.py
```

### 3. Перезагрузка systemd и запуск
```bash
systemctl daemon-reload
systemctl enable proxy8800
systemctl start proxy8800
```

### 4. Проверка статуса
```bash
systemctl status proxy8800
```

### 5. Просмотр логов
```bash
journalctl -u proxy8800 -f
```

## Управление сервисом

```bash
# Запуск
systemctl start proxy8800

# Остановка
systemctl stop proxy8800

# Перезапуск
systemctl restart proxy8800

# Статус
systemctl status proxy8800

# Логи
journalctl -u proxy8800 -f
```

## Тестирование

### 1. Проверка порта
```bash
netstat -tulpn | grep 1080
# Должно показать: tcp 0.0.0.0:1080 LISTEN
```

### 2. Тест подключения (с локального компьютера)
```bash
# Установите curl с поддержкой SOCKS5
curl --socks5 AbCd1234:XyZ78765@QWJDZDEyMzQ6WHlaNzg3NjU.8800.life:1080 https://api.ipify.org
# Должен вернуть IP сервера: 104.233.9.112
```

### 3. Тест через Telegram
1. Откройте бота
2. Купите прокси
3. Нажмите на ссылку подключения
4. Telegram должен подключиться к прокси

## Мониторинг

### Проверка активных подключений
```bash
# Количество подключений
netstat -an | grep :1080 | grep ESTABLISHED | wc -l

# Список подключений
netstat -an | grep :1080 | grep ESTABLISHED
```

### Использование ресурсов
```bash
# CPU и память процесса
ps aux | grep start_proxy.py

# Общая статистика
top -p $(pgrep -f start_proxy.py)
```

## Устранение неполадок

### Сервис не запускается
```bash
# Проверьте логи
journalctl -u proxy8800 -n 50

# Проверьте синтаксис Python
python3 /root/proxy8800/start_proxy.py
```

### Порт занят
```bash
# Найдите процесс на порту 1080
lsof -i :1080

# Убейте процесс
kill -9 <PID>
```

### DNS не работает
```bash
# Проверьте DNS
nslookup test.8800.life
dig test.8800.life

# Очистите кеш DNS (на клиенте)
ipconfig /flushdns  # Windows
sudo systemd-resolve --flush-caches  # Linux
```

## Безопасность

### Рекомендации:
1. Используйте только порт 1080 для прокси
2. Не открывайте другие порты без необходимости
3. Регулярно обновляйте систему: `apt update && apt upgrade`
4. Мониторьте логи на подозрительную активность
5. Ограничьте SSH доступ (смените порт, используйте ключи)

## Обновление кода

```bash
# Остановите сервис
systemctl stop proxy8800

# Обновите файлы
cd /root/proxy8800
# Загрузите новые версии файлов

# Запустите сервис
systemctl start proxy8800

# Проверьте статус
systemctl status proxy8800
```

## Автоматическое обновление

Создайте скрипт для автоматического обновления:
```bash
nano /root/update_proxy.sh
```

```bash
#!/bin/bash
cd /root/proxy8800
git pull  # Если используете git
systemctl restart proxy8800
echo "Proxy server updated at $(date)" >> /var/log/proxy_updates.log
```

```bash
chmod +x /root/update_proxy.sh
```

## Резервное копирование

```bash
# Создайте бэкап конфигурации
tar -czf /root/proxy8800_backup_$(date +%Y%m%d).tar.gz /root/proxy8800/

# Автоматический бэкап (добавьте в crontab)
crontab -e
# Добавьте: 0 3 * * * tar -czf /root/proxy8800_backup_$(date +\%Y\%m\%d).tar.gz /root/proxy8800/
```
