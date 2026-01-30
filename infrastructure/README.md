# Infrastructure - Scripts d'infrastructure

Ce dossier contient les scripts d'initialisation de l'infrastructure VertiFlow.

## Structure

```
infrastructure/
├── __init__.py
├── init_infrastructure.py           # Script principal d'initialisation
└── init_scripts/                    # Scripts par technologie
    ├── clickhouse/                  # Scripts SQL ClickHouse
    │   ├── 01_tables.sql            # Creation des tables
    │   ├── 02_powerbi_views.sql     # Vues materialisees
    │   └── 03_external_data.sql     # Tables donnees externes
    └── mongodb/                     # Scripts MongoDB
        ├── plant_recipes.js         # Recettes de culture
        └── seed_data.js             # Donnees initiales
```

## Scripts ClickHouse

### 01_tables.sql
Creation des tables principales :
- `sensor_telemetry` - Donnees capteurs (156 colonnes)
- `hourly_aggregates` - Agregations horaires
- `daily_aggregates` - Agregations journalieres
- `alerts` - Table des alertes

### 02_powerbi_views.sql
Vues materialisees pour Power BI :
- `mv_operational_kpis` - KPIs operationnels
- `mv_zone_summary` - Resume par zone
- `mv_energy_costs` - Couts energetiques

### 03_external_data.sql
Tables pour donnees externes :
- `external_weather` - Donnees meteo
- `external_energy` - Donnees energie
- `reference_crops` - Parametres cultures

## Scripts MongoDB

### plant_recipes.js
35 recettes de culture :
- Parametres optimaux (EC, pH, DLI)
- Durees de cycle
- Alertes et seuils

### seed_data.js
Donnees initiales :
- Configuration systeme
- Utilisateurs par defaut
- Parametres globaux

## Utilisation

### Execution complete
```bash
python infrastructure/init_infrastructure.py
```

### Execution par etape
```bash
# ClickHouse uniquement
python scripts/init/init_clickhouse.py

# MongoDB uniquement
python scripts/init/init_mongodb.py
```

### Verification
```bash
# Verifier les tables
clickhouse-client -q "SHOW TABLES IN vertiflow"

# Verifier MongoDB
mongosh --eval "db.plant_recipes.countDocuments()"
```
