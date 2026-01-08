.PHONY: help install test test-quick test-verbose coverage lint format clean build

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests with coverage"
	@echo "  make test-quick   - Run tests without coverage"
	@echo "  make test-verbose - Run tests with verbose output"
	@echo "  make coverage     - Run tests and show coverage report"
	@echo "  make lint         - Check code formatting and imports with ruff"
	@echo "  make format       - Format code and sort imports with ruff"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make build        - Build the package"

install:
	uv sync

test:
	uv run pytest

test-quick:
	uv run pytest --no-cov

test-verbose:
	uv run pytest -vv --no-cov

coverage:
	uv run pytest --cov-report=html
	@echo "Coverage report generated in htmlcov/"

lint:
	uv run ruff check urlfinderlib tests
	uv run ruff format --check urlfinderlib tests

format:
	uv run ruff check --fix urlfinderlib tests
	uv run ruff format urlfinderlib tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build: clean
	uv build
