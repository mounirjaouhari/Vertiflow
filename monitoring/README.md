# Monitoring - Observabilite

Ce dossier contient la configuration de monitoring de VertiFlow.

## Structure

```
monitoring/
├── __init__.py
├── prometheus_alerts.yml            # Regles d'alertes Prometheus
└── alertmanager/
    └── alertmanager.yml             # Configuration AlertManager
```

## Prometheus

### Alertes configurees

#### Infrastructure
```yaml
- alert: ClickHouseDown
  expr: up{job="clickhouse"} == 0
  for: 1m
  severity: critical

- alert: KafkaLagHigh
  expr: kafka_consumer_lag > 10000
  for: 5m
  severity: warning
```

#### Application
```yaml
- alert: HighErrorRate
  expr: rate(errors_total[5m]) > 0.1
  for: 2m
  severity: warning

- alert: LatencyHigh
  expr: histogram_quantile(0.99, http_request_duration_seconds) > 5
  for: 5m
  severity: warning
```

#### Agronomie
```yaml
- alert: TemperatureOutOfRange
  expr: air_temp_internal > 30 or air_temp_internal < 15
  for: 10m
  severity: warning

- alert: VPDCritical
  expr: vapor_pressure_deficit > 1.5 or vapor_pressure_deficit < 0.4
  for: 15m
  severity: critical
```

## AlertManager

### Configuration
```yaml
# alertmanager.yml
route:
  receiver: 'vertiflow-team'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'vertiflow-team'
    slack_configs:
      - channel: '#vertiflow-alerts'
    email_configs:
      - to: 'alerts@vertiflow.ai'
```

## Metriques cles

| Metrique | Source | Seuil |
|----------|--------|-------|
| `clickhouse_queries_failed` | ClickHouse | > 0 |
| `kafka_consumer_lag` | Kafka | < 10000 |
| `nifi_queue_size` | NiFi | < 100000 |
| `air_temp_internal` | Capteurs | 18-28°C |
| `vapor_pressure_deficit` | Calcule | 0.4-1.2 kPa |

## Demarrage

```bash
# Avec docker-compose
docker-compose -f docker-compose.metrics.yml up -d

# Verifier Prometheus
curl http://localhost:9090/-/healthy

# Verifier AlertManager
curl http://localhost:9093/-/healthy
```
