"""
/********************************************************************************
 * PROJET : CLOUD CITADEL - VertiFlow Ecosystem
 * COMPOSANT : Consommateur de flux IA (Stream Processor)
 * TICKET : #025 - Implementation du connecteur de donnees pour l'IA
 * DESCRIPTION : Ce script permet d'ecouter les donnees de telemetrie filtrees
 * sur Kafka et de les transmettre aux modeles d'analyse.
 ********************************************************************************/
"""

import sys
import json
import logging
from pathlib import Path

from kafka import KafkaConsumer, KafkaProducer

# Ajouter le chemin racine pour importer les constantes
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.vertiflow_constants import KafkaTopics, Infrastructure

# Configuration du logging pour suivre l'etat du flux en production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Processor_IA_Ticket_025")

class IAStreamConnector:
    """
    Gestionnaire de connexion Kafka dedie a l'alimentation des algorithmes IA.
    """
    def __init__(self, bootstrap_servers=None, topic_in=None):
        # Utilise les constantes centralisees par defaut
        if bootstrap_servers is None:
            bootstrap_servers = [Infrastructure.KAFKA_BOOTSTRAP_SERVERS]
        if topic_in is None:
            topic_in = KafkaTopics.TELEMETRY_FULL

        # Initialisation du consommateur Kafka (ecoute les donnees entrantes)
        self.consumer = KafkaConsumer(
            topic_in,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',  # On commence par les derniers messages produits
            group_id='vertiflow_ia_engine'  # Identifiant du groupe de consommateurs
        )

        # Initialisation du producteur Kafka (publie les resultats d'analyse)
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )

    def lancer_traitement(self, fonction_ia):
        """
        Boucle principale de lecture du flux.
        :param fonction_ia: La fonction ou le modèle qui traite les données reçues.
        """
        logger.info(f"Démarrage de l'écoute sur le topic : {self.consumer.subscription()}")
        
        try:
            for message in self.consumer:
                # Extraction des données JSON du message
                donnees_capteurs = message.value
                
                # Exécution de la logique d'analyse (IA / Heuristique)
                resultat_analyse = fonction_ia(donnees_capteurs)
                
                # Si l'IA detecte un besoin d'action ou une anomalie
                if resultat_analyse:
                    # Envoi du resultat vers le topic dedie aux alertes (utilise constantes)
                    self.producer.send(KafkaTopics.ALERTS, resultat_analyse)
                    logger.info(f"Analyse IA publiee sur '{KafkaTopics.ALERTS}'.")
                    
        except KeyboardInterrupt:
            logger.info("Arrêt manuel du processeur de flux.")
        except Exception as e:
            logger.error(f"Erreur critique lors du traitement du flux : {e}")
        finally:
            # Fermeture propre des connexions
            self.consumer.close()
            logger.info("Connexions Kafka fermées.")

if __name__ == "__main__":
    # Exemple d'usage : on définit une fonction d'analyse simple (Mock)
    def detecter_anomalie_test(data):
        # Logique de test : vérifie si la température dépasse un seuil
        # Utilise air_temp_internal (champ du simulateur kafka_telemetry_producer.py)
        temp = data.get('air_temp_internal', 0)
        if temp > 30:
            return {"status": "ALERTE", "valeur": temp, "msg": "Surchauffe détectée"}
        return None

    # Instance du connecteur (Ticket #025)
    processeur = IAStreamConnector()
    processeur.lancer_traitement(detecter_anomalie_test)