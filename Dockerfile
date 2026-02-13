FROM python:3.11-slim

WORKDIR /app

# Копируем только requirements сначала (для кеширования слоя)
COPY requirements.txt .

# Устанавливаем зависимости (этот слой будет кешироваться)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота (только после установки зависимостей)
COPY core/ ./core/
COPY handlers/ ./handlers/
COPY keyboards/ ./keyboards/
COPY services/ ./services/
COPY utils/ ./utils/
COPY main.py .

# Запуск бота
CMD ["python", "-u", "main.py"]
