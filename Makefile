# Makefile for Ataccama AI Expert

.PHONY: setup crawl process qa run-all clean help

# Default target
help: ## Display this help message
	@echo "Ataccama AI Expert - Makefile targets:"
	@echo ""
	@echo "  setup     - Setup the environment (install dependencies, setup Playwright)"
	@echo "  crawl     - Crawl Ataccama documentation"
	@echo "  process   - Process crawled data into chunks"
	@echo "  qa        - Start the Q&A system"
	@echo "  run-all   - Run the complete pipeline (crawl, process, qa)"
	@echo "  clean     - Clean data directories"
	@echo "  help      - Show this help message"
	@echo ""
	@echo "Usage: make [target]"

setup: ## Setup the environment (install dependencies, setup Playwright)
	pip install -r requirements.txt
	python -m playwright install --with-deps chromium
	@echo "Setup complete!"

crawl: ## Crawl Ataccama documentation
	python -m src.cli crawl --start https://docs.ataccama.com/one/latest/overview.html --out ./data/01_raw

process: ## Process crawled data into chunks
	python -m src.cli process --input ./data/01_raw --output ./data/02_processed/chunks.jsonl

qa: ## Start the Q&A system
	python -m src.cli qa

run-all: crawl process qa ## Run the complete pipeline (crawl, process, qa)

clean: ## Clean data directories
	rm -rf ./data/01_raw/*
	rm -rf ./data/02_processed/*
	rm -rf ./data/03_vector_store/*
	@echo "Data directories cleaned!"

# Configuration options with defaults
START_URL ?= https://docs.ataccama.com/one/latest/overview.html
RAW_DIR ?= ./data/01_raw
PROCESSED_FILE ?= ./data/02_processed/chunks.jsonl
VECTOR_STORE ?= ./data/03_vector_store

crawl-config: ## Crawl with custom configuration
	python -m src.cli crawl --start $(START_URL) --out $(RAW_DIR)

process-config: ## Process with custom configuration
	python -m src.cli process --input $(RAW_DIR) --output $(PROCESSED_FILE)

qa-config: ## Q&A with custom configuration
	python -m src.cli qa --data $(PROCESSED_FILE) --vector-store $(VECTOR_STORE)