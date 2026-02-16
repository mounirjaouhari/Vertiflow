# 🚀 GUIDE D'INTÉGRATION RAPIDE - Agri-Copilot Pro

## ✅ Status: INTÉGRATION RÉUSSIE

Agri-Copilot Pro est maintenant **complètement intégré** dans `vertiflow_cloud_release` comme un **SERVICE** (comme les ML engines, NiFi, etc.).

---

## 📋 Checklist d'Intégration

- ✅ **Aucune duplication de services** - Utilise ClickHouse, MongoDB, Kafka existants
- ✅ **Configuration harmonieuse** - Hosts Docker (clickhouse, mongodb, kafka)  
- ✅ **Port 8000** - API FastAPI exposée
- ✅ **Docker Compose intégré** - Ajouté au docker-compose.yml root
- ✅ **Documentation complète** - INTEGRATION.md, README.md, .env.example
- ✅ **Validation passée** - 45/45 tests ✅

---

## 🎯 Étapes de Déploiement

### 1️⃣ En Développement Local

```bash
# Aller au dossier agri-copilot-pro
cd /path/to/vertiflow_cloud_release/agri-copilot-pro

# Installer les dépendances
pip install -r requirements.txt

# Configurer (optionnel, utilise les défauts pour Docker)
# cp .env.example .env

# Lancer l'API FastAPI (port 8000)
python3 main.py

# OU lancer la UI Streamlit (dev local uniquement, port 8501)
streamlit run app.py

# Tests
pytest tests/
```

### 2️⃣ Avec Docker Compose (Production/Staging)

```bash
# Aller au projet root
cd /path/to/vertiflow_cloud_release

# Démarrer agri-copilot comme service
docker-compose up -d agri-copilot

# Vérifier le déploiement
docker-compose ps | grep agri

# Logs
docker-compose logs -f agri-copilot

# Vérifier la santé
curl http://localhost:8000/api/health

# API docs (dev mode)
curl http://localhost:8000/api/docs
```

### 3️⃣ Vérifications Importantes

```bash
# ✅ Vérifier que ClickHouse répond
docker exec agri_copilot_pro python3 -c \
  "from src.api.clients import ClickHouseClient; c = ClickHouseClient(); print('ClickHouse OK' if c.health_check() else 'FAIL')"

# ✅ Vérifier que MongoDB répond
docker exec agri_copilot_pro python3 -c \
  "from src.api.clients import MongoDBClient; c = MongoDBClient(); print('MongoDB OK' if c.health_check() else 'FAIL')"

# ✅ Vérifier l'API
curl -s http://localhost:8000/api/health | jq .
```

---

## 📂 Structure Finale

```
agri-copilot-pro/
├── 🎯 SERVICE INTÉGRÉ (PAS d'application standalone)
│
├── 📁 Code Source
│   ├── main.py          → API FastAPI (port 8000)
│   ├── app.py           → UI Streamlit (dev local)
│   └── src/             → Services, API clients, modèles
│
├── 📁 Configuration
│   ├── .env.example     → Variables (hosts Docker)
│   ├── setup.py         → Package config
│   └── pyproject.toml   → Python 3.10+ config
│
├── 📁 Tests
│   ├── tests/unit/      → Tests unitaires
│   └── tests/integration/ → Tests d'intégration
│
└── 📖 Documentation
    ├── INTEGRATION.md   → Détails d'intégration
    ├── README.md        → Guide utilisateur
    ├── CHANGELOG.md     → Historique versions
    └── validate_integration.py → Script validation
```

**Fichiers PAS présents (c'est normal!):**
- ❌ `docker-compose.yml` - C'est le docker-compose root qui les gère
- ❌ `Dockerfile` - Utilise python:3.11-slim du docker-compose root
- ❌ `.github/workflows/ci-cd.yml` - Gestion au niveau projet

---

## 🔌 Points d'Intégration avec VertiFlow

| Composant | Intégration |
|-----------|-----------|
| **ClickHouse** | Service existant, port 9000 (TCP)  |
| **MongoDB** | Service existant pour audit trail |
| **Kafka** | Service existant pour événements |
| **NiFi** | Indépendant, données partagées via ClickHouse |
| **ML Engines** | Indépendants, données partagées via ClickHouse |
| **Network** | `vertiflow-network` (Docker bridge) |

---

## 🌐 API Endpoints (Port 8000)

```
POST   /api/auth/login           # Authentification
POST   /api/auth/register        # Création utilisateur
POST   /api/auth/refresh         # Renouveler token

POST   /api/query/execute        # Exécuter requête (NL ou SQL)
GET    /api/query/history        # Historique requêtes

GET    /api/admin/audit-report   # Rapport audit (AGRONOME+)
GET    /api/admin/violations     # Violations sécurité (ADMIN)

GET    /health                   # Santé basique
GET    /api/health/full          # Santé complète

GET    /api/docs                 # Documentation Swagger
```

---

## ⚙️ Variables d'Environnement (Docker)

Le service reçoit automatiquement du `docker-compose.yml`:

```yaml
CLICKHOUSE_HOST=clickhouse         # Service Docker
CLICKHOUSE_PORT=8123              # Port HTTP
CLICKHOUSE_DATABASE=vertiflow      

MONGODB_HOST=mongodb              # Service Docker
MONGODB_PORT=27017

KAFKA_BOOTSTRAP_SERVERS=kafka:29092

GCP_PROJECT_ID=${GCP_PROJECT_ID}   # Hérité du projet
GEMINI_API_KEY=${GEMINI_API_KEY}

SECRET_KEY=...                     # JWT signing
```

**Pour développement local:**
- Copier `.env.example` → `.env`
- Adapter hosts si pas dans Docker (localhost)
- Les défauts fonctionnent avec docker-compose

---

## 🧪 Tests de Validation

**Voir l'intégration:**
```bash
cd agri-copilot-pro
python3 validate_integration.py
```

**Résultat attendu:** ✅ 45/45 tests passés

---

## 📖 Documentation Détaillée

Pour info complète sur l'intégration avec vertiflow_cloud_release:

👉 **[INTEGRATION.md](./INTEGRATION.md)**
- Architecture détaillée
- Intégration des services
- Configuration par étape
- Troubleshooting

👉 **[README.md](./README.md)**
- Guide utilisateur
- Exemples d'API
- Rôles et permissions

👉 **[docker-compose.yml](../docker-compose.yml)** [PROJECT ROOT]
- Voir section `agri-copilot:`
- Dépendances: clickhouse, mongodb, kafka

---

## 🔒 Sécurité en Production

```bash
# 1. Générer clé sécurisée
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Mettre dans .env du projet root
# SECRET_KEY=<generated-key>

# 3. Déployer
docker-compose up -d agri-copilot

# 4. Vérifier
curl -s http://localhost:8000/api/health/full | jq .
```

---

## 📈 Performance Production

Pour ajuster en production:

```env
# .env du projet root
CACHE_TTL_SECONDS=7200         # Cache 2h
CACHE_MAX_SIZE=5000            # Capacité
RATE_LIMIT_REQUESTS_PER_MINUTE=100  # Puissant
LOG_LEVEL=WARNING              # Moins verbose
ENVIRONMENT=production         # Désactiver docs API
```

---

## 🆘 Dépannage

**Connexion ClickHouse échouée?**
```bash
docker exec agri_copilot_pro python3 -c \
  "from src.api.clients import ClickHouseClient; print(ClickHouseClient().health_check())"
```

**Connexion MongoDB échouée?**
```bash
docker exec agri_copilot_pro python3 -c \
  "from src.api.clients import MongoDBClient; print(MongoDBClient().health_check())"
```

**Vérifier les logs?**
```bash
docker-compose logs agri-copilot | grep ERROR
tail -f logs/agri-copilot/logs/audit.log | jq .
```

---

## 🎉 C'est Prêt!

Agri-Copilot Pro est **entièrement intégré** et prêt à :

✅ **Déployer** avec `docker-compose up -d agri-copilot`
✅ **Développer** localement avec `python3 main.py`
✅ **Tester** avec `pytest tests/`
✅ **Monitorer** via `/api/health` et audit logs
✅ **Scaler** en tant que service Docker

---

**Questions?** 👉 Voir [INTEGRATION.md](./INTEGRATION.md)
