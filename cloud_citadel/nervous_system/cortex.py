#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - INTELLIGENCE ARTIFICIELLE (PHASE 4)
================================================================================
MODULE: cortex.py (ALGO A11)
DESCRIPTION: Cerveau Supérieur (Optimisation).
             Analyse les performances passées (ClickHouse) et propose de nouvelles
             cibles (Recipes) pour maximiser le ROI.

Développé par        : @Mounir
Ticket(s) associé(s): TICKET-029
Sprint              : Semaine 5 - Phase Intelligence Prescriptive
================================================================================
"""

import os
import sys
import time
import logging
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from clickhouse_driver import Client
from pymongo import MongoClient

# Ajouter le chemin racine pour importer les constantes
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.vertiflow_constants import Infrastructure, ClickHouseTables, MongoDBCollections

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CORTEX] - %(levelname)s - %(message)s')
logger = logging.getLogger("VertiFlowCortex")

class RecipeOptimizer:
    def __init__(self):
        # Utilise les constantes centralisees (config/vertiflow_constants.py)
        self.ch_client = Client(
            host=os.getenv('CLICKHOUSE_HOST', Infrastructure.CLICKHOUSE_HOST),
            port=int(os.getenv('CLICKHOUSE_PORT', Infrastructure.CLICKHOUSE_PORT)),
            user=os.getenv('CLICKHOUSE_USER', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', 'default')
        )
        # MongoDB connection - utilise env var si disponible
        mongo_uri = os.getenv('MONGODB_URI', Infrastructure.MONGODB_URI)
        self.mongo_client = MongoClient(mongo_uri)
        self.db_ops = self.mongo_client[MongoDBCollections.DATABASE]
        
    def fetch_performance_data(self):
        """Récupère les données agrégées des 30 derniers jours.

        Note: Utilise la table principale basil_ultimate_realtime.
        Voir config/vertiflow_constants.py pour la source de vérité.
        """
        logger.info("📥 Récupération des données de performance (ClickHouse)...")
        query = """
        SELECT
            rack_id,
            avg(fresh_biomass_est) as avg_biomass_g,
            avg(essential_oil_yield) as avg_oil_pct,
            avg(fresh_biomass_est) / nullIf(avg(energy_footprint_hourly), 0) as efficiency_g_per_eur
        FROM vertiflow.basil_ultimate_realtime
        WHERE timestamp > now() - INTERVAL 30 DAY
        GROUP BY rack_id
        LIMIT 5
        """
        try:
            return self.ch_client.execute(query)
        except Exception as e:
            logger.error(f"Erreur ClickHouse: {e}")
            # Return mock data for testing if table doesn't exist yet
            logger.info("Utilisation de données simulées pour le test")
            return [
                ("R01", 45.2, 2.1, 18.5),
                ("R02", 42.8, 1.9, 17.2),
                ("R03", 48.1, 2.3, 19.8)
            ]

    def objective_function(self, params):
        """
        Fonction à optimiser (Simulée).
        Score = Yield * 0.6 + Quality * 0.4 - Cost * 0.2
        """
        temp, ec, dli = params
        # Modèle théorique simplifié (Parabole)
        yield_score = -1.5 * (temp - 24)**2 + 100
        quality_score = -5.0 * (ec - 1.8)**2 + 100
        cost_penalty = dli * 2.5
        
        return -(yield_score * 0.6 + quality_score * 0.4 - cost_penalty)

    def optimize_recipe(self, current_recipe_id):
        """Exécute l'optimisation Scipy."""
        logger.info(f"🧠 Lancement de l'optimisation pour {current_recipe_id}...")
        
        # Point de départ (Actuel)
        x0 = [22.0, 1.6, 12.0] # Temp, EC, DLI
        
        # Bornes (Contraintes biologiques)
        bounds = [(18, 28), (1.2, 2.5), (10, 20)]
        
        result = minimize(self.objective_function, x0, bounds=bounds, method='L-BFGS-B')
        
        if result.success:
            new_params = result.x
            logger.info(f"🚀 Optimum trouvé: Temp={new_params[0]:.1f}°C, EC={new_params[1]:.1f}, DLI={new_params[2]:.1f}")
            return {
                "temp_opt": round(new_params[0], 1),
                "ec_target": round(new_params[1], 1),
                "dli_target": round(new_params[2], 1)
            }
        return None

    def apply_new_recipe(self, recipe_id, new_targets):
        """Met à jour MongoDB pour que l'Algo A4 (Alertes) utilise les nouvelles cibles."""
        logger.info(f"💾 Application de la nouvelle recette {recipe_id} dans MongoDB...")
        
        self.db_ops.plant_recipes.update_one(
            {"recipe_id": recipe_id},
            {"$set": {
                "targets.temp_opt": new_targets['temp_opt'],
                "targets.ec_target": new_targets['ec_target'],
                "targets.dli_target": new_targets['dli_target'],
                "last_optimized": datetime.now()
            }}
        )
        logger.info("✅ Recette mise à jour. Les automates vont s'adapter.")

    def run_cycle(self):
        """Cycle principal (Toutes les 24h)."""
        while True:
            logger.info("--- Début du Cycle d'Optimisation Cortex ---")
            
            # 1. Analyser
            data = self.fetch_performance_data()
            if data:
                # 2. Optimiser (Exemple sur la recette Standard)
                new_targets = self.optimize_recipe("RECIPE_GENOVESE_STD_V1")
                
                # 3. Appliquer
                if new_targets:
                    self.apply_new_recipe("RECIPE_GENOVESE_STD_V1", new_targets)
            
            logger.info("--- Fin du Cycle. Veille 24h ---")
            time.sleep(86400) # 24h

if __name__ == "__main__":
    cortex = RecipeOptimizer()
    # Lancement du cycle d'optimisation (boucle infinie, cycle toutes les 24h)
    cortex.run_cycle()