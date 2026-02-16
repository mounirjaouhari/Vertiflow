.PHONY: help install dev test lint format clean docker docker-up docker-down docs

# Default target
help:
	@echo "Agri-Copilot Pro - Development Commands"
	@echo "======================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run-api       - Run FastAPI server"
	@echo "  make run-ui        - Run Streamlit UI"
	@echo "  make run-both      - Run both API and UI"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-int      - Run integration tests only"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make lint          - Run code linters"
	@echo "  make format        - Format code with black and isort"
	@echo "  make type-check    - Run type checking with mypy"
	@echo ""
	@echo "Docker:"
	@echo "  make docker        - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make docs          - Build documentation"
	@echo "  make clean         - Clean up temporary files"
	@echo "  make requirements  - Update requirements.txt"
	@echo ""

# Installation targets
install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Development targets
run-api:
	python main.py

run-ui:
	streamlit run app.py

run-both:
	@echo "Starting API on http://localhost:8000"
	@echo "Starting UI on http://localhost:8501"
	@echo "Press Ctrl+C to stop"
	python main.py &
	streamlit run app.py

# Testing targets
test:
	pytest -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-int:
	pytest tests/integration/ -v --tb=short

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

# Code quality targets
lint:
	flake8 src/ tests/
	pylint src/ --disable=C0111,R0903

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# Docker targets
docker:
	docker build -t agri-copilot-pro:latest .

docker-up:
	docker-compose up -d
	@echo "Services started:"
	@echo "  API:       http://localhost:8000"
	@echo "  UI:        http://localhost:8501"
	@echo "  Docs:      http://localhost:8000/api/docs"
	@echo "  ClickHouse: http://localhost:8123"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

# Utilities
docs:
	cd docs && mkdocs build

docs-serve:
	cd docs && mkdocs serve

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name '.coverage' -delete
	find . -type d -name 'htmlcov' -exec rm -rf {} +
	find . -type d -name 'dist' -exec rm -rf {} +
	find . -type d -name 'build' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +

requirements:
	pip freeze > requirements.txt

# Git shortcuts
git-setup:
	git config core.hooksPath .git/hooks
	chmod +x .git/hooks/pre-commit

# Development environment setup
setup: install dev
	@echo "Environment setup complete!"
	@echo "1. Copy .env.example to .env"
	@echo "2. Update .env with your configuration"
	@echo "3. Run 'make run-both' to start the application"

# Run linters and tests before commit
pre-commit: format lint test
	@echo "Pre-commit checks passed!"

# Production build
build-prod: clean test lint
	pip install -e .

# Database operations (if needed)
db-migrate:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

# Security checks
security-check:
	pip install safety bandit
	safety check
	bandit -r src/

# Performance profiling
profile:
	python -m cProfile -s cumtime main.py

# API documentation
api-docs:
	@echo "API documentation available at: http://localhost:8000/api/docs"
	@echo "Starting server..."
	python main.py

# Watch mode for development
watch:
	@echo "Watching for changes..."
	find src/ tests/ -name "*.py" -type f | entr make test lint

# Version info
version:
	@python -c "from src.core.config import get_settings; print(f'Agri-Copilot Pro v{get_settings().app_version}')"

# Health check
health-check:
	curl -f http://localhost:8000/health || echo "API not running"
	curl -f http://localhost:8501 || echo "UI not running"
