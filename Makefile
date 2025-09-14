.PHONY: help install install-dev lint format check test test-unit test-integration test-coverage clean run pre-commit-install pre-commit-run

# Default target
help:
	@echo "🚀 RAG System Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install           Install production dependencies"
	@echo "  install-dev       Install development dependencies"
	@echo "  pre-commit-install Install pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint              Run ruff linter"
	@echo "  format            Run ruff formatter"
	@echo "  check             Run all code quality checks"
	@echo "  pre-commit-run    Run pre-commit on all files"
	@echo ""
	@echo "Testing:"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests"
	@echo "  test-coverage     Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  run               Start the development server"
	@echo "  clean             Clean cache and build files"
	@echo ""

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Pre-commit setup
pre-commit-install:
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

pre-commit-run:
	pre-commit run --all-files

# Code quality
lint:
	ruff check app/ --fix

format:
	ruff format app/

check:
	python check_code.py

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m "integration"
	python test_system.py

test-coverage:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Development
run:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete

# Docker commands
docker-build:
	docker build -t rag-system .

docker-run:
	docker run -p 8000:8000 --env-file .env rag-system

docker-test:
	docker build -t rag-system:test .
	docker run --rm -p 8000:8000 -e CHROMADB_PATH=/app/test_db rag-system:test &
	sleep 10 && curl -f http://localhost:8000/health && docker stop $$(docker ps -q --filter ancestor=rag-system:test)

# CI/CD commands
ci-setup:
	make install-dev
	make pre-commit-install

ci-test:
	make lint
	make check
	make test-coverage

# Full development setup
setup-dev: install-dev pre-commit-install
	@echo "🎉 Development environment setup complete!"
	@echo "Run 'make check' to verify everything is working"
	@echo "Run 'make test' to run the test suite"
