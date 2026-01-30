###############################################################################
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                       VERTIFLOW™ AUTOMATION PLAYBOOK                      ║
# ║                             File: Makefile                                ║
# ║                             Ticket: TICKET-133                            ║
# ║                   Maintainer: @Mouhammed (Data Engineer)                  ║
# ║                   Reviewers: @Imrane (DevOps), @Mounir (ML)               ║
# ║ Purpose: Unified developer ergonomics (setup, tests, ETL, deployments).   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
###############################################################################

SHELL := /usr/bin/env bash
PYTHON ?= python3
COMPOSE ?= docker compose
ENV_FILE ?= .env

.DEFAULT_GOAL := help

## ---------------------------------------------------------------------------
## HELPERS
## ---------------------------------------------------------------------------
.PHONY: help check-env
help:
	@printf "\nVertiFlow Make targets\n=======================\n"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
		sed -E 's/:.*?##/: /' | sort

check-env:
	@[ -f $(ENV_FILE) ] || (echo "[ERROR] $(ENV_FILE) is missing. Run 'make env' first." && exit 1)

## ---------------------------------------------------------------------------
## ENVIRONMENT & DEPENDENCIES
## ---------------------------------------------------------------------------
.PHONY: env install clean
env: ## Generate .env from template when absent
	@if [ ! -f $(ENV_FILE) ]; then cp .env.example $(ENV_FILE); echo "[OK] $(ENV_FILE) created"; else echo "[SKIP] $(ENV_FILE) already exists"; fi

install: ## Install Python dependencies into current interpreter
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

clean: ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache dist build

## ---------------------------------------------------------------------------
## QUALITY GATES
## ---------------------------------------------------------------------------
.PHONY: lint test coverage
lint: ## Static analysis (syntax + schema validation)
	$(PYTHON) -m compileall cloud_citadel models scripts tests
	@test -f config/mapping.json
	@test -f config/agronomic_parameters.yaml
	@test -f config/external_data_sources.yaml

test: ## Execute pytest suite with default profile
	$(PYTHON) -m pytest --maxfail=1 --disable-warnings

coverage: ## Run pytest with coverage reports
	$(PYTHON) -m pytest --cov=cloud_citadel --cov=scripts --cov=models --cov-report=term-missing

## ---------------------------------------------------------------------------
## DATA PIPELINE SHORTCUTS
## ---------------------------------------------------------------------------
.PHONY: etl-transform etl-external etl-aggregate simulators
etl-transform: check-env ## Run telemetry transformer locally
	$(PYTHON) scripts/etl/transform_telemetry.py --mapping-file config/mapping.json

etl-external: check-env ## Load configured external datasets
	$(PYTHON) scripts/etl/load_external_data.py --config config/external_data_sources.yaml

etl-aggregate: check-env ## Compute daily/hourly aggregates in ClickHouse
	$(PYTHON) scripts/etl/aggregate_metrics.py

simulators: check-env ## Launch IoT simulator to feed MQTT broker
	$(PYTHON) scripts/simulators/iot_sensor_simulator.py

## ---------------------------------------------------------------------------
## CONTAINER ORCHESTRATION
## ---------------------------------------------------------------------------
.PHONY: compose-up compose-down metrics-up metrics-down logs
compose-up: check-env ## Start core stack (Kafka, ClickHouse, NiFi, etc.)
	$(COMPOSE) -f docker-compose.yml up -d

compose-down: ## Stop core stack
	$(COMPOSE) -f docker-compose.yml down --remove-orphans

metrics-up: ## Start monitoring stack (Grafana/Prometheus)
	$(COMPOSE) -f docker-compose.metrics.yml up -d

metrics-down: ## Stop monitoring stack
	$(COMPOSE) -f docker-compose.metrics.yml down --remove-orphans

logs: ## Tail docker-compose logs (press Ctrl+C to exit)
	$(COMPOSE) logs -f --tail=200

## ---------------------------------------------------------------------------
## MODEL TRAINING
## ---------------------------------------------------------------------------
.PHONY: train-oracle train-quality train-harvest
train-oracle: check-env ## Train RandomForest oracle model
	$(PYTHON) models/train_oracle_model.py --output-model models/oracle_rf.pkl

train-quality: check-env ## Train quality classifier
	$(PYTHON) models/train_quality_classifier.py --output-model models/rf_quality_v1.pkl

train-harvest: check-env ## Train harvest LSTM + scaler
	$(PYTHON) models/train_harvest_lstm.py --output-model models/lstm_harvest_v1.h5

###############################################################################
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ END OF FILE — VertiFlow Make targets                                      ║
# ║ Submit PR referencing TICKET-133 before updating automation entries.      ║
# ╚══════════════════════════════════════════════════════════════════════════╝
###############################################################################
