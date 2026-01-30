#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Configuration NiFi Centralisee
================================================================================
Ce module centralise la configuration NiFi pour tous les scripts de deploiement.
Utilise les variables d'environnement pour les credentials.

Usage:
    from nifi_config import NiFiConfig
    config = NiFiConfig()
    # Utiliser config.base_url, config.username, config.password
================================================================================
"""

import os
import sys
from pathlib import Path

# Ajouter le chemin racine pour importer les constantes du projet
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Essayer d'importer les constantes du projet si disponibles
try:
    from config.vertiflow_constants import Infrastructure
    USE_PROJECT_CONSTANTS = True
except ImportError:
    USE_PROJECT_CONSTANTS = False


class NiFiConfig:
    """Configuration centralisee pour l'API NiFi."""

    def __init__(self):
        # URL de base de l'API NiFi
        self.base_url = os.getenv(
            'NIFI_BASE_URL',
            'https://localhost:8443/nifi-api'
        ).rstrip('/')

        # Credentials - TOUJOURS utiliser les variables d'environnement
        self.username = os.getenv('NIFI_USERNAME', 'admin')

        # Le mot de passe DOIT etre defini dans .env ou variables d'environnement
        # Ne jamais hardcoder de mot de passe ici
        self.password = os.getenv('NIFI_PASSWORD')

        if not self.password:
            print("ATTENTION: NIFI_PASSWORD n'est pas defini!")
            print("Definissez-le dans .env ou comme variable d'environnement")
            print("Exemple: export NIFI_PASSWORD='votre_mot_de_passe'")
            # Utiliser une valeur par defaut pour le developpement local uniquement
            self.password = os.getenv('NIFI_DEFAULT_PASSWORD', '')

        # Headers par defaut
        self.headers = {'Content-Type': 'application/json'}

        # Timeout pour les requetes
        self.timeout = int(os.getenv('NIFI_TIMEOUT', '30'))

        # Verification SSL (desactive par defaut pour dev local)
        self.verify_ssl = os.getenv('NIFI_VERIFY_SSL', 'false').lower() == 'true'

    def get_auth_headers(self, token: str) -> dict:
        """Retourne les headers avec le token d'authentification."""
        headers = self.headers.copy()
        headers['Authorization'] = f'Bearer {token}'
        return headers

    @staticmethod
    def get_exchange_path() -> str:
        """Retourne le chemin du repertoire d'echange NiFi."""
        return os.getenv('NIFI_EXCHANGE_PATH', '/opt/nifi/nifi-current/exchange')

    @staticmethod
    def get_input_path() -> str:
        """Retourne le chemin du repertoire d'entree NiFi."""
        return os.getenv('NIFI_INPUT_PATH', '/exchange/input')

    @staticmethod
    def get_output_path() -> str:
        """Retourne le chemin du repertoire de sortie NiFi."""
        return os.getenv('NIFI_OUTPUT_PATH', '/exchange/output')


# Singleton pour reutilisation
_config_instance = None


def get_config() -> NiFiConfig:
    """Retourne l'instance singleton de la configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = NiFiConfig()
    return _config_instance


# Pour compatibilite avec les anciens scripts
NIFI_BASE_URL = os.getenv('NIFI_BASE_URL', 'https://localhost:8443/nifi-api')
NIFI_USERNAME = os.getenv('NIFI_USERNAME', 'admin')
NIFI_PASSWORD = os.getenv('NIFI_PASSWORD', '')
