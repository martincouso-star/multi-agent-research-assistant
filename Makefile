.PHONY: install install-api install-web lint lint-api lint-web test test-api test-web typecheck build eval dev-api dev-web up ci

PYTHON ?= python3
NPM ?= npm

export PYTHONPATH := $(CURDIR)/apps/api/src:$(PYTHONPATH)

install: install-api install-web

install-api:
	$(PYTHON) -m pip install -e "./apps/api[dev]"

install-web:
	cd apps/web && $(NPM) install

lint: lint-api lint-web

lint-api:
	ruff check apps/api evals

lint-web:
	cd apps/web && $(NPM) run lint

test: test-api test-web

test-api:
	pytest apps/api/tests

test-web:
	cd apps/web && $(NPM) test

typecheck:
	cd apps/web && $(NPM) run typecheck

build:
	cd apps/web && $(NPM) run build

eval:
	$(PYTHON) evals/run_eval.py

dev-api:
	uvicorn research_assistant.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd apps/web && $(NPM) run dev

up:
	docker compose up --build

ci: lint test typecheck build eval
