.PHONY: help install dev test lint format clean build

help:
	@echo "Available commands:"
	@echo "  make install    Install dependencies"
	@echo "  make dev        Install dev dependencies"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linting"
	@echo "  make format     Format code"
	@echo "  make clean      Clean build artifacts"
	@echo "  make build      Build package"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v --cov=agenticraft --cov-report=html

lint:
	ruff check src tests
	mypy src

format:
	black src tests
	ruff check --fix src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build dist *.egg-info
	rm -rf .coverage htmlcov .pytest_cache

build: clean
	python -m build
