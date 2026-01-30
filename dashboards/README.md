# Dashboards - Visualisation

Ce dossier contient les dashboards et visualisations de VertiFlow.

## Structure

```
dashboards/
├── dashboards_powerbi.pbix          # Dashboard Power BI principal
├── dashboards_presentation_v1.pptx  # Presentation v1
├── dashboards_presentation_v2.pptx  # Presentation v2
└── grafana/                         # Dashboards Grafana (JSON)
    ├── 01_operational_cockpit.json  # Operations temps reel
    ├── 02_science_lab.json          # Analyses scientifiques
    ├── 03_executive_finance.json    # KPIs financiers
    └── 04_system_health.json        # Sante systeme
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

| Dashboard | Source | Refresh |
|-----------|--------|---------|
| Operational | ClickHouse (live) | 5s |
| Science Lab | ClickHouse (hourly) | 1min |
| Finance | ClickHouse (daily) | 1h |
| System Health | Prometheus | 15s |
