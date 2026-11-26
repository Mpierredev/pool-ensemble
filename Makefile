.PHONY: api-dev web-dev dev lint typecheck test validate check

api-dev:
	cd apps/api && uv run uvicorn pool_ensemble.main:app --reload --port 8000

web-dev:
	cd apps/web && npm run dev

dev:
	docker compose up --build

lint:
	cd apps/api && uv run ruff check . ../../scripts && uv run ruff format --check . ../../scripts
	cd apps/web && npm run lint

typecheck:
	cd apps/api && uv run mypy src tests
	cd apps/web && npm run typecheck

test:
	cd apps/api && uv run pytest
	cd apps/web && npm test

validate:
	cd apps/api && uv run python ../../scripts/validate_content.py

check: lint typecheck validate test
