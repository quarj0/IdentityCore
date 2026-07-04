SHELL := /bin/bash

COMPOSE := docker compose

.PHONY: up down logs shell migrate makemigrations createsuperuser test lint ensure-env

ensure-env:
	@test -f .env || cp .env.example .env

up: ensure-env
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

shell:
	$(COMPOSE) exec django /bin/bash

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
