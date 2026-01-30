# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                   VERTIFLOW™ DATA PLATFORM — DOCKERFILE                  ║
# ║                         Path: ./Dockerfile (Root)                        ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║ Date            : 2026-01-17                                             ║
# ║ Version         : 1.0.0 (Production Release)                             ║
# ║ Ticket          : TICKET-132 (Container Runtime Image)                   ║
# ║ Squad           : Core Platform Operations                               ║
# ║ Owner           : @Imrane (DevOps)                                       ║
# ║ Reviewers       : @Mounir (ML), @Mouhammed (Data)                        ║
# ║ Classification  : Internal - Confidential                                ║
# ║ Purpose         : Provide a reproducible runtime image for VertiFlow.    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# 1. IMAGE DE BASE
# Utilisation de Python 3.11 version "slim" pour réduire la taille et la surface d'attaque.
FROM python:3.11-slim AS base

# 2. VARIABLES D'ENVIRONNEMENT GLOBALES
# - APP_HOME : Dossier d'installation
# - PYTHONUNBUFFERED : Force les logs en temps réel (CRITIQUE pour le débogage Cloud)
# - PIP_NO_CACHE_DIR : Optimisation de l'espace disque
ENV APP_HOME=/opt/vertiflow \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VERTIFLOW_ENV=production

# Définition du répertoire de travail
WORKDIR ${APP_HOME}

# 3. DÉPENDANCES SYSTÈME (OS)
# Installation des librairies nécessaires pour compiler Kafka, ClickHouse driver, etc.
# Nettoyage automatique des caches apt pour alléger l'image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        curl \
        git \
        libssl-dev \
        libffi-dev \
        liblz4-dev \
        libsnappy-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 4. DÉPENDANCES PYTHON
# On copie d'abord le requirements.txt seul pour profiter du cache Docker.
COPY requirements.txt ${APP_HOME}/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# 5. COPIE DU CODE SOURCE
# Copie de l'intégralité du projet (scripts, cloud_citadel, infrastructure...)
COPY . ${APP_HOME}

# 6. PERMISSIONS & SÉCURITÉ
# CRUCIAL : On rend le script d'orchestration exécutable.
RUN chmod +x ${APP_HOME}/scripts/start_vertiflow.py

# Création d'un utilisateur non-root 'vertiflow' pour la sécurité.
RUN useradd --create-home --shell /bin/bash vertiflow \
    && chown -R vertiflow:vertiflow ${APP_HOME}

# Bascule sur l'utilisateur sécurisé
USER vertiflow

# Configuration du PYTHONPATH pour que les imports inter-dossiers fonctionnent
ENV PYTHONPATH=${APP_HOME}

# 7. COMMANDE DE DÉMARRAGE (L'ORCHESTRATEUR)
# Lance le script principal avec les options spécifiques au Cloud :
# --skip-docker-check : Car le conteneur ne peut pas voir le Docker de l'hôte.
# --with-ml : Active Oracle (A9), Classifier (A10) et Cortex (A11).
CMD ["python", "scripts/start_vertiflow.py", "--skip-docker-check", "--with-ml"]

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ END OF FILE — VertiFlow Dockerfile. Validated by @Imrane & @Mounir.      ║
# ╚══════════════════════════════════════════════════════════════════════════╝