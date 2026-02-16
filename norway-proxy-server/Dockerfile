FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
RUN pip install --no-cache-dir aiohttp

# Копирование файлов
COPY proxy_server.py .
COPY mtproto_server.py .
COPY api_server.py .

# Создание директории для данных
RUN mkdir -p /data

EXPOSE 443 8800 8801

# Запуск всех сервисов
CMD sh -c "python api_server.py & python mtproto_server.py & python proxy_server.py"
