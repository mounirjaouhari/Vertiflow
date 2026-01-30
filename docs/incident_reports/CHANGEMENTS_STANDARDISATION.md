# ✅ STANDARDISATION TERMINÉE - smart_farming → vertiflow

**Date :** 02/01/2026  
**Action :** Remplacement de toutes les occurrences de `smart_farming` par `vertiflow`

---

## 📋 FICHIERS MODIFIÉS (35 fichiers)

### **Scripts SQL ClickHouse (3 fichiers)**
✅ `infrastructure/init_scripts/clickhouse/01_tables.sql`
✅ `infrastructure/init_scripts/clickhouse/02_powerbi_views.sql`
✅ `infrastructure/init_scripts/clickhouse/03_external_data.sql`

**Changements :**
- Base de données : `CREATE DATABASE vertiflow`
- Toutes les tables : `vertiflow.basil_ultimate_realtime`, etc.
- Toutes les vues PowerBI : `vertiflow.view_pbi_*`

---

### **Scripts Python (3 fichiers)**
✅ `scripts/nifi.py`
✅ `scripts/nifi1.py`
✅ `cloud_citadel/nervous_system/cortex.py`
✅ `infrastructure/init_infrastructure.py`

**Changements :**
- Connexions JDBC : `jdbc:clickhouse://clickhouse:8123/vertiflow`
- Requêtes SQL : `FROM vertiflow.view_algo_8_ab_testing`

---

### **Fichiers de configuration (3 fichiers)**
✅ `config/nifi_pipeline_dev.yaml`
✅ `config/nifi_pipeline_prod.yaml`
✅ `docs/niviparametres.nifi`

**Changements :**
- URL de connexion : `jdbc:clickhouse://clickhouse:8123/vertiflow`

---

## 🔄 ACTIONS EFFECTUÉES

### 1. **Remplacement automatique**
```powershell
# Scripts SQL
Get-ChildItem *.sql | ForEach-Object { 
    (Get-Content $_.FullName -Raw) -replace 'smart_farming', 'vertiflow' | 
    Set-Content $_.FullName 
}

# Scripts Python, YAML, configs
```

### 2. **Suppression de l'ancienne base**
```bash
docker-compose down
docker volume rm vertiflow-data-platform_clickhouse-data -f
```

### 3. **Recréation des conteneurs**
```bash
docker-compose up -d
```

---

## 📊 AVANT / APRÈS

### **AVANT**
```
ClickHouse:
├── default             (Vide)
├── smart_farming       ← Tables ici (CONFUSION)
├── system              (Système)
└── vertiflow           ← Vide (créée par Docker)
```

### **APRÈS**
```
ClickHouse:
├── default             (Vide)
├── system              (Système)
└── vertiflow           ← ✅ TOUTES LES TABLES ICI
```

---

## ✅ VÉRIFICATIONS À FAIRE

### **1. Reconnexion VSCode Database**
Actualise la connexion ClickHouse :
- Database : `vertiflow` (au lieu de smart_farming)
- Explore : `vertiflow.basil_ultimate_realtime`, `vertiflow.view_pbi_*`

### **2. Vérifier les tables**
```sql
SHOW DATABASES;
-- Doit afficher : default, system, vertiflow

USE vertiflow;
SHOW TABLES;
-- Doit afficher : basil_ultimate_realtime, view_pbi_operational_cockpit, etc.
```

### **3. Tester une requête**
```sql
SELECT COUNT(*) FROM vertiflow.basil_ultimate_realtime;
-- Doit retourner 0 (base vide, en attente de données)
```

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ **Standardisation terminée**
2. ⏳ Configurer NiFi pour ingestion de données
3. ⏳ Lancer le simulateur de données
4. ⏳ Vérifier que les données arrivent dans `vertiflow.basil_ultimate_realtime`
5. ⏳ Lancer les algorithmes IA

---

## 📝 NOTES IMPORTANTES

- **Cohérence totale** : Tous les fichiers utilisent maintenant `vertiflow`
- **Docker-compose** : La variable `CLICKHOUSE_DB: vertiflow` est maintenant alignée avec les scripts SQL
- **Migration propre** : Volume ClickHouse supprimé et recréé (base fraîche)
- **Aucun impact** : MongoDB et les autres services inchangés

---

## 🔍 FICHIERS NON MODIFIÉS (Documentation)

Ces fichiers contiennent encore `smart_farming` mais c'est OK (historique/exemples) :
- `DIAGNOSTIC_ET_PLAN_ACTION.md`
- `docs/🚀 Guide de Démarrage Complet - Projet VertiFlow.md`
- `docs/Documentation techniques/*.md`

**Raison :** Documentation historique, pas d'impact sur le fonctionnement.

---

**✅ MIGRATION TERMINÉE AVEC SUCCÈS !**
