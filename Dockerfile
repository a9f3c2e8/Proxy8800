FROM python:3.11-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы бота
COPY core/ ./core/
COPY handlers/ ./handlers/
COPY keyboards/ ./keyboards/
COPY services/ ./services/
COPY utils/ ./utils/
COPY main.py .
COPY .env .

# Запуск бота
CMD ["python", "main.py"]
