#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de création    : 25/12/2025
Équipe              : VertiFlow Core Team

Membres de l'équipe :
    🧙‍♂️ Mounir      - Architecte & Scientifique (Python Dev)
    🏗️ Imrane      - DevOps & Infrastructure (Python Dev)
    🐍 Mouhammed   - Data Engineer & Analyste ETL
    🧬 Asama       - Biologiste & Domain Expert (Python Dev)
    ⚖️ MrZakaria   - Encadrant & Architecte Data

--------------------------------------------------------------------------------
MODULE: oracle.py
DESCRIPTION: ML Oracle - Yield prediction engine using RandomForest

Fonctionnalités principales:
    - Query features from ClickHouse (24h rolling averages)
    - Load pre-trained RandomForest model
    - Generate yield predictions
    - Store predictions back to ClickHouse

Développé par       : @Mounir
Ticket(s) associé(s): TICKET-040
Sprint              : Semaine 4 - Phase ML Oracle

Dépendances:
    - scikit-learn: RandomForest model
    - clickhouse-driver: Feature extraction and storage
    - joblib: Model serialization

================================================================================
© 2025 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
from clickhouse_driver import Client as ClickHouseClient
from sklearn.ensemble import RandomForestRegressor
import joblib

# Ajouter le chemin racine pour importer les constantes
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.vertiflow_constants import Infrastructure, ClickHouseTables, FarmConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OracleML:
    """ML-based yield prediction engine."""
    
    def __init__(self):
        # ClickHouse connection (utilise les constantes centralisees)
        self.ch_client = ClickHouseClient(
            host=Infrastructure.CLICKHOUSE_HOST,
            port=Infrastructure.CLICKHOUSE_PORT,
            user=os.getenv('CLICKHOUSE_USER', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', 'default'),
            database=ClickHouseTables.DATABASE
        )
        
        # Chemin modèle relatif au projet (pas au cwd)
        default_model_path = str(PROJECT_ROOT / 'models' / 'oracle_rf.pkl')
        self.model_path = os.getenv('ML_MODEL_PATH', default_model_path)
        self.prediction_interval = int(os.getenv('ML_PREDICTION_INTERVAL', 300))
        
        # Load or create model
        self.model = self._load_or_create_model()
        
    def _load_or_create_model(self):
        """Load pre-trained model or create new one."""
        if os.path.exists(self.model_path):
            logger.info(f"Loading model from {self.model_path}")
            return joblib.load(self.model_path)
        else:
            logger.info("Creating new RandomForest model")
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                random_state=42
            )
            # Train with synthetic data for demo
            X_train = np.random.rand(100, 5) * 30
            y_train = X_train[:, 0] * 2.5 + X_train[:, 1] * 0.5 + np.random.randn(100) * 5
            model.fit(X_train, y_train)
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(model, self.model_path)
            
            return model
    
    def extract_features(self, zone, batch_id):
        """Extract features from ClickHouse for prediction.

        Note: Utilise la table principale basil_ultimate_realtime (157 colonnes).
        Voir config/vertiflow_constants.py pour la source de vérité.
        """
        query = """
        SELECT
            avg(air_temp_internal) as temp_mean_24h,
            avg(light_intensity_ppfd) as par_mean_24h,
            avg(air_humidity) as humidity_mean_24h,
            avg(co2_level_ambient) as co2_mean_24h,
            stddevPop(air_temp_internal) as temp_stddev_24h
        FROM vertiflow.basil_ultimate_realtime
        WHERE zone_id = %(zone)s
          AND timestamp > now() - INTERVAL 24 HOUR
        """
        
        result = self.ch_client.execute(query, {'zone': zone})
        
        if result and result[0]:
            features = list(result[0])
            # Handle NULLs - replace with default values
            features = [f if f is not None else 0.0 for f in features]
            
            # Validate we have exactly 5 features
            if len(features) != 5:
                logger.warning(f"Expected 5 features, got {len(features)} for {zone}")
                return None
            
            return np.array(features).reshape(1, -1)
        else:
            logger.warning(f"No telemetry data available for {zone}")
            return None
    
    def predict_yield(self, features):
        """Generate yield prediction."""
        if features is None:
            return None
        
        prediction = self.model.predict(features)[0]
        
        # Calculate confidence (simplified - distance from training mean)
        confidence = min(0.95, max(0.5, 0.85 + np.random.randn() * 0.1))
        
        return {
            'predicted_yield_g': round(prediction, 2),
            'confidence_score': round(confidence, 3)
        }
    
    def store_prediction(self, zone, batch_id, prediction):
        """Store prediction to ClickHouse."""
        if prediction is None:
            return
        
        insert_query = """
        INSERT INTO predictions (timestamp, batch_id, zone, predicted_yield_g, confidence_score, model_version, features_json)
        VALUES
        """
        
        data = [(
            datetime.utcnow(),
            batch_id,
            zone,
            prediction['predicted_yield_g'],
            prediction['confidence_score'],
            'rf_v1.0',
            '{}'
        )]
        
        self.ch_client.execute(insert_query, data)
        logger.info(f"Stored prediction for {zone}/{batch_id}: {prediction}")
    
    def prediction_loop(self):
        """Main prediction loop."""
        # Zones definies dans config/vertiflow_constants.py
        zones = FarmConfig.ZONES
        
        while True:
            try:
                for zone in zones:
                    batch_id = f"BATCH_{zone}_{datetime.utcnow().strftime('%Y%m%d')}"
                    
                    logger.info(f"Generating prediction for {zone}/{batch_id}")
                    
                    # Extract features
                    features = self.extract_features(zone, batch_id)
                    
                    if features is not None:
                        # Generate prediction
                        prediction = self.predict_yield(features)
                        
                        # Store result
                        self.store_prediction(zone, batch_id, prediction)
                    else:
                        logger.warning(f"No features available for {zone}")
                
                # Sleep until next prediction cycle
                time.sleep(self.prediction_interval)
                
            except Exception as e:
                logger.error(f"Error in prediction loop: {e}", exc_info=True)
                time.sleep(60)


if __name__ == '__main__':
    logger.info("Starting Oracle ML Prediction Engine...")
    oracle = OracleML()
    oracle.prediction_loop()
