.PHONY: dev prod install help

PYTHON ?= python3

dev:
	@echo "[make] Starting place-an-order-printer in developement mode..."
	$(PYTHON) main.py dev

prod:
	@echo "[make] Starting place-an-order-printer in production mode..."
	$(PYTHON) main.py prod

install:
	@echo "[make] Installing dependencies …"
	pip install -r requirements.txt

help:
	@echo ""
	@echo "  make dev      Start listener using .env.dev"
	@echo "  make prod     Start listener using .env.prod"
	@echo "  make install  Install Python dependencies from requirements.txt"
	@echo "  make help     Show this help"
	@echo ""
