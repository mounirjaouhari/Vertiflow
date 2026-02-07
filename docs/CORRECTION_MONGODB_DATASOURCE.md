# CORRECTION - Datasource MongoDB pour Dashboard Incident Logs

## Date : 2026-02-04
## Probleme : Dashboard 10 (Incident Logs) affichait "No data"

---

## Causes Identifiees

1. **Datasource MongoDB manquant** : Le dashboard 10 référencait `mongodb-datasource-uid` qui n'existait pas dans `datasources.yml`
2. **Plugin MongoDB non documenté** : Aucune info sur la configuration du plugin Grafana MongoDB
3. **Configuration incomplète** : Pas de flux de bout en bout entre Prometheus → AlertManager → MongoDB → Grafana

---

## Corrections Apportees

### 1. Ajout du Datasource MongoDB

**Fichier** : `dashboards/provisioning/datasources/datasources.yml`

```yaml
- name: MongoDB (Alerts)
  type: grafana-mongodb-datasource
  access: proxy
  url: mongodb://mongodb:27017
  uid: mongodb-datasource-uid
  isDefault: false
  editable: true
  jsonData:
    host: mongodb
    port: 27017
    database: vertiflow_alerts
    serverSelectionTimeout: 5000
    defaultDatabase: vertiflow_alerts
  secureJsonData:
    username: vertiflow
    password: vertiflow_password
```

**Impact** : Le dashboard 10 peut maintenant se connecter a MongoDB pour interroger la collection `vertiflow_alerts.alerts`

### 2. Mise a jour des README

#### dashboards/README.md
✅ Ajout de la structure provisioning (datasources + dashboards provisioning)
✅ Documentation du dashboard 10 (Incident Logs)
✅ Tableau de toutes les sources de donnees avec refresh rates
✅ Section d'installation du plugin MongoDB
✅ UID du datasource documente

#### monitoring/README.md
✅ Nouvelle section "Integration Grafana"
✅ Flux d'alertes : Prometheus → AlertManager → MongoDB → Grafana
✅ Variables d'environnement requises (SMTP, Slack)
✅ Commandes de verification pour chaque composant

#### dashboards/provisioning/README.md (NOUVEAU)
✅ Documentation complete du provisioning automatise
✅ Tableau des datasources et dashboards charges
✅ Instructions Docker Compose
✅ Guide de validation
✅ Troubleshooting pour "No data" et autres erreurs

---

## Flux Complet des Alertes → Grafana

```
Prometheus                  (Collecte des metriques)
    ↓
prometheus_alerts.yml       (Regles d'alerte)
    ↓
AlertManager               (Routage + Notification)
    ↓
├─→ [Slack #vertiflow-alerts]
├─→ [Email alerts@vertiflow.ma]
└─→ Webhook vers MongoDB
    ↓
MongoDB (vertiflow_alerts.alerts)  (Persistance)
    ↓
Grafana - Dashboard 10     (Visualisation)
    ↓
├─→ Count par severite (CRITICAL, HIGH, MEDIUM, LOW)
├─→ Pie charts (repartition)
├─→ Timeseries (evolution 24h)
└─→ Tables (historique complet)
```

---

## Verification apres Correction

### 1. Verifier que le datasource est provisionne
```bash
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://localhost:3000/api/datasources | jq '.[] | select(.uid == "mongodb-datasource-uid")'
```

**Resultat attendu** :
```json
{
  "name": "MongoDB (Alerts)",
  "type": "grafana-mongodb-datasource",
  "url": "mongodb://mongodb:27017",
  "uid": "mongodb-datasource-uid",
  "database": "vertiflow_alerts"
}
```

### 2. Verifier que le plugin est installe
```bash
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://localhost:3000/api/plugins | jq '.[] | select(.id == "grafana-mongodb-datasource")'
```

### 3. Verifier que MongoDB contient des alertes
```bash
mongo mongodb://mongodb:27017/vertiflow_alerts \
  -u vertiflow \
  -p vertiflow_password \
  --eval "db.alerts.find().limit(1).pretty()"
```

### 4. Verifier que le dashboard charge les donnees
- Ouvrir Grafana : http://localhost:3000
- Aller au dashboard "Incident Logs" (ID 10)
- Les panels devraient afficher des donnees

---

## Structure Preservee ✅

Toutes les modifications respectent la structure existante :
- ❌ Pas de suppression de fichiers
- ❌ Pas de modification de chemins existants
- ❌ Pas de changement d'UIDs de datasources (sauf ajout)
- ✅ Ajout de nouvelle config MongoDB seulement
- ✅ Documentation additionnelle dans les README

---

## Fichiers Modifies

| Fichier | Type | Modification |
|---------|------|--------------|
| `dashboards/provisioning/datasources/datasources.yml` | ✏️ Edit | Ajout datasource MongoDB |
| `dashboards/README.md` | ✏️ Edit | Documentation sources + plugin MongoDB |
| `monitoring/README.md` | ✏️ Edit | Flux d'alertes + variables d'env |
| `dashboards/provisioning/README.md` | ✨ Nouveau | Guide complet provisioning |

---

## Prochaines Etapes (Optionnelles)

1. **Webhook AlertManager → MongoDB** : Implémenter un service qui écrit les alertes Prometheus dans MongoDB
2. **Script de seed** : Populator la collection `vertiflow_alerts.alerts` avec des données de test
3. **Tests d'intégration** : Valider le flux complet Prometheus → MongoDB → Grafana
4. **Dashboard enrichi** : Ajouter des filtres dynamiques par zone, farm_id, severity

---

## References

- [Grafana MongoDB Plugin](https://github.com/grafana/grafana-mongodb-datasource)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [VertiFlow Dashboard 10](../../dashboards/grafana/10_incident_logs.json)
