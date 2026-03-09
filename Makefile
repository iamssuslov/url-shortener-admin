.PHONY: install run test test-api test-ui test-allure test-parallel clean docker-build docker-up docker-down migrate upgrade downgrade

install:
	python -m pip install -U pip setuptools wheel
	pip install -r requirements.txt
	playwright install

run:
	uvicorn app.main:app --reload

test:
	pytest

test-api:
	pytest -m api

test-ui:
	pytest -m ui

test-parallel:
	pytest -n auto

test-allure:
	rm -rf allure-results allure-report
	pytest --alluredir=allure-results
	@echo "Allure raw results saved to allure-results"

clean:
	rm -f app.db test.db
	rm -rf allure-results allure-report test-artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete

docker-build:
	docker compose build

docker-up:
	docker compose up

docker-down:
	docker compose down

migrate:
	alembic revision --autogenerate -m "update schema"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1