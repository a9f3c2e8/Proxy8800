.PHONY: build up down restart logs clean status

# Определяем версию docker compose
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

# Быстрая сборка (с кешем)
build:
	$(DOCKER_COMPOSE) build

# Быстрая сборка без кеша (если что-то сломалось)
rebuild:
	$(DOCKER_COMPOSE) build --no-cache

# Запуск
up:
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "✅ Сервисы запущены!"
	@echo "Проверить статус: make status"
	@echo "Посмотреть логи: make logs"

# Остановка
down:
	$(DOCKER_COMPOSE) down

# Перезапуск
restart:
	$(DOCKER_COMPOSE) restart

# Логи всех сервисов
logs:
	$(DOCKER_COMPOSE) logs -f --tail=100

# Логи бота
logs-bot:
	$(DOCKER_COMPOSE) logs -f --tail=100 bot

# Логи прокси
logs-proxy:
	$(DOCKER_COMPOSE) logs -f --tail=100 proxy

# Статус
status:
	$(DOCKER_COMPOSE) ps

# Очистка
clean:
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

# Обновление (быстрое)
update:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up -d --build

# Полная переустановка
reinstall:
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up -d
