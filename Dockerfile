FROM python:3.11-slim

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY core/ ./core/
COPY handlers/ ./handlers/
COPY keyboards/ ./keyboards/
COPY services/ ./services/
COPY utils/ ./utils/
COPY main.py .

# Создаем директорию для данных
RUN mkdir -p /app/data

# Запуск бота
CMD ["python", "-u", "main.py"]
