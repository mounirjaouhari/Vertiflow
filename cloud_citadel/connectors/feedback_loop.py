"""
/********************************************************************************
 * PROJET : CLOUD CITADEL - VertiFlow Ecosystem
 * COMPOSANT : Boucle de Retroaction (Feedback Loop)
 * TICKET : #026 - Systeme d'emission de commandes automatisees
 * DESCRIPTION : Ce composant traduit les decisions de l'IA en commandes
 * standardisees envoyees aux fermes via le bus Kafka.
 ********************************************************************************/
"""

import sys
import json
import uuid
import datetime
import logging
from pathlib import Path

from kafka import KafkaProducer

# Ajouter le chemin racine pour importer les constantes
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.vertiflow_constants import KafkaTopics, Infrastructure

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Feedback_Loop_Ticket_026")

class FeedbackLoop:
    """
    Interface d'emission de commandes pour piloter l'infrastructure a distance.
    """
    def __init__(self, bootstrap_servers=None):
        # Utilise les constantes centralisees par defaut
        if bootstrap_servers is None:
            bootstrap_servers = [Infrastructure.KAFKA_BOOTSTRAP_SERVERS]

        # Initialisation du producteur Kafka pour l'envoi de commandes
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )

    def emettre_commande(self, farm_id, device_id, type_action, parametres, priorite="NORMAL"):
        """
        Formate une commande au format standard VertiFlow et l'envoie au Edge.
        
        :param farm_id: Identifiant de la ferme cible
        :param device_id: Identifiant de l'équipement (pompe, LED, etc.)
        :param type_action: Type de commande (ex: WATER_ON, LIGHT_OFF)
        :param parametres: Dictionnaire de réglages (ex: {"duree": 60})
        :param priorite: Niveau d'urgence (LOW, NORMAL, HIGH, CRITICAL)
        """
        
        # Construction de l'enveloppe de commande (Standardisée Ticket #026)
        payload_commande = {
            "id_transaction": str(uuid.uuid4()),
            "horodatage": datetime.datetime.utcnow().isoformat() + "Z",
            "cible": {
                "ferme": farm_id,
                "equipement": device_id
            },
            "action": type_action,
            "priorite": priorite,
            "valeurs": parametres,
            "emetteur": "MOTEUR_CORTEX_IA",
            "confirmation_requise": True
        }
        
        try:
            # Publication sur le topic des commandes (utilise constantes centralisees)
            futur = self.producer.send(KafkaTopics.COMMANDS, payload_commande)
            # On attend la confirmation de Kafka (Optionnel mais securise)
            futur.get(timeout=10)
            logger.info(f"Commande [{type_action}] relayee pour la ferme {farm_id}")
            return True
        except Exception as e:
            logger.error(f"Echec de l'envoi de la commande : {e}")
            return False

if __name__ == "__main__":
    # Démo : Simulation d'une décision IA demandant l'arrosage
    actionneur = FeedbackLoop()
    
    # Envoi d'une commande d'arrosage d'urgence (Ticket #026)
    actionneur.emettre_commande(
        farm_id="ZONE-ALPHA-01",
        device_id="PUMP-MAIN",
        type_action="WATER_ON",
        parametres={"debit": "1.5L/min", "duree_sec": 30},
        priorite="HIGH"
    )