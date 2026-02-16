FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
RUN pip install --no-cache-dir aiohttp cryptography

# Копирование файлов
COPY mtproto_server.py .
COPY api_server.py .
COPY start.sh .

# Делаем скрипт исполняемым
RUN chmod +x start.sh

# Создание директории для данных
RUN mkdir -p /data

EXPOSE 8800 8801

# Запуск через скрипт
CMD ["sh", "start.sh"]
