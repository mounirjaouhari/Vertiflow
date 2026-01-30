# Plan d'Exécution du Système VertiFlow

**Date**: 04 Janvier 2026
**Version**: 1.0
**Ticket**: TICKET-005 (Harmonisation)

---

## Prérequis

### Logiciels Requis
- Docker Desktop (avec Docker Compose v2)
- Python 3.10+
- Git

### Vérification des Prérequis
```bash
# Vérifier Docker
docker --version
docker compose version

# Vérifier Python
python --version
pip --version
```

---

## Phase 1: Préparation de l'Environnement

### Étape 1.1: Configuration de l'Environnement
```bash
# 1. Cloner le projet (si pas déjà fait)
cd d:\vertiflow-data-platform

# 2. Créer le fichier .env à partir du template
copy .env.example .env
# ou avec Make:
make env
```

### Étape 1.2: Installation des Dépendances Python
```bash
# Créer un environnement virtuel (recommandé)
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt
# ou avec Make:
make install
```

### Étape 1.3: Créer les Dossiers Requis
```bash
# Dossiers nécessaires pour NiFi
mkdir -p drivers
mkdir -p nifi_exchange/input
mkdir -p nifi_exchange/output

# Télécharger le driver ClickHouse JDBC (requis pour NiFi)
# URL: https://github.com/ClickHouse/clickhouse-jdbc/releases
# Placer clickhouse-jdbc-0.4.6-all.jar dans ./drivers/
```

---

## Phase 2: Démarrage de l'Infrastructure Docker

### Étape 2.1: Lancer les Services de Base
```bash
# Démarrer tous les conteneurs
docker compose up -d
# ou avec Make:
make compose-up

# Vérifier l'état des services
docker compose ps
```

### Étape 2.2: Attendre que les Services Soient Prêts
```bash
# Surveiller les logs jusqu'à ce que tout soit stable
docker compose logs -f

# Vérifier individuellement:
# Zookeeper (port 2181)
docker logs zookeeper

# Kafka (port 9092)
docker logs kafka

# ClickHouse (port 8123)
docker logs clickhouse

# MongoDB (port 27017)
docker logs mongodb

# Mosquitto (port 1883)
docker logs mosquitto

# NiFi (port 8443) - Peut prendre 2-3 minutes
docker logs nifi
```

### Ordre de Démarrage (Automatique via depends_on)
```
1. Zookeeper       (30s)
2. Kafka           (30s) - dépend de Zookeeper
3. ClickHouse      (20s)
4. MongoDB         (20s)
5. Mosquitto       (10s)
6. NiFi            (2-3min) - le plus long
```

---

## Phase 3: Initialisation des Bases de Données

### Étape 3.1: Vérifier l'Initialisation Automatique
Les scripts d'initialisation sont montés via Docker volumes:
- **ClickHouse**: `./init_scripts/clickhouse/*.sql` → Exécutés automatiquement
- **MongoDB**: `./init_scripts/mongodb/*.js` → Exécutés automatiquement

### Étape 3.2: Exécuter le Script d'Initialisation Python
```bash
# Ce script vérifie et complète l'initialisation
python infrastructure/init_infrastructure.py
```

**Ce script fait:**
- Vérifie la connexion à ClickHouse, MongoDB, Kafka
- Crée les topics Kafka (basil_telemetry_full, vertiflow.commands, etc.)
- Seed MongoDB avec les recettes de plantes
- Crée les collections quality_predictions et recipe_optimizations

### Étape 3.3: Vérifier les Bases de Données
```bash
# Vérifier ClickHouse
docker exec -it clickhouse clickhouse-client --query "SHOW TABLES FROM vertiflow"
# Attendu: basil_ultimate_realtime, ext_weather_history, etc.

# Vérifier MongoDB
docker exec -it mongodb mongosh --eval "db.getSiblingDB('vertiflow_ops').getCollectionNames()"
# Attendu: live_state, incident_logs, plant_recipes

# Vérifier les topics Kafka
docker exec -it kafka kafka-topics --bootstrap-server kafka:29092 --list
# Attendu: basil_telemetry_full, vertiflow.commands, vertiflow.alerts, etc.
```

---

## Phase 4: Configuration du Pipeline NiFi

### Étape 4.1: Accéder à l'Interface NiFi
```
URL: https://localhost:8443/nifi
Username: admin
Password: ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB
```

> **Note**: Accepter le certificat auto-signé dans le navigateur.

### Étape 4.2: Déployer le Pipeline Automatiquement
```bash
# Exécuter le script de déploiement NiFi
python scripts/setup_vertiflow_governance_pipeline.py
```

**Ce script crée:**
- Controller Services (ClickHouse, MongoDB, JSON Reader/Writer)
- Zone 1: Ingestion (MQTT, HTTP, File)
- Zone 2: Contextualisation (Lookup, VPD, Jolt Transform)
- Zone 3: Persistance (ClickHouse, MongoDB, Archive)
- Zone 4: Rétroaction (Alertes → MQTT Actionneurs)

### Étape 4.3: Activer le Pipeline dans NiFi
1. Dans l'interface NiFi, sélectionner le Process Group "VertiFlow Governance Pipeline"
2. Clic droit → "Start" pour démarrer tous les processeurs

---

## Phase 5: Lancer les Simulateurs IoT

### Étape 5.1: Démarrer le Simulateur Principal
```bash
# Simulateur de capteurs IoT (climat, hardware)
python scripts/simulators/iot_sensor_simulator.py
# ou avec Make:
make simulators
```

### Étape 5.2: Démarrer les Simulateurs Additionnels (Optionnel)
```bash
# Dans des terminaux séparés:

# Simulateur LED (spectre lumineux)
python scripts/simulators/led_spectrum_simulator.py

# Simulateur Nutriments (hydroponique)
python scripts/simulators/nutrient_sensor_simulator.py

# Ou lancer tous les simulateurs ensemble:
python scripts/run_all_simulators.py
```

### Étape 5.3: Vérifier la Réception MQTT
```bash
# Souscrire aux topics MQTT pour voir les messages
docker exec -it mosquitto mosquitto_sub -h localhost -t "vertiflow/telemetry/#" -v
```

---

## Phase 6: Vérification du Flux de Données

### Étape 6.1: Vérifier Kafka
```bash
# Consommer quelques messages du topic principal
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic basil_telemetry_full \
  --from-beginning \
  --max-messages 5
```

### Étape 6.2: Vérifier ClickHouse
```bash
# Compter les enregistrements
docker exec -it clickhouse clickhouse-client --query \
  "SELECT count() FROM vertiflow.basil_ultimate_realtime"

# Voir les derniers enregistrements
docker exec -it clickhouse clickhouse-client --query \
  "SELECT timestamp, farm_id, rack_id, air_temp_internal, nutrient_n_total
   FROM vertiflow.basil_ultimate_realtime
   ORDER BY timestamp DESC
   LIMIT 5"
```

### Étape 6.3: Vérifier MongoDB
```bash
# Voir l'état temps réel
docker exec -it mongodb mongosh --eval \
  "db.getSiblingDB('vertiflow_ops').live_state.find().limit(3).pretty()"

# Voir les incidents
docker exec -it mongodb mongosh --eval \
  "db.getSiblingDB('vertiflow_ops').incident_logs.find().sort({timestamp: -1}).limit(3).pretty()"
```

---

## Phase 7: Lancer les Algorithmes IA (Optionnel)

### Étape 7.1: Lancer le Cortex (Optimisation A11)
```bash
python cloud_citadel/nervous_system/cortex.py
```

### Étape 7.2: Lancer le Classifier (Qualité A10)
```bash
python cloud_citadel/nervous_system/classifier.py
```

### Étape 7.3: Lancer l'Oracle (Prédiction A9)
```bash
python cloud_citadel/nervous_system/oracle.py
```

---

## Diagramme de Démarrage

```
┌─────────────────────────────────────────────────────────────────┐
│                     PLAN D'EXÉCUTION                            │
└─────────────────────────────────────────────────────────────────┘

Phase 1: PRÉPARATION (5 min)
├── 1.1 Créer .env
├── 1.2 pip install -r requirements.txt
└── 1.3 Créer dossiers (drivers/, nifi_exchange/)

                    │
                    ▼

Phase 2: DOCKER (5 min)
├── 2.1 docker compose up -d
└── 2.2 Attendre que tous les services soient healthy
        ┌─────────────────────────────────────┐
        │ Zookeeper → Kafka → ClickHouse      │
        │ MongoDB → Mosquitto → NiFi          │
        └─────────────────────────────────────┘

                    │
                    ▼

Phase 3: INITIALISATION (2 min)
├── 3.1 Scripts SQL/JS exécutés automatiquement
├── 3.2 python infrastructure/init_infrastructure.py
└── 3.3 Vérifier les bases (ClickHouse, MongoDB, Kafka)

                    │
                    ▼

Phase 4: NIFI PIPELINE (3 min)
├── 4.1 Accéder à https://localhost:8443/nifi
├── 4.2 python scripts/setup_vertiflow_governance_pipeline.py
└── 4.3 Start le Process Group dans l'UI

                    │
                    ▼

Phase 5: SIMULATEURS (1 min)
├── 5.1 python scripts/simulators/iot_sensor_simulator.py
├── 5.2 (Optionnel) led_spectrum_simulator.py
└── 5.3 (Optionnel) nutrient_sensor_simulator.py

                    │
                    ▼

Phase 6: VÉRIFICATION (2 min)
├── 6.1 Kafka: Messages dans basil_telemetry_full
├── 6.2 ClickHouse: Données dans basil_ultimate_realtime
└── 6.3 MongoDB: Documents dans live_state

                    │
                    ▼

Phase 7: IA (Optionnel)
├── 7.1 cortex.py (Optimisation recettes)
├── 7.2 classifier.py (Classification qualité)
└── 7.3 oracle.py (Prédictions récolte)
```

---

## Commandes Rapides (Makefile)

| Commande | Description |
|----------|-------------|
| `make env` | Créer .env depuis .env.example |
| `make install` | Installer les dépendances Python |
| `make compose-up` | Démarrer Docker Compose |
| `make compose-down` | Arrêter Docker Compose |
| `make logs` | Voir les logs Docker |
| `make simulators` | Lancer le simulateur IoT |
| `make etl-transform` | Exécuter l'ETL de transformation |
| `make test` | Exécuter les tests |
| `make lint` | Vérifier la syntaxe |

---

## Arrêt du Système

### Arrêt Propre
```bash
# 1. Arrêter les simulateurs (Ctrl+C dans les terminaux)

# 2. Arrêter les algorithmes IA (Ctrl+C)

# 3. Arrêter Docker Compose
docker compose down
# ou avec Make:
make compose-down

# Pour supprimer aussi les volumes (ATTENTION: perte de données):
docker compose down -v
```

---

## Dépannage

### NiFi ne démarre pas
```bash
# Vérifier les logs
docker logs nifi

# Redémarrer NiFi
docker compose restart nifi
```

### Kafka ne reçoit pas de messages
```bash
# Vérifier que Zookeeper est up
docker exec -it zookeeper zkCli.sh -cmd status

# Vérifier les topics
docker exec -it kafka kafka-topics --bootstrap-server kafka:29092 --describe
```

### ClickHouse: Table non trouvée
```bash
# Réexécuter les scripts d'init
docker exec -it clickhouse clickhouse-client < infrastructure/init_scripts/clickhouse/01_tables.sql
```

### MongoDB: Collection manquante
```bash
# Réexécuter le seed
docker exec -it mongodb mongosh < infrastructure/init_scripts/mongodb/seed_data.js
```

---

## URLs des Services

| Service | URL | Credentials |
|---------|-----|-------------|
| NiFi UI | https://localhost:8443/nifi | admin / ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB |
| ClickHouse HTTP | http://localhost:8123 | default / (vide) |
| MongoDB | mongodb://localhost:27017 | (pas d'auth par défaut) |
| Kafka | localhost:9092 | - |
| MQTT | localhost:1883 | - |

---

## Temps Total Estimé

| Phase | Durée |
|-------|-------|
| Préparation | 5 min |
| Docker Startup | 5 min |
| Initialisation | 2 min |
| NiFi Pipeline | 3 min |
| Simulateurs | 1 min |
| Vérification | 2 min |
| **TOTAL** | **~18 minutes** |

---

**Auteur**: Claude AI (Harmonisation TICKET-005)
**Dernière mise à jour**: 04 Janvier 2026
