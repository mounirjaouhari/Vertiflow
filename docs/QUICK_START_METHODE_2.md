# 🚀 GUIDE RAPIDE - Methode 2 Opérationnelle

## 📍 Accès Immédiat

### Grafana Dashboard
```
URL: http://localhost:3000/d/vertiflow-alerts-infinity
Credentials: admin / admin
Dashboard Name: "Alertes IoT - REST API (Infinity)"
```

### REST API
```
Base URL: http://localhost:5000
Health: http://localhost:5000/health
```

### Prometheus & Clickhouse (Existing)
```
Prometheus: http://localhost:9090
Clickhouse: http://localhost:8123
```

---

## ✅ Vérifications Rapides

### 1. Vérifier l'API est opérationnelle
```bash
curl http://localhost:5000/health | jq
```

**Résultat attendu**:
```json
{
  "status": "healthy",
  "database": "vertiflow_ops",
  "collection": "alerts",
  "total_documents": 50,
  "timestamp": "2026-02-04T..."
}
```

### 2. Voir les statistiques complètes
```bash
curl http://localhost:5000/api/alerts/stats | jq
```

**Résultat attendu**:
```json
{
  "summary": {
    "total": 50,
    "active": 36,
    "resolved": 14,
    "resolution_rate": 28.0
  },
  "by_severity": {
    "CRITICAL": 14,
    "HIGH": 12,
    "MEDIUM": 12,
    "LOW": 12
  },
  "by_type": {
    "PARAMETER_ISSUE": 50
  }
}
```

### 3. Vérifier les datasources Grafana
```bash
curl -u admin:admin http://localhost:3000/api/datasources | jq '.[] | {name, type, uid}'
```

**Chercher**:
- `"Alerts API (Infinity)"` avec uid `"infinity-alerts-uid"` ✅

### 4. Voir les logs de l'API
```bash
docker compose -f docker-compose.metrics.yml logs alerts-api -f --tail=50
```

### 5. Vérifier tous les services
```bash
docker compose -f docker-compose.metrics.yml ps
```

---

## 🔧 Commandes Essentielles

### Redémarrer les services
```bash
# Redémarrer juste l'API
docker compose -f docker-compose.metrics.yml restart alerts-api

# Redémarrer Grafana
docker compose -f docker-compose.metrics.yml restart grafana

# Redémarrer toute la stack
docker compose -f docker-compose.metrics.yml restart
```

### Reconstruire les images (après modifications)
```bash
docker compose -f docker-compose.metrics.yml up -d --build
```

### Arrêter / Démarrer
```bash
# Arrêter
docker compose -f docker-compose.metrics.yml down

# Démarrer
docker compose -f docker-compose.metrics.yml up -d
```

---

## 📊 Endpoints API Disponibles

| Endpoint | Exemple |
|----------|---------|
| Health | `curl http://localhost:5000/health` |
| Tous les alertes | `curl "http://localhost:5000/api/alerts/all?limit=10"` |
| Alertes actives | `curl "http://localhost:5000/api/alerts/active?limit=50"` |
| Comptage par sévérité | `curl "http://localhost:5000/api/alerts/count-by-severity"` |
| Stats complètes | `curl http://localhost:5000/api/alerts/stats` |
| Timeseries (24h) | `curl "http://localhost:5000/api/alerts/timeseries?hours=24"` |
| Comptage total | `curl http://localhost:5000/api/alerts/count` |

---

## 📈 Paramètres de Requête

```bash
# Pagination
curl "http://localhost:5000/api/alerts/all?page=1&limit=50"

# Filtrer par statut
curl "http://localhost:5000/api/alerts/count-by-severity?resolved=false"

# Timeseries personnalisé
curl "http://localhost:5000/api/alerts/timeseries?hours=48"

# Tri personnalisé
curl "http://localhost:5000/api/alerts/all?sort=timestamp&order=-1&limit=20"
```

---

## 🐛 Dépannage

### Le dashboard affiche "No data"
1. Vérifiez que `/health` répond → `curl http://localhost:5000/health`
2. Vérifiez le datasource dans Grafana: Settings → Data sources → "Alerts API (Infinity)"
3. Vérifiez les logs: `docker compose -f docker-compose.metrics.yml logs grafana -f`

### L'API ne démarre pas
1. Vérifiez MongoDB est UP: `docker ps | grep mongodb`
2. Vérifiez les logs API: `docker compose -f docker-compose.metrics.yml logs alerts-api`
3. Reconnectez MongoDB: `docker compose restart mongodb` puis `docker compose up -d alerts-api`

### Grafana ne se connecte pas à l'API
1. Vérifiez le network Docker: `docker network ls | grep vertiflow`
2. Testez depuis Grafana container: `docker compose exec grafana curl http://alerts-api:5000/health`
3. Vérifiez l'URL dans le datasource: doit être `http://alerts-api:5000` (pas localhost)

---

## 📁 Fichiers Importants

| Fichier | Rôle |
|---------|------|
| `scripts/api/alerts_api.py` | Service API Flask |
| `docker/Dockerfile.alerts_api` | Image Docker API |
| `docker-compose.metrics.yml` | Orchestration services |
| `dashboards/grafana/10_incident_logs_infinity.json` | Dashboard Infinity |
| `dashboards/provisioning/datasources/datasources.yml` | Config datasources |
| `METHODE_2_IMPLEMENTATION.md` | Documentation complète |

---

## 🚀 Prochaines Étapes

### Ajouter plus d'alertes (test)
```bash
docker compose exec mongodb mongosh vertiflow_ops << EOF
db.alerts.insertMany([
  {alert_id: "test_1", severity: "CRITICAL", timestamp: new Date(), resolved: false, ...},
  {alert_id: "test_2", severity: "HIGH", timestamp: new Date(), resolved: false, ...}
])
EOF
```

### Créer un nouvel endpoint API
1. Éditer `scripts/api/alerts_api.py`
2. Ajouter nouvelle fonction `@app.route("/api/alerts/new")`
3. Rebuild: `docker compose up -d --build alerts-api`
4. Tester: `curl http://localhost:5000/api/alerts/new`

### Étendre le dashboard
1. Ouvrir Grafana → Dashboard `vertiflow-alerts-infinity`
2. Ajouter panel → Query → Infinity datasource
3. URL: `/api/alerts/...`
4. Parse: JSON

---

## 📞 Support

**Issues courantes**:
- Vérifier les logs: `docker logs <container_name> -f`
- Redémarrer le service: `docker compose restart <service>`
- Vider le cache Grafana: `rm -rf <grafana-volume>/*` (attention!)

**Documentation**:
- Voir [METHODE_2_IMPLEMENTATION.md](METHODE_2_IMPLEMENTATION.md) pour détails complets
- Voir [dashboards/README.md](dashboards/README.md) pour autres dashboards
- Voir [monitoring/README.md](monitoring/README.md) pour stack monitoring

---

**✅ Status**: OpenSource Solution Ready for Production  
**📅 Last Updated**: 2026-02-04  
**👤 Owner**: VertiFlow Team
