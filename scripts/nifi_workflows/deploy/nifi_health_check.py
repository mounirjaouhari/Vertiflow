#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - NiFi Health Check & Fix
================================================================================
MODULE: nifi_health_check.py
DESCRIPTION: Diagnostic et correction automatique des problèmes NiFi.

              Fonctionnalités:
              1. Vérifier la connectivité NiFi
              2. Lister les Controller Services et leur état
              3. Activer les Controller Services désactivés
              4. Lister les Processors et leur état
              5. Démarrer les Processors arrêtés
              6. Afficher les bulletins d'erreur

Usage:
    python nifi_health_check.py --check          # Diagnostic seulement
    python nifi_health_check.py --fix            # Diagnostic + Corrections
    python nifi_health_check.py --start-all      # Démarrer tous les processeurs

Développé par        : VertiFlow Core Team
================================================================================
"""

import requests
import json
import time
import urllib3
import logging
import sys
import os
import argparse

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NiFiHealthChecker:
    def __init__(self, base_url=None, username=None, password=None):
        self.base_url = (base_url or os.getenv('NIFI_BASE_URL', "https://localhost:8443/nifi-api")).rstrip('/')
        self.username = username or os.getenv('NIFI_USERNAME', "admin")
        self.password = password or os.getenv('NIFI_PASSWORD', "ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB")
        self.headers = {'Content-Type': 'application/json'}
        self.token = None
        self.root_id = None

    def connect(self):
        """Authentification à NiFi"""
        logger.info(f"Connexion à NiFi ({self.base_url})...")

        max_retries = 5
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/access/token"
                data = {'username': self.username, 'password': self.password}
                response = requests.post(url, data=data, verify=False, timeout=10)

                if response.status_code == 201:
                    self.token = response.text
                    self.headers['Authorization'] = f'Bearer {self.token}'
                    logger.info("Authentification réussie")

                    self.root_id = self.get_root_id()
                    return True
                elif response.status_code in [400, 403]:
                    logger.error(f"Échec authentification: {response.status_code}")
                    return False
                else:
                    logger.warning(f"NiFi en cours de démarrage... (Tentative {attempt+1}/{max_retries})")
            except Exception as e:
                logger.warning(f"NiFi indisponible (Tentative {attempt+1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                time.sleep(5)

        return False

    def get_root_id(self):
        """Récupère l'ID du Process Group racine"""
        res = requests.get(f"{self.base_url}/process-groups/root", headers=self.headers, verify=False)
        res.raise_for_status()
        return res.json()['id']

    def get_all_controller_services(self):
        """Récupère tous les Controller Services"""
        url = f"{self.base_url}/flow/process-groups/{self.root_id}/controller-services"
        res = requests.get(url, headers=self.headers, verify=False)
        if res.status_code == 200:
            return res.json().get('controllerServices', [])
        return []

    def get_all_process_groups(self, parent_id=None):
        """Récupère récursivement tous les Process Groups"""
        if parent_id is None:
            parent_id = self.root_id

        groups = [parent_id]
        url = f"{self.base_url}/process-groups/{parent_id}/process-groups"
        res = requests.get(url, headers=self.headers, verify=False)

        if res.status_code == 200:
            for pg in res.json().get('processGroups', []):
                groups.extend(self.get_all_process_groups(pg['id']))

        return groups

    def get_all_processors(self):
        """Récupère tous les Processors de tous les groupes"""
        all_processors = []

        for pg_id in self.get_all_process_groups():
            url = f"{self.base_url}/process-groups/{pg_id}/processors"
            res = requests.get(url, headers=self.headers, verify=False)

            if res.status_code == 200:
                processors = res.json().get('processors', [])
                for p in processors:
                    p['parentGroupId'] = pg_id
                all_processors.extend(processors)

        return all_processors

    def get_bulletins(self):
        """Récupère les bulletins d'erreur"""
        url = f"{self.base_url}/flow/bulletin-board"
        res = requests.get(url, headers=self.headers, verify=False)

        if res.status_code == 200:
            return res.json().get('bulletinBoard', {}).get('bulletins', [])
        return []

    def enable_controller_service(self, service_id):
        """Active un Controller Service"""
        try:
            # Récupérer la version actuelle
            get_res = requests.get(f"{self.base_url}/controller-services/{service_id}",
                                   headers=self.headers, verify=False)
            if get_res.status_code != 200:
                return False

            data = get_res.json()
            current_version = data['revision']['version']
            current_state = data['component']['state']

            if current_state == "ENABLED":
                return True

            # Activer le service
            payload = {
                "revision": {"version": current_version},
                "component": {
                    "id": service_id,
                    "state": "ENABLED"
                }
            }
            res = requests.put(f"{self.base_url}/controller-services/{service_id}/run-status",
                              json=payload, headers=self.headers, verify=False)

            return res.status_code == 200
        except Exception as e:
            logger.error(f"Erreur activation service {service_id}: {e}")
            return False

    def start_processor(self, processor_id):
        """Démarre un Processor"""
        try:
            # Récupérer la version actuelle
            get_res = requests.get(f"{self.base_url}/processors/{processor_id}",
                                   headers=self.headers, verify=False)
            if get_res.status_code != 200:
                return False

            data = get_res.json()
            current_version = data['revision']['version']
            current_state = data['component']['state']

            if current_state == "RUNNING":
                return True

            # Démarrer le processeur
            payload = {
                "revision": {"version": current_version},
                "component": {
                    "id": processor_id,
                    "state": "RUNNING"
                }
            }
            res = requests.put(f"{self.base_url}/processors/{processor_id}/run-status",
                              json=payload, headers=self.headers, verify=False)

            return res.status_code == 200
        except Exception as e:
            logger.error(f"Erreur démarrage processeur {processor_id}: {e}")
            return False

    def start_all_processors_in_group(self, pg_id):
        """Démarre tous les processeurs d'un groupe"""
        try:
            payload = {
                "id": pg_id,
                "state": "RUNNING"
            }
            res = requests.put(f"{self.base_url}/flow/process-groups/{pg_id}",
                              json=payload, headers=self.headers, verify=False)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Erreur démarrage groupe {pg_id}: {e}")
            return False

    def run_diagnostic(self):
        """Exécute le diagnostic complet"""
        logger.info("=" * 70)
        logger.info("DIAGNOSTIC NIFI - VERTIFLOW")
        logger.info("=" * 70)

        # 1. Controller Services
        logger.info("\n--- CONTROLLER SERVICES ---")
        services = self.get_all_controller_services()

        enabled_count = 0
        disabled_count = 0
        disabled_services = []

        for svc in services:
            comp = svc.get('component', svc)
            name = comp.get('name', 'Unknown')
            state = comp.get('state', 'UNKNOWN')
            svc_type = comp.get('type', 'Unknown').split('.')[-1]

            if state == "ENABLED":
                enabled_count += 1
                logger.info(f"  [OK] {name} ({svc_type})")
            else:
                disabled_count += 1
                disabled_services.append(svc)
                logger.warning(f"  [DISABLED] {name} ({svc_type}) - ID: {svc['id']}")

        logger.info(f"\nRésumé: {enabled_count} activés, {disabled_count} désactivés")

        # 2. Processors
        logger.info("\n--- PROCESSEURS ---")
        processors = self.get_all_processors()

        running_count = 0
        stopped_count = 0
        invalid_count = 0
        stopped_processors = []

        for proc in processors:
            comp = proc.get('component', proc)
            name = comp.get('name', 'Unknown')
            state = comp.get('state', 'UNKNOWN')
            validation = comp.get('validationStatus', 'VALID')
            proc_type = comp.get('type', 'Unknown').split('.')[-1]

            if state == "RUNNING":
                running_count += 1
            elif validation != "VALID":
                invalid_count += 1
                logger.error(f"  [INVALID] {name} ({proc_type})")
                # Afficher les erreurs de validation
                errors = comp.get('validationErrors', [])
                for err in errors[:3]:  # Limiter à 3 erreurs
                    logger.error(f"      -> {err}")
            else:
                stopped_count += 1
                stopped_processors.append(proc)
                logger.warning(f"  [STOPPED] {name} ({proc_type})")

        logger.info(f"\nRésumé: {running_count} en cours, {stopped_count} arrêtés, {invalid_count} invalides")

        # 3. Bulletins (Alertes)
        logger.info("\n--- BULLETINS D'ERREUR (derniers) ---")
        bulletins = self.get_bulletins()

        if bulletins:
            for b in bulletins[:10]:  # Derniers 10
                msg = b.get('bulletin', {}).get('message', 'No message')
                src = b.get('bulletin', {}).get('sourceId', 'Unknown')
                level = b.get('bulletin', {}).get('level', 'INFO')
                logger.warning(f"  [{level}] {msg[:80]}...")
        else:
            logger.info("  Aucun bulletin d'erreur")

        logger.info("\n" + "=" * 70)

        return {
            'disabled_services': disabled_services,
            'stopped_processors': stopped_processors,
            'stats': {
                'services_enabled': enabled_count,
                'services_disabled': disabled_count,
                'processors_running': running_count,
                'processors_stopped': stopped_count,
                'processors_invalid': invalid_count
            }
        }

    def fix_issues(self, diagnostic_results):
        """Corrige les problèmes identifiés"""
        logger.info("\n" + "=" * 70)
        logger.info("CORRECTION DES PROBLÈMES")
        logger.info("=" * 70)

        # 1. Activer les Controller Services
        disabled_services = diagnostic_results.get('disabled_services', [])
        if disabled_services:
            logger.info(f"\nActivation de {len(disabled_services)} Controller Services...")
            for svc in disabled_services:
                name = svc.get('component', {}).get('name', 'Unknown')
                if self.enable_controller_service(svc['id']):
                    logger.info(f"  [OK] {name} activé")
                else:
                    logger.error(f"  [FAIL] Impossible d'activer {name}")
                time.sleep(1)  # Attendre entre les activations

        # 2. Démarrer les Processors arrêtés
        stopped_processors = diagnostic_results.get('stopped_processors', [])
        if stopped_processors:
            logger.info(f"\nDémarrage de {len(stopped_processors)} Processors...")
            for proc in stopped_processors:
                name = proc.get('component', {}).get('name', 'Unknown')
                if self.start_processor(proc['id']):
                    logger.info(f"  [OK] {name} démarré")
                else:
                    logger.warning(f"  [SKIP] {name} - vérifiez la configuration")

        logger.info("\n" + "=" * 70)
        logger.info("CORRECTION TERMINÉE")
        logger.info("=" * 70)

    def start_all(self):
        """Démarre tous les processeurs de tous les groupes"""
        logger.info("\n" + "=" * 70)
        logger.info("DÉMARRAGE DE TOUS LES PROCESSEURS")
        logger.info("=" * 70)

        # D'abord activer tous les Controller Services
        services = self.get_all_controller_services()
        for svc in services:
            state = svc.get('component', {}).get('state', 'UNKNOWN')
            if state != "ENABLED":
                name = svc.get('component', {}).get('name', 'Unknown')
                logger.info(f"Activation du service: {name}")
                self.enable_controller_service(svc['id'])
                time.sleep(1)

        # Attendre que les services soient prêts
        time.sleep(3)

        # Démarrer les processeurs groupe par groupe
        groups = self.get_all_process_groups()
        for pg_id in groups:
            logger.info(f"Démarrage du groupe: {pg_id}")
            self.start_all_processors_in_group(pg_id)
            time.sleep(1)

        logger.info("\nTous les processeurs ont été démarrés (ou tentative effectuée)")


def main():
    parser = argparse.ArgumentParser(description="NiFi Health Check & Fix")
    parser.add_argument('--check', action='store_true', help='Diagnostic seulement')
    parser.add_argument('--fix', action='store_true', help='Diagnostic + Corrections')
    parser.add_argument('--start-all', action='store_true', help='Démarrer tous les processeurs')
    parser.add_argument('--url', default=None, help='URL NiFi API')

    args = parser.parse_args()

    # Par défaut, faire un check
    if not any([args.check, args.fix, args.start_all]):
        args.check = True

    checker = NiFiHealthChecker(base_url=args.url)

    if not checker.connect():
        logger.error("Impossible de se connecter à NiFi")
        sys.exit(1)

    if args.check or args.fix:
        results = checker.run_diagnostic()

        if args.fix:
            checker.fix_issues(results)
            # Re-run diagnostic après corrections
            time.sleep(2)
            logger.info("\n--- VÉRIFICATION POST-CORRECTION ---")
            checker.run_diagnostic()

    if args.start_all:
        checker.start_all()
        time.sleep(3)
        checker.run_diagnostic()


if __name__ == "__main__":
    main()
