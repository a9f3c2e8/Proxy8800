.PHONY: build up down restart logs clean status

# Быстрая сборка (с кешем)
build:
	docker-compose build

# Быстрая сборка без кеша (если что-то сломалось)
rebuild:
	docker-compose build --no-cache

# Запуск
up:
	docker-compose up -d
	@echo ""
	@echo "✅ Сервисы запущены!"
	@echo "Проверить статус: make status"
	@echo "Посмотреть логи: make logs"

# Остановка
down:
	docker-compose down

# Перезапуск
restart:
	docker-compose restart

# Логи всех сервисов
logs:
	docker-compose logs -f --tail=100

# Логи бота
logs-bot:
	docker-compose logs -f --tail=100 bot

# Логи прокси
logs-proxy:
	docker-compose logs -f --tail=100 proxy

# Статус
status:
	docker-compose ps

# Очистка
clean:
	docker-compose down -v
	docker system prune -f

# Обновление (быстрое)
update:
	docker-compose down
	docker-compose up -d --build

# Полная переустановка
reinstall:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d
