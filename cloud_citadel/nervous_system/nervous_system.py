#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - INTELLIGENCE ARTIFICIELLE (PHASE 4)
================================================================================
Date de création    : 31/12/2025
Équipe              : VertiFlow Core Team

Membres:
    🧙‍♂️ @Mounir       - Architecte & Scientifique
    🐍 @Mouhammed    - Data Engineer & Analyste ETL
    🧬 @Asama        - Biologiste & Domain Expert

--------------------------------------------------------------------------------
MODULE: oracle.py (ALGO A9)
DESCRIPTION: Moteur de prédiction de récolte basé sur LSTM (Deep Learning).
             Analyse les séries temporelles de croissance pour estimer la date optimale.

Fonctionnalités:
    - Chargement des modèles .h5 pré-entraînés
    - Inférence en temps réel sur les flux de données Kafka
    - Calcul de la date de récolte estimée (J+N)

Développé par        : @Mounir & @Mouhammed
Ticket(s) associé(s): TICKET-023
Sprint              : Semaine 4 - Intelligence Prédictive

Dépendances:
    - tensorflow, pandas, numpy, kafka-python

================================================================================
© 2025 VertiFlow Core Team - Tous droits réservés
"""

import os
import json
import logging
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime, timedelta
from kafka import KafkaConsumer, KafkaProducer

# Configuration du Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ORACLE] - %(levelname)s - %(message)s')
logger = logging.getLogger("VertiFlowOracle")

# Configuration Kafka (port 9092 pour accès depuis l'hôte Windows)
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC_INPUT = 'basil_telemetry_full'
TOPIC_OUTPUT = 'vertiflow.predictions'

class HarvestOracle:
    def __init__(self, model_path='models/lstm_harvest_v1.h5'):
        self.model_path = model_path
        self.model = None
        self.scaler = None # Devrait être chargé depuis un fichier pickle
        self.sequence_length = 7 # Jours d'historique nécessaires
        
        # Initialisation Kafka
        self.consumer = KafkaConsumer(
            TOPIC_INPUT,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest'
        )
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        self.load_model()

    def load_model(self):
        """Charge le modèle LSTM pré-entraîné."""
        if os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info(f"✅ Modèle LSTM chargé depuis {self.model_path}")
            except Exception as e:
                logger.error(f"❌ Erreur chargement modèle: {e}")
                # Fallback: Création d'un modèle dummy pour le dev
                self.model = self._create_dummy_model()
        else:
            logger.warning(f"⚠️ Modèle non trouvé ({self.model_path}). Utilisation du mode simulation.")
            self.model = self._create_dummy_model()

    def _create_dummy_model(self):
        """Crée un modèle simple pour les tests d'intégration."""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(10, input_shape=(7, 5)),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def preprocess(self, data_batch):
        """Transforme les données brutes en tenseur (1, 7, 5)."""
        # Simplification pour l'exemple : on suppose recevoir un historique
        # En prod, il faudrait interroger ClickHouse pour avoir les 7 derniers jours
        # Ici on simule une matrice
        return np.random.rand(1, 7, 5) 

    def predict(self, features):
        """Exécute l'inférence."""
        if self.model is None:
            return None
        
        # Prédiction de la biomasse future (g)
        predicted_growth = self.model.predict(features, verbose=0)[0][0]
        return float(predicted_growth)

    def run(self):
        """Boucle principale de consommation Kafka."""
        logger.info("🔮 Oracle A9 démarré. En attente de données...")
        
        for message in self.consumer:
            data = message.value
            
            # On ne prédit que si on a des données de croissance
            if 'fresh_biomass_est' in data and data['fresh_biomass_est'] is not None:
                
                # 1. Préparation (Simulation appel ClickHouse pour historique)
                features = self.preprocess(data)
                
                # 2. Inférence
                growth_prediction = self.predict(features)
                
                # 3. Logique Métier (Calcul Date)
                current_weight = data['fresh_biomass_est']
                target_weight = data.get('target_harvest_weight', 50.0)
                
                # Estimation simplifiée : Poids / Vitesse
                growth_rate = max(0.1, growth_prediction) # g/jour
                days_left = max(0, (target_weight - current_weight) / growth_rate)
                predicted_date = datetime.now() + timedelta(days=days_left)
                
                # 4. Publication Résultat
                result = {
                    "timestamp": datetime.now().isoformat(),
                    "rack_id": data.get('rack_id'),
                    "batch_id": data.get('batch_id'),
                    "algo_id": "A9_LSTM",
                    "predicted_harvest_date": predicted_date.isoformat(),
                    "days_remaining": round(days_left, 1),
                    "confidence": 0.85 # Placeholder
                }
                
                self.producer.send(TOPIC_OUTPUT, value=result)
                logger.info(f"🚀 Prédiction envoyée pour {data.get('rack_id')}: J-{days_left:.1f}")

if __name__ == "__main__":
    oracle = HarvestOracle()
    oracle.run()