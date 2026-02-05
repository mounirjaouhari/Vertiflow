# AGENTS.md - VertiFlow Development Guide

## Overview

VertiFlow is an enterprise-grade data engineering platform for intelligent vertical farming automation. This file provides essential information for AI agents working in this repository.

**Language**: Python 3.11+  
**Architecture**: Microservices with Docker, Kafka, ClickHouse, MongoDB  
**Testing**: pytest with unit/integration/e2e suites  
**Primary Domains**: IoT telemetry, ML predictions, ETL pipelines, agronomic automation  

---

## Build, Lint & Test Commands

### Core Commands
```bash
# Setup environment (creates .env from template)
make env

# Install dependencies
make install

# Clean caches and build artifacts  
make clean

# Static analysis and validation
make lint

# Run pytest suite (default profile)
make test

# Run tests with coverage report
make coverage

# Run single test file
pytest tests/unit/test_oracle.py -v

# Run single test function
pytest tests/unit/test_oracle.py::TestOracleYieldPredictor::test_feature_extraction -v

# Run tests with specific marker
pytest -m "not slow" --maxfail=1

# Run tests for specific module
pytest tests/unit/ -k "oracle" -v
```

### Data Pipeline Commands
```bash
# Start core infrastructure (Kafka, ClickHouse, NiFi, etc.)
make compose-up

# Stop infrastructure
make compose-down

# Start monitoring stack (Grafana/Prometheus)
make metrics-up

# Run telemetry transformer
make etl-transform

# Load external datasets
make etl-external

# Compute aggregates
make etl-aggregate

# Run IoT simulators
make simulators
```

### ML Model Training
```bash
# Train yield oracle model
make train-oracle

# Train quality classifier
make train-quality

# Train harvest LSTM
make train-harvest
```

---

## Code Style Guidelines

### File Headers & Documentation
Every Python file must include the standard VertiFlow header with ticket references:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║                   COMPONENT NAME (TICKET-XXX)                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : YYYY-MM-DD                                                 ║
║ Version         : X.X.X                                                      ║
║ Author(s)       : @username                                                   ║
║ Reviewer(s)     : @username                                                   ║
║ Product Owner   : @username                                                   ║
║ Classification  : Internal - Confidential                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PURPOSE                                                                     ║
║ -------                                                                      ║
║ Brief description of component purpose and business value.                  ║
║                                                                              ║
║ TICKET / TEAM                                                                ║
║ ---------------                                                              ║
║ - Ticket: TICKET-XXX                                                         ║
║ - Squad : Core Data Foundation                                                ║
║ - Members: @name (owner), @name (collaborator)                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
```

### Import Organization
```python
from __future__ import annotations

# Standard library imports
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
import pandas as pd
import numpy as np
from kafka import KafkaConsumer, KafkaProducer
import pytest

# Local imports
from cloud_citadel.core.config import PipelineConfig
from models.base import BaseModel
```

### Naming Conventions
- **Files**: `snake_case.py` (e.g., `transform_telemetry.py`)
- **Classes**: `PascalCase` (e.g., `PipelineConfig`, `OracleYieldPredictor`)
- **Functions**: `snake_case` (e.g., `extract_features()`, `validate_schema()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `KAFKA_BOOTSTRAP_SERVERS`, `DEFAULT_TIMEOUT`)
- **Variables**: `snake_case` (e.g., `sensor_data`, `prediction_result`)

### Type Hints
All functions must include type hints using modern Python typing:

```python
from typing import Any, Dict, List, Optional, Union, Generator
from dataclasses import dataclass, field

def process_telemetry(
    data: Dict[str, Any],
    config: PipelineConfig,
    retry_count: int = 0
) -> Optional[Dict[str, Any]]:
    """Process telemetry data with validation and enrichment."""
    pass

@dataclass
class SensorReading:
    timestamp: datetime
    sensor_id: str
    value: float
    unit: str
    quality_score: float = field(default=1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Error Handling
Follow structured error handling with specific exception types:

```python
import structlog

logger = structlog.get_logger(__name__)

class VertiFlowError(Exception):
    """Base exception for VertiFlow platform."""
    pass

class ValidationError(VertiFlowError):
    """Raised when data validation fails."""
    pass

def process_sensor_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process sensor data with comprehensive error handling."""
    try:
        if not validate_schema(data):
            raise ValidationError(f"Schema validation failed: {data}")
        
        # Process data
        result = transform_data(data)
        logger.info("Data processed successfully", sensor_id=data.get("sensor_id"))
        return result
        
    except ValidationError as e:
        logger.error("Validation error", error=str(e), data=data)
        # Send to Dead Letter Queue
        send_to_dlq(data, str(e))
        return {}
        
    except Exception as e:
        logger.error("Unexpected error processing data", 
                    error=str(e), 
                    sensor_id=data.get("sensor_id"))
        raise VertiFlowError(f"Processing failed: {e}") from e
```

### Logging Standards
Use structured logging with JSON format for production:

```python
import structlog

logger = structlog.get_logger("telemetry.transformer")

# Structured logging examples
logger.info("Processing telemetry batch", 
           batch_size=len(data),
           sensor_count=len(set(d["sensor_id"] for d in data)),
           processing_start=datetime.utcnow().isoformat())

logger.warning("Sensor data quality degraded",
              sensor_id=sensor_id,
              quality_score=quality_score,
              threshold=0.8)

logger.error("Failed to write to ClickHouse",
             error=str(e),
             table_name="telemetry_enriched",
             retry_count=retry_count)
```

### Testing Patterns

#### Unit Tests
```python
class TestTelemetryTransformer:
    """Unit tests for telemetry transformation logic."""
    
    def test_feature_extraction_valid_data(self, sample_telemetry_data):
        """Test feature extraction with valid input."""
        transformer = TelemetryTransformer()
        features = transformer.extract_features([sample_telemetry_data])
        
        assert "temperature_avg" in features
        assert isinstance(features["temperature_avg"], float)
        assert 0 <= features["temperature_avg"] <= 50  # Reasonable bounds
    
    def test_feature_extraction_missing_data(self, incomplete_data):
        """Test graceful handling of incomplete sensor data."""
        transformer = TelemetryTransformer()
        with pytest.raises(ValidationError, match="Missing required field"):
            transformer.extract_features([incomplete_data])
```

#### Integration Tests
```python
@pytest.mark.integration
class TestKafkaPipeline:
    """Integration tests for Kafka processing pipeline."""
    
    def test_end_to_end_processing(self, mock_kafka_producer, sample_batch_data):
        """Test complete pipeline from Kafka to ClickHouse."""
        # Setup mocks
        mock_producer = MagicMock()
        
        # Execute pipeline
        result = process_kafka_batch(sample_batch_data, mock_producer)
        
        # Verify results
        assert result["processed_count"] == len(sample_batch_data)
        mock_producer.send.assert_called()
```

### Configuration Management
Use dataclasses for configuration with environment variable fallbacks:

```python
@dataclass
class PipelineConfig:
    """Centralized configuration management."""
    
    kafka_bootstrap: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "telemetry-transformer")
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", "9000"))
    
    # ML-specific config
    model_path: str = os.getenv("MODEL_PATH", "models/oracle_rf.pkl")
    prediction_threshold: float = float(os.getenv("PREDICTION_THRESHOLD", "0.8"))
    
    # Performance tuning
    batch_size: int = int(os.getenv("BATCH_SIZE", "1000"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
```

### ML Model Standards
- Models are serialized with `joblib` (scikit-learn) or `.h5` (TensorFlow)
- Always save metadata alongside models: `model_name.metrics.json`
- Include feature importance, training metrics, and validation results
- Use `inputs/features/outputs` structure for clear interfaces

### Database Operations
```python
# ClickHouse example
def write_telemetry_batch(data: List[Dict[str, Any]]) -> None:
    """Write telemetry batch to ClickHouse using JSONEachRow format."""
    client = get_clickhouse_client()
    
    json_data = [json.dumps(record) for record in data]
    query = f"INSERT INTO telemetry_enriched FORMAT JSONEachRow"
    
    try:
        client.execute(query, json_data)
        logger.info("Successfully wrote batch", record_count=len(data))
    except Exception as e:
        logger.error("ClickHouse write failed", error=str(e))
        raise

# MongoDB example  
def save_recipe(recipe: PlantRecipe) -> str:
    """Save plant recipe to MongoDB with metadata."""
    client = get_mongodb_client()
    db = client[DB_NAME]
    
    recipe_dict = recipe.to_dict()
    recipe_dict["created_at"] = datetime.utcnow()
    recipe_dict["created_by"] = "vertiflow_system"
    
    result = db.plant_recipes.insert_one(recipe_dict)
    return str(result.inserted_id)
```

---

## Development Workflow

1. **Always run `make env` first** to ensure .env file exists
2. **Use `make install`** after dependency changes  
3. **Run `make lint`** before commits to catch syntax errors
4. **Use `make test`** for basic testing, `make coverage` for detailed reports
5. **Test single components** with specific pytest commands
6. **Use `make compose-up`** to start required infrastructure for integration tests

## Key Directories

- `cloud_citadel/` - Core platform logic and ML models
- `models/` - Machine learning model training scripts
- `scripts/etl/` - Data transformation and pipeline scripts
- `scripts/simulators/` - IoT sensor simulators
- `infrastructure/` - Database initialization and configuration
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests across services
- `tests/e2e/` - End-to-end system tests
- `config/` - Configuration files and mapping definitions

## Common Pitfalls

- **Missing .env file**: Always run `make env` before first usage
- **Kafka connectivity**: Ensure `make compose-up` is running before integration tests
- **ClickHouse schema**: Run schema initialization scripts before data operations
- **Python version**: Use Python 3.11+ - some dependencies fail on older versions
- **kafka-python-ng**: Use this instead of kafka-python for Python 3.13+ compatibility