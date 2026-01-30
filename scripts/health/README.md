# Health - Verification de sante

Ce dossier contient les scripts de verification de sante de l'infrastructure VertiFlow.

## Structure

```
health/
└── health_check.py                  # Verification de tous les services
```

## Scripts

### health_check.py
Verification de l'etat de tous les services de la plateforme :
- ClickHouse (connexion, tables)
- Kafka (brokers, topics)
- MongoDB (connexion, collections)
- NiFi (API, processeurs)
- Mosquitto (broker MQTT)

```bash
python scripts/health/health_check.py
```

## Sortie

```
[OK] ClickHouse: Connected (5 tables)
[OK] Kafka: 3 brokers, 5 topics
[OK] MongoDB: Connected (3 collections)
[OK] NiFi: Running (12 processors)
[OK] MQTT: Broker accessible
```

## Codes de retour

| Code | Signification |
|------|---------------|
| 0 | Tous les services OK |
| 1 | Un ou plusieurs services en erreur |
| 2 | Erreur de configuration |
