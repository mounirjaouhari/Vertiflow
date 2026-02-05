# Dashboards - Visualisation

Ce dossier contient les dashboards et visualisations de VertiFlow.

## Structure

```
dashboards/
├── dashboards_powerbi.pbix          # Dashboard Power BI principal
├── dashboards_presentation_v1.pptx  # Presentation v1
├── dashboards_presentation_v2.pptx  # Presentation v2
├── provisioning/                    # Configuration Grafana (datasources & dashboards)
│   ├── datasources/
│   │   └── datasources.yml         # Definition des datasources (ClickHouse, Prometheus, MongoDB)
│   └── dashboards/
│       └── dashboards.yaml         # Provisioning des dashboards Grafana
└── grafana/                         # Dashboards Grafana (JSON)
    ├── 01_operational_cockpit.json  # Operations temps reel (ClickHouse)
    ├── 02_science_lab.json          # Analyses scientifiques (ClickHouse)
    ├── 03_executive_finance.json    # KPIs financiers (ClickHouse)
    ├── 04_system_health.json        # Sante systeme (Prometheus)
    └── 10_incident_logs.json        # Alertes IoT & Incidents (MongoDB)
```

## Dashboards Grafana

### 01 - Operational Cockpit
Dashboard operationnel temps reel :
- Temperature, humidite, CO2 par zone
- Alertes actives
- Status des actuateurs
- Tendances 24h

### 02 - Science Lab
Dashboard scientifique :
- VPD et DLI par rack
- Correlations environnementales
- Historique de croissance
- Predictions ML

### 03 - Executive Finance
KPIs financiers :
- Cout energetique par zone
- Rendement vs objectif
- ROI par cycle
- Projections

### 04 - System Health
Monitoring infrastructure :
- Status des services
- Latences Kafka
- Requetes ClickHouse
- Alertes systeme

### 10 - Incident Logs
Tableau de bord des alertes IoT et incidents :
- Alertes critiques actives
- Repartition par severite, type, module
- Historique complet des alertes
- Parametres hors normes
- Tendances temporelles
- Source : MongoDB (collection `vertiflow_alerts.alerts`)

## Power BI

Le fichier `dashboards_powerbi.pbix` contient :
- Connexion directe a ClickHouse
- Vues materialisees pre-calculees
- Rapports interactifs
- Export PDF automatise

## Import Grafana

```bash
# Import via API
curl -X POST \
  http://localhost:3000/api/dashboards/db \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d @dashboards/grafana/01_operational_cockpit.json
```

## Sources de donnees

| Dashboard | Source | Base de donnees | Refresh |
|-----------|--------|-----------------|----------|
| 01 - Operational | ClickHouse | vertiflow (telemetry_raw) | 5s |
| 02 - Science Lab | ClickHouse | vertiflow (telemetry_enriched) | 1min |
| 03 - Finance | ClickHouse | vertiflow (materialized views) | 1h |
| 04 - System Health | Prometheus | (metriques temps reel) | 15s |
| 10 - Incident Logs | MongoDB | vertiflow_ops (alerts) | 30s |

## Datasources Grafana requises

### ClickHouse
- **Type** : grafana-clickhouse-datasource
- **Host** : clickhouse:8123
- **Database** : vertiflow
- **Default** : true

### Prometheus
- **Type** : prometheus
- **URL** : http://prometheus:9090
- **Default** : false

### MongoDB (Incidents)
- **Type** : grafana-mongodb-datasource
- **URL** : mongodb://mongodb:27017
- **Database** : vertiflow_ops
- **Default Collection** : alerts
- **UID** : mongodb-incidents-uid
- **Plugin necessaire** : grafana-mongodb-datasource (voir installation)

## Installation du plugin MongoDB

```bash
# Installer le plugin Grafana MongoDB
grafana-cli admin plugins install grafana-mongodb-datasource

# Ou via docker (dans docker-compose)
environment:
  GF_INSTALL_PLUGINS: grafana-mongodb-datasource

# Redemarrer Grafana
docker-compose restart grafana
```
