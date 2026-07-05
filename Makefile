SHELL := /bin/bash

COMPOSE := docker compose

.PHONY: up down ps logs logs-django logs-ai logs-worker logs-webhooks logs-notifications logs-beat shell shell-worker shell-worker-webhooks shell-worker-notifications migrate makemigrations createsuperuser test lint ensure-env

ensure-env:
	@test -f .env || cp .env.example .env

up: ensure-env
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-django:
	$(COMPOSE) logs -f django

logs-ai:
	$(COMPOSE) logs -f ai-service

logs-worker:
	$(COMPOSE) logs -f celery-worker
	

logs-webhooks:
	$(COMPOSE) logs -f celery-worker-webhooks

logs-notifications:
	$(COMPOSE) logs -f celery-worker-notifications

logs-beat:
	$(COMPOSE) logs -f celery-beat

shell:
	$(COMPOSE) exec django /bin/bash

shell-worker:
	$(COMPOSE) exec celery-worker /bin/bash

shell-worker-webhooks:
	$(COMPOSE) exec celery-worker-webhooks /bin/bash

shell-worker-notifications:
	$(COMPOSE) exec celery-worker-notifications /bin/bash

migrate:
	$(COMPOSE) run --rm django python manage.py migrate

makemigrations:
	$(COMPOSE) run --rm django python manage.py makemigrations

createsuperuser:
	$(COMPOSE) run --rm django python manage.py createsuperuser

test:
	$(COMPOSE) run --rm -e DJANGO_SETTINGS_MODULE=config.settings.testing django python manage.py test
	$(COMPOSE) run --rm ai-service pytest

lint:
	$(COMPOSE) run --rm django ruff check .
	$(COMPOSE) run --rm django black --check .
	$(COMPOSE) run --rm django mypy backend
