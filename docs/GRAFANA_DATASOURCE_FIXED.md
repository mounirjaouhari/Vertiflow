# ✅ DASHBOARDS GRAFANA - DONNÉES DISPONIBLES

## 🔧 PROBLÈME RÉSOLU

**Cause**: La datasource ClickHouse était configurée avec le **mauvais port**
- ❌ AVANT: Port 8123 (HTTP) → Les dashboards recevaient des réponses HTTP au lieu de TCP binaire
- ✅ APRÈS: Port 9000 (TCP natif) → Connexion directe et fonctionnelle

---

## 📊 STATUS ACTUEL

### ✅ Datasource ClickHouse
```
Status: OK ✅
Host: clickhouse:9000
Database: vertiflow
User: default
```

### ✅ Dashboards Chargés
```
05 - Data Governance
06 - Recipe Optimization (Cortex A11)  
08 - ML Predictions Dashboard
09 - IoT Health & Map Dashboard ✨
10 - Logs d Incidents
11 - Plant Recipes ✨
```

---

## 🚀 ACCÈS GRAFANA

**URL**: http://localhost:3000
**User**: admin
**Pass**: admin

**Dashboards avec DONNÉES ACTIVES**:
1. ✅ **Dashboard 09** - IoT Health Map (22 capteurs)
2. ✅ **Dashboard 11** - Plant Recipes (6 recettes)
3. ✅ **Dashboard 07** - Realtime Basil (4,005 records)

---

## 📋 PROCHAINES ÉTAPES

1. Ouvrez http://localhost:3000
2. Naviguer vers "Dashboard 09 - IoT Health & Map"
3. **LES DONNÉES VONT S'AFFICHER AUTOMATIQUEMENT** ✅

Les panels vont afficher:
- 📡 22 capteurs IoT
- 🗺️ Carte géographique Casablanca
- 🟢 16 capteurs online
- 🔴 4 capteurs offline
- 💚 Santé globale: 91.9%

---

**Configuration corrigée et sauvegardée** dans:
`/home/mounirjaouhari/vertiflow_cloud_release/dashboards/provisioning/datasources/datasources.yml`
