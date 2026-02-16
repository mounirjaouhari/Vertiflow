# 🌿 Agri-Copilot Pro - Intégration VertiFlow

## Architecture d'Intégration

**Agri-Copilot Pro** est un **SERVICE INTÉGRÉ** au projet **vertiflow_cloud_release**, non une application standalone.

```
┌─────────────────────────────────────────────────────────┐
│                   VertiFlow Cloud Release                │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Services Existants (Parteur Docker)    │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ • Kafka (9092, 29092)      → Bus événements      │   │
│  │ • Mosquitto (1883)          → IoT Broker         │   │
│  │ • ClickHouse (9000, 8123)  → Golden Record       │   │
│  │ • MongoDB (27017)           → Opérations         │   │
│  │ • NiFi (8443)               → Gouvernance data   │   │
│  │ • ML Engine (A9)            → Prédictions        │   │
│  │ • ML Classifier (A10)       → Classifications    │   │
│  │ • ML Cortex (A11)           → Optimisations      │   │
│  │ • Harvest Predictor (A9b)   → GDD Scientifique   │   │
│  │ • IoT Simulator             → Données test       │   │
│  └──────────────────────────────────────────────────┘   │
│           ↓                                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │      🎯 AGRI-COPILOT PRO (Service Nouveau)       │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  API REST (FastAPI)              │ Port: 8000   │   │
│  │  • Execution de requêtes          │              │   │
│  │  • Génération SQL IA (Gemini)     │              │   │
│  │  • Authentification & RBAC        │              │   │
│  │  • Audit compliance               │              │   │
│  │  • Cache distribué                │              │   │
│  │  • Rate limiting                  │              │   │
│  └──────────────────────────────────────────────────┘   │
│           ↓                                               │
│  [VirtualNetwork: vertiflow-network]                     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Structure du Projet

```
agri-copilot-pro/
├── INTEGRATION.md              ← Ce fichier
├── README.md                   ← Documentation utilisateur
├── main.py                     ← Entrée API FastAPI (port 8000)
├── app.py                      ← UI Streamlit (local dev uniquement)
├── requirements.txt            ← Dépendances Python
├── setup.py                    ← Configuration package
├── pyproject.toml              ← Config Python moderne
├── conftest.py                 ← Fixtures pytest
├── .env.example                ← Template variables
├── Makefile                    ← Commandes développement
│
├── src/
│   ├── core/
│   │   ├── config.py          ← **ADAPTÉ:** Services Docker existants
│   │   ├── exceptions.py       ← Hiérarchie erreurs
│   │   ├── logging_config.py   ← Logging structuré JSON
│   │   └── security.py         ← Validation SQL, RBAC, hash
│   │
│   ├── api/
│   │   ├── clients.py          ← **ADAPTÉ:** ClickHouse TCP (9000), MongoDB, Gemini, BigQuery
│   │   ├── cache_manager.py    ← Cache LRU avec TTL
│   │   └── rate_limiter.py     ← Token bucket, sliding window
│   │
│   ├── services/
│   │   ├── auth.py             ← JWT, registration, permissions
│   │   ├── query.py            ← NL-to-SQL via Gemini
│   │   └── audit.py            ← **ADAPTÉ:** MongoDB pour audit trail
│   │
│   ├── models/
│   │   └── schemas.py          ← Pydantic v2 models
│   │
│   └── utils/
│       └── validators.py       ← Input validation
│
├── tests/
│   ├── unit/
│   │   ├── test_auth.py        ← 14 test cases
│   │   └── test_validators.py  ← 16 test cases
│   │
│   └── integration/
│       └── test_api.py         ← 20+ test cases
│
└── logs/                        ← Audit & application logs (vol persistant)
```

## Variables d'Environnement (Docker Compose)

Le service agri-copilot utilise les variables du docker-compose existant :

```yaml
# Services existants (non dupliqués)
CLICKHOUSE_HOST=clickhouse       # Service Docker
CLICKHOUSE_PORT=8123             # Port HTTP (9000 pour TCP natif)
CLICKHOUSE_DATABASE=vertiflow    # Synchronisé avec docker-compose

MONGODB_HOST=mongodb             # Service Docker
MONGODB_PORT=27017               # Synchronisé avec docker-compose

KAFKA_BOOTSTRAP_SERVERS=kafka:29092  # Service Docker
KAFKA_TOPIC_EVENTS=agri_copilot_events

# External APIs (hérités du projet)
GCP_PROJECT_ID=${GCP_PROJECT_ID}
GEMINI_API_KEY=${GEMINI_API_KEY}

# Security
SECRET_KEY=...                   # JWT signing key (min 32 chars)
JWT_EXPIRY_HOURS=24
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

## Déploiement & Lancement

### 1. Déployer avec VertiFlow

```bash
cd /path/to/vertiflow_cloud_release

# Démarrer tout (incluant agri-copilot-pro)
docker-compose up -d

# Logs du service
docker-compose logs -f agri-copilot

# API santé
curl http://localhost:8000/api/health
```

### 2. Développement Local

```bash
cd agri-copilot-pro

# Installer dépendances
make install

# Lancer l'API seule (FastAPI)
make run-api
# Accès: http://localhost:8000/api/docs

# Lancer l'UI seule (Streamlit, optionnel)
make run-ui
# Accès: http://localhost:8501

# Lancer les tests
make test

# Vérifier la qualité code
make lint
```

### 3. Configuration Production

```bash
# Copier template et configurer
cp .env.example .env

# Éditer les secrets
vi .env
# GCP_PROJECT_ID=...
# GEMINI_API_KEY=...
# SECRET_KEY=... (générer 32+ chars aléatoires)
```

## Points d'Intégration Clés

### ✅ Pas de Duplication de Services

- **ClickHouse**: Partage avec NiFi, ML Engine, etc.
- **MongoDB**: Partage avec bande opérationnelle
- **Kafka**: Évènements agri-copilot partage avec l'écosystème
- **Redis**: Optionnel (non configuré actuellement)

### ✅ Configuration Dynamique

```python
# src/core/config.py
clickhouse_host = "clickhouse"      # Nom service Docker
mongodb_host = "mongodb"            # Nom service Docker
kafka_bootstrap_servers = "kafka:29092"  # Port INTERNAL

# Adapté automatiquement aux services existants
```

### ✅ Clients Adaptés

```python
# src/api/clients.py

class ClickHouseClient:
    """Utilise port TCP 9000 (natif), pas HTTP 8123"""
    host, port = settings.get_clickhouse_tcp_url()  # → (clickhouse, 9000)

class MongoDBClient:
    """Nouveau client intégré avec MongoDB existant"""
    uri = settings.get_mongodb_uri()  # → mongodb://mongodb:27017/...

class GeminiClient:
    """API externe Google Cloud (credentials du projet)"""
    key = settings.gemini_api_key  # ← Hérité du .env du projet
```

### ✅ Volume Audit Persistant

```yaml
# docker-compose.yml
volumes:
  - ./logs/agri-copilot:/opt/vertiflow/agri-copilot-pro/logs

# Audit trail persistant
audit_service.log_authentication()    # → logs/audit.log
audit_service.log_query_execution()   # → logs/audit.log
audit_service.log_security_violation()  # → logs/audit.log
```

## API Endpoints Disponibles

### Authentification
- `POST /api/auth/login` - Connexion
- `POST /api/auth/register` - Inscription
- `POST /api/auth/refresh` - Renouveler token

### Requêtes
- `POST /api/query/execute` - Exécuter requête (NL ou SQL)
- `GET /api/query/history` - Historique requêtes

### Admin
- `GET /api/admin/audit-report` - Rapport audit (AGRONOME+)
- `GET /api/admin/violations` - Violations sécurité (ADMIN)

### Santé
- `GET /health` - Santé basique
- `GET /api/health/full` - Santé complète (services)

📊 **Documentation interactive**: `http://localhost:8000/api/docs`

## Rôles & Permissions

```
UserRole.AGRICULTEUR
├── Exécuter requêtes (leurs propres données)
├── Voir historique personnel
└── Consulter cache

UserRole.AGRONOME
├── Accès complet requêtes
├── Voir audit reports
└── Analyser patterns

UserRole.ADMIN
├── Gestion utilisateurs
├── Voir violations sécurité
├── Configuration système
└── Rapports complets
```

## Monitoring & Santé

### Health Check Automatique

```bash
# Docker santé
docker-compose ps
# agri-copilot  healthy (ou unhealthy)

# Endpoint santé
curl http://localhost:8000/api/health/full

# Logs
docker-compose logs agri-copilot | grep ERROR
```

### Audit Trail

```bash
# Voir audit logs
tail -f logs/agri-copilot/logs/audit.log

# Format JSON structuré
cat logs/agri-copilot/logs/audit.log | tail -1 | jq .
```

## Contribution & Développement

### Code Style
```bash
make format      # Black (88 chars)
make lint       # flake8, pylint
make type-check # mypy type hints
```

### Tests
```bash
make test           # Tous les tests
make test-unit      # Tests unitaires
make test-coverage  # Avec couverture
```

### CI/CD

GitHub Actions pipeline (si dans projet public):
- ✅ Tests (Python 3.10-3.12)
- ✅ Linting & type checking
- ✅ Security scanning (Bandit, Safety)
- ✅ Docker build & push

## Dépannage

### Problème: "ClickHouse connection refused"
```bash
# ✅ Vérifier que ClickHouse est running
docker-compose ps | grep clickhouse

# ✅ Vérifier la config
env | grep CLICKHOUSE

# ✅ Tester connexion
docker exec agri_copilot_pro python3 -c \
  "from src.api.clients import ClickHouseClient; c = ClickHouseClient(); print(c.health_check())"
```

### Problème: "MongoDB connection timeout"
```bash
# ✅ Vérifier MongoDB
docker-compose ps | grep mongodb

# ✅ Tester connexion
docker exec agri_copilot_pro python3 -c \
  "from src.api.clients import MongoDBClient; c = MongoDBClient(); print(c.health_check())"
```

### Problème: "JWT token invalid"
```bash
# ✅ Vérifier SECRET_KEY configuré
grep SECRET_KEY .env

# ✅ Utiliser nouveau token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

## Performance & Scalabilité

### Implication ClickHouse (Golden Record)

L'app accède directement à ClickHouse pour requêtes analytiques:
- ✅ Requêtes directes vs. passage par NiFi
- ✅ Cache LRU (1000 entités, TTL 3600s)
- ⚠️ Rate limiting (60 req/min par défaut)

### Conseil Production

```python
# .env production
CACHE_TTL_SECONDS=7200         # 2h cache
CACHE_MAX_SIZE=5000            # Plus capacité
RATE_LIMIT_REQUESTS_PER_MINUTE=100  # Augmenter
LOG_LEVEL=WARNING              # Moins logs
ENVIRONMENT=production         # Désactiver docs API
```

## Support & Documentation

- 📖 [README.md](./README.md) - Guide utilisateur
- 🧪 [tests/](./tests/) - Exemples test
- 📝 [docs/](../docs/) - Architecture VertiFlow
- 🐛 [Issues](../../issues) - Rapporter bugs
- 💬 [Discussions](../../discussions) - Questions

---

**Agri-Copilot Pro** = Brique d'IA au service de vertiflow_cloud_release 🌿
