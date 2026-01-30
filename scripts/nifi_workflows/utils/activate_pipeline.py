#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import urllib3
import logging
import time
import os
import sys
from pathlib import Path

# Ajouter le chemin parent pour importer nifi_config
sys.path.insert(0, str(Path(__file__).parent.parent))
from nifi_config import get_config

# Desactivation des alertes SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NiFiActivator:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.headers = {'Content-Type': 'application/json'}
        
        # Authentification
        auth_url = f"{self.base_url}/access/token"
        response = requests.post(auth_url, data={'username': username, 'password': password}, verify=False)
        if response.status_code in [200, 201]:
            self.headers['Authorization'] = f'Bearer {response.text}'
            logger.info("✅ Authentification réussie.")
        else:
            raise Exception("Échec d'authentification.")

    def set_run_status(self, entity_type, entity_id, status):
        """
        Démarrer ou arrêter une entité (process-groups, processors, ports).
        status: 'RUNNING' ou 'STOPPED'
        """
        # Pour les groupes de processus, l'endpoint est différent
        if entity_type == "process-groups":
            url = f"{self.base_url}/flow/process-groups/{entity_id}"
            payload = {"id": entity_id, "state": status}
        else:
            # Pour les processeurs et ports
            url = f"{self.base_url}/{entity_type}/{entity_id}/run-status"
            payload = {
                "revision": self.get_revision(entity_type, entity_id),
                "state": status
            }
            
        res = requests.put(url, json=payload, headers=self.headers, verify=False)
        return res.status_code == 200

    def get_revision(self, entity_type, entity_id):
        """Récupère la version actuelle pour la mise à jour."""
        res = requests.get(f"{self.base_url}/{entity_type}/{entity_id}", headers=self.headers, verify=False)
        return res.json()['revision']

    def start_all_groups(self):
        """Démarre récursivement tous les groupes de processus à partir de la racine."""
        logger.info("Démarrage de tous les groupes de processus...")
        res = requests.get(f"{self.base_url}/process-groups/root/process-groups", headers=self.headers, verify=False)
        groups = res.json().get('processGroups', [])
        
        for pg in groups:
            pg_id = pg['id']
            pg_name = pg['component']['name']
            # On démarre le groupe lui-même
            if self.set_run_status("process-groups", pg_id, "RUNNING"):
                logger.info(f"▶️ Zone activée : {pg_name}")
            else:
                logger.warning(f"⚠️ Impossible d'activer la zone : {pg_name}")

    def run(self):
        logger.info("=== ACTIVATION DU PIPELINE VERTIFLOW ===")
        self.start_all_groups()
        logger.info("========================================")
        logger.info("🚀 Pipeline opérationnel. Vérifiez l'interface NiFi.")

if __name__ == "__main__":
    # Utilise la configuration centralisee
    config = get_config()
    activator = NiFiActivator(
        config.base_url,
        config.username,
        config.password
    )
    activator.run()