.PHONY: fresh

fresh:
	docker compose down -v --remove-orphans
	docker system prune -f
	docker compose up -d db redis
	sleep 5
	docker compose build backend
	docker compose run --rm backend alembic upgrade head
	docker compose up --build -d
	docker compose logs -f backend celery
