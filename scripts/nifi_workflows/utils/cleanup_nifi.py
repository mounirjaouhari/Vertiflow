#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VERTIFLOW - NETTOYAGE NIFI (CLEANUP)
================================================================================
Description : Supprime tous les Process Groups, Controller Services et composants
              du Root Group pour repartir d'une feuille blanche.
================================================================================
"""

import requests
import urllib3
import logging
import os
import sys
from pathlib import Path

# Ajouter le chemin parent pour importer nifi_config
sys.path.insert(0, str(Path(__file__).parent.parent))
from nifi_config import get_config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NiFiCleaner:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.headers = {'Content-Type': 'application/json'}
        self.token = self._authenticate(username, password)
        self.headers['Authorization'] = f'Bearer {self.token}'

    def _authenticate(self, username, password):
        url = f"{self.base_url}/access/token"
        data = {'username': username, 'password': password}
        try:
            response = requests.post(url, data=data, verify=False)
            if response.status_code == 201:
                return response.text
            logger.error(f"❌ Auth failed: {response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return None

    def get_root_id(self):
        res = requests.get(f"{self.base_url}/process-groups/root", headers=self.headers, verify=False)
        return res.json()['id']

    def stop_process_group(self, pg_id):
        """Arrête tous les composants d'un groupe"""
        payload = {
            "id": pg_id,
            "state": "STOPPED",
            "disconnectedNodeAcknowledged": True
        }
        requests.put(f"{self.base_url}/flow/process-groups/{pg_id}", json=payload, headers=self.headers, verify=False)

    def delete_process_group_content(self, pg_id):
        """Supprime récursivement le contenu d'un PG"""
        # 1. Arrêter le groupe
        logger.info(f"🛑 Arrêt du groupe {pg_id}...")
        self.stop_process_group(pg_id)
        
        # 2. Récupérer le contenu
        res = requests.get(f"{self.base_url}/process-groups/{pg_id}/process-groups", headers=self.headers, verify=False)
        pgs = res.json().get('processGroups', [])
        
        # 3. Supprimer les sous-groupes
        for pg in pgs:
            sub_id = pg['id']
            self.delete_process_group_content(sub_id) # Récursif
            # Supprimer le groupe lui-même
            version = pg['revision']['version']
            logger.info(f"🗑️ Suppression du sous-groupe {pg['component']['name']} ({sub_id})...")
            requests.delete(f"{self.base_url}/process-groups/{sub_id}?version={version}&disconnectedNodeAcknowledged=true", headers=self.headers, verify=False)

        # 4. Supprimer les connexions
        res = requests.get(f"{self.base_url}/process-groups/{pg_id}/connections", headers=self.headers, verify=False)
        connections = res.json().get('connections', [])
        for conn in connections:
            c_id = conn['id']
            version = conn['revision']['version']
            logger.info(f"✂️ Suppression connexion {c_id}...")
            requests.delete(f"{self.base_url}/connections/{c_id}?version={version}&disconnectedNodeAcknowledged=true", headers=self.headers, verify=False)

        # 5. Supprimer les processeurs
        res = requests.get(f"{self.base_url}/process-groups/{pg_id}/processors", headers=self.headers, verify=False)
        processors = res.json().get('processors', [])
        for proc in processors:
            p_id = proc['id']
            version = proc['revision']['version']
            logger.info(f"🗑️ Suppression processeur {proc['component']['name']}...")
            requests.delete(f"{self.base_url}/processors/{p_id}?version={version}&disconnectedNodeAcknowledged=true", headers=self.headers, verify=False)

        # 6. Supprimer les Controller Services (Scope Group)
        res = requests.get(f"{self.base_url}/flow/process-groups/{pg_id}/controller-services", headers=self.headers, verify=False)
        services = res.json().get('controllerServices', [])
        for svc in services:
            s_id = svc['id']
            version = svc['revision']['version']
            # Désactiver d'abord
            requests.put(f"{self.base_url}/controller-services/{s_id}", 
                         json={"revision": {"version": version}, "component": {"id": s_id, "state": "DISABLED"}}, 
                         headers=self.headers, verify=False)
            # Supprimer
            # Note: Il faut récupérer la nouvelle version après désactivation
            svc_refresh = requests.get(f"{self.base_url}/controller-services/{s_id}", headers=self.headers, verify=False).json()
            new_version = svc_refresh['revision']['version']
            logger.info(f"🗑️ Suppression service {svc['component']['name']}...")
            requests.delete(f"{self.base_url}/controller-services/{s_id}?version={new_version}&disconnectedNodeAcknowledged=true", headers=self.headers, verify=False)

    def clean_root(self):
        if not self.token: return
        root_id = self.get_root_id()
        logger.info(f"🧹 Nettoyage du Root Group {root_id}...")
        self.delete_process_group_content(root_id)
        logger.info("✨ Nettoyage terminé. NiFi est vide.")

if __name__ == "__main__":
    # Utilise la configuration centralisee
    config = get_config()
    cleaner = NiFiCleaner(config.base_url, config.username, config.password)
    cleaner.clean_root()
