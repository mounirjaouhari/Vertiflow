#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de création    : 05/02/2026
Équipe              : VertiFlow Core Team

Membres de l'équipe :
    🧙‍♂️ Mounir      - Architecte & Scientifique (Python Dev)
    🏗️ Imrane      - DevOps & Infrastructure (Python Dev)
    🐍 Mouhammed   - Data Engineer & Analyste ETL
    🧬 Asama       - Biologiste & Domain Expert (Python Dev)
    ⚖️ MrZakaria   - Encadrant & Architecte Data

--------------------------------------------------------------------------------
MODULE: harvest_predictor.py (ALGO A9b)
DESCRIPTION: Prédiction de date de récolte basée sur les modèles agronomiques
             scientifiquement validés.

Modèles Scientifiques Utilisés:
    1. GDD (Growing Degree Days) - McMaster & Wilhelm (1997)
       Formule: GDD = max(0, T_moyenne - T_base)
       Basilic: T_base = 10°C, GDD_maturité = 400-600

    2. DLI (Daily Light Integral) - Faust & Logan (2018)
       Basilic optimal: 12-17 mol/m²/jour
       Impact: +/- 10% sur vitesse de croissance

    3. VPD (Vapor Pressure Deficit) - Tetens (1930)
       Basilic optimal: 0.8-1.2 kPa
       Stress si VPD > 1.5 kPa

    4. Courbe de Croissance Gompertz - Zwietering et al. (1990)
       W(t) = W_max * exp(-exp((µ_max * e / W_max) * (λ - t) + 1))

Références:
    - McMaster, G.S., Wilhelm, W.W. (1997). Growing degree-days: one equation,
      two interpretations. Agricultural and Forest Meteorology.
    - Faust, J.E., Logan, J. (2018). Daily Light Integral: A Research Review.
      Greenhouse Product News.

Développé par       : @Mounir
Ticket(s) associé(s): TICKET-045
Sprint              : Semaine 5 - Phase ML Avancé

================================================================================
© 2026 VertiFlow Core Team - Tous droits réservés
================================================================================
"""

import os
import sys
import time
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

import numpy as np
from clickhouse_driver import Client as ClickHouseClient

# Ajouter le chemin racine pour importer les constantes
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.vertiflow_constants import Infrastructure, ClickHouseTables

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [HARVEST] - %(levelname)s - %(message)s')
logger = logging.getLogger("HarvestPredictor")


# =============================================================================
# CONSTANTES AGRONOMIQUES SCIENTIFIQUES
# =============================================================================

@dataclass
class BasilParameters:
    """Paramètres scientifiques pour Ocimum basilicum (Basilic Genovese).
    
    Références:
        - Walters & Currey (2015) - Effects of nutrient solution concentration
        - Moccaldi & Runkle (2007) - Photoperiod and DLI for basil production
        - Chang et al. (2008) - Effects of temperature on basil growth
    """
    # Growing Degree Days (GDD)
    T_BASE: float = 10.0        # Température de base (°C)
    GDD_VEGETATIVE: float = 150  # GDD pour phase végétative
    GDD_MATURE: float = 450      # GDD pour maturité
    GDD_HARVEST: float = 550     # GDD pour récolte optimale
    
    # Daily Light Integral (DLI)
    DLI_MIN: float = 12.0       # mol/m²/jour minimum
    DLI_OPTIMAL: float = 17.0   # mol/m²/jour optimal
    DLI_MAX: float = 25.0       # mol/m²/jour maximum (stress)
    
    # Vapor Pressure Deficit (VPD)
    VPD_MIN: float = 0.4        # kPa minimum
    VPD_OPTIMAL: float = 1.0    # kPa optimal
    VPD_MAX: float = 1.5        # kPa maximum (stress)
    
    # Biomasse
    BIOMASS_TARGET: float = 50.0  # g/plant à la récolte
    
    # Gompertz parameters (calibrés pour basilic)
    GOMPERTZ_WMAX: float = 60.0   # g - biomasse max asymptotique
    GOMPERTZ_MU: float = 0.15     # taux de croissance max (g/GDD)
    GOMPERTZ_LAG: float = 50.0    # GDD avant démarrage exponentiel


# Mapping zones vers zone_id ClickHouse (cohérent avec oracle.py)
ZONE_MAPPING = {
    "ZONE_A": "Z1",
    "ZONE_B": "Z2",
    "NURSERY": "Z3",
    "ZONE_GERMINATION": "Z1",
    "ZONE_CROISSANCE": "Z2",
}


# =============================================================================
# MODÈLES SCIENTIFIQUES
# =============================================================================

class AgronomicModels:
    """Modèles agronomiques scientifiquement validés."""
    
    @staticmethod
    def calculate_gdd(temp_avg: float, t_base: float = 10.0) -> float:
        """
        Calcul des Growing Degree Days (GDD).
        
        Méthode: Simple averaging method (McMaster & Wilhelm, 1997)
        Formule: GDD = max(0, T_avg - T_base)
        
        Args:
            temp_avg: Température moyenne journalière (°C)
            t_base: Température de base pour le basilic (°C)
        
        Returns:
            GDD pour la période (degrés-jours)
        """
        return max(0.0, temp_avg - t_base)
    
    @staticmethod
    def calculate_vpd(temperature_c: float, humidity_pct: float) -> float:
        """
        Calcul du Vapor Pressure Deficit (VPD).
        
        Méthode: Équation de Tetens (1930)
        Formule: SVP = 0.6108 * exp(17.27 * T / (T + 237.3))
                 VPD = SVP * (1 - RH/100)
        
        Args:
            temperature_c: Température (°C)
            humidity_pct: Humidité relative (%)
        
        Returns:
            VPD en kPa
        """
        # Pression de vapeur saturante (Tetens formula)
        svp_kpa = 0.6108 * math.exp((17.27 * temperature_c) / (temperature_c + 237.3))
        # VPD
        vpd_kpa = svp_kpa * (1 - humidity_pct / 100.0)
        return max(0.0, vpd_kpa)
    
    @staticmethod
    def calculate_dli(ppfd_avg: float, photoperiod_hours: float = 16.0) -> float:
        """
        Calcul du Daily Light Integral (DLI).
        
        Formule: DLI = PPFD * photoperiod * 3600 / 1_000_000
        
        Args:
            ppfd_avg: PPFD moyen (µmol/m²/s)
            photoperiod_hours: Durée d'éclairage (heures)
        
        Returns:
            DLI en mol/m²/jour
        """
        return ppfd_avg * photoperiod_hours * 3600 / 1_000_000
    
    @staticmethod
    def gompertz_growth(gdd_accumulated: float, params: BasilParameters) -> float:
        """
        Modèle de croissance de Gompertz.
        
        Équation: W(t) = W_max * exp(-exp((µ * e / W_max) * (λ - GDD) + 1))
        
        Référence: Zwietering et al. (1990)
        
        Args:
            gdd_accumulated: GDD accumulés depuis plantation
            params: Paramètres de croissance
        
        Returns:
            Biomasse estimée (g)
        """
        e = math.e
        W_max = params.GOMPERTZ_WMAX
        mu = params.GOMPERTZ_MU
        lag = params.GOMPERTZ_LAG
        
        exponent = (mu * e / W_max) * (lag - gdd_accumulated) + 1
        biomass = W_max * math.exp(-math.exp(exponent))
        
        return max(0.0, biomass)
    
    @staticmethod
    def stress_factor(vpd: float, dli: float, params: BasilParameters) -> float:
        """
        Calcul du facteur de stress environnemental.
        
        Combine le stress hydrique (VPD) et lumineux (DLI).
        
        Args:
            vpd: VPD actuel (kPa)
            dli: DLI actuel (mol/m²/jour)
            params: Paramètres de référence
        
        Returns:
            Facteur multiplicatif [0.5, 1.2]
        """
        # Stress VPD (gaussien centré sur optimal)
        vpd_factor = math.exp(-0.5 * ((vpd - params.VPD_OPTIMAL) / 0.5) ** 2)
        
        # Stress DLI (plateau entre min et optimal)
        if dli < params.DLI_MIN:
            dli_factor = dli / params.DLI_MIN
        elif dli > params.DLI_MAX:
            dli_factor = 1.0 - 0.2 * ((dli - params.DLI_MAX) / params.DLI_MAX)
        else:
            dli_factor = min(1.0, dli / params.DLI_OPTIMAL)
        
        # Facteur combiné (moyenne pondérée)
        combined = 0.4 * vpd_factor + 0.6 * dli_factor
        
        return max(0.5, min(1.2, combined))


# =============================================================================
# HARVEST PREDICTOR
# =============================================================================

class HarvestPredictor:
    """Prédicteur de date de récolte basé sur les modèles agronomiques."""
    
    def __init__(self):
        self.params = BasilParameters()
        
        # ClickHouse connection
        self.ch_client = ClickHouseClient(
            host=os.getenv('CLICKHOUSE_HOST', Infrastructure.CLICKHOUSE_HOST),
            port=int(os.getenv('CLICKHOUSE_PORT', Infrastructure.CLICKHOUSE_PORT)),
            user=os.getenv('CLICKHOUSE_USER', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', 'default'),
            database=ClickHouseTables.DATABASE
        )
        
        self.prediction_interval = int(os.getenv('HARVEST_PREDICTION_INTERVAL', 300))
        
        logger.info("HarvestPredictor initialisé avec paramètres scientifiques")
        logger.info(f"  T_base={self.params.T_BASE}°C, GDD_harvest={self.params.GDD_HARVEST}")
        logger.info(f"  DLI_optimal={self.params.DLI_OPTIMAL} mol/m²/jour")
        logger.info(f"  VPD_optimal={self.params.VPD_OPTIMAL} kPa")
    
    def get_zone_conditions(self, zone: str) -> Optional[Dict]:
        """
        Récupère les conditions environnementales moyennes (24h) depuis ClickHouse.
        """
        db_zone = ZONE_MAPPING.get(zone, zone)
        
        query = """
        SELECT
            avg(air_temp_internal) as temp_avg,
            avg(air_humidity) as humidity_avg,
            avg(light_intensity_ppfd) as ppfd_avg,
            avg(co2_level_ambient) as co2_avg,
            min(timestamp) as oldest_data,
            max(timestamp) as newest_data,
            count() as data_points
        FROM vertiflow.basil_ultimate_realtime
        WHERE zone_id = %(zone)s
          AND timestamp > now() - INTERVAL 24 HOUR
        """
        
        result = self.ch_client.execute(query, {'zone': db_zone})
        
        if result and result[0] and result[0][0] is not None:
            row = result[0]
            return {
                'temp_avg': float(row[0] or 22.0),
                'humidity_avg': float(row[1] or 65.0),
                'ppfd_avg': float(row[2] or 300.0),
                'co2_avg': float(row[3] or 800.0),
                'data_points': int(row[6] or 0)
            }
        return None
    
    def get_accumulated_gdd(self, zone: str, days_since_planting: int = 20) -> float:
        """
        Calcule les GDD accumulés depuis la plantation.
        
        En l'absence de date de plantation réelle, utilise days_since_planting.
        """
        db_zone = ZONE_MAPPING.get(zone, zone)
        
        # Récupérer l'historique de température
        query = """
        SELECT
            toDate(timestamp) as day,
            avg(air_temp_internal) as temp_avg
        FROM vertiflow.basil_ultimate_realtime
        WHERE zone_id = %(zone)s
          AND timestamp > now() - INTERVAL %(days)s DAY
        GROUP BY day
        ORDER BY day
        """
        
        result = self.ch_client.execute(query, {'zone': db_zone, 'days': days_since_planting})
        
        total_gdd = 0.0
        for row in result:
            if row[1] is not None:
                daily_gdd = AgronomicModels.calculate_gdd(float(row[1]), self.params.T_BASE)
                total_gdd += daily_gdd
        
        # Si pas assez de données, estimer avec température moyenne et jours
        if total_gdd == 0 and days_since_planting > 0:
            # Estimation: température moyenne de 24°C → GDD = 14/jour
            total_gdd = days_since_planting * 14.0
        
        return total_gdd
    
    def predict_harvest(self, zone: str, batch_id: str) -> Optional[Dict]:
        """
        Prédit la date de récolte optimale pour une zone.
        
        Returns:
            Dict avec: gdd_accumulated, gdd_remaining, days_to_harvest,
                      predicted_date, biomass_estimated, confidence
        """
        # 1. Conditions actuelles
        conditions = self.get_zone_conditions(zone)
        if not conditions:
            logger.warning(f"Pas de données pour {zone}")
            return None
        
        # 2. GDD accumulés (estimation basée sur 20 jours depuis plantation)
        days_since_planting = 20  # TODO: récupérer depuis batch_id
        gdd_accumulated = self.get_accumulated_gdd(zone, days_since_planting)
        
        # 3. Calculs scientifiques
        vpd = AgronomicModels.calculate_vpd(
            conditions['temp_avg'], 
            conditions['humidity_avg']
        )
        
        dli = AgronomicModels.calculate_dli(
            conditions['ppfd_avg'], 
            photoperiod_hours=16.0
        )
        
        # 4. GDD journalier avec facteur de stress
        daily_gdd = AgronomicModels.calculate_gdd(conditions['temp_avg'], self.params.T_BASE)
        stress = AgronomicModels.stress_factor(vpd, dli, self.params)
        effective_daily_gdd = daily_gdd * stress
        
        # 5. GDD restants jusqu'à récolte
        gdd_remaining = max(0, self.params.GDD_HARVEST - gdd_accumulated)
        
        # 6. Jours restants
        if effective_daily_gdd > 0:
            days_to_harvest = gdd_remaining / effective_daily_gdd
        else:
            days_to_harvest = 999  # Conditions trop froides
        
        # 7. Date prédite
        predicted_date = datetime.utcnow() + timedelta(days=days_to_harvest)
        
        # 8. Biomasse estimée (Gompertz)
        biomass_estimated = AgronomicModels.gompertz_growth(gdd_accumulated, self.params)
        
        # 9. Confiance basée sur la qualité des données et le stress
        data_quality = min(1.0, conditions['data_points'] / 100)
        confidence = 0.5 + 0.3 * data_quality + 0.2 * stress
        
        # 10. Stade de croissance
        if gdd_accumulated < self.params.GDD_VEGETATIVE:
            growth_stage = "SEEDLING"
        elif gdd_accumulated < self.params.GDD_MATURE:
            growth_stage = "VEGETATIVE"
        elif gdd_accumulated < self.params.GDD_HARVEST:
            growth_stage = "MATURE"
        else:
            growth_stage = "HARVEST_READY"
        
        return {
            'zone': zone,
            'batch_id': batch_id,
            'timestamp': datetime.utcnow(),
            
            # GDD
            'gdd_accumulated': round(gdd_accumulated, 1),
            'gdd_remaining': round(gdd_remaining, 1),
            'gdd_daily_effective': round(effective_daily_gdd, 2),
            
            # Prédictions
            'days_to_harvest': round(days_to_harvest, 1),
            'predicted_harvest_date': predicted_date.strftime('%Y-%m-%d'),
            'biomass_estimated_g': round(biomass_estimated, 1),
            'growth_stage': growth_stage,
            
            # Environnement
            'vpd_kpa': round(vpd, 2),
            'dli_mol': round(dli, 1),
            'stress_factor': round(stress, 2),
            
            # Méta
            'confidence': round(confidence, 3),
            'model_version': 'gdd_gompertz_v1.0'
        }
    
    def store_prediction(self, prediction: Dict) -> None:
        """Stocke la prédiction dans ClickHouse."""
        insert_query = """
        INSERT INTO harvest_predictions 
        (timestamp, zone, batch_id, gdd_accumulated, gdd_remaining, 
         days_to_harvest, predicted_harvest_date, biomass_estimated_g,
         growth_stage, vpd_kpa, dli_mol, stress_factor, confidence, model_version)
        VALUES
        """
        
        # Convertir la date string en objet date pour ClickHouse
        harvest_date = datetime.strptime(prediction['predicted_harvest_date'], '%Y-%m-%d').date()
        
        data = [(
            prediction['timestamp'],
            prediction['zone'],
            prediction['batch_id'],
            prediction['gdd_accumulated'],
            prediction['gdd_remaining'],
            prediction['days_to_harvest'],
            harvest_date,
            prediction['biomass_estimated_g'],
            prediction['growth_stage'],
            prediction['vpd_kpa'],
            prediction['dli_mol'],
            prediction['stress_factor'],
            prediction['confidence'],
            prediction['model_version']
        )]
        
        try:
            self.ch_client.execute(insert_query, data)
            logger.info(f"✅ Prédiction stockée: {prediction['zone']} → "
                       f"J-{prediction['days_to_harvest']:.0f} ({prediction['growth_stage']})")
        except Exception as e:
            logger.error(f"Erreur stockage ClickHouse: {e}")
    
    def prediction_loop(self):
        """Boucle principale de prédiction."""
        zones = list(ZONE_MAPPING.keys())
        
        logger.info("🌱 HarvestPredictor démarré - Modèle GDD + Gompertz")
        logger.info(f"   Zones: {zones}")
        logger.info(f"   Intervalle: {self.prediction_interval}s")
        
        while True:
            try:
                for zone in zones:
                    batch_id = f"BATCH_{zone}_{datetime.utcnow().strftime('%Y%m%d')}"
                    
                    prediction = self.predict_harvest(zone, batch_id)
                    
                    if prediction:
                        self.store_prediction(prediction)
                        
                        # Log détaillé
                        logger.info(
                            f"📊 {zone}: GDD={prediction['gdd_accumulated']:.0f}/{self.params.GDD_HARVEST}, "
                            f"Biomasse={prediction['biomass_estimated_g']:.0f}g, "
                            f"VPD={prediction['vpd_kpa']:.2f}kPa, "
                            f"Récolte: {prediction['predicted_harvest_date']}"
                        )
                
                time.sleep(self.prediction_interval)
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle: {e}", exc_info=True)
                time.sleep(60)


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("VERTIFLOW - Harvest Predictor (Modèle Scientifique)")
    logger.info("Basé sur: GDD (McMaster 1997) + Gompertz (Zwietering 1990)")
    logger.info("=" * 60)
    
    predictor = HarvestPredictor()
    predictor.prediction_loop()
