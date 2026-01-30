#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Diagnose Controller Services
================================================================================
Analyse les propriétés exactes des Controller Services MongoDB et ClickHouse
pour identifier les noms corrects des propriétés.
================================================================================
"""

import requests
import json
import urllib3
import logging
import sys
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NiFiDiagnostic:
    def __init__(self):
        self.base_url = os.getenv('NIFI_BASE_URL', "https://localhost:8443/nifi-api").rstrip('/')
        self.username = os.getenv('NIFI_USERNAME', "admin")
        self.password = os.getenv('NIFI_PASSWORD', "ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB")
        self.headers = {'Content-Type': 'application/json'}
        self.token = None
        self.root_id = None

    def connect(self):
        logger.info(f"Connexion à NiFi ({self.base_url})...")
        try:
            url = f"{self.base_url}/access/token"
            data = {'username': self.username, 'password': self.password}
            response = requests.post(url, data=data, verify=False, timeout=10)
            if response.status_code == 201:
                self.token = response.text
                self.headers['Authorization'] = f'Bearer {self.token}'
                self.root_id = self.get_root_id()
                logger.info("Authentification réussie")
                return True
        except Exception as e:
            logger.error(f"Erreur: {e}")
        return False

    def get_root_id(self):
        res = requests.get(f"{self.base_url}/process-groups/root", headers=self.headers, verify=False)
        return res.json()['id']

    def get_all_controller_services_recursive(self, pg_id=None):
        if pg_id is None:
            pg_id = self.root_id
        all_services = []

        url = f"{self.base_url}/flow/process-groups/{pg_id}/controller-services"
        res = requests.get(url, headers=self.headers, verify=False)
        if res.status_code == 200:
            all_services.extend(res.json().get('controllerServices', []))

        url = f"{self.base_url}/process-groups/{pg_id}/process-groups"
        res = requests.get(url, headers=self.headers, verify=False)
        if res.status_code == 200:
            for child in res.json().get('processGroups', []):
                all_services.extend(self.get_all_controller_services_recursive(child['id']))

        return all_services

    def get_controller_service_full(self, svc_id):
        url = f"{self.base_url}/controller-services/{svc_id}"
        res = requests.get(url, headers=self.headers, verify=False)
        if res.status_code == 200:
            return res.json()
        return None

    def diagnose(self):
        logger.info("=" * 70)
        logger.info("DIAGNOSTIC DES CONTROLLER SERVICES")
        logger.info("=" * 70)

        services = self.get_all_controller_services_recursive()

        # Find MongoDB and ClickHouse services
        seen = set()
        for svc in services:
            svc_id = svc['id']
            if svc_id in seen:
                continue
            seen.add(svc_id)

            name = svc.get('component', {}).get('name', '')
            svc_type = svc.get('component', {}).get('type', '')

            if 'MongoDB' in name or 'MongoDB' in svc_type or 'ClickHouse' in name:
                logger.info(f"\n{'='*60}")
                logger.info(f"SERVICE: {name}")
                logger.info(f"TYPE: {svc_type}")
                logger.info(f"ID: {svc_id}")
                logger.info(f"STATE: {svc.get('component', {}).get('state', 'UNKNOWN')}")
                logger.info(f"VALIDATION: {svc.get('component', {}).get('validationStatus', 'UNKNOWN')}")

                # Get full details
                full = self.get_controller_service_full(svc_id)
                if full:
                    comp = full.get('component', {})

                    # Show validation errors
                    errors = comp.get('validationErrors', [])
                    if errors:
                        logger.info(f"\nVALIDATION ERRORS:")
                        for err in errors:
                            logger.info(f"  - {err}")

                    # Show current properties
                    props = comp.get('properties', {})
                    logger.info(f"\nCURRENT PROPERTIES:")
                    for key, value in props.items():
                        logger.info(f"  {key}: {value}")

                    # Show property descriptors (supported properties)
                    descriptors = comp.get('descriptors', {})
                    logger.info(f"\nSUPPORTED PROPERTIES (descriptors):")
                    for key, desc in descriptors.items():
                        display_name = desc.get('displayName', key)
                        required = desc.get('required', False)
                        default = desc.get('defaultValue', 'N/A')
                        req_marker = " [REQUIRED]" if required else ""
                        logger.info(f"  {key}{req_marker}")
                        logger.info(f"      Display: {display_name}")
                        logger.info(f"      Default: {default}")


def main():
    diag = NiFiDiagnostic()
    if not diag.connect():
        logger.error("Impossible de se connecter à NiFi")
        sys.exit(1)
    diag.diagnose()


if __name__ == "__main__":
    main()
