# Guide de Deploiement Pipeline VertiFlow

Ce guide explique comment deployer et demarrer le pipeline de donnees VertiFlow.

## Architecture du Pipeline

```
IoT Sensors --> MQTT --> NiFi --> Kafka --> ETL --> ClickHouse
                          |
                          v
                       MongoDB (configs, recettes)
```

**Alternative simplifiee (recommandee pour les tests):**
```
Simulateur Python --> Kafka (direct) --> ETL Python --> ClickHouse
```

## Prerequis

1. Docker et Docker Compose installes
2. Python 3.9+ avec les dependances (`pip install -r requirements.txt`)
3. Ports disponibles: 8443 (NiFi), 9092 (Kafka), 8123/9000 (ClickHouse), 27017 (MongoDB), 1883 (MQTT)

## Etape 1: Demarrer l'Infrastructure Docker

```bash
# Depuis la racine du projet
docker compose up -d

# Verifier que tous les services sont demarres
docker compose ps
```

Services attendus:
- `zookeeper` - Running
- `kafka` - Running (Healthy)
- `clickhouse` - Running (Healthy)
- `mongodb` - Running (Healthy)
- `mosquitto` - Running
- `nifi` - Running (Healthy)

## Etape 2: Initialiser l'Infrastructure

```bash
python infrastructure/init_infrastructure.py
```

Ce script:
- Verifie que ClickHouse, MongoDB et Kafka sont accessibles
- Cree la base de donnees ClickHouse `vertiflow`
- Cree les topics Kafka (basil_telemetry_full, vertiflow.commands, etc.)
- Seed MongoDB avec les recettes de plantes

## Etape 3: Option A - Pipeline Simplifie (Recommande pour les tests)

### 3a. Demarrer le Simulateur Kafka Direct

```bash
python scripts/simulators/kafka_telemetry_producer.py
```

Ce simulateur:
- Genere des donnees de telemetrie au format Golden Record (153 colonnes)
- Publie directement sur le topic Kafka `basil_telemetry_full`
- Bypass MQTT et NiFi pour un test rapide

### 3b. Demarrer l'ETL Simplifie

Dans un nouveau terminal:
```bash
python scripts/etl/kafka_to_clickhouse.py
```

Ce script:
- Consomme les messages du topic Kafka `basil_telemetry_full`
- Insere les donnees dans ClickHouse `vertiflow.basil_ultimate_realtime`

### 3c. Verifier les Donnees

```bash
# Via Docker
docker exec -it clickhouse clickhouse-client -q "SELECT count() FROM vertiflow.basil_ultimate_realtime"

# Ou via le client Python
python -c "
from clickhouse_driver import Client
c = Client('localhost', port=9000, user='default', password='default')
print(c.execute('SELECT count() FROM vertiflow.basil_ultimate_realtime'))
"
```

## Etape 3: Option B - Pipeline Complet avec NiFi

### 3a. Acceder a NiFi

1. Ouvrir https://localhost:8443/nifi
2. Accepter le certificat SSL auto-signe
3. Login: `admin` / `ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB`

### 3b. Deployer le Pipeline

```bash
python scripts/nifi_workflows/deploy/deploy_pipeline_v2_full.py
```

### 3c. Verifier et Corriger les Problemes

```bash
# Diagnostic seulement
python scripts/nifi_workflows/deploy/nifi_health_check.py --check

# Diagnostic + Corrections automatiques
python scripts/nifi_workflows/deploy/nifi_health_check.py --fix

# Demarrer tous les processeurs
python scripts/nifi_workflows/deploy/nifi_health_check.py --start-all
```

### Problemes Courants NiFi

#### Controller Services Desactives
- Aller dans NiFi > Controller Settings > Controller Services
- Activer: ClickHouse_Connection_Pool, MongoDB_Client_Service, JsonTreeReader, JsonRecordSetWriter

#### Processeurs Invalides (rouge)
Causes frequentes:
1. **Driver JDBC manquant**: Verifier que `drivers/clickhouse-jdbc-0.6.0-all.jar` existe
2. **Connexion Kafka**: Bootstrap server doit etre `kafka:29092` (reseau Docker interne)
3. **Connexion MongoDB**: URI doit etre `mongodb://mongodb:27017`
4. **Dossiers manquants**: Les dossiers `/opt/nifi/nifi-current/exchange/input` etc. doivent exister

## Etape 4: Lancement Unifie

Pour tout demarrer en une commande:

```bash
python scripts/start_vertiflow.py
```

Options:
- `--init-only`: Initialiser l'infrastructure seulement
- `--skip-nifi`: Ne pas deployer le pipeline NiFi
- `--skip-simulator`: Ne pas demarrer le simulateur
- `--skip-etl`: Ne pas demarrer l'ETL
- `--status`: Afficher l'etat du systeme

## Ports et Services

| Service     | Port  | URL                          |
|-------------|-------|------------------------------|
| NiFi UI     | 8443  | https://localhost:8443/nifi  |
| ClickHouse  | 8123  | HTTP API                     |
| ClickHouse  | 9000  | Native Protocol              |
| MongoDB     | 27017 | mongodb://localhost:27017    |
| Kafka       | 9092  | localhost:9092 (externe)     |
| Kafka       | 29092 | kafka:29092 (Docker interne) |
| MQTT        | 1883  | tcp://localhost:1883         |
| WebSocket   | 9001  | ws://localhost:9001          |

## Verification du Flux de Donnees

```bash
# Verifier les topics Kafka
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Consommer des messages Kafka
docker exec -it kafka kafka-console-consumer --topic basil_telemetry_full --bootstrap-server localhost:9092 --from-beginning --max-messages 5

# Verifier les donnees ClickHouse
docker exec -it clickhouse clickhouse-client -q "SELECT rack_id, count(), avg(air_temp_internal) FROM vertiflow.basil_ultimate_realtime GROUP BY rack_id"

# Verifier MongoDB
docker exec -it mongodb mongosh --eval "db = db.getSiblingDB('vertiflow_ops'); db.plant_recipes.find().pretty()"
```

## Troubleshooting

### NiFi ne demarre pas
```bash
docker logs nifi
```

### Kafka non accessible
```bash
docker exec -it kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

### ClickHouse erreur d'authentification
Le mot de passe par defaut est `default`. Verifier:
```bash
docker exec -it clickhouse clickhouse-client --user default --password default
```

### ETL bloque sur Consumer
Verifier que le topic Kafka contient des messages:
```bash
docker exec -it kafka kafka-console-consumer --topic basil_telemetry_full --bootstrap-server localhost:9092 --from-beginning --max-messages 1
```
