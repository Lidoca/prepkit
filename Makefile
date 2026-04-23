.PHONY: run dev migrate makemigration test lint format

run:
	fastapi run app/main.py

dev:
	fastapi dev app/main.py

migrate:
	alembic upgrade head

makemigration:
	alembic revision --autogenerate -m "$(m)"

test:
	coverage run -m pytest
	coverage report

lint:
	ruff check app tests

format:
	ruff format app tests
