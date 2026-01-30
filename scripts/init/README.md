# Init - Scripts d'initialisation

Ce dossier contient les scripts d'initialisation de l'infrastructure VertiFlow.

## Structure

```
init/
├── init_clickhouse.py               # Bootstrap schema ClickHouse
├── init_kafka_topics.py             # Creation des topics Kafka
├── init_mongodb.py                  # Seeding MongoDB
└── clickhouse-seed.py               # Donnees de test ClickHouse
```

## Scripts

### init_clickhouse.py (v1.0)
**Ticket:** TICKET-134 | **Owner:** @Imrane

Bootstrap du schema ClickHouse :
- Execute les scripts SQL dans `infrastructure/init_scripts/clickhouse/`
- Creation de la base `vertiflow`
- Creation des tables et vues materialisees

```bash
# Execution normale
python scripts/init/init_clickhouse.py

# Mode dry-run
python scripts/init/init_clickhouse.py --dry-run

# Mode verbose
python scripts/init/init_clickhouse.py --verbose
```

### init_kafka_topics.py
**Ticket:** TICKET-135 | **Owner:** @Imrane

Creation des topics Kafka :
- `telemetry.raw` - Donnees brutes capteurs
- `telemetry.enriched` - Donnees transformees
- `telemetry.deadletter` - Messages invalides
- `commands` - Commandes actuateurs
- `alerts` - Alertes systeme

```bash
python scripts/init/init_kafka_topics.py
```

### init_mongodb.py
**Ticket:** TICKET-136 | **Owner:** @Mouhammed

Seeding MongoDB :
- Collections `plant_recipes`, `configurations`
- Recettes de culture (Cornell, HydroBuddy)
- Parametres systeme

```bash
python scripts/init/init_mongodb.py
```

### clickhouse-seed.py
Insertion de donnees de test dans ClickHouse pour validation.

```bash
python scripts/init/clickhouse-seed.py
```

## Variables d'environnement

| Variable | Defaut | Description |
|----------|--------|-------------|
| `CLICKHOUSE_HOST` | `localhost` | Hote ClickHouse |
| `CLICKHOUSE_PORT` | `9000` | Port natif |
| `CLICKHOUSE_USER` | `default` | Utilisateur |
| `CLICKHOUSE_DB` | `vertiflow` | Base de donnees |
| `KAFKA_BOOTSTRAP` | `localhost:9092` | Serveurs Kafka |
| `MONGODB_URI` | `mongodb://localhost:27017` | URI MongoDB |

## Ordre d'execution

```bash
# 1. ClickHouse (schema)
python scripts/init/init_clickhouse.py

# 2. Kafka (topics)
python scripts/init/init_kafka_topics.py

# 3. MongoDB (seed)
python scripts/init/init_mongodb.py

# 4. Donnees de test (optionnel)
python scripts/init/clickhouse-seed.py
```
