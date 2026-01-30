# Utils - Utilitaires

Ce dossier contient les scripts utilitaires pour VertiFlow.

## Structure

```
utils/
├── generate_data_dictionary.py      # Generation du catalogue de donnees
└── validate_deployment.py           # Validation du deploiement
```

## Scripts

### generate_data_dictionary.py
Genere automatiquement le catalogue de donnees a partir des schemas ClickHouse :
- Liste des tables et colonnes
- Types de donnees
- Descriptions
- Export Markdown/JSON

```bash
python scripts/utils/generate_data_dictionary.py
```

### validate_deployment.py
Valide que l'infrastructure est correctement deployee :
- Verification des services (ClickHouse, Kafka, MongoDB, NiFi)
- Validation des schemas
- Test de connectivite
- Rapport de conformite

```bash
python scripts/utils/validate_deployment.py
```

## Sortie de validation

```
=== VERTIFLOW DEPLOYMENT VALIDATION ===

[1/5] ClickHouse Schema
  [OK] Table sensor_telemetry (156 columns)
  [OK] Table hourly_aggregates
  [OK] Materialized views

[2/5] Kafka Topics
  [OK] telemetry.raw (3 partitions)
  [OK] telemetry.enriched (3 partitions)

[3/5] MongoDB Collections
  [OK] plant_recipes (35 documents)
  [OK] configurations

[4/5] NiFi Pipelines
  [OK] Process Group: VertiFlow Governance
  [OK] 12 processors running

[5/5] Connectivity
  [OK] MQTT broker accessible
  [OK] External APIs reachable

=== VALIDATION COMPLETE ===
Status: PASSED
```
