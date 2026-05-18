.PHONY: install api-dev train test manual-smoke

install:
	python -m pip install -r requirements.txt

api-dev:
	python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

train:
	python -m src.ml.train

test:
	pytest tests/ -v

manual-smoke:
	python scripts/manual_http_smoke.py
