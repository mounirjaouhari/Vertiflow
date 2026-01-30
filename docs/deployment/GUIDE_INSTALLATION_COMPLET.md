================================================================================
GUIDE D'INSTALLATION COMPLET - VERTIFLOW DATA PLATFORM
================================================================================
Date de création : 2026-01-04
Version          : 1.0.0
Auteur           : @Imrane (DevOps Lead)
Relecteurs       : @Mounir (ML), @Mouhammed (Data)
Ticket associé   : TICKET-133 - Documentation Installation
Classification   : Interne - Confidentiel
================================================================================

# 🧭 Table des matières
- [GUIDE D'INSTALLATION COMPLET - VERTIFLOW DATA PLATFORM](#guide-dinstallation-complet---vertiflow-data-platform)
- [Classification   : Interne - Confidentiel](#classification----interne---confidentiel)
- [🧭 Table des matières](#-table-des-matières)
  - [Objectif du document](#objectif-du-document)
  - [Vue d'ensemble de la plateforme](#vue-densemble-de-la-plateforme)
  - [Prérequis matériels et logiciels](#prérequis-matériels-et-logiciels)
    - [Matériel minimal (développement)](#matériel-minimal-développement)
    - [Logiciel obligatoire](#logiciel-obligatoire)
  - [Préparation de l'environnement](#préparation-de-lenvironnement)
  - [Clonage et configuration du dépôt](#clonage-et-configuration-du-dépôt)
  - [Configuration des variables d'environnement](#configuration-des-variables-denvironnement)
  - [Initialisation des dépendances Docker](#initialisation-des-dépendances-docker)
  - [Lancement de la stack VertiFlow](#lancement-de-la-stack-vertiflow)
    - [Mode complet (services + observabilité)](#mode-complet-services--observabilité)
    - [Cible minimale (développement rapide)](#cible-minimale-développement-rapide)
  - [Initialisation des bases de données](#initialisation-des-bases-de-données)
  - [Validation fonctionnelle](#validation-fonctionnelle)
  - [Surveillance et observabilité](#surveillance-et-observabilité)
  - [Promotion vers Staging / Production](#promotion-vers-staging--production)
  - [Dépannage rapide](#dépannage-rapide)
  - [Annexes](#annexes)
- [FIN DU DOCUMENT - Guide d'installation complet VertiFlow (TICKET-133). Pour toute mise à jour, contacter @Imrane / DevOps Guild.](#fin-du-document---guide-dinstallation-complet-vertiflow-ticket-133-pour-toute-mise-à-jour-contacter-imrane--devops-guild)

---

## Objectif du document
Ce guide décrit étape par étape comment installer et vérifier VertiFlow sur :
- Une station de développement locale (Windows 11 + WSL2, macOS, Linux).
- Un serveur d'intégration (VM Cloud ou bare-metal) en mode staging / production.

Le document complète `README.md` (vision produit) et `DEPLOYMENT_GUIDE.md` (runbook avancé) en fournissant un parcours opiniâtre depuis un poste vierge jusqu'à une stack opérationnelle.

---

## Vue d'ensemble de la plateforme
Architectures clés :
- **Ingestion** : Mosquitto → NiFi → Kafka.
- **Stockage** : ClickHouse (télémetrie), MongoDB (recettes), Redis (cache optionnel).
- **Intelligence** : Services Python (Oracle, Cortex, Simulateur) déployés via Docker.
- **Observabilité** : Prometheus, Loki, Grafana (via `docker-compose.metrics.yml`).
- **Automatisation** : Workflows GitHub Actions (CI, Docker build, Deploy).

Chaque service utilise une configuration déclarative versionnée (YAML/JSON) et des secrets injectés via `.env`.

---

## Prérequis matériels et logiciels
### Matériel minimal (développement)
- CPU 4 cœurs, 16 Go RAM, 80 Go SSD.
- Connexion Internet stable (>25 Mbps) pour l'image NiFi.

### Logiciel obligatoire
| Outil | Version recommandée | Vérification |
|-------|---------------------|--------------|
| Git | ≥ 2.40 | `git --version` |
| Python | 3.11.x | `python --version` |
| Docker Engine | ≥ 24.0 | `docker version` |
| Docker Compose | plugin v2 | `docker compose version` |
| Make (optionnel Windows via WSL) | ≥ 4.3 | `make --version` |

**Windows** : activer WSL2 + Ubuntu 22.04, installer Docker Desktop (WSL backend) et VS Code.

---

## Préparation de l'environnement
1. Créer un utilisateur système disposant des droits Docker.
2. Mettre à jour l'OS (`sudo apt update && sudo apt upgrade -y`).
3. Vérifier l'espace disque (`df -h`) et libérer ≥ 30 Go.
4. Configurer un pare-feu autorisant les ports listés dans `DEPLOYMENT_GUIDE.md` (1883, 8443, 9000, 9092, etc.).

---

## Clonage et configuration du dépôt
```bash
# 1. Cloner le monorepo
git clone https://github.com/J-Mounir/test-projet-agri.git
cd test-projet-agri/vertiflow-data-platform

# 2. Vérifier l'intégrité
git status
ls -1
```
Pour les contributeurs internes, configurer l'origine SSH (`git remote set-url origin git@github.com:...`).

---

## Configuration des variables d'environnement
1. Copier le modèle : `cp .env.example .env`.
2. Remplir les sections critiques :
   - `CLICKHOUSE_PASSWORD`: mot de passe fort.
   - `MONGODB_USER/MONGODB_PASSWORD`: compte applicatif.
   - `NIFI_PASSWORD`: générer via `openssl rand -base64 24`.
   - `NASA_POWER_API_KEY`, `OPENWEATHER_API_KEY`, etc.
3. Versionner uniquement `.env.example`. Le `.env` réel reste local ou stocké dans le gestionnaire de secrets (Vault, GitHub Environments).

> **Astuce** : utiliser `scripts/validate_env.py` (si disponible) ou `grep -nE "=\s*$" .env` pour détecter les variables vides.

---

## Initialisation des dépendances Docker
1. Télécharger les images critiques à l'avance :
   ```bash
   docker pull clickhouse/clickhouse-server:23.8
   docker pull mongo:7.0
   docker pull apache/nifi:1.23.2
   ```
2. Construire l'image VertiFlow (services Python) :
   ```bash
   docker build -t ghcr.io/j-mounir/test-projet-agri:dev .
   ```
3. Vérifier les images locales : `docker images | grep vertiflow`.

---

## Lancement de la stack VertiFlow
### Mode complet (services + observabilité)
```bash
# Lancer l'infra principale
docker compose up -d

# Ajouter la stack monitoring (Prometheus/Grafana)
docker compose -f docker-compose.metrics.yml up -d

# Suivre l'état
docker compose ps
```
### Cible minimale (développement rapide)
```bash
docker compose up -d clickhouse mongodb kafka mosquitto
```

---

## Initialisation des bases de données
1. **ClickHouse** :
   ```bash
   docker compose exec -T clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS vertiflow"
   python scripts/init_scripts/init_clickhouse.py  # si fourni
   ```
2. **MongoDB** :
   ```bash
   docker compose exec -T mongodb mongosh /docker-entrypoint-initdb.d/bootstrap.js
   ```
3. **Kafka Topics** :
   ```bash
   python scripts/setup_vertiflow_governance_pipeline.py --create-topics
   ```
4. **NiFi** : importer `docs/niviparametres.nifi` via l'interface (https://localhost:8443) avec les identifiants `.env`.

---

## Validation fonctionnelle
1. Exécuter le validateur :
   ```bash
   python scripts/validate_deployment.py
   ```
2. Lancer les tests unitaires :
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt pytest
   pytest --maxfail=1 --disable-warnings
   ```
3. Vérifier les endpoints :
   - ClickHouse UI : http://localhost:8123/?user=default.
   - NiFi : https://localhost:8443/nifi.
   - Grafana : http://localhost:3000 (admin/admin par défaut, à changer).

---

## Surveillance et observabilité
1. Accéder à Grafana (port 3000) et importer les dashboards `dashboards/grafana/*.json`.
2. Prometheus (9090) doit référencer `config/prometheus.yml` monté via docker-compose.
3. Ajouter des alertes basiques (CPU, latence pipeline) via Alertmanager ou Grafana Alerting.
4. Consulter les logs applicatifs :
   ```bash
   docker compose logs -f kafka
   docker compose logs -f cloud-citadel-api  # exemple de microservice
   ```

---

## Promotion vers Staging / Production
1. **Images** : lancer le workflow GitHub `VertiFlow Docker Build` ou exécuter `make docker-push` (si Makefile configuré).
2. **CI/CD** :
   - `VertiFlow CI` (tests) → `VertiFlow Docker Build` (images) → `VertiFlow Deploy` (bastion SSH).
   - S'assurer que les secrets GitHub (`DEPLOY_HOST`, `DEPLOY_USER`, etc.) sont renseignés.
3. **Serveur distant** : mettre à jour `/etc/docker/daemon.json` (miroirs, proxy) et tester `docker compose pull` avant chaque release.

---

## Dépannage rapide
| Problème | Symptômes | Résolution |
|----------|-----------|------------|
| NiFi inaccessible | Timeout 8443 | Vérifier certificat auto-signé, variable `NIFI_WEB_HTTPS_HOST`, volume `nifi-conf`. |
| Kafka refuse connexions | `Connection refused kafka:29092` | Vérifier `KAFKA_ADVERTISED_LISTENERS`, redémarrer zookeeper+kafka, purger volumes. |
| ClickHouse insert échoue | `Code: 60` | Créer table `telemetry_enriched` via scripts init, vérifier permissions. |
| Docker build échoue | `pip install` timeout | Utiliser mirroirs PyPI (`PIP_INDEX_URL`), augmenter cache Docker. |
| Tests KO | `clickhouse_driver` introuvable | Vérifier `requirements.txt`, recréer venv, exécuter `pip install -r requirements.txt`. |

---

## Annexes
- **A. Ports réservés** : détaillés dans `DEPLOYMENT_GUIDE.md` section 1.3.
- **B. Secrets recommandés** : stocker dans Vault / GitHub environments (DEV, STG, PRD).
- **C. Référence workflows** : `.github/workflows/ci.yml`, `deploy.yml`, `docker-build.yml`.
- **D. Checklist Go-Live** :
  1. Dashboards importés.
  2. Backups ClickHouse/Mongo configurés.
  3. Alertes critiques actives.
  4. Tests E2E passés.
  5. Documentation signée par PO.

---

Restez alignés avec les tickets en vigueur (Jira / Notion). Toute modification majeure doit citer le ticket correspondant dans les PRs.

================================================================================
FIN DU DOCUMENT - Guide d'installation complet VertiFlow (TICKET-133). Pour toute mise à jour, contacter @Imrane / DevOps Guild.
================================================================================
