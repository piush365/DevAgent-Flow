.PHONY: dev backend frontend test lint format docker-build docker-up docker-down help

help:
	@echo "DevFlow Agent — available targets:"
	@echo "  make dev          Start Flask backend (terminal 1)"
	@echo "  make frontend     Start Streamlit frontend (terminal 2)"
	@echo "  make test         Run test suite with coverage"
	@echo "  make lint         Run ruff linter"
	@echo "  make format       Auto-format with black"
	@echo "  make docker-build Build Docker images"
	@echo "  make docker-up    Start all services via docker-compose"
	@echo "  make docker-down  Stop all services"

dev:
	python run.py

frontend:
	streamlit run frontend/streamlit_app.py

test:
	pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

lint:
	ruff check app/ tests/ frontend/

format:
	black app/ tests/ frontend/ run.py

docker-build:
	docker compose build

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
