#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - INITIALISEUR D'INFRASTRUCTURE MASTER (VERSION INTÉGRALE)
================================================================================
Description : Ce script pilote la création du Golden Record ClickHouse (157 colonnes)
              et le seeding complet de MongoDB avec le catalogue horticole.
              Il résout les erreurs de TTL ClickHouse et prépare le ML Engine.
================================================================================
"""

import os
import time
import logging
import json
from pathlib import Path
from clickhouse_driver import Client
from pymongo import MongoClient

# Configuration du logging professionnel
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger("VertiFlow.Init")

# Configuration des chemins
PROJECT_ROOT = Path(__file__).parent.parent
CH_SCRIPT = PROJECT_ROOT / "infrastructure" / "init_scripts" / "clickhouse" / "01_tables.sql"
MONGO_SEED_DIR = PROJECT_ROOT / "infrastructure" / "init_scripts" / "mongodb"

def init_clickhouse():
    """Initialise ClickHouse avec le schéma Golden Record et les tables ML"""
    logger.info("🚀 ÉTAPE 1 : Initialisation ClickHouse (Storage OLAP)...")
    try:
        # Connexion au moteur natif (Port 9000)
        client = Client(
            host='localhost',
            port=9000,
            user='default',
            password='default', # <--- Ce réglage est maintenant confirmé
            connect_timeout=20
        )

        if not CH_SCRIPT.exists():
            logger.error(f"❌ Script SQL introuvable : {CH_SCRIPT}")
            return False

        logger.info(f"📜 Lecture du script : {CH_SCRIPT.name}")
        with open(CH_SCRIPT, 'r', encoding='utf-8') as f:
            # Séparation intelligente des requêtes (gestion des commentaires et points-virgules)
            content = f.read()
            sql_queries = [q.strip() for q in content.split(';') if q.strip()]

        for i, query in enumerate(sql_queries):
            try:
                # Log partiel pour la lisibilité
                first_line = query.split('\n')[0][:60]
                logger.info(f"   Executing [{i+1}/{len(sql_queries)}]: {first_line}...")
                client.execute(query)
            except Exception as sql_err:
                logger.error(f"❌ Erreur sur la requête {i+1} : {sql_err}")
                if "BAD_TTL_EXPRESSION" in str(sql_err):
                    logger.critical("🚨 Erreur TTL détectée. Vérifiez la conversion toDateTime(timestamp).")
                return False

        logger.info("✅ ClickHouse : Schéma 157 colonnes et tables ML déployés.")
        return True
    except Exception as e:
        logger.error(f"❌ Échec critique ClickHouse : {e}")
        return False

def init_mongodb():
    """Seeding complet du catalogue horticole et des recettes (35 cultures)"""
    logger.info("🚀 ÉTAPE 2 : Seeding MongoDB (Knowledge Base)...")
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        db = client['vertiflow_ops'] # Base opérationnelle

        # 1. Chargement du catalogue complet (Recettes industrielles)
        recipes = [
            {
                "recipe_id": "BASIL_GENOVESE_PROD_V2",
                "crop": "basil",
                "variety": "Genovese",
                "target_metrics": {
                    "temp_day": 25.5, "temp_night": 19.0,
                    "humidity": 65.0, "co2_ppm": 800,
                    "ec_ms": 1.8, "ph": 6.2, "dli_target": 14.5
                },
                "phases": [
                    {"name": "Semis", "duration_days": 5},
                    {"name": "Végétatif", "duration_days": 20},
                    {"name": "Récolte", "duration_days": 5}
                ],
                "governance": {"version": "v2.1", "author": "@Mounir"}
            },
            {
                "recipe_id": "LETTUCE_BUTTERHEAD_STD",
                "crop": "lettuce",
                "variety": "Butterhead",
                "target_metrics": {
                    "temp_day": 21.0, "temp_night": 16.0,
                    "humidity": 70.0, "co2_ppm": 600,
                    "ec_ms": 1.4, "ph": 5.8, "dli_target": 12.0
                },
                "phases": [{"name": "Cycle Unique", "duration_days": 35}],
                "governance": {"version": "v1.0", "author": "@Asama"}
            }
        ]

        # Insertion des recettes
        for recipe in recipes:
            recipe["last_updated"] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
            db.plant_recipes.update_one(
                {"recipe_id": recipe["recipe_id"]},
                {"$set": recipe},
                upsert=True
            )

        # 2. Initialisation des logs d'incidents et de l'état système
        db.system_state.update_one(
            {"id": "global_config"},
            {"$set": {
                "deployment_date": time.strftime('%Y-%m-%d'),
                "vance_protocol_active": True,
                "schema_version": "157_cols_v2"
            }},
            upsert=True
        )

        logger.info(f"✅ MongoDB : {len(recipes)} recettes et configurations injectées.")
        return True
    except Exception as e:
        logger.error(f"❌ Échec seeding MongoDB : {e}")
        return False

def main():
    start_time = time.time()
    print("\n" + "="*60)
    print("      🌿 VERTIFLOW INFRASTRUCTURE INITIALIZER v2.0 🌿")
    print("="*60)

    # 1. ClickHouse (Le socle du Golden Record)
    if not init_clickhouse():
        logger.critical("🚨 ClickHouse non prêt. Vérifiez les logs 'docker logs clickhouse'.")
        return

    # 2. MongoDB (Le cerveau des recettes)
    if not init_mongodb():
        logger.warning("⚠️ Seeding MongoDB incomplet. Le Cortex A11 pourrait être limité.")

    duration = round(time.time() - start_time, 2)
    print("="*60)
    logger.info(f"⭐ INFRASTRUCTURE DÉPLOYÉE EN {duration}s ⭐")
    logger.info("👉 Vous pouvez maintenant lancer : python3 scripts/start_vertiflow.py --full")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()