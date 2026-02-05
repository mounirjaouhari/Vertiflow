# Provisioning Grafana - Configuration automatisée

Ce dossier contient les configurations automatisées pour Grafana et ses datasources.

## Structure

```
provisioning/
├── datasources/
│   └── datasources.yml          # Definition des sources de donnees
└── dashboards/
    └── dashboards.yaml          # Configuration des dashboards
```

## Datasources (datasources.yml)

### ClickHouse
- **Type** : grafana-clickhouse-datasource
- **Host** : clickhouse:8123
- **Database** : vertiflow
- **Dashboards** : 01, 02, 03, 04 (System Health partiellement)
- **Donnees** : Telemetrie, environnement, nutrition en temps reel

### Prometheus
- **Type** : prometheus
- **URL** : http://prometheus:9090
- **Port** : 9090
- **Dashboards** : 04 (System Health)
- **Donnees** : Metriques infrastructure, Kafka, ClickHouse, NiFi, Docker

### MongoDB (Alerts)
- **Type** : grafana-mongodb-datasource
- **URL** : mongodb://mongodb:27017
- **Database** : vertiflow_alerts
- **UID** : mongodb-datasource-uid
- **Dashboards** : 10 (Incident Logs)
- **Donnees** : Historique des alertes, incidents, anomalies detaillees
- **Collections cles** :
  - `alerts` : Tous les incidents declenchés
  - `incident_history` : Historique temps reel
  - `alert_metadata` : Metadonnees d'alerte

## Dashboards (dashboards.yaml)

Le provisioning automatique charge tous les fichiers JSON du dossier `/dashboards/grafana/` dans Grafana.

```yaml
providers:
  - name: vertiflow-dashboards      # Nom du provider
    type: file                       # Type (fichier)
    disableDeletion: false           # Autorise la suppression
    editable: true                   # Permet la modification
    allowUiUpdates: true             # Autorise les mises a jour depuis l'UI
    options:
      path: /dashboards              # Chemin des fichiers
```

### Dashboards charges

| ID | Nom | Source | Refresh |
|----|-----|--------|---------|
| 01 | Operational Cockpit | ClickHouse | 5s |
| 02 | Science Lab | ClickHouse | 1min |
| 03 | Executive Finance | ClickHouse | 1h |
| 04 | System Health | Prometheus | 15s |
| 10 | Incident Logs | MongoDB | 30s |

## Integration Docker Compose

```yaml
# docker-compose.yml (section grafana)
grafana:
  image: grafana/grafana:latest
  volumes:
    - ./dashboards/provisioning:/etc/grafana/provisioning
    - ./dashboards/grafana:/dashboards
  environment:
    - GF_INSTALL_PLUGINS=grafana-mongodb-datasource
  ports:
    - "3000:3000"
```

## Validation

### Verifier que les datasources sont charges
```bash
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://localhost:3000/api/datasources
```

### Verifier que MongoDB est accessible
```bash
mongo mongodb://mongodb:27017/vertiflow_alerts \
  --username vertiflow \
  --password vertiflow_password \
  --eval "db.alerts.find().limit(1)"
```

### Verifier les dashboards charges
```bash
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://localhost:3000/api/search?type=dash-db
```

## Problemes courants

### Erreur "No data" dans le dashboard 10
**Cause** : Datasource MongoDB pas provisionne
**Solution** : Assurez-vous que :
1. Le plugin `grafana-mongodb-datasource` est installe
2. La collection `vertiflow_alerts.alerts` existe et contient des donnees
3. La connexion MongoDB est valide dans datasources.yml

### Les datasources ne se rechargent pas
**Cause** : Les volumes ne sont pas montes correctement
**Solution** :
```bash
docker-compose down
docker volume prune  # Optionnel
docker-compose -f docker-compose.metrics.yml up -d
```

### Grafana affiche "Failed to get token"
**Cause** : Variable d'environnement GRAFANA_TOKEN manquante
**Solution** :
```bash
export GRAFANA_TOKEN=your_grafana_admin_token
curl -H "Authorization: Bearer $GRAFANA_TOKEN" http://localhost:3000/api/health
```

## Mise a jour des dashboards

Pour ajouter un nouveau dashboard :
1. Creer le fichier JSON dans `dashboards/grafana/`
2. Nommer le fichier avec le pattern `NN_nom_du_dashboard.json`
3. Redemarrer Grafana ou attendre le rechargement automatique

```bash
# Rechargement immediat
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://localhost:3000/api/admin/provisioning/dashboards/reload
```

## References

- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Grafana MongoDB Datasource](https://grafana.com/grafana/plugins/grafana-mongodb-datasource/)
- [ClickHouse Datasource](https://grafana.com/grafana/plugins/grafana-clickhouse-datasource/)
