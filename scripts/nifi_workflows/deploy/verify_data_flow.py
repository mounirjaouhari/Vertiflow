#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - ORCHESTRATEUR MAÎTRE (VERSION FINALE)
================================================================================
Architecture : Full Stack (Infra + NiFi + ML + Sim)
Description  : Lance et surveille TOUS les services sans exception.
================================================================================
"""

import argparse
import logging
import os
import subprocess
import sys
import time
import signal
from pathlib import Path
from typing import Dict

# --- VÉRIFICATION DÉPENDANCES ---
try:
    from clickhouse_driver import Client
    from pymongo import MongoClient
    from kafka import KafkaAdminClient
except ImportError:
    print("❌ Bibliothèques manquantes. pip install kafka-python clickhouse-driver pymongo")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("VertiFlow.Master")

PROJECT_ROOT = Path(__file__).parent.parent
running_processes: Dict[str, subprocess.Popen] = {}

def shutdown_all():
    logger.info("\n🛑 Arrêt global du système VertiFlow...")
    for name, proc in running_processes.items():
        if proc.poll() is None:
            proc.terminate()
    sys.exit(0)

def check_health():
    """Vérifie que les ports Docker sont ouverts avant de lancer les scripts"""
    try:
        # Kafka
        KafkaAdminClient(bootstrap_servers='localhost:9092', request_timeout_ms=2000).list_topics()
        # ClickHouse
        Client(host='localhost', port=9000).execute('SELECT 1')
        # MongoDB
        MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000).admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"❌ Infra non prête : {e}")
        return False

def run_background(script_path, name):
    """Lance un service en arrière-plan et l'enregistre"""
    if not script_path.exists():
        logger.error(f"❌ Script introuvable : {script_path}")
        return
    proc = subprocess.Popen([sys.executable, str(script_path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    running_processes[name] = proc
    logger.info(f"🚀 {name} démarré (PID: {proc.pid})")

def main():
    signal.signal(signal.SIGINT, lambda s, f: shutdown_all())

    if not check_health():
        logger.error("⚠️ Lancez 'docker compose up -d' et attendez l'état HEALTHY.")
        sys.exit(1)

    # 1. INITIALISATION DES TABLES (01_tables.sql via init_infrastructure.py)
    logger.info("Step 1: Initialisation des schémas de données...")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "infrastructure" / "init_infrastructure.py")], check=True)

    # 2. DÉPLOIEMENT NIFI (Les 6 Zones de Gouvernance)
    logger.info("Step 2: Déploiement du pipeline NiFi Master...")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "nifi_workflows" / "deploy" / "deploy_pipeline_v2_full.py")], check=True)

    # 3. ML ENGINE (LE SERVICE MANQUANT)
    # On lance les scripts du cerveau ML (Oracle & Classifier)
    logger.info("Step 3: Activation du ML Engine (Intelligence Artificielle)...")
    ml_dir = PROJECT_ROOT / "cloud_citadel" / "nervous_system"
    run_background(ml_dir / "oracle.py", "ML_Oracle")
    run_background(ml_dir / "classifier.py", "ML_Classifier")

    # 4. SIMULATEUR IOT (Cycle de vie complet)
    logger.info("Step 4: Démarrage du simulateur IoT (Cycle de vie)...")
    run_background(PROJECT_ROOT / "scripts" / "simulators" / "kafka_telemetry_producer.py", "IoT_Simulator")

    logger.info("⭐ SYSTÈME VERTIFLOW OPÉRATIONNEL À 100% ⭐")

    # Surveillance des processus
    try:
        while True:
            for name, proc in list(running_processes.items()):
                if proc.poll() is not None:
                    logger.warning(f"⚠️ {name} s'est arrêté !")
                    del running_processes[name]
            time.sleep(10)
    except KeyboardInterrupt:
        shutdown_all()

if __name__ == "__main__":
    main()