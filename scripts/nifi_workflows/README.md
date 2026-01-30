# NiFi Workflows - Scripts de deploiement

Ce dossier contient les scripts de deploiement et gestion des pipelines Apache NiFi pour VertiFlow.

## Structure (Optimisée 2026-01-15)

```
nifi_workflows/
├── deploy/                              # Scripts de deploiement
│   ├── deploy_pipeline_v2_full.py       # Pipeline complet (6 zones + DLQ) - SEUL SCRIPT REQUIS
│   ├── nifi_health_check.py             # Diagnostic sante pipeline
│   ├── diagnose_services.py             # Diagnostic services
│   ├── verify_data_flow.py              # Verification flux donnees
│   └── _archived/                       # Scripts obsoletes (ne pas utiliser)
├── utils/                               # Utilitaires
│   ├── activate_pipeline.py             # Active/demarre les process groups
│   ├── blockchain_hash_processor.py     # Hash SHA-256 pour tracabilite
│   ├── cleanup_nifi.py                  # Nettoie NiFi (supprime tout)
│   └── generate_test_data.py            # Genere donnees de test
└── tests/                               # Tests
    └── test_mqtt_pipeline.py            # Test MQTT simple
```

## Workflow de Deploiement Simplifie

### Etape 1: Deployer le pipeline (script unique)
```bash
python scripts/nifi_workflows/deploy/deploy_pipeline_v2_full.py
```
> Ce script gere automatiquement: creation des zones, correction des processeurs, et configuration complete.

### Etape 2: Diagnostiquer (si necessaire)
```bash
python scripts/nifi_workflows/deploy/nifi_health_check.py
```

### Etape 3: Verifier le flux de donnees
```bash
python scripts/nifi_workflows/deploy/verify_data_flow.py
```

### Etape 4: Activer le pipeline
```bash
python scripts/nifi_workflows/utils/activate_pipeline.py
```

### Reset complet (optionnel)
```bash
python scripts/nifi_workflows/utils/cleanup_nifi.py
```

## Variables d'environnement

| Variable | Defaut | Description |
|----------|--------|-------------|
| `NIFI_BASE_URL` | `https://localhost:8443/nifi-api` | URL de l'API NiFi |
| `NIFI_USERNAME` | `admin` | Utilisateur NiFi |
| `NIFI_PASSWORD` | (voir .env) | Mot de passe NiFi |

## Architecture du pipeline v2

```
Zone 0 - External Data APIs
    ├── Open-Meteo (meteo horaire)
    ├── NASA POWER (climat agricole)
    └── OpenAQ (qualite air)

Zone 1 - Ingestion & Validation
    ├── ListenHTTP (port 8080)
    ├── ConsumeMQTT
    ├── GetFile
    └── ValidateRecord

Zone 2 - Contextualisation
    ├── LookupRecord (MongoDB recipes)
    ├── ExecuteScript (calcul VPD)
    └── JoltTransformJSON

Zone 2.5 - Blockchain Hash (Tracabilite)
    └── ExecuteScript (blockchain_hash_processor.py)
        ├── blockchain_hash (SHA-256)
        └── audit_trail_signature (HMAC-SHA256)

Zone 3 - Persistance
    ├── PutDatabaseRecord → ClickHouse
    ├── PutMongo → MongoDB
    └── PutFile → Archive

Zone 4 - Retroaction & Alertes
    ├── QueryRecord (detection anomalies)
    └── PublishMQTT (commandes actuateurs)

Zone 5 - Static Data Loaders
    ├── CSV/Datasets
    ├── Lab Data
    └── Plant Recipes

DLQ - Dead Letter Queue
    └── Gestion des erreurs
```

## Erreurs Connues et Solutions

### 1. GetFile - Repertoire inexistant
**Erreur:** `Directory '/opt/nifi/...' does not exist`
**Solution:** `deploy_pipeline_v2_full.py` corrige automatiquement les chemins.

### 2. PutMongo - Mode upsert invalide
**Erreur:** `Upsert Condition is not valid JSON`
**Solution:** Corrige automatiquement par `deploy_pipeline_v2_full.py` (mode 'insert').

### 3. ExecuteScript - Erreur BigDecimal
**Erreur:** `No signature of method: java.math.BigDecimal.div()`
**Solution:** Script VPD corrige avec conversions explicites vers double.

### 4. QueryRecord - Colonne VPD non trouvee
**Erreur:** `Column 'vpd' not found`
**Solution:** Utiliser `vapor_pressure_deficit` (corrige dans deploy_pipeline_v2_full.py).

### 5. PublishKafka - Timeout
**Erreur:** `TimeoutException: Timeout expired while initializing producer`
**Solution:** S'assurer que Kafka est demarre avant NiFi (`docker-compose up kafka`).

## Blockchain Hash - Tracabilite des Donnees

Le module `blockchain_hash_processor.py` ajoute deux champs de tracabilite a chaque enregistrement:

| Champ | Type | Description |
|-------|------|-------------|
| `blockchain_hash` | SHA-256 (64 chars) | Hash deterministe du contenu pour preuve d'integrite |
| `audit_trail_signature` | HMAC-SHA256 (64 chars) | Signature pour verification d'origine |

### Integration dans NiFi

1. **Ajouter un processeur ExecuteScript** apres la zone de contextualisation
2. **Configurer le script**: `/opt/nifi/scripts/blockchain_hash_processor.py`
3. **Placer AVANT** PutDatabaseRecord (ClickHouse)

### Test standalone

```bash
python scripts/nifi_workflows/utils/blockchain_hash_processor.py
```

### Verification d'integrite

```python
from blockchain_hash_processor import verify_hash, verify_signature

record = {...}  # Enregistrement avec blockchain_hash
is_valid = verify_hash(record)      # True si donnees non modifiees
is_signed = verify_signature(record) # True si origine VertiFlow
```

## Documentation Complementaire

- [CORRECTIONS_APPLIQUEES.md](./CORRECTIONS_APPLIQUEES.md) - Log detaille des corrections
- [NiFi_Flow.json](./NiFi_Flow.json) - Export du workflow actuel
