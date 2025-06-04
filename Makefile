.PHONY: help install install-dev setup test test-watch lint format type-check clean build docs docs-serve

# Default target
.DEFAULT_GOAL := help

help:
	@echo "AgentiCraft Development Commands"
	@echo "==============================="
	@echo "Setup:"
	@echo "  make setup         Complete development setup"
	@echo "  make install       Install package"
	@echo "  make install-dev   Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run all tests with coverage"
	@echo "  make test-watch    Run tests in watch mode"
	@echo "  make lint          Run linting (ruff)"
	@echo "  make format        Format code (black + ruff)"
	@echo "  make type-check    Run type checking (mypy)"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs          Build documentation"
	@echo "  make docs-serve    Serve docs locally"
	@echo ""
	@echo "Build & Clean:"
	@echo "  make build         Build distribution packages"
	@echo "  make clean         Clean all generated files"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make check         Run all checks (lint, type, test)"
	@echo "  make fix           Fix all auto-fixable issues"

# Setup commands
setup:
	@bash scripts/setup_dev.sh

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test]"
	pre-commit install

# Testing commands
test:
	pytest tests/ -v --cov=agenticraft --cov-report=term-missing --cov-report=html --cov-fail-under=95

test-watch:
	pytest-watch tests/ -v

test-unit:
	pytest tests/ -v -m "unit"

test-integration:
	pytest tests/ -v -m "integration"

test-structure:
	pytest tests/test_structure.py -v --no-cov

# Code quality commands
lint:
	ruff check agenticraft tests

format:
	black agenticraft tests
	ruff check --fix agenticraft tests

type-check:
	mypy agenticraft

# Combined commands
check: lint type-check test

fix: format

# Documentation commands
docs:
	mkdocs build

docs-serve:
	mkdocs serve --dev-addr localhost:8000

# Build commands
build: clean
	python -m build

# Clean commands
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -rf site  # mkdocs build directory

# Release commands
release-test: clean build
	python -m twine upload --repository testpypi dist/*

release: clean build
	python -m twine upload dist/*

# Development shortcuts
.PHONY: dev
dev: install-dev

.PHONY: t
t: test

.PHONY: l
l: lint

.PHONY: f
f: format
