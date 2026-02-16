FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
RUN pip install --no-cache-dir cryptography

# Копирование файла прокси
COPY proxy_mtproto.py .

EXPOSE 8800

# Запуск MTProto
CMD ["python", "-u", "proxy_mtproto.py"]
