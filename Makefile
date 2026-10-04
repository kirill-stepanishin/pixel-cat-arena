.PHONY: install backend frontend dev test lint

install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
	cd frontend && npm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Start 'make backend' and 'make frontend' in separate terminals."

test:
	cd backend && .venv/bin/pytest
	cd frontend && npm test -- --run

lint:
	cd backend && .venv/bin/ruff check .
	cd frontend && npm run build
