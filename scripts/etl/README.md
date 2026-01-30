# ETL - Pipelines de transformation

Ce dossier contient les scripts ETL (Extract, Transform, Load) pour VertiFlow.

## Structure

```
etl/
├── transform_telemetry.py           # Transformation des donnees IoT
├── load_external_data.py            # Chargement des donnees externes
└── aggregate_metrics.py             # Agregation des metriques
```

## Scripts

### transform_telemetry.py (v1.0)
**Ticket:** TICKET-123 | **Owner:** @Mouhammed

Transformation complete des donnees IoT :
- Consomme depuis Kafka `telemetry.raw`
- Validation de schema avec DLQ
- Normalisation des unites (F->C, Pa->kPa, lux->PPFD)
- Calculs derives (VPD, Dew Point, Growth Score)
- Insert batch vers ClickHouse
- Republication vers `telemetry.enriched`

```bash
# Mode normal
python scripts/etl/transform_telemetry.py

# Mode dry-run (sans ecriture)
python scripts/etl/transform_telemetry.py --dry-run
```

### load_external_data.py
**Ticket:** TICKET-125 | **Owner:** @Mouhammed

Chargement des donnees externes dans ClickHouse/MongoDB :
- Datasets NASA POWER, OpenAg, Wageningen
- Integration avec les tables de reference

```bash
python scripts/etl/load_external_data.py
```

### aggregate_metrics.py
**Ticket:** TICKET-126 | **Owner:** @Mouhammed

Calcul des agregations temporelles :
- Agregations 1 min, 1 heure, journalieres
- Vues materialisees Power BI

```bash
python scripts/etl/aggregate_metrics.py
```

## Variables d'environnement

| Variable | Defaut | Description |
|----------|--------|-------------|
| `KAFKA_BOOTSTRAP` | `kafka:9092` | Serveurs Kafka |
| `KAFKA_SOURCE_TOPIC` | `telemetry.raw` | Topic source |
| `KAFKA_TARGET_TOPIC` | `telemetry.enriched` | Topic destination |
| `CLICKHOUSE_URL` | `http://clickhouse:8123` | URL ClickHouse |
| `CLICKHOUSE_TABLE` | `telemetry_enriched` | Table cible |
| `BATCH_SIZE` | `500` | Taille des batchs |

## Metriques calculees

| Metrique | Formule | Description |
|----------|---------|-------------|
| VPD | Tetens equation | Deficit de pression de vapeur |
| Dew Point | Magnus formula | Point de rosee |
| Growth Score | Heuristic 0-1 | Score de confort agronomique |
