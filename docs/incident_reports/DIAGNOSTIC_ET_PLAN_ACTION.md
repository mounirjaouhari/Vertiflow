# 🔍 DIAGNOSTIC COMPLET - VERTIFLOW DATA PLATFORM
**Date d'analyse :** 01/01/2026  
**Analyste :** GitHub Copilot  
**État global du projet :** ⚠️ **EN CONSTRUCTION** (Infrastructure OK, Pipelines Partiels)

---

## 📊 VUE GÉNÉRALE DU PROJET

### Qu'est-ce que VertiFlow ?
**VertiFlow** est une **plateforme de données industrielle** pour l'**agriculture verticale intelligente**. Elle :
- ✅ Ingère **millions de télémétries** de capteurs IoT (température, humidité, nutriments, etc.)
- ✅ Valide les données avec un protocole **Zero-Trust** (schémas JSON strictes)
- ✅ Stocke dans une architecture **hybride** (ClickHouse + MongoDB)
- ✅ Exécute des **modèles ML** en temps réel (prédictions de récolte, optimisations)
- ✅ Expose des **dashboards** (Grafana) et des **APIs**

### Architecture globale
```
Capteurs IoT (MQTT) 
    ↓
Eclipse Mosquitto (MQTT Broker)
    ↓
Apache NiFi (Ingestion & ETL)
    ↓
Apache Kafka (Event Streaming)
    ↓
Cloud Citadel (Python AI Engine)
    ↓
ClickHouse (Telemetry - OLAP) + MongoDB (Configs - Document)
    ↓
Grafana (Dashboards) + APIs (Queries)
```

---

## ✅ CE QUI FONCTIONNE

### Infrastructure Docker (100% prêt)
| Service | Port | Statut | Vérification |
|---------|------|--------|-------------|
| **Zookeeper** | 2181 | ✅ Prêt | `docker ps` |
| **Kafka** | 9092/29092 | ✅ Prêt | Port 9092 accessible |
| **ClickHouse** | 9000/8123 | ✅ Prêt | Base `vertiflow` créée |
| **MongoDB** | 27017 | ✅ Prêt | Base `vertiflow_ops` créée |
| **Mosquitto (MQTT)** | 1883/9001 | ✅ Prêt | Broker actif |
| **NiFi** | 8443 | ✅ Prêt | HTTPS actif (admin/ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB) |
| **Prometheus** | 9090 | ✅ Prêt | Métriques collectées |
| **Grafana** | 3000 | ✅ Prêt | admin/admin |

**Démarrage :** `docker-compose up -d` (+ `docker-compose.metrics.yml` pour monitoring)

### Scripts de Configuration (Partiels)
```
📁 infrastructure/init_scripts/
├── clickhouse/01_tables.sql          ✅ Créé (153 colonnes telemetry_raw)
├── clickhouse/02_powerbi_views.sql   ✅ Créé (Vues d'agrégation)
├── clickhouse/03_external_data.sql   ✅ Créé (NASA Power, OpenAg)
└── mongodb/seed_data.js              ✅ Créé (Collections + Indices)
```

### Python Core (Cloud Citadel)
```
📁 cloud_citadel/
├── nervous_system/
│   ├── oracle.py                 ✅ Prédictions LSTM (modèle dummy)
│   ├── classifier.py             ✅ Classification anomalies
│   ├── cortex.py                 ✅ Orchestration IA
│   ├── simulator.py              ✅ Simulation de données
│   └── calibration/agronomic_parameters.yaml  ✅ Config métier
└── connectors/
    ├── stream_processor.py       ✅ Consumer Kafka
    └── feedback_loop.py          ✅ Boucle feedback
```

---

## ❌ CE QUI MANQUE OU EST INCOMPLET

### 1. **Pipelines NiFi non configurés**
**Problème :** NiFi tourne mais **aucun flow de données n'est établi**

**État actuel :**
- NiFi accessible à `https://localhost:8443` (admin/ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB)
- ❌ Pas de processeur MQTT → NiFi
- ❌ Pas de route vers Kafka
- ❌ Pas de validateurs de schéma JSON
- ❌ Pas de Dead Letter Queue (DLQ) configurée

**Impact :** Zéro donnée ne circule du capteur à la base de données

---

### 2. **Sources de données (test/simulation) manquantes**
**Problème :** Les algorithmes IA n'ont pas de données à traiter

**État actuel :**
- Scripts Python existent mais dépendent de données en provenance de Kafka
- Données externes (NASA Power, OpenAg) non intégrées dans l'ingestion
- Pas de générateur de données de test (simulator.py existe mais non lancé)

**Fichiers concernés :**
- `scripts/download_nasa_power.py` - Télécharge NASA Power → fichier local (pas d'intégration)
- `scripts/vision_system_simulator.py` - Génère données fictives (pas lancé en boucle)
- `cloud_citadel/nervous_system/simulator.py` - Simulation IA (prêt, pas lancé)

---

### 3. **Modèles ML incomplets**
**Problème :** Modèles IA refèrent à des fichiers `.h5` qui n'existent pas

**État actuel :**
- `oracle.py` cherche `models/lstm_harvest_v1.h5` → **INTROUVABLE**
- Fallback sur modèle dummy (fonctionne mais pas production-ready)
- Pas de dossier `models/` tracké en Git

**Impacte :** Prédictions de récolte = aléatoire (modèle dummy)

---

### 4. **Connectivité Kafka incomplète**
**Problème :** Kafka est prêt, mais aucun producteur ne publie de données

**État actuel :**
- Kafka en écoute sur `kafka:29092` (interne Docker) et `localhost:9092` (externe)
- Topics à créer : `basil_telemetry_full`, `vertiflow.predictions`, etc.
- ❌ NiFi ne publie rien (pas de flow configuré)
- ❌ Pas de script producteur de test

---

### 5. **Bases de données prêtes mais vides**
**État actuel :**
- ✅ ClickHouse : Schéma créé (`smart_farming.basil_ultimate_realtime` - 153 colonnes)
- ✅ MongoDB : Collections créées (`live_state`, `incident_logs`, etc.) avec validateurs
- ❌ **ZÉRO DONNÉES INSÉRÉES**

**Pourquoi :** Pas de source de données entrante (voir point 2)

---

## 🎯 PLAN D'ACTION EXACT (À FAIRE)

### **PHASE 1 : Vérifier que Docker tourne (5 min)**
```bash
cd d:\vertiflow-data-platform\vertiflow-data-platform
docker-compose up -d
docker ps
# Vérifier que 7 services sont "Up"
```

### **PHASE 2 : Configurer NiFi (30 min)**
**Objectif :** Établir le flux MQTT → NiFi → Kafka → ClickHouse

1. Accéder à NiFi : `https://localhost:8443`
2. Login : `admin` / `ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB`
3. Créer les processeurs :
   - **ConsumeMQTT** : Écoute `mosquitto:1883`, topic `#` (tous)
   - **ValidateRecord** : Valide contre schéma JSON (dossier `/docs/schemas`)
   - **PutKafka** : Publie vers topic `basil_telemetry_full`
   - **RoutOnAttribute** : Rejette les invalides vers DLQ
4. Connecter les processeurs en séquence
5. Activer le flow

**Ressource :** Scripts existants
- `scripts/setup_nifi_pipeline_v2.py` - À adapter/utiliser

---

### **PHASE 3 : Lancer un générateur de données (15 min)**
**Objectif :** Alimenter MQTT avec des télémétries de test

**Option A (Recommandé - Simulation Python) :**
```bash
python cloud_citadel/nervous_system/simulator.py
# Génère des messages MQTT + Kafka en boucle
```

**Option B (Script existant) :**
```bash
python scripts/vision_system_simulator.py
```

**Vérification :** Voir les données arriver dans ClickHouse
```sql
SELECT COUNT(*) FROM smart_farming.basil_ultimate_realtime;
```

---

### **PHASE 4 : Valider les bases de données (10 min)**
**Via VSCode (DBCode extension) :**

1. **ClickHouse :**
   - Connexion : Host `localhost`, Port `8123`
   - Test query : `SELECT 1; SHOW TABLES;`
   - Vérifier : Table `basil_ultimate_realtime` avec ~153 colonnes

2. **MongoDB :**
   - Connexion : `mongodb://localhost:27017/vertiflow_ops`
   - Vérifier : Collections `live_state`, `incident_logs`
   - Insérer test : `db.live_state.insertOne({...})`

---

### **PHASE 5 : Lancer les algorithmes IA (15 min)**
**Objectif :** Alimenter les prédictions

```bash
# Terminal 1 : Oracle (Prédictions de récolte)
python cloud_citadel/nervous_system/oracle.py

# Terminal 2 : Classifier (Détection d'anomalies)
python cloud_citadel/nervous_system/classifier.py

# Terminal 3 : Cortex (Orchestration)
python cloud_citadel/nervous_system/cortex.py
```

---

### **PHASE 6 : Vérifier les dashboards (5 min)**
1. **Grafana** : `http://localhost:3000` (admin/admin)
   - Vérifier les métriques Prometheus
   - Créer des panels sur les données ClickHouse

2. **ClickHouse HTTP UI** : `http://localhost:8123`
   - Requête de vérification : `SELECT COUNT(*) FROM smart_farming.basil_ultimate_realtime;`

---

## 🔧 VÉRIFICATIONS RAPIDES (À FAIRE MAINTENANT)

### Vérifier Docker
```powershell
# Terminal
docker ps
docker logs kafka
docker logs clickhouse
docker logs mongodb
```

### Vérifier ClickHouse
```powershell
# Via terminal ou DBCode
curl http://localhost:8123/?query=SELECT%201
# Doit retourner : 1
```

### Vérifier MongoDB
```powershell
mongosh mongodb://localhost:27017
use vertiflow_ops
db.live_state.find().limit(1)
```

### Vérifier Kafka
```powershell
docker exec kafka kafka-topics --bootstrap-server kafka:29092 --list
# Doit lister les topics (ou être vide si aucun créé)
```

---

## 📋 CHECKLIST POUR SUIVRE

- [ ] Docker tourne (7 services)
- [ ] Accès ClickHouse (8123 ou 9000)
- [ ] Accès MongoDB (27017)
- [ ] Accès NiFi (8443)
- [ ] DBCode connecté aux 2 bases
- [ ] Simulateur de données lancé
- [ ] Données dans ClickHouse (COUNT > 0)
- [ ] Données dans MongoDB (live_state > 0)
- [ ] Algorithmes IA lancés (Oracle, Classifier, Cortex)
- [ ] Grafana affiche des métriques

---

## 📞 QUESTIONS FRÉQUENTES

**Q: Pourquoi aucune donnée n'arrive ?**  
A: NiFi n'a pas de flow configuré. Phase 2 obligatoire.

**Q: Le modèle LSTM ne fonctionne pas ?**  
A: Le fichier `models/lstm_harvest_v1.h5` est manquant. Trainer ou utiliser le modèle dummy (acceptable en dev).

**Q: Comment intégrer les données NASA Power ?**  
A: `scripts/download_nasa_power.py` télécharge localement. À intégrer dans NiFi ou le simulateur.

**Q: Comment voir ce qui se passe en temps réel ?**  
A: VSCode + DBCode Explorer pour inspecter les tables, ou Kafka UI (à installer si besoin).

---

**🎯 PROCHAINE ÉTAPE :** Vérifier Docker, puis je te guide pour configurer NiFi.
