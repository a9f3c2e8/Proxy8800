FROM python:3.11-slim

# Установка зависимостей
RUN pip install --no-cache-dir requests

# Создание рабочей директории
WORKDIR /app

# Копирование файлов
COPY proxy_server.py .

# Открытие порта
EXPOSE 1080

# Запуск сервера
CMD ["python", "proxy_server.py"]
