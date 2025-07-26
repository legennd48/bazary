.PHONY: help install test lint format clean docker-build docker-up docker-down migrate collectstatic shell

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install dependencies"
	@echo "  test             Run tests with coverage"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black and isort"
	@echo "  clean            Clean up temporary files"
	@echo "  docker-build     Build Docker containers"
	@echo "  docker-up        Start Docker containers"
	@echo "  docker-down      Stop Docker containers"
	@echo "  migrate          Run Django migrations"
	@echo "  collectstatic    Collect static files"
	@echo "  shell            Open Django shell"
	@echo "  createsuperuser  Create Django superuser"
	@echo "  check            Run Django system checks"
	@echo "  security         Run security checks"

# Development setup
install:
	pip install -r requirements/development.txt
	pre-commit install

# Testing
test:
	pytest apps/ --cov=apps/ --cov-report=html --cov-report=term-missing

test-fast:
	pytest apps/ -x --disable-warnings

test-integration:
	pytest apps/ -m integration

test-unit:
	pytest apps/ -m unit

# Code quality
lint:
	black --check .
	isort --check-only .
	flake8 .
	mypy apps/

format:
	black .
	isort .

# Security
security:
	bandit -r apps/ bazary/
	safety check

# Django commands
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

collectstatic:
	python manage.py collectstatic --noinput

shell:
	python manage.py shell

createsuperuser:
	python manage.py createsuperuser

check:
	python manage.py check
	python manage.py check --deploy

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f web

docker-shell:
	docker-compose exec web python manage.py shell

docker-test:
	docker-compose exec web pytest apps/

# Development server
runserver:
	python manage.py runserver

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Git Flow shortcuts
feature:
	@read -p "Feature name: " name; \
	git checkout develop && \
	git pull origin develop && \
	git checkout -b feature/$$name

release:
	@read -p "Release version: " version; \
	git checkout develop && \
	git pull origin develop && \
	git checkout -b release/$$version

hotfix:
	@read -p "Hotfix name: " name; \
	git checkout main && \
	git pull origin main && \
	git checkout -b hotfix/$$name

# CI/CD simulation
ci-test:
	black --check .
	isort --check-only .
	flake8 .
	bandit -r apps/ bazary/
	safety check
	pytest apps/ --cov=apps/ --cov-fail-under=80

# Production commands
production-check:
	python manage.py check --deploy
	python manage.py collectstatic --noinput --dry-run

# Documentation
docs-serve:
	mkdocs serve

docs-build:
	mkdocs build

# Database
reset-db:
	rm -f db.sqlite3
	python manage.py migrate
	python manage.py loaddata fixtures/initial_data.json || echo "No fixtures found"
