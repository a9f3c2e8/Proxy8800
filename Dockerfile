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

# Копируем MTProto прокси и стартовый скрипт
COPY proxy_mtproto.py .
COPY start_all.sh .

# Делаем скрипт исполняемым
RUN chmod +x start_all.sh

# Создаем директорию для данных
RUN mkdir -p /app/data

# Запуск через скрипт
CMD ["./start_all.sh"]
