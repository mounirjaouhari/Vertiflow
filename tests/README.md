# Tests - Suite de tests

Ce dossier contient la suite de tests automatises de VertiFlow.

## Structure

```
tests/
├── __init__.py
├── conftest.py                      # Fixtures pytest
├── unit/                            # Tests unitaires
│   ├── __init__.py
│   ├── test_classifier.py           # Tests A10
│   ├── test_cortex.py               # Tests A11
│   ├── test_feedback_loop.py        # Tests feedback
│   ├── test_oracle.py               # Tests A9
│   ├── test_simulator.py            # Tests simulateur
│   └── test_stream_processor.py     # Tests stream
├── integration/                     # Tests d'integration
│   ├── __init__.py
│   ├── test_clickhouse.py           # Tests ClickHouse
│   ├── test_kafka_connectivity.py   # Tests connexion Kafka
│   ├── test_kafka_pipeline.py       # Tests pipeline Kafka
│   └── test_mqtt_to_clickhouse.py   # Tests flux complet
└── e2e/                             # Tests end-to-end
    ├── __init__.py
    └── test_full_pipeline.py        # Test pipeline complet
```

## Execution

### Tous les tests
```bash
pytest tests/

# Avec couverture
pytest tests/ --cov=cloud_citadel --cov=scripts --cov-report=html

# Via Makefile
make test
make coverage
```

### Par categorie
```bash
# Tests unitaires
pytest tests/unit/

# Tests d'integration
pytest tests/integration/

# Tests E2E
pytest tests/e2e/
```

### Test specifique
```bash
pytest tests/unit/test_oracle.py -v
pytest tests/unit/test_oracle.py::test_prediction_accuracy -v
```

## Fixtures (conftest.py)

### Fixtures disponibles
```python
@pytest.fixture
def sample_telemetry():
    """Donnees de telemetrie exemple."""
    return {...}

@pytest.fixture
def clickhouse_client():
    """Client ClickHouse connecte."""
    return Client(host='localhost')

@pytest.fixture
def kafka_producer():
    """Producer Kafka configure."""
    return KafkaProducer(bootstrap_servers='localhost:9092')
```

## Tests unitaires

### test_oracle.py
```python
def test_prediction_accuracy():
    """Oracle doit avoir R2 > 0.85."""
    oracle = YieldOracle()
    r2 = oracle.evaluate(X_test, y_test)
    assert r2 > 0.85

def test_feature_importance():
    """Les features DLI et temp doivent etre importantes."""
    importance = oracle.feature_importance()
    assert importance['dli'] > 0.1
```

### test_classifier.py
```python
def test_classification_grades():
    """Classifier doit retourner Premium/Standard/Reject."""
    result = classifier.classify(harvest_data)
    assert result in ['Premium', 'Standard', 'Reject']
```

## Tests d'integration

### test_clickhouse.py
```python
def test_insert_telemetry(clickhouse_client):
    """Insert doit reussir dans sensor_telemetry."""
    result = clickhouse_client.execute(
        "INSERT INTO sensor_telemetry VALUES",
        [sample_row]
    )
    assert result == 1
```

### test_kafka_pipeline.py
```python
def test_message_flow(kafka_producer, kafka_consumer):
    """Message doit passer de raw a enriched."""
    kafka_producer.send('telemetry.raw', message)
    received = kafka_consumer.poll(timeout=10)
    assert received is not None
```

## Couverture cible

| Module | Couverture |
|--------|------------|
| cloud_citadel | > 80% |
| scripts/etl | > 75% |
| scripts/simulators | > 70% |
| **Total** | **> 75%** |
