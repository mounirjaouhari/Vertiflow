# Ordre d'exécution complet

Ce guide décrit l'enchaînement recommandé pour démarrer, initialiser et valider la plateforme VertiFlow depuis zéro.

## 1. Préparation de l'environnement
- Installer Docker Desktop (WSL2 activé) et vérifier qu'il est démarré.
- Créer un environnement Python 3.11+ et installer les dépendances :
  ```bash
  python -m venv .venv
  .venv\\Scripts\\activate
  pip install -r requirements.txt
  ```
- Exporter les secrets nécessaires (`.env` ou variables PowerShell) avant de lancer les services.

## 2. Lancement de l'infrastructure conteneurisée
- Depuis `vertiflow-data-platform/` :
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.metrics.yml up -d
  docker compose ps
  ```
- Vérifier que Mosquitto est bien `Up` et exposé (`docker compose ps mosquitto`).

## 3. Initialisation des bases et métadonnées
Exécuter les scripts dans l'ordre suivant avec l'environnement virtuel activé :
```bash
python scripts/init_clickhouse.py
python scripts/init_mongodb.py
python scripts/init_kafka_topics.py
python scripts/generate_data_dictionary.py
```
- Contrôler les logs pour détecter les erreurs de connexion.

## 4. Mise en place du pipeline NiFi
- Alimenter NiFi avec les gabarits et variables :
  ```bash
  python scripts/setup_vertiflow_governance_pipeline.py --env dev
  ```
- Ouvrir l'UI NiFi (https://localhost:9443) puis démarrer les Process Groups créés.
- Reproduire l'opération avec `--env prod` si nécessaire.

## 5. Ingestion des sources de données
- Télécharger/rafraîchir les jeux externes :
  ```bash
  python scripts/download_nasa_power.py
  bash scripts/download_all_sources.sh   # via WSL ou Git Bash
  python datasyn/dat.py
  ```
- Déposer les fichiers requis dans `nifi_exchange/input/` pour déclencher les flux batch.

## 6. Simulateurs et flux temps réel
- S'assurer que Mosquitto (ports 1883/8883/9001) accepte les connexions.
- Lancer les simulateurs dans des terminaux séparés :
  ```bash
  python scripts/simulators/iot_sensor_simulator.py
  python scripts/simulators/lab_data_generator.py
  python scripts/vision_system_simulator.py
  ```
- Confirmer la consommation côté Kafka et ClickHouse via les tableaux de bord ou `docker compose logs` ciblés.

## 7. Observabilité et validation
- Vérifier Prometheus et Grafana :
  - Prometheus : http://localhost:9090
  - Grafana : http://localhost:3000 (importer les dashboards depuis `dashboards/grafana/`).
- Utiliser `scripts/validate_deployment.py` pour un contrôle automatisé :
  ```bash
  python scripts/validate_deployment.py
  ```

## 8. Arrêt contrôlé et maintenance
- Arrêter les simulateurs (Ctrl+C) puis les services :
  ```bash
  docker compose down
  ```
- Sauvegarder les exports NiFi/Grafana si des modifications ont été réalisées.
- Documenter toute anomalie dans `docs/Rapport d'Incident/`.
