.PHONY: build up down restart logs clean

# Быстрая сборка (с кешем)
build:
	docker-compose build

# Быстрая сборка без кеша (если что-то сломалось)
rebuild:
	docker-compose build --no-cache

# Запуск
up:
	docker-compose up -d

# Остановка
down:
	docker-compose down

# Перезапуск
restart:
	docker-compose restart

# Логи
logs:
	docker-compose logs -f

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
