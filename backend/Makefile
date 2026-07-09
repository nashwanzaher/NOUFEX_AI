.PHONY: help install dev test lint type test-unit test-integration test-cov seed migrate revision format clean docker-up docker-down

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run dev server
	uvicorn noufex_ai.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit -m "not integration and not slow"

test-integration: ## Run integration tests
	pytest tests/integration -m integration

test-cov: ## Run tests with coverage
	pytest --cov=noufex_ai --cov-report=html --cov-report=term

lint: ## Lint with ruff
	ruff check noufex_ai

format: ## Format with ruff
	ruff format noufex_ai

type: ## Type check with mypy
	mypy noufex_ai

seed: ## Seed database
	python -m scripts.seed

migrate: ## Apply all migrations
	alembic upgrade head

revision: ## Create a new migration
	alembic revision --autogenerate -m "$(msg)"

docker-up: ## Start docker compose
	docker compose -f ../infrastructure/docker-compose.yml up -d

docker-down: ## Stop docker compose
	docker compose -f ../infrastructure/docker-compose.yml down

clean: ## Clean cache and artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage
