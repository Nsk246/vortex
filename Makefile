.PHONY: dev api web orchestrator ml test-python

dev:
	docker compose up --build

api:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

orchestrator:
	cd workers/orchestrator && celery -A app.celery_app.celery_app worker -Q orchestration --loglevel=INFO

ml:
	cd workers/ml && celery -A app.celery_app.celery_app worker -Q ml --loglevel=INFO --concurrency=1

test-python:
	cd workers/orchestrator && python -m pytest
	cd apps/api && python -m pytest
