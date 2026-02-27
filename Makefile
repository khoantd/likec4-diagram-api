.PHONY: install run test lint docker-build docker-up

install:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v

lint:
	ruff check app tests

docker-build:
	docker compose build

docker-up:
	docker compose up --build
