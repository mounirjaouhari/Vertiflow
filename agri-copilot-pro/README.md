# 🌿 Agri-Copilot Pro

**SERVICE INTÉGRÉ - AI Assistant for Vertical Farming with SQL Generation**

Agri-Copilot Pro est un **service intégré** du projet **vertiflow_cloud_release** qui fournit une assistance IA intelligente pour l'analyse de données en agriculture verticale. 

> 🔔 **IMPORTANT**: Cette application est un **SERVICE au sein de vertiflow_cloud_release**, pas une application standalone. Elle n'utilise PAS son propre docker-compose, mais les services existants (ClickHouse, MongoDB, Kafka, etc.).

**📋 Voir [INTEGRATION.md](./INTEGRATION.md) pour les détails d'intégration avec vertiflow_cloud_release**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-darkgreen)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31%2B-red)](https://streamlit.io/)

## 🎯 Caractéristiques

### 🤖 Traitement de Requêtes Alimentées par l'IA
- **Langage Naturel vers SQL**: Convertit automatiquement les requêtes en français, anglais et arabe
- **Intégration Gemini**: Utilise le modèle Gemini de Google pour la génération SQL intelligente
- **Support Multilingue**: FR (Français), EN (English), AR (العربية), KAB (Tamazight)

### 📊 Analyse de Données
- **Intégration BigQuery**: Analyser des ensembles de données agricoles de grande taille
- **Support ClickHouse**: Analyse de données de séries chronologiques pour les lectures de capteurs
- **Analyse en Temps Réel**: Surveiller les systèmes agricoles verticaux en direct

### 🔐 Sécurité & Conformité
- **Contrôle d'Accès Basé sur les Rôles**: Rôles ADMIN, AGRONOME, AGRICULTEUR
- **Protection contre les Injections SQL**: Validation de sécurité multi-couches
- **Journal d'Audit**: Piste d'audit complète pour la conformité
- **Authentification JWT**: Authentification sécurisée par token

### 💾 Mise en Cache Avancée
- **Cache LRU**: Mise en cache efficace des réponses avec TTL
- **Mise en Cache des Résultats de Requête**: Éviter les requêtes de base de données redondantes
- **Statistiques de Cache**: Surveiller les performances en temps réel

### ⏱️ Limitation de Débit
- **Algorithme Token Bucket**: Limitation de débit équitable
- **Limites Par Utilisateur**: Requêtes configurables par minute
- **Recul Intelligent**: Guidance automatique de retry-after

### 📈 Surveillance et Observabilité
- **Vérifications de Santé**: Surveillance des dépendances de service
- **Journalisation Structurée**: Logs au format JSON pour agrégation
- **Piste d'Audit de Sécurité**: Suivi de tous les événements d'authentification et d'autorisation
- **Métriques de Performance**: Suivi du temps d'exécution des requêtes

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.10+
- Accès aux services VertiFlow (ClickHouse, MongoDB, Kafka)
- Credentials Google Cloud (pour Gemini et BigQuery)
- Voir [INTEGRATION.md](./INTEGRATION.md) pour détails

### Installation

1. **Navigation au répertoire agri-copilot-pro**
   ```bash
   cd /path/to/vertiflow_cloud_release/agri-copilot-pro
   ```

2. **Créer l'environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   # Ou utiliser: make install
   ```

4. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec votre configuration
   # IMPORTANT: Pour docker-compose, utiliser les vals par défaut (clickhouse, mongodb, kafka)
   ```

5. **Lancer l'application**

   **UI Streamlit (développement local uniquement):**
   ```bash
   streamlit run app.py
   # Accès: http://localhost:8501
   ```

   **Serveur FastAPI (API):**
   ```bash
   python main.py
   # Ou avec uvicorn:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   # Accès: http://localhost:8000/api/docs
   ```

   **Avec Docker Compose (depuis le projet root):**
   ```bash
   cd /path/to/vertiflow_cloud_release
   docker-compose up -d agri-copilot
   # Accès API: http://localhost:8000
   ```

## 📚 Exemples d'Utilisation

### Via l'Interface Streamlit (Développement Local)
   - "Compare humidity levels between zones"

### Via FastAPI
```bash
# Get authentication token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"password123"}'

# Execute query
curl -X POST http://localhost:8000/api/query/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the average temperature last week",
    "query_type": "natural_language",
    "language": "EN",
    "database": "bigquery"
  }'
```

### Python SDK
```python
from src.services.query import QueryService
from src.models.schemas import QueryRequest, UserModel

service = QueryService()
request = QueryRequest(
    query="What is the average basil yield?",
    language="FR",
    database="bigquery"
)

response = service.execute_query(request, user)
print(response.data)
```

## 🏗️ Architecture

```
agri-copilot-pro/
├── src/
│   ├── api/                 # API utilities
│   │   ├── cache_manager.py # LRU caching system
│   │   ├── rate_limiter.py  # Rate limiting implementation
│   │   └── clients.py       # External API clients
│   ├── core/                # Core functionality
│   │   ├── config.py        # Configuration management
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── logging_config.py# Logging setup
│   │   └── security.py      # Security validation
│   ├── models/              # Data models
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── auth.py          # Authentication
│   │   ├── audit.py         # Audit logging
│   │   └── query.py         # Query processing
│   └── utils/               # Utilities
│       └── validators.py    # Input validation
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── app.py                   # Streamlit UI
├── main.py                  # FastAPI server
├── requirements.txt         # Python dependencies
├── setup.py                 # Package configuration
├── .env.example             # Environment template
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── README.md               # This file
```

## 🔐 Configuration

### Environment Variables

**Essential:**
- `GCP_PROJECT_ID` - Your Google Cloud project ID
- `GEMINI_API_KEY` - Gemini API key
- `SECRET_KEY` - JWT signing secret (min 32 chars)

**Database:**
- `CLICKHOUSE_HOST` - ClickHouse server address
- `BIGQUERY_DATASET` - BigQuery dataset name

**Security:**
- `RATE_LIMIT_REQUESTS_PER_MINUTE` - Default: 60
- `CACHE_TTL_SECONDS` - Default: 3600
- `JWT_EXPIRY_HOURS` - Default: 24

See `.env.example` for complete configuration options.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_auth.py

# Run tests in CI mode
pytest --cov=src --cov-report=xml tests/
```

## 🐳 Docker

### Using Docker Compose
```bash
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker
```bash
# Build image
docker build -t agri-copilot-pro:latest .

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  agri-copilot-pro:latest
```

## 📊 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/register` - Register new user
- `POST /api/auth/refresh` - Refresh access token

### Query Endpoints
- `POST /api/query/execute` - Execute query
- `GET /api/query/history` - Get user's query history

### Admin Endpoints
- `GET /api/admin/audit-report` - View audit logs (AGRONOME+)
- `GET /api/admin/violations` - View security violations (ADMIN)

### Health Endpoints
- `GET /health` - Basic health check
- `GET /api/health/full` - Full service health status

Full API documentation available at `/api/docs` (development mode)

## 🔄 Database Schemas

### BigQuery Tables
- `farming_data.sensor_readings` - Real-time sensor data
- `farming_data.yield_predictions` - ML-generated predictions
- `farming_data.environmental_metrics` - Climate data

### ClickHouse Tables
- `vertiflow.basil_ultimate_realtime` - Live farming metrics
- `vertiflow.quality_predictions` - Product quality scores
- `vertiflow.external_data` - External data sources

### MongoDB Collections
- `live_state` - Current system state
- `plant_recipes` - Farming protocols
- `quality_predictions` - Quality analysis results
- `incident_logs` - Incident tracking

## 🛠️ Development

### Code Style
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Import sorting
isort src/ tests/
```

### Adding New Features

1. Create branch: `git checkout -b feature/your-feature`
2. Implement feature with tests
3. Run test suite: `pytest --cov=src`
4. Submit pull request

### Project Structure Guidelines

- **Services**: Business logic (in `src/services/`)
- **Models**: Data schemas (in `src/models/`)
- **API**: Client integrations (in `src/api/`)
- **Core**: Cross-cutting concerns (in `src/core/`)
- **Utils**: Helper functions (in `src/utils/`)

## 📝 Logging

Logs are written to `logs/` directory in JSON format:
```json
{
  "timestamp": "2024-02-15T10:30:45.123456",
  "level": "INFO",
  "logger": "src.services.query",
  "message": "Query executed successfully",
  "execution_time_ms": 152.5,
  "user_id": "user123"
}
```

Audit logs track all security-sensitive events in `logs/audit.log`

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙋 Support

- **Documentation**: [Full docs](https://agri-copilot-pro.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/vertiflow/agri-copilot-pro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vertiflow/agri-copilot-pro/discussions)
- **Email**: support@vertiflow.io

## 🎓 Training & Resources

- [Vertical Farming Basics](docs/training/vertical-farming-101.md)
- [SQL Query Examples](docs/examples/sql-examples.md)
- [API Integration Guide](docs/guides/api-integration.md)
- [Troubleshooting](docs/troubleshooting.md)

## 📈 Roadmap

- [ ] Real-time data streaming support
- [ ] Advanced ML models for yield prediction
- [ ] Multi-farm management dashboard
- [ ] Mobile app (iOS/Android)
- [ ] GraphQL API support
- [ ] Advanced visualization with Plotly
- [ ] Webhook integrations
- [ ] Custom report generation

## 🔮 Vision

Agri-Copilot Pro empowers vertical farming operations with AI-driven insights, making advanced data analytics accessible to everyone in agriculture through conversational AI.

---

**Made with ❤️ for the future of vertical farming**

VertiFlow © 2024 | All rights reserved
