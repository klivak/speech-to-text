.PHONY: run test lint format build clean install

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

install-gpu:
	pip install -r requirements-gpu.txt

run:
	python -m src.main

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	ruff check src/
	ruff format --check src/
	mypy src/ --ignore-missing-imports

format:
	ruff check --fix src/
	ruff format src/

build:
	pyinstaller --onefile --windowed --icon=assets/icon.ico --name=EchoScribe --add-data "assets;assets" src/main.py

clean:
	rm -rf build/ dist/ *.spec __pycache__ .mypy_cache .ruff_cache htmlcov .coverage
