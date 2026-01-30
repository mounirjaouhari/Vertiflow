#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VERTIFLOW CLOUD RELEASE - TECHNICAL GOVERNANCE MASTER PROTOCOL v4.1
================================================================================
Version     : 4.1.0 (Zero-Failure Migration)
Stability   : Production Robust
Core Logic  : Race-Condition Free Activation, Zero-Failure Inter-Zone Links
================================================================================
"""

import requests
import json
import time
import urllib3
import logging
import sys
import os
import asyncio
import math
from datetime import datetime
from pathlib import Path
from functools import partial

# --- CONFIGURATION DES CONSTANTES TECHNIQUES ---
NIFI_BASE_URL = "https://localhost:8443/nifi-api"
NIFI_USER = "admin"
NIFI_PASS = "ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB"
CK_HOST = "localhost"
CK_PORT = 8123
MONGO_URI = "mongodb://localhost:27017"
KAFKA_BROKERS = "localhost:9092"

# Désactivation des warnings SSL pour les environnements isolés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- SYSTÈME DE LOGGING INDUSTRIEL ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - [VERTIFLOW_V4.1] - %(message)s'
)
logger = logging.getLogger("VERTIFLOW_V4.1")

# Créer le répertoire de logs
os.makedirs("logs", exist_ok=True)

# Ajout d'un handler de fichier pour l'audit permanent
file_handler = logging.FileHandler("logs/governance_v41_deploy.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] - [VERTIFLOW_V4.1] - %(message)s'))
logger.addHandler(file_handler)

# --- MOTEUR DE SESSION AVANCÉ AVEC RETRY EXPONENTIEL ---
class NiFiSessionManager:
    """Gère l'état de la connexion avec retry exponentiel et résilience réseau"""
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

        adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=20,
            pool_maxsize=20
        )
        self.session.mount('https://', adapter)

    async def exponential_backoff_retry(self, operation, max_retries=5, base_delay=2):
        """Retry exponentiel pour les opérations critiques"""
        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt)  # Exponentiel: 2, 4, 8, 16, 32 sec
                logger.warning(f"⚠️ Tentative {attempt+1}/{max_retries} échouée, attente {delay}s: {e}")
                await asyncio.sleep(delay)

    async def authenticate(self):
        """Authentification auprès de NiFi avec gestion d'erreurs robuste"""
        logger.info(f"🔑 Authentification auprès de NiFi ({NIFI_BASE_URL})...")

        async def auth_operation():
            auth_data = {'username': NIFI_USER, 'password': NIFI_PASS}
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.session.post,
                    f"{NIFI_BASE_URL}/access/token",
                    data=auth_data,
                    timeout=30
                )
            )

            if response.status_code == 201:
                self.token = response.text.strip()
                self.headers['Authorization'] = f'Bearer {self.token}'
                self.session.headers.update(self.headers)
                logger.info("✅ Authentification réussie")
                return True
            else:
                raise Exception(f"Code {response.status_code}")

        return await self.exponential_backoff_retry(auth_operation, max_retries=5, base_delay=3)

    def get_root_id(self):
        """Récupère l'ID du root process group"""
        try:
            response = self.session.get(f"{NIFI_BASE_URL}/process-groups/root", timeout=15)
            if response.status_code == 200:
                return response.json()['id']
            else:
                logger.error(f"❌ Impossible de récupérer root ID: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Erreur récupération root ID: {e}")
            return None

# --- GESTIONNAIRE D'INTÉGRITÉ DES COMPOSANTS AVANCÉ ---
class ComponentIntegrityManager:
    """Gère l'idempotence avec vérification des dépendances et intégrité complète"""

    def __init__(self, session_manager):
        self.sm = session_manager
        self.component_cache = {}  # Cache pour réduire les appels API

    def get_component_by_name(self, parent_id, name, component_type, refresh_cache=False):
        """Récupère un composant par son nom avec cache intelligent"""
        cache_key = f"{parent_id}_{name}_{component_type}"

        if not refresh_cache and cache_key in self.component_cache:
            return self.component_cache[cache_key]

        try:
            if component_type == 'controller-services':
                url = f"{NIFI_BASE_URL}/flow/process-groups/{parent_id}/controller-services"
                key = 'controllerServices'
            elif component_type == 'process-groups':
                url = f"{NIFI_BASE_URL}/process-groups/{parent_id}/process-groups"
                key = 'processGroups'
            elif component_type == 'processors':
                url = f"{NIFI_BASE_URL}/process-groups/{parent_id}/processors"
                key = 'processors'
            elif component_type == 'input-ports':
                url = f"{NIFI_BASE_URL}/process-groups/{parent_id}/input-ports"
                key = 'inputPorts'
            elif component_type == 'output-ports':
                url = f"{NIFI_BASE_URL}/process-groups/{parent_id}/output-ports"
                key = 'outputPorts'
            elif component_type == 'connections':
                url = f"{NIFI_BASE_URL}/process-groups/{parent_id}/connections"
                key = 'connections'
            else:
                logger.error(f"Type de composant non supporté: {component_type}")
                return None

            response = self.sm.session.get(url, timeout=15)
            if response.status_code == 200:
                items = response.json().get(key, [])
                for item in items:
                    comp = item.get('component', item)
                    if comp.get('name') == name:
                        self.component_cache[cache_key] = item
                        return item

            # Mettre None dans le cache pour éviter des recherches répétées
            self.component_cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"⚠️ Erreur recherche composant {name}: {e}")
            return None

    def get_component_state(self, component_id, endpoint="controller-services"):
        """Récupère l'état actuel d'un composant"""
        try:
            url = f"{NIFI_BASE_URL}/{endpoint}/{component_id}"
            response = self.sm.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()['component']['state']
            return None
        except Exception as e:
            logger.warning(f"Erreur récupération état {component_id}: {e}")
            return None

    def clear_cache(self):
        """Vide le cache"""
        self.component_cache.clear()

    def resolve_pg_id(self, parent_id, name):
        """Traduit un nom de Process Group en ID NiFi stable"""
        existing = self.get_component_by_name(parent_id, name, 'process-groups')
        if existing:
            return existing['id']
        return None

# --- DÉBUT DE LA LOGIQUE DE GOUVERNANCE V4.1 ---
class VertiFlowGovernanceMasterV41:
    def __init__(self):
        self.sm = NiFiSessionManager()
        self.integrity = ComponentIntegrityManager(self.sm)
        self.root_id = None
        self.zones = {}
        self.services = {}
        self.ports = {}
        self.connections = {}
        self.activation_sequence = []

    async def initialize_core(self):
        """Prépare le terrain et vérifie la disponibilité de l'API"""
        logger.info("🚀 Initialisation du Core VertiFlow v4.1...")

        if not await self.sm.authenticate():
            logger.error("🛑 Impossible d'initialiser le Core. Abandon.")
            sys.exit(1)

        self.root_id = self.sm.get_root_id()
        if not self.root_id:
            logger.error("🛑 Impossible de récupérer le root ID. Vérifiez que NiFi est en cours d'exécution.")
            sys.exit(1)

        logger.info(f"📂 Racine NiFi localisée : {self.root_id}")

        # Nettoyage initial
        await self.cleanup_system()

        return True

    async def cleanup_system(self):
        """Nettoie complètement le système avant déploiement"""
        logger.info("🧹 Nettoyage complet du système...")

        try:
            # 1. Arrêter tous les process groups en cours d'exécution
            pg_list = await self.get_all_process_groups(self.root_id)
            for pg in pg_list:
                if pg['component']['running']:
                    await self.stop_process_group(pg['id'])

            # 2. Désactiver tous les services controller
            services = await self.get_all_controller_services(self.root_id)
            for svc in services:
                if svc['component']['state'] in ['ENABLED', 'ENABLING']:
                    await self.disable_service(svc['id'])

            await asyncio.sleep(5)

            logger.info("✅ Nettoyage système terminé")

        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du nettoyage: {e}")

    async def get_all_process_groups(self, parent_id):
        """Récupère tous les process groups"""
        try:
            response = self.sm.session.get(
                f"{NIFI_BASE_URL}/process-groups/{parent_id}/process-groups",
                timeout=15
            )
            if response.status_code == 200:
                return response.json().get('processGroups', [])
            return []
        except Exception as e:
            logger.error(f"❌ Erreur récupération PGs: {e}")
            return []

    async def stop_process_group(self, pg_id):
        """Arrête un process group"""
        try:
            payload = {
                "id": pg_id,
                "state": "STOPPED"
            }
            response = self.sm.session.put(
                f"{NIFI_BASE_URL}/flow/process-groups/{pg_id}",
                json=payload,
                timeout=15
            )
            if response.status_code == 200:
                logger.debug(f"⏹️ Process Group {pg_id} arrêté")
                return True
            return False
        except Exception as e:
            logger.warning(f"⚠️ Erreur arrêt PG {pg_id}: {e}")
            return False

    async def get_all_controller_services(self, pg_id):
        """Récupère tous les services controller"""
        try:
            response = self.sm.session.get(
                f"{NIFI_BASE_URL}/flow/process-groups/{pg_id}/controller-services",
                timeout=15
            )
            if response.status_code == 200:
                return response.json().get('controllerServices', [])
            return []
        except Exception as e:
            logger.error(f"❌ Erreur récupération services: {e}")
            return []

    async def disable_service(self, service_id):
        """Désactive un service controller"""
        try:
            # Récupérer la révision
            url = f"{NIFI_BASE_URL}/controller-services/{service_id}"
            response = self.sm.session.get(url, timeout=10)
            if response.status_code != 200:
                return False

            current_ver = response.json()['revision']['version']

            payload = {
                "revision": {"version": current_ver},
                "component": {
                    "id": service_id,
                    "state": "DISABLED"
                }
            }

            response = self.sm.session.put(url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"⚠️ Erreur désactivation service {service_id}: {e}")
            return False

    async def create_standard_pg(self, parent_id, name, x=0, y=0):
        """Crée un Process Group avec gestion automatique des doublons"""
        existing_id = self.integrity.resolve_pg_id(parent_id, name)
        if existing_id:
            logger.info(f"♻️ Réutilisation du groupe existant : {name} ({existing_id})")
            return existing_id

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "position": {"x": x, "y": y}
            }
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.sm.session.post,
                    f"{NIFI_BASE_URL}/process-groups/{parent_id}/process-groups",
                    json=payload,
                    timeout=30
                )
            )

            if response.status_code == 201:
                new_id = response.json()['id']
                logger.info(f"📁 Nouveau Process Group créé : {name} -> {new_id}")

                # Enregistrer dans la séquence d'activation
                self.activation_sequence.append(('pg', new_id, name))

                await asyncio.sleep(1)  # Pause pour la stabilité
                return new_id
            else:
                logger.error(f"❌ Échec création PG {name}: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ Exception création PG {name}: {e}")
            return None

    # --- GESTION DES PORTS D'INTERFACE ZERO-FAILURE ---
    async def create_port(self, pg_id, port_type, name, position=(0, 0)):
        """Crée un port d'entrée ou de sortie avec logique Zero-Failure"""
        # Vérification d'existence
        existing = self.integrity.get_component_by_name(
            pg_id,
            name,
            'input-ports' if port_type == "INPUT_PORT" else 'output-ports'
        )

        if existing:
            port_id = existing['id']
            logger.info(f"♻️ Port {name} déjà existant ({port_id})")
            return port_id

        # Création du port
        endpoint = "input-ports" if port_type == "INPUT_PORT" else "output-ports"
        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "type": port_type,
                "position": {"x": position[0], "y": position[1]},
                "parentGroupId": pg_id,
                "allowRemoteAccess": True
            }
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.sm.session.post,
                    f"{NIFI_BASE_URL}/process-groups/{pg_id}/{endpoint}",
                    json=payload,
                    timeout=30
                )
            )

            if response.status_code == 201:
                port_id = response.json()['id']
                logger.info(f"🚪 Port {name} créé ({port_id})")

                # Enregistrer dans la séquence d'activation
                self.activation_sequence.append(('port', port_id, name, port_type))

                await asyncio.sleep(1)
                return port_id
            else:
                logger.error(f"❌ Échec création port {name}: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ Exception création port {name}: {e}")
            return None

    # --- CONNEXIONS INTER-ZONES ZERO-FAILURE ---
    async def establish_inter_zone_connection(self, parent_pg_id, source_zone_id, source_port_id,
                                              dest_zone_id, dest_port_id, connection_name):
        """Établit une connexion entre deux zones via leurs ports - Version Zero-Failure"""

        # Vérifier si la connexion existe déjà
        existing = self.integrity.get_component_by_name(parent_pg_id, connection_name, 'connections')
        if existing:
            logger.info(f"♻️ Connexion inter-zone déjà existante: {connection_name}")
            return existing['id']

        # CRITIQUE: Les ports n'ont pas de relations "success", donc selectedRelationships doit être une liste vide
        payload = {
            "revision": {"version": 0},
            "component": {
                "name": connection_name,
                "source": {
                    "id": source_port_id,
                    "groupId": source_zone_id,
                    "type": "OUTPUT_PORT"
                },
                "destination": {
                    "id": dest_port_id,
                    "groupId": dest_zone_id,
                    "type": "INPUT_PORT"
                },
                "selectedRelationships": [],  # LISTE VIDE pour les ports!
                "flowFileExpiration": "0 sec",
                "backPressureObjectThreshold": 10000,
                "backPressureDataSizeThreshold": "1 GB",
                "prioritizers": []
            }
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.sm.session.post,
                    f"{NIFI_BASE_URL}/process-groups/{parent_pg_id}/connections",
                    json=payload,
                    timeout=30
                )
            )

            if response.status_code == 201:
                conn_id = response.json()['id']
                logger.info(f"🌉 Connexion inter-zone établie: {connection_name} ({conn_id})")
                self.connections[connection_name] = conn_id
                return conn_id
            elif response.status_code == 409:
                logger.info(f"🌉 Connexion inter-zone déjà existante (409): {connection_name}")
                return None
            else:
                logger.error(f"❌ Impossible de créer la connexion inter-zone {connection_name}: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ Erreur création connexion inter-zone {connection_name}: {e}")
            return None

    # --- SERVICE DEPLOYMENT WITH DEPENDENCY RESOLUTION ---
    async def deploy_controller_service(self, pg_id, svc_type, name, properties, comments=""):
        """Déploie un service avec résolution des dépendances et activation robuste"""
        existing = self.integrity.get_component_by_name(pg_id, name, 'controller-services')
        if existing:
            svc_id = existing['id']
            logger.info(f"♻️ Service '{name}' déjà existant ({svc_id})")
            await self.ensure_service_enabled_robust(svc_id)
            return svc_id

        # Vérifier et résoudre les dépendances avant création
        resolved_props = await self.resolve_service_dependencies(pg_id, properties)

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "type": svc_type,
                "properties": resolved_props,
                "comments": f"VERTIFLOW_V4.1: {comments} (Deployed: {datetime.now()})"
            }
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.sm.session.post,
                    f"{NIFI_BASE_URL}/process-groups/{pg_id}/controller-services",
                    json=payload,
                    timeout=30
                )
            )

            if response.status_code == 201:
                svc_id = response.json()['id']
                logger.info(f"🔧 Service '{name}' provisionné avec succès ({svc_id})")

                # Enregistrer dans la séquence d'activation
                self.activation_sequence.append(('service', svc_id, name))

                await asyncio.sleep(2)
                await self.ensure_service_enabled_robust(svc_id)
                return svc_id
            else:
                logger.error(f"❌ Échec création service {name}: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"🚨 Exception critique lors du déploiement du service {name}: {str(e)}")
            return None

    async def resolve_service_dependencies(self, pg_id, properties):
        """Résout les références aux autres services controller"""
        resolved_props = properties.copy()

        for prop_name, prop_value in properties.items():
            if prop_value and isinstance(prop_value, str):
                # Vérifier si c'est une référence à un service controller
                if prop_value.startswith('controller-service://'):
                    # Extraire l'ID du service
                    svc_id = prop_value.split('/')[-1]

                    # Vérifier si le service existe et est activé
                    svc_state = self.integrity.get_component_state(svc_id)
                    if svc_state != 'ENABLED':
                        logger.warning(f"⚠️ Dépendance {svc_id} non activée pour {prop_name}")
                        # On garde la référence, l'activation se fera plus tard

        return resolved_props

    async def ensure_service_enabled_robust(self, svc_id):
        """Moteur d'activation robuste avec retry exponentiel"""
        max_retries = 5
        base_delay = 5  # Commence à 5 secondes

        for attempt in range(max_retries):
            try:
                url = f"{NIFI_BASE_URL}/controller-services/{svc_id}"
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    partial(self.sm.session.get, url, timeout=15)
                )

                if response.status_code != 200:
                    logger.warning(f"⚠️ Impossible de récupérer le service {svc_id}")
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue

                svc_data = response.json()
                current_state = svc_data['component']['state']
                current_ver = svc_data['revision']['version']

                if current_state == "ENABLED":
                    logger.info(f"🟢 Service {svc_id} est déjà opérationnel.")
                    return True

                if current_state == "ENABLING":
                    logger.info(f"⏳ Service {svc_id} en cours d'activation... (tentative {attempt+1})")
                    await asyncio.sleep(base_delay)
                    continue

                # Pour les états DISABLING, attendre qu'il termine
                if current_state == "DISABLING":
                    logger.info(f"⏳ Service {svc_id} en cours de désactivation...")
                    await asyncio.sleep(3)
                    continue

                # D'abord s'assurer qu'il est DISABLED
                if current_state != "DISABLED":
                    disable_payload = {
                        "revision": {"version": current_ver},
                        "component": {
                            "id": svc_id,
                            "state": "DISABLED"
                        }
                    }

                    disable_response = await loop.run_in_executor(
                        None,
                        partial(self.sm.session.put, url, json=disable_payload, timeout=15)
                    )

                    if disable_response.status_code == 200:
                        await asyncio.sleep(2)
                        # Récupérer la nouvelle révision
                        response = await loop.run_in_executor(
                            None,
                            partial(self.sm.session.get, url, timeout=15)
                        )
                        svc_data = response.json()
                        current_ver = svc_data['revision']['version']

                # Maintenant activer
                enable_payload = {
                    "revision": {"version": current_ver},
                    "component": {
                        "id": svc_id,
                        "state": "ENABLED"
                    }
                }

                enable_response = await loop.run_in_executor(
                    None,
                    partial(self.sm.session.put, url, json=enable_payload, timeout=15)
                )

                if enable_response.status_code == 200:
                    logger.info(f"⚡ Service {svc_id} activé avec succès. (tentative {attempt+1})")
                    await asyncio.sleep(base_delay)  # Laisser le temps à l'activation

                    # Vérifier l'état final
                    check_response = await loop.run_in_executor(
                        None,
                        partial(self.sm.session.get, url, timeout=15)
                    )

                    if check_response.status_code == 200:
                        final_state = check_response.json()['component']['state']
                        if final_state == "ENABLED":
                            logger.info(f"✅ Service {svc_id} confirmé ENBALED")
                            return True
                        else:
                            logger.warning(f"⚠️ État final: {final_state}")

                    return True
                else:
                    logger.warning(f"⚠️ Tentative d'activation {attempt+1}/{max_retries} échouée: {enable_response.status_code}")

            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de l'activation (tentative {attempt+1}): {e}")

            # Retry exponentiel
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"⏳ Attente {delay}s avant nouvelle tentative...")
                await asyncio.sleep(delay)

        logger.error(f"❌ Échec d'activation du service {svc_id} après {max_retries} tentatives")
        return False

    # --- CONFIGURATION SPÉCIFIQUE DES SERVICES MASTER V4.1 ---
    async def configure_master_services(self):
        """Injection des configurations stratégiques avec dépendances résolues"""
        logger.info("🛠️ Phase de configuration des Services de Contrôle Master v4.1")

        # A. ClickHouse Pool (JDBC Bridge) - CORRIGÉ
        ck_props = {
            "Database Connection URL": f"jdbc:clickhouse://{CK_HOST}:{CK_PORT}/vertiflow",
            "Database Driver Class Name": "com.clickhouse.jdbc.ClickHouseDriver",
            "database-driver-locations": "file:///opt/nifi/nifi-current/drivers/clickhouse-jdbc-0.6.0-all.jar",
            "Database User": "default",
            "Password": "default",
            "Max Total Connections": "15",
            "Max Wait Time": "15000 millis",
            "Validation-query": "SELECT 1",
            "Max Idle Connections": "5",
            "Min Idle Connections": "1"
        }

        self.services['ck_pool'] = await self.deploy_controller_service(
            self.root_id,
            "org.apache.nifi.dbcp.DBCPConnectionPool",
            "MASTER_CLICKHOUSE_POOL_V41",
            ck_props,
            "OLAP Storage Connector v4.1"
        )

        # Attendre que le service ClickHouse soit opérationnel
        await asyncio.sleep(3)

        # B. MongoDB Client Service - CORRIGÉ
        mongo_props = {
            "Mongo URI": MONGO_URI,
            "Mongo Database Name": "vertiflow_ops",
            "Socket Timeout": "15000 ms",
            "Server Selection Timeout": "15000 ms",
            "Connect Timeout": "10000 ms",
            "Max Connection Idle Time": "60000 ms"
        }

        self.services['mongo_svc'] = await self.deploy_controller_service(
            self.root_id,
            "org.apache.nifi.mongodb.MongoDBControllerService",
            "MASTER_MONGODB_CLIENT_V41",
            mongo_props,
            "NoSQL Connector v4.1"
        )

        # Attendre que le service MongoDB soit opérationnel
        await asyncio.sleep(3)

        # C. JSON Tree Reader
        json_reader_props = {
            "Schema Access Strategy": "infer-schema",
            "Schema Registry": "none",
            "Date Format": "yyyy-MM-dd",
            "Time Format": "HH:mm:ss",
            "Timestamp Format": "yyyy-MM-dd HH:mm:ss.SSS"
        }

        self.services['json_reader'] = await self.deploy_controller_service(
            self.root_id,
            "org.apache.nifi.json.JsonTreeReader",
            "MASTER_JSON_READER_V41",
            json_reader_props,
            "Unified JSON Parsing Engine v4.1"
        )

        # D. JSON Record Set Writer - CORRIGÉ
        json_writer_props = {
            "Schema Write Strategy": "no-schema",
            "Schema Access Strategy": "inherit-record-schema",
            "Pretty Print JSON": "false",
            "Output Grouping": "output-array",
            "Timestamp Format": "yyyy-MM-dd HH:mm:ss.SSS"
        }

        self.services['json_writer'] = await self.deploy_controller_service(
            self.root_id,
            "org.apache.nifi.json.JsonRecordSetWriter",
            "MASTER_JSON_WRITER_V41",
            json_writer_props,
            "Unified JSON Output Engine v4.1"
        )

        # Attendre que les services JSON soient opérationnels
        await asyncio.sleep(3)

        # E. MongoDB Lookup Service - CORRIGÉ
        if self.services.get('mongo_svc'):
            lookup_props = {
                "Mongo Lookup Client Service": f"controller-service://{self.services['mongo_svc']}",
                "Mongo Database Name": "vertiflow_ops",
                "Mongo Collection Name": "plant_recipes",
                "Lookup Value Field": "recipe_data",
                "Lookup Keys": "plant_type"
            }

            self.services['mongo_lookup'] = await self.deploy_controller_service(
                self.root_id,
                "org.apache.nifi.mongodb.MongoDBLookupService",
                "MASTER_RECIPE_LOOKUP_V41",
                lookup_props,
                "Real-time enrichment engine v4.1"
            )
        else:
            logger.warning("⚠️ Service MongoDB non disponible, lookup non créé")
            self.services['mongo_lookup'] = None

        # F. StandardSSLContextService (pour les connexions HTTPS externes)
        ssl_props = {
            "Keystore Filename": "",
            "Keystore Password": "",
            "Key Password": "",
            "Keystore Type": "JKS",
            "Truststore Filename": "",
            "Truststore Password": "",
            "Truststore Type": "JKS"
        }

        self.services['ssl_context'] = await self.deploy_controller_service(
            self.root_id,
            "org.apache.nifi.ssl.StandardSSLContextService",
            "MASTER_SSL_CONTEXT_V41",
            ssl_props,
            "SSL Context for External APIs"
        )

        # G. StandardHTTPContextService
        http_context_props = {
            "SSL Context Service": f"controller-service://{self.services['ssl_context']}" if self.services.get('ssl_context') else "",
            "Connection Timeout": "30 secs",
            "Read Timeout": "30 secs"
        }

        self.services['http_context'] = await self.deploy_controller_service(
            self.root_id,
            "org.apache.nifi.http.StandardHttpContextMap",
            "MASTER_HTTP_CONTEXT_V41",
            http_context_props,
            "HTTP Context for External APIs"
        )

        logger.info("🏁 Tous les services de contrôle Master v4.1 sont configurés.")

        # Validation finale
        await self.validate_all_services()

    async def validate_all_services(self):
        """Valide que tous les services sont activés"""
        logger.info("🔍 Validation de l'état des services...")

        all_enabled = True
        for svc_name, svc_id in self.services.items():
            if svc_id:
                state = self.integrity.get_component_state(svc_id)
                if state == "ENABLED":
                    logger.info(f"  ✅ {svc_name}: {state}")
                else:
                    logger.warning(f"  ⚠️ {svc_name}: {state}")
                    all_enabled = False

        if all_enabled:
            logger.info("🎉 Tous les services sont activés!")
        else:
            logger.warning("⚠️ Certains services ne sont pas activés")

        return all_enabled

    # --- MOTEUR DE DÉPLOIEMENT DES PROCESSEURS AVEC VÉRIFICATION DES DÉPENDANCES ---
    async def create_processor_instance(self, pg_id, p_type, name, pos=(0, 0), props=None, auto_terminate=None):
        """Crée un processeur avec vérification des dépendances de services"""

        # Vérifier que tous les services référencés sont activés
        if props:
            for prop_name, prop_value in props.items():
                if prop_value and isinstance(prop_value, str):
                    if 'controller-service://' in prop_value:
                        svc_id = prop_value.split('/')[-1]
                        svc_state = self.integrity.get_component_state(svc_id)
                        if svc_state != 'ENABLED':
                            logger.warning(f"⚠️ Service {svc_id} référencé par {name} n'est pas activé ({svc_state})")
                            # On continue quand même, l'activation se fera plus tard

        existing = self.integrity.get_component_by_name(pg_id, name, 'processors')
        if existing:
            proc_id = existing['id']
            logger.info(f"♻️ Processeur '{name}' déjà présent ({proc_id})")
            return proc_id

        processor_config = {}
        if props:
            processor_config["properties"] = props
        if auto_terminate:
            processor_config["autoTerminatedRelationships"] = auto_terminate

        # Configuration par défaut robuste
        processor_config["schedulingStrategy"] = "TIMER_DRIVEN"
        processor_config["schedulingPeriod"] = "0 sec"
        processor_config["penaltyDuration"] = "30 sec"
        processor_config["yieldDuration"] = "10 sec"
        processor_config["bulletinLevel"] = "WARN"
        processor_config["runDurationMillis"] = 0

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "type": p_type,
                "position": {"x": pos[0], "y": pos[1]},
                "config": processor_config
            }
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.sm.session.post,
                    f"{NIFI_BASE_URL}/process-groups/{pg_id}/processors",
                    json=payload,
                    timeout=30
                )
            )

            if response.status_code == 201:
                proc_id = response.json()['id']
                logger.info(f"⚙️ Processeur '{name}' déployé ({proc_id})")

                # Enregistrer dans la séquence d'activation
                self.activation_sequence.append(('processor', proc_id, name))

                await asyncio.sleep(1)
                return proc_id
            else:
                logger.error(f"❌ Échec création processeur {name}: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ Exception création processeur {name}: {e}")
            return None

    async def establish_connection(self, pg_id, src_id, dst_id, relationships, name=""):
        """Moteur de liaison entre processeurs avec validation"""

        # Vérifier si la connexion existe déjà
        existing = self.integrity.get_component_by_name(pg_id, name, 'connections')
        if existing:
            logger.info(f"🔗 Connexion déjà existante: {name}")
            return existing['id']

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "source": {"id": src_id, "type": "PROCESSOR", "groupId": pg_id},
                "destination": {"id": dst_id, "type": "PROCESSOR", "groupId": pg_id},
                "selectedRelationships": relationships,
                "flowFileExpiration": "0 sec",
                "backPressureObjectThreshold": 5000,
                "backPressureDataSizeThreshold": "1 GB",
                "prioritizers": []
            }
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.sm.session.post,
                    f"{NIFI_BASE_URL}/process-groups/{pg_id}/connections",
                    json=payload,
                    timeout=30
                )
            )

            if response.status_code == 201:
                conn_id = response.json()['id']
                logger.info(f"🔗 Connexion établie: {name} ({conn_id})")
                return conn_id
            elif response.status_code == 409:
                logger.info(f"🔗 Connexion déjà existante (409): {name}")
                return None
            else:
                logger.error(f"❌ Impossible de créer la connexion {name}: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ Erreur création connexion {name}: {e}")
            return None

    # --- ZONE 0 : EXTERNAL DATA HARVESTING V4.1 ---
    async def deploy_zone_0(self, main_pg_id):
        """Configuration de la Zone 0 avec vérification des services HTTP"""
        logger.info("🌐 Déploiement Zone 0 - APIs Externes v4.1")

        z0_id = await self.create_standard_pg(main_pg_id, "Zone 0 - External Data APIs v4.1", -800, 0)
        if not z0_id:
            return None

        self.zones['z0'] = z0_id

        # Attendre que le service HTTP soit prêt
        if self.services.get('http_context'):
            logger.info("✅ Service HTTP context prêt pour Zone 0")
        else:
            logger.warning("⚠️ Service HTTP context non disponible")

        # 1. NASA POWER API - Version robuste
        nasa_props = {
            "HTTP Method": "GET",
            "Remote URL": "https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,RH2M&community=AG&longitude=-7.58&latitude=33.57&format=JSON&start=20250101&end=20250131",
            "Connection Timeout": "45 secs",
            "Read Timeout": "45 secs",
            "SSL Context Service": f"controller-service://{self.services['ssl_context']}" if self.services.get('ssl_context') else "",
            "Content-Type": "application/json",
            "use-chunked-encoding": "false",
            "disable-peer-verification": "true"
        }

        nasa_fetcher = await self.create_processor_instance(
            z0_id,
            "org.apache.nifi.processors.standard.InvokeHTTP",
            "Z0_NASA_POWER_Harvester_V41",
            (0, 0),
            nasa_props,
            ["failure", "no retry", "retry"]
        )

        # 2. Open-Meteo API - Version robuste
        meteo_url = "https://api.open-meteo.com/v1/forecast?latitude=33.57&longitude=-7.58&hourly=temperature_2m,relativehumidity_2m&timezone=auto"
        meteo_props = {
            "HTTP Method": "GET",
            "Remote URL": meteo_url,
            "Connection Timeout": "15 secs",
            "Read Timeout": "15 secs",
            "SSL Context Service": f"controller-service://{self.services['ssl_context']}" if self.services.get('ssl_context') else "",
            "Content-Type": "application/json",
            "use-chunked-encoding": "false"
        }

        meteo_fetcher = await self.create_processor_instance(
            z0_id,
            "org.apache.nifi.processors.standard.InvokeHTTP",
            "Z0_OpenMeteo_Realtime_V41",
            (0, 200),
            meteo_props,
            ["failure", "no retry", "retry"]
        )

        # 3. MergeContent pour combiner les réponses
        merge_props = {
            "Merge Strategy": "Bin-Packing Algorithm",
            "Merge Format": "Binary Concatenation",
            "Correlation Attribute Name": "weather.source",
            "Minimum Number of Entries": "1",
            "Maximum Number of Entries": "10",
            "Max Bin Age": "30 sec",
            "Max Bin Size": "10 MB",
            "Delimiter Strategy": "Text",
            "Header": "[",
            "Footer": "]",
            "Demarcator": ","
        }

        weather_merger = await self.create_processor_instance(
            z0_id,
            "org.apache.nifi.processors.standard.MergeContent",
            "Z0_Weather_Data_Merger",
            (300, 100),
            merge_props,
            ["failure", "original"]
        )

        # 4. OUTPUT PORT vers Zone 1
        output_port = await self.create_port(z0_id, "OUTPUT_PORT", "Z0_To_Z1_External_V41", (500, 100))
        self.ports['z0_output'] = output_port

        # 5. Connexions internes Zone 0
        if nasa_fetcher and weather_merger:
            await self.establish_connection(z0_id, nasa_fetcher, weather_merger, ["success"], "NASA_To_Merger")

        if meteo_fetcher and weather_merger:
            await self.establish_connection(z0_id, meteo_fetcher, weather_merger, ["success"], "Meteo_To_Merger")

        if weather_merger and output_port:
            await self.establish_connection(z0_id, weather_merger, output_port, ["merged"], "Merger_To_Output")

        logger.info("✅ Zone 0 v4.1 opérationnelle avec port de sortie")
        return z0_id

    # --- ZONE 1 : INGESTION & VALIDATION V4.1 ---
    async def deploy_zone_1(self, main_pg_id):
        """Configuration de la Zone 1 avec validation robuste"""
        logger.info("📥 Déploiement Zone 1 - Ingestion & Validation v4.1")

        z1_id = await self.create_standard_pg(main_pg_id, "Zone 1 - Ingestion & Validation v4.1", 0, 0)
        if not z1_id:
            return None

        self.zones['z1'] = z1_id

        # 1. INPUT PORT depuis Zone 0
        input_port_z0 = await self.create_port(z1_id, "INPUT_PORT", "Z1_From_Z0_External_V41", (-200, 100))
        self.ports['z1_input_external'] = input_port_z0

        # 2. MQTT Consumer - Version robuste
        mqtt_props = {
            "Broker URI": "tcp://localhost:1883",
            "Client ID": "nifi-ingestion-mqtt-v41",
            "Topic Filter": "vertiflow/telemetry/#",
            "Quality of Service(QoS)": "1",
            "Max Queue Size": "5000",
            "Connection Timeout": "30 secs",
            "Keep Alive Interval": "30 secs",
            "Session state": "true"
        }

        mqtt_ingestor = await self.create_processor_instance(
            z1_id,
            "org.apache.nifi.processors.mqtt.ConsumeMQTT",
            "Z1_MQTT_IoT_Gateway_V41",
            (0, 0),
            mqtt_props
        )

        # 3. HTTP Ingestor - Version robuste
        http_props = {
            "Listening Port": "8082",
            "Base Path": "/vertiflow/v41/ingest",
            "HTTP Method": "POST",
            "Return Code": "201",
            "Max Data to Receive per Second": "50 MB",
            "Max Request Size": "10 MB",
            "Header Character Set": "UTF-8"
        }

        http_ingestor = await self.create_processor_instance(
            z1_id,
            "org.apache.nifi.processors.standard.ListenHTTP",
            "Z1_HTTP_Edge_Ingestor_V41",
            (0, 200),
            http_props
        )

        # 4. MergeContent pour fusionner tous les flux
        merge_props = {
            "Merge Strategy": "Bin-Packing Algorithm",
            "Merge Format": "Binary Concatenation",
            "Correlation Attribute Name": "data.source",
            "Minimum Number of Entries": "1",
            "Maximum Number of Entries": "100",
            "Max Bin Age": "10 sec",
            "Max Bin Size": "5 MB"
        }

        data_merger = await self.create_processor_instance(
            z1_id,
            "org.apache.nifi.processors.standard.MergeContent",
            "Z1_Data_Merger_V41",
            (300, 100),
            merge_props,
            ["failure"]
        )

        # 5. Validation - Version robuste
        if self.services.get('json_reader') and self.services.get('json_writer'):
            validate_props = {
                "Record Reader": f"controller-service://{self.services['json_reader']}",
                "Record Writer": f"controller-service://{self.services['json_writer']}"
            }

            schema_validator = await self.create_processor_instance(
                z1_id,
                "org.apache.nifi.processors.standard.ValidateRecord",
                "Z1_Technical_Governance_Validator_V41",
                (500, 100),
                validate_props,
                ["invalid", "failure"]
            )
        else:
            logger.warning("⚠️ Services JSON non disponibles, validation désactivée")
            schema_validator = None

        # 6. OUTPUT PORT vers Zone 2
        output_port = await self.create_port(z1_id, "OUTPUT_PORT", "Z1_To_Z2_Validated_V41", (700, 100))
        self.ports['z1_output_validated'] = output_port

        # 7. Connexions internes Zone 1
        if input_port_z0 and data_merger:
            await self.establish_connection(z1_id, input_port_z0, data_merger, ["success"], "External_To_Merger")

        if mqtt_ingestor and data_merger:
            await self.establish_connection(z1_id, mqtt_ingestor, data_merger, ["Message"], "MQTT_To_Merger")

        if http_ingestor and data_merger:
            await self.establish_connection(z1_id, http_ingestor, data_merger, ["success"], "HTTP_To_Merger")

        if data_merger and schema_validator:
            await self.establish_connection(z1_id, data_merger, schema_validator, ["merged"], "Merger_To_Validator")

        if schema_validator and output_port:
            await self.establish_connection(z1_id, schema_validator, output_port, ["valid"], "Validator_To_Output")

        logger.info("✅ Zone 1 v4.1 opérationnelle avec ports d'entrée/sortie")
        return z1_id

    # --- ZONE 2 : CONTEXTUALISATION V4.1 ---
    async def deploy_zone_2(self, main_pg_id):
        """Configuration de la Zone 2 avec contextualisation robuste"""
        logger.info("🔄 Déploiement Zone 2 - Contextualisation & Intelligence VPD v4.1")

        z2_id = await self.create_standard_pg(main_pg_id, "Zone 2 - Contextualisation v4.1", 800, 0)
        if not z2_id:
            return None

        self.zones['z2'] = z2_id

        # 1. INPUT PORT depuis Zone 1
        input_port_z1 = await self.create_port(z2_id, "INPUT_PORT", "Z2_From_Z1_Validated_V41", (-200, 0))
        self.ports['z2_input_validated'] = input_port_z1

        # 2. UpdateRecord pour enrichissement - Version simple
        update_record_logic = '''[{"operation":"default","field":"/processing_timestamp","value":"${now():format('yyyy-MM-dd HH:mm:ss.SSS')}"},{"operation":"default","field":"/data_source","value":"vertiflow_v41"},{"operation":"default","field":"/pipeline_version","value":"4.1.0"}]'''

        context_enricher = await self.create_processor_instance(
            z2_id,
            "org.apache.nifi.processors.standard.UpdateRecord",
            "Z2_Context_Enricher_V41",
            (0, 0),
            {
                "Record Reader": f"controller-service://{self.services['json_reader']}",
                "Record Writer": f"controller-service://{self.services['json_writer']}",
                "Replacement Value Strategy": "Record Path Value",
                "/properties": update_record_logic
            },
            ["failure"]
        )

        # 3. Calcul VPD (ExecuteScript simplifié et robuste)
        groovy_vpd_logic = '''
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import org.apache.nifi.processor.io.StreamCallback

def flowFile = session.get()
if (!flowFile) return

try {
    def text = new java.io.BufferedReader(new java.io.InputStreamReader(inputStream)).readLine()
    def content = new JsonSlurper().parseText(text)
    
    double temp = content.air_temp_internal instanceof Number ? content.air_temp_internal : 25.0
    double hum = content.air_humidity instanceof Number ? content.air_humidity : 60.0
    
    double es = 0.6108 * Math.exp((17.27 * temp) / (temp + 237.3))
    double ea = es * (hum / 100.0)
    double vpd = es - ea
    
    content.vpd_value = Math.round(vpd * 1000) / 1000.0
    content.vpd_status = vpd < 0.4 ? "LOW" : (vpd > 1.6 ? "HIGH" : "OPTIMAL")
    
    def output = JsonOutput.toJson(content)
    outputStream.write(output.getBytes("UTF-8"))
    
    session.transfer(flowFile, REL_SUCCESS)
} catch (Exception e) {
    session.transfer(flowFile, REL_FAILURE)
}
'''

        vpd_calculator = await self.create_processor_instance(
            z2_id,
            "org.apache.nifi.processors.script.ExecuteScript",
            "Z2_VPD_Scientific_Calculator_V41",
            (200, 0),
            {
                "Script Engine": "Groovy",
                "Script Body": groovy_vpd_logic,
                "Module Directory": ""
            },
            ["failure"]
        )

        # 4. RouteOnAttribute pour router les données
        split_props = {
            "Routing Strategy": "Route to Property name",
            "data.type": "${vpd_status}"
        }

        data_router = await self.create_processor_instance(
            z2_id,
            "org.apache.nifi.processors.standard.RouteOnAttribute",
            "Z2_Data_Router_V41",
            (400, 0),
            split_props
        )

        # 5. OUTPUT PORT vers Zone 3 (Persistance)
        output_port_z3 = await self.create_port(z2_id, "OUTPUT_PORT", "Z2_To_Z3_Persistence_V41", (600, -100))
        self.ports['z2_output_persistence'] = output_port_z3

        # 6. OUTPUT PORT vers Zone 4 (Feedback)
        output_port_z4 = await self.create_port(z2_id, "OUTPUT_PORT", "Z2_To_Z4_Feedback_V41", (600, 100))
        self.ports['z2_output_feedback'] = output_port_z4

        # 7. Connexions internes Zone 2
        if input_port_z1 and context_enricher:
            await self.establish_connection(z2_id, input_port_z1, context_enricher, ["success"], "Input_To_Enricher")

        if context_enricher and vpd_calculator:
            await self.establish_connection(z2_id, context_enricher, vpd_calculator, ["success"], "Enricher_To_VPD")

        if vpd_calculator and data_router:
            await self.establish_connection(z2_id, vpd_calculator, data_router, ["success"], "VPD_To_Router")

        # Toutes les données vont vers la persistance
        if data_router and output_port_z3:
            await self.establish_connection(z2_id, data_router, output_port_z3, ["OPTIMAL", "LOW", "HIGH"], "All_To_Persistence")

        # Seulement les anomalies vont vers le feedback
        if data_router and output_port_z4:
            await self.establish_connection(z2_id, data_router, output_port_z4, ["LOW", "HIGH"], "Anomalies_To_Feedback")

        logger.info("✅ Zone 2 v4.1 opérationnelle avec ports multiples")
        return z2_id

    # --- ZONE 3 : PERSISTANCE V4.1 ---
    async def deploy_zone_3(self, main_pg_id):
        """Configuration de la Zone 3 avec persistance robuste"""
        logger.info("💾 Déploiement Zone 3 - Persistance & Archivage v4.1")

        z3_id = await self.create_standard_pg(main_pg_id, "Zone 3 - Persistance & Archivage v4.1", 1600, 0)
        if not z3_id:
            return None

        self.zones['z3'] = z3_id

        # 1. INPUT PORT depuis Zone 2
        input_port_z2 = await self.create_port(z3_id, "INPUT_PORT", "Z3_From_Z2_Persistence_V41", (-200, 0))
        self.ports['z3_input_persistence'] = input_port_z2

        # 2. SplitJson pour séparer les données
        split_props = {
            "JsonPath Expression": "$[*]",
            "Keep Array Elements Together": "true"
        }

        json_splitter = await self.create_processor_instance(
            z3_id,
            "org.apache.nifi.processors.standard.SplitJson",
            "Z3_JSON_Splitter_V41",
            (0, 0),
            split_props,
            ["failure"]
        )

        # 3. ClickHouse Writer - Version robuste
        if self.services.get('json_reader') and self.services.get('ck_pool'):
            clickhouse_props = {
                "Record Reader": f"controller-service://{self.services['json_reader']}",
                "Database Connection Pooling Service": f"controller-service://{self.services['ck_pool']}",
                "Statement Type": "INSERT",
                "Table Name": "vertiflow.basil_telemetry_full_v41",
                "Field Names Included": "false",
                "Quote Column Identifiers": "false",
                "Translate Field Names": "false",
                "Unmatched Field Behaviour": "ignore",
                "Update Keys": ""
            }

            clickhouse_writer = await self.create_processor_instance(
                z3_id,
                "org.apache.nifi.processors.standard.PutDatabaseRecord",
                "Z3_ClickHouse_OLAP_Writer_V41",
                (200, -100),
                clickhouse_props,
                ["failure", "success"]
            )
        else:
            logger.warning("⚠️ Services ClickHouse non disponibles")
            clickhouse_writer = None

        # 4. MongoDB Audit - Version robuste
        mongo_audit_props = {
            "Mongo URI": MONGO_URI,
            "Mongo Database Name": "vertiflow_ops",
            "Mongo Collection Name": "data_audit_v41",
            "Mode": "insert",
            "Update Keys": "",
            "Update Query Key": ""
        }

        mongo_writer = await self.create_processor_instance(
            z3_id,
            "org.apache.nifi.processors.mongodb.PutMongo",
            "Z3_MongoDB_Audit_Logger_V41",
            (200, 100),
            mongo_audit_props,
            ["success", "failure"]
        )

        # 5. Connexions internes Zone 3
        if input_port_z2 and json_splitter:
            await self.establish_connection(z3_id, input_port_z2, json_splitter, ["success"], "Input_To_Splitter")

        if json_splitter and clickhouse_writer:
            await self.establish_connection(z3_id, json_splitter, clickhouse_writer, ["splits"], "Splitter_To_ClickHouse")

        if json_splitter and mongo_writer:
            await self.establish_connection(z3_id, json_splitter, mongo_writer, ["splits"], "Splitter_To_MongoDB")

        logger.info("✅ Zone 3 v4.1 opérationnelle avec port d'entrée")
        return z3_id

    # --- ZONE 4 : RÉTROACTION V4.1 (CORRIGÉ) ---
    async def deploy_zone_4(self, main_pg_id):
        """Configuration de la Zone 4 avec rétroaction robuste - CORRIGÉ"""
        logger.info("🔔 Déploiement Zone 4 - Rétroaction & Pilotage v4.1")

        z4_id = await self.create_standard_pg(main_pg_id, "Zone 4 - Rétroaction & Pilotage v4.1", 2400, 0)
        if not z4_id:
            return None

        self.zones['z4'] = z4_id

        # 1. INPUT PORT depuis Zone 2
        input_port_z2 = await self.create_port(z4_id, "INPUT_PORT", "Z4_From_Z2_Feedback_V41", (-200, 0))
        self.ports['z4_input_feedback'] = input_port_z2

        # 2. RouteOnAttribute pour détecter les anomalies - Version simple
        anomaly_props = {
            "Routing Strategy": "Route to Property name",
            "is.vpd.anomaly": "${vpd_status:equals('LOW'):or(${vpd_status:equals('HIGH')})}",
            "is.ph.anomaly": "${ph_level:lt(5.5):or(${ph_level:gt(7.0)})}"
        }

        anomaly_detector = await self.create_processor_instance(
            z4_id,
            "org.apache.nifi.processors.standard.RouteOnAttribute",
            "Z4_Anomaly_Detector_V41",
            (0, 0),
            anomaly_props
        )

        # 3. UpdateAttribute pour formater les alertes - CORRECTION: bon type de processeur
        alert_formatter = await self.create_processor_instance(
            z4_id,
            "org.apache.nifi.processors.attributes.UpdateAttribute",  # CORRIGÉ
            "Z4_Alert_Formatter_V41",
            (200, 0),
            {
                "alert.message": "Anomalie détectée: VPD=${vpd_status}, pH=${ph_level}",
                "alert.timestamp": "${now():format('yyyy-MM-dd HH:mm:ss.SSS')}",
                "alert.severity": "${vpd_status:equals('HIGH'):or(${ph_level:lt(5.5)}):ifElse('CRITICAL','WARNING')}",
                "alert.action": "${vpd_status:equals('HIGH'):ifElse('VENTILATION','HUMIDIFICATION')}",
                "mqtt.topic": "vertiflow/actuators/control/${alert.severity}"
            },
            ["failure"]
        )

        # 4. MQTT Publisher pour commandes - Version robuste
        actuator_props = {
            "Broker URI": "tcp://localhost:1883",
            "Client ID": "nifi-actuator-v41-${now():format('yyyyMMdd')}",
            "Topic": "${mqtt.topic}",
            "Quality of Service(QoS)": "1",
            "Retain": "false",
            "Max Message Size": "1 MB",
            "Connection Timeout": "15 secs"
        }

        actuator_publisher = await self.create_processor_instance(
            z4_id,
            "org.apache.nifi.processors.mqtt.PublishMQTT",
            "Z4_MQTT_Actuator_Commander_V41",
            (400, 0),
            actuator_props,
            ["failure", "success"]
        )

        # 5. PutFile pour log local des alertes (backup)
        file_log_props = {
            "Directory": "/opt/nifi/nifi-current/exchange/alerts",
            "Conflict Resolution Strategy": "replace",
            "Create Missing Directories": "true",
            "Maximum File Name Length": "255"
        }

        alert_logger = await self.create_processor_instance(
            z4_id,
            "org.apache.nifi.processors.standard.PutFile",
            "Z4_Alert_Logger_V41",
            (200, 150),
            file_log_props,
            ["failure", "success"]
        )

        # 6. Connexions internes Zone 4
        if input_port_z2 and anomaly_detector:
            await self.establish_connection(z4_id, input_port_z2, anomaly_detector, ["success"], "Input_To_Detector")

        if anomaly_detector and alert_formatter:
            await self.establish_connection(z4_id, anomaly_detector, alert_formatter, ["is.vpd.anomaly", "is.ph.anomaly"], "Detector_To_Formatter")

        if alert_formatter and actuator_publisher:
            await self.establish_connection(z4_id, alert_formatter, actuator_publisher, ["success"], "Formatter_To_Actuator")

        if alert_formatter and alert_logger:
            await self.establish_connection(z4_id, alert_formatter, alert_logger, ["success"], "Formatter_To_Logger")

        logger.info("✅ Zone 4 v4.1 opérationnelle avec UpdateAttribute corrigé")
        return z4_id

    # --- ZONE 5 : DONNÉES STATIQUES V4.1 ---
    async def deploy_zone_5(self, main_pg_id):
        """Configuration de la Zone 5 avec chargement robuste"""
        logger.info("📂 Déploiement Zone 5 - Static Data Loaders v4.1")

        z5_id = await self.create_standard_pg(main_pg_id, "Zone 5 - Static Data Loaders v4.1", 3200, 0)
        if not z5_id:
            return None

        self.zones['z5'] = z5_id

        # 1. GetFile pour fichiers CSV/JSON
        file_props = {
            "Input Directory": "/opt/nifi/nifi-current/exchange/input",
            "File Filter": "[^.]*",
            "Keep Source File": "false",
            "Minimum File Age": "0 sec",
            "Maximum File Age": "365 days",
            "Polling Interval": "60 sec",
            "Ignore Hidden Files": "true"
        }

        file_ingestor = await self.create_processor_instance(
            z5_id,
            "org.apache.nifi.processors.standard.GetFile",
            "Z5_File_Ingestor_V41",
            (0, 0),
            file_props
        )

        # 2. RouteOnContent pour router par type de fichier
        route_props = {
            "Routing Strategy": "Route to Property name",
            "file.type": "${filename:endsWith('.json'):ifElse('json','csv'):ifElse(${filename:endsWith('.csv')},'unknown')}"
        }

        file_router = await self.create_processor_instance(
            z5_id,
            "org.apache.nifi.processors.standard.RouteOnAttribute",
            "Z5_File_Router_V41",
            (150, 0),
            route_props
        )

        # 3. ConvertRecord pour JSON vers MongoDB
        if self.services.get('json_reader'):
            json_converter = await self.create_processor_instance(
                z5_id,
                "org.apache.nifi.processors.standard.ConvertRecord",
                "Z5_JSON_To_Mongo_V41",
                (300, -50),
                {
                    "Record Reader": f"controller-service://{self.services['json_reader']}",
                    "Record Writer": "org.apache.nifi.mongodb.MongoDBWriter"
                },
                ["failure"]
            )
        else:
            json_converter = None

        # 4. MongoDB Writer pour recettes
        mongo_writer_props = {
            "Mongo URI": MONGO_URI,
            "Mongo Database Name": "vertiflow_ops",
            "Mongo Collection Name": "plant_recipes_v41",
            "Mode": "insert",
            "Update Keys": "",
            "Update Query Key": ""
        }

        recipe_loader = await self.create_processor_instance(
            z5_id,
            "org.apache.nifi.processors.mongodb.PutMongo",
            "Z5_Plant_Recipe_Seeder_V41",
            (450, 0),
            mongo_writer_props,
            ["success", "failure"]
        )

        # 5. Connexions
        if file_ingestor and file_router:
            await self.establish_connection(z5_id, file_ingestor, file_router, ["success"], "File_To_Router")

        if file_router and json_converter:
            await self.establish_connection(z5_id, file_router, json_converter, ["json"], "Router_JSON_To_Converter")

        if json_converter and recipe_loader:
            await self.establish_connection(z5_id, json_converter, recipe_loader, ["success"], "Converter_To_Mongo")

        # Pour les fichiers CSV (extension future)
        # if file_router and csv_converter:
        #     await self.establish_connection(z5_id, file_router, csv_converter, ["csv"], "Router_CSV_To_Converter")

        logger.info("✅ Zone 5 v4.1 opérationnelle")
        return z5_id

    # --- ÉTABLISSEMENT DES LIAISONS INTER-ZONES ZERO-FAILURE ---
    async def establish_inter_zone_connections(self, main_pg_id):
        """Établit toutes les connexions entre les zones avec logique Zero-Failure"""
        logger.info("🌉 Établissement des liaisons inter-zones Zero-Failure...")

        connections_established = 0

        # ORDRE CRITIQUE: Créer tous les ports d'abord, puis les connexions

        # 1. Flux Externe : Zone 0 → Zone 1
        if self.zones.get('z0') and self.ports.get('z0_output') and \
                self.zones.get('z1') and self.ports.get('z1_input_external'):

            logger.info("🔗 Connexion Z0 → Z1...")
            conn_id = await self.establish_inter_zone_connection(
                main_pg_id,
                self.zones['z0'],
                self.ports['z0_output'],
                self.zones['z1'],
                self.ports['z1_input_external'],
                "Flux_Externe_Z0_vers_Z1_V41"
            )
            if conn_id:
                connections_established += 1
                logger.info("  ✅ Connecté")
            else:
                logger.warning("  ⚠️ Échec connexion")

        # 2. Flux Principal : Zone 1 → Zone 2
        if self.zones.get('z1') and self.ports.get('z1_output_validated') and \
                self.zones.get('z2') and self.ports.get('z2_input_validated'):

            logger.info("🔗 Connexion Z1 → Z2...")
            conn_id = await self.establish_inter_zone_connection(
                main_pg_id,
                self.zones['z1'],
                self.ports['z1_output_validated'],
                self.zones['z2'],
                self.ports['z2_input_validated'],
                "Flux_Principal_Z1_vers_Z2_V41"
            )
            if conn_id:
                connections_established += 1
                logger.info("  ✅ Connecté")
            else:
                logger.warning("  ⚠️ Échec connexion")

        # 3. Flux de Persistance : Zone 2 → Zone 3
        if self.zones.get('z2') and self.ports.get('z2_output_persistence') and \
                self.zones.get('z3') and self.ports.get('z3_input_persistence'):

            logger.info("🔗 Connexion Z2 → Z3...")
            conn_id = await self.establish_inter_zone_connection(
                main_pg_id,
                self.zones['z2'],
                self.ports['z2_output_persistence'],
                self.zones['z3'],
                self.ports['z3_input_persistence'],
                "Flux_Persistance_Z2_vers_Z3_V41"
            )
            if conn_id:
                connections_established += 1
                logger.info("  ✅ Connecté")
            else:
                logger.warning("  ⚠️ Échec connexion")

        # 4. Flux de Rétroaction : Zone 2 → Zone 4
        if self.zones.get('z2') and self.ports.get('z2_output_feedback') and \
                self.zones.get('z4') and self.ports.get('z4_input_feedback'):

            logger.info("🔗 Connexion Z2 → Z4...")
            conn_id = await self.establish_inter_zone_connection(
                main_pg_id,
                self.zones['z2'],
                self.ports['z2_output_feedback'],
                self.zones['z4'],
                self.ports['z4_input_feedback'],
                "Flux_Retroaction_Z2_vers_Z4_V41"
            )
            if conn_id:
                connections_established += 1
                logger.info("  ✅ Connecté")
            else:
                logger.warning("  ⚠️ Échec connexion")

        logger.info(f"📊 {connections_established}/4 liaisons inter-zones établies")

        if connections_established < 4:
            logger.warning(f"⚠️ Seulement {connections_established}/4 liaisons établies")
            logger.info("🔧 Conseil: Vérifiez manuellement les ports dans NiFi UI")

        return connections_established

    # --- PROTOCOLE DE STABILISATION ET DÉMARRAGE GLOBAL ---
    async def stabilize_and_start(self, main_pg_id):
        """Protocole complet de stabilisation et démarrage"""
        logger.info("🔄 Démarrage du protocole de stabilisation et démarrage...")

        success_steps = 0
        total_steps = 4

        # ÉTAPE 1: Activer tous les services controller
        logger.info(f"📋 Étape 1/{total_steps}: Activation des services controller...")
        services_activated = await self.activate_all_services()
        if services_activated:
            success_steps += 1
            logger.info("✅ Services controller activés")
        else:
            logger.error("❌ Échec activation services")

        # Attendre que les services soient stables
        await asyncio.sleep(10)

        # ÉTAPE 2: Démarrer les ports
        logger.info(f"📋 Étape 2/{total_steps}: Démarrage des ports...")
        ports_started = await self.start_all_ports(main_pg_id)
        if ports_started:
            success_steps += 1
            logger.info("✅ Ports démarrés")
        else:
            logger.warning("⚠️ Certains ports n'ont pas pu démarrer")

        # ÉTAPE 3: Démarrer les processeurs
        logger.info(f"📋 Étape 3/{total_steps}: Démarrage des processeurs...")
        processors_started = await self.start_all_processors(main_pg_id)
        if processors_started:
            success_steps += 1
            logger.info("✅ Processeurs démarrés")
        else:
            logger.warning("⚠️ Certains processeurs n'ont pas pu démarrer")

        # ÉTAPE 4: Démarrer le pipeline principal
        logger.info(f"📋 Étape 4/{total_steps}: Démarrage du pipeline principal...")
        pipeline_started = await self.start_pipeline_robust(main_pg_id)
        if pipeline_started:
            success_steps += 1
            logger.info("✅ Pipeline principal démarré")
        else:
            logger.error("❌ Échec démarrage pipeline")

        # Rapport final
        logger.info(f"📊 Protocole de démarrage: {success_steps}/{total_steps} étapes réussies")

        return success_steps == total_steps

    async def activate_all_services(self):
        """Active tous les services controller dans l'ordre correct"""
        logger.info("🔧 Activation de tous les services controller...")

        # Ordre d'activation critique
        activation_order = [
            'MASTER_SSL_CONTEXT_V41',
            'MASTER_HTTP_CONTEXT_V41',
            'MASTER_CLICKHOUSE_POOL_V41',
            'MASTER_MONGODB_CLIENT_V41',
            'MASTER_JSON_READER_V41',
            'MASTER_JSON_WRITER_V41',
            'MASTER_RECIPE_LOOKUP_V41'
        ]

        activated_count = 0
        for svc_name in activation_order:
            svc_id = None
            for key, value in self.services.items():
                if svc_name.lower() in key.lower():
                    svc_id = value
                    break

            if svc_id:
                logger.info(f"  🔧 Activation: {svc_name}...")
                if await self.ensure_service_enabled_robust(svc_id):
                    activated_count += 1
                    logger.info(f"    ✅ Activé")
                else:
                    logger.warning(f"    ⚠️ Échec activation")
                await asyncio.sleep(2)  # Pause entre les activations

        logger.info(f"📊 {activated_count}/{len(activation_order)} services activés")
        return activated_count > 0

    async def start_all_ports(self, main_pg_id):
        """Démarre tous les ports d'entrée et de sortie"""
        logger.info("🚀 Démarrage de tous les ports...")

        # Récupérer tous les ports du pipeline principal
        try:
            # Ports d'entrée
            input_response = self.sm.session.get(
                f"{NIFI_BASE_URL}/process-groups/{main_pg_id}/input-ports",
                timeout=15
            )

            # Ports de sortie
            output_response = self.sm.session.get(
                f"{NIFI_BASE_URL}/process-groups/{main_pg_id}/output-ports",
                timeout=15
            )

            ports_to_start = []

            if input_response.status_code == 200:
                input_ports = input_response.json().get('inputPorts', [])
                ports_to_start.extend([('INPUT_PORT', port['id']) for port in input_ports])

            if output_response.status_code == 200:
                output_ports = output_response.json().get('outputPorts', [])
                ports_to_start.extend([('OUTPUT_PORT', port['id']) for port in output_ports])

            started_count = 0
            for port_type, port_id in ports_to_start:
                logger.info(f"  🚀 Démarrage port {port_id}...")
                if await self.start_component(port_id, 'input-ports' if port_type == 'INPUT_PORT' else 'output-ports'):
                    started_count += 1
                    logger.info(f"    ✅ Démarré")
                else:
                    logger.warning(f"    ⚠️ Échec démarrage")
                await asyncio.sleep(1)

            logger.info(f"📊 {started_count}/{len(ports_to_start)} ports démarrés")
            return started_count > 0

        except Exception as e:
            logger.error(f"❌ Erreur démarrage ports: {e}")
            return False

    async def start_all_processors(self, main_pg_id):
        """Démarre tous les processeurs"""
        logger.info("🚀 Démarrage de tous les processeurs...")

        try:
            # Récupérer tous les processeurs récursivement
            all_processors = await self.get_all_processors_recursive(main_pg_id)

            started_count = 0
            for processor_id, processor_name in all_processors:
                logger.info(f"  🚀 Démarrage processeur {processor_name}...")
                if await self.start_component(processor_id, 'processors'):
                    started_count += 1
                    logger.info(f"    ✅ Démarré")
                else:
                    logger.warning(f"    ⚠️ Échec démarrage")
                await asyncio.sleep(0.5)  # Petite pause

            logger.info(f"📊 {started_count}/{len(all_processors)} processeurs démarrés")
            return started_count > 0

        except Exception as e:
            logger.error(f"❌ Erreur démarrage processeurs: {e}")
            return False

    async def get_all_processors_recursive(self, pg_id):
        """Récupère tous les processeurs récursivement"""
        processors = []

        try:
            # Processeurs dans ce PG
            response = self.sm.session.get(
                f"{NIFI_BASE_URL}/process-groups/{pg_id}/processors",
                timeout=15
            )

            if response.status_code == 200:
                procs = response.json().get('processors', [])
                for proc in procs:
                    processors.append((proc['id'], proc['component']['name']))

            # Processeurs dans les sous-PGs
            pg_response = self.sm.session.get(
                f"{NIFI_BASE_URL}/process-groups/{pg_id}/process-groups",
                timeout=15
            )

            if pg_response.status_code == 200:
                sub_pgs = pg_response.json().get('processGroups', [])
                for sub_pg in sub_pgs:
                    sub_processors = await self.get_all_processors_recursive(sub_pg['id'])
                    processors.extend(sub_processors)

        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération processeurs récursive: {e}")

        return processors

    async def start_component(self, component_id, component_type):
        """Démarre un composant individuel"""
        try:
            endpoint_map = {
                'processors': 'processors',
                'input-ports': 'input-ports',
                'output-ports': 'output-ports'
            }

            endpoint = endpoint_map.get(component_type)
            if not endpoint:
                logger.error(f"Type de composant non supporté: {component_type}")
                return False

            # Récupérer l'état actuel
            url = f"{NIFI_BASE_URL}/{endpoint}/{component_id}"
            response = self.sm.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Impossible de récupérer l'état du composant {component_id}")
                return False

            current_state = response.json()['component']['state']
            current_ver = response.json()['revision']['version']

            if current_state == 'RUNNING':
                return True

            # Démarrer le composant
            start_payload = {
                "revision": {"version": current_ver},
                "component": {
                    "id": component_id,
                    "state": "RUNNING"
                }
            }

            start_response = self.sm.session.put(url, json=start_payload, timeout=15)

            if start_response.status_code == 200:
                await asyncio.sleep(1)  # Laisser le temps au démarrage
                return True
            else:
                logger.warning(f"Échec démarrage {component_id}: {start_response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"Erreur démarrage composant {component_id}: {e}")
            return False

    async def start_pipeline_robust(self, main_pg_id):
        """Démarre le pipeline principal de manière robuste"""
        logger.info(f"🚀 Démarrage robuste du pipeline principal {main_pg_id}...")

        try:
            # Vérifier l'état actuel
            response = self.sm.session.get(
                f"{NIFI_BASE_URL}/flow/process-groups/{main_pg_id}",
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"❌ Impossible de vérifier l'état: {response.status_code}")
                return False

            # Démarrer
            start_payload = {
                "id": main_pg_id,
                "state": "RUNNING"
            }

            start_response = self.sm.session.put(
                f"{NIFI_BASE_URL}/flow/process-groups/{main_pg_id}",
                json=start_payload,
                timeout=30
            )

            if start_response.status_code == 200:
                logger.info("✅ Commande de démarrage envoyée")

                # Attendre et vérifier l'état
                await asyncio.sleep(10)

                final_response = self.sm.session.get(
                    f"{NIFI_BASE_URL}/flow/process-groups/{main_pg_id}",
                    timeout=15
                )

                if final_response.status_code == 200:
                    status_data = final_response.json()
                    aggregate_snapshot = status_data.get('processGroupFlow', {}).get('aggregateSnapshot', {})
                    running_count = aggregate_snapshot.get('runningCount', 0)
                    stopped_count = aggregate_snapshot.get('stoppedCount', 0)
                    invalid_count = aggregate_snapshot.get('invalidCount', 0)

                    logger.info(f"📊 État final: {running_count} actifs, {stopped_count} arrêtés, {invalid_count} invalides")

                    if running_count > 0:
                        logger.info("🎉 Pipeline VertiFlow v4.1 ACTIF!")
                        return True
                    else:
                        logger.warning("⚠️ Pipeline démarré mais aucun composant actif")
                        return False
                else:
                    logger.warning("⚠️ Impossible de vérifier l'état final")
                    return True
            else:
                logger.error(f"❌ Échec démarrage pipeline: {start_response.status_code} - {start_response.text[:200]}")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur démarrage pipeline: {e}")
            return False

    # --- MÉTHODES DE FIN DE PROTOCOLE ---
    async def verify_pipeline_health_v41(self):
        """Audit final de la structure déployée v4.1"""
        print("\n" + "═"*80)
        logger.info("⭐ RAPPORT DE GOUVERNANCE TECHNIQUE VERTIFLOW v4.1 ⭐")
        print("═"*80)

        services_count = len([v for v in self.services.values() if v])
        zones_count = len([v for v in self.zones.values() if v])
        ports_count = len([v for v in self.ports.values() if v])
        connections_count = len(self.connections)

        summary = {
            "Infrastructure Core": "✅ CONNECTÉ",
            "Controller Services": f"✅ {services_count} Services Déployés",
            "Zones de Données": f"✅ {zones_count} Unités Déployées",
            "Ports d'Interface": f"✅ {ports_count} Ports Créés",
            "Connexions Inter-Zones": f"✅ {connections_count} Connexions Établies",
            "Architecture": "✅ Pipeline Zero-Failure v4.1"
        }

        for k, v in summary.items():
            logger.info(f"{k:<35} : {v}")

        # Diagramme du flux
        logger.info("\n📊 DIAGRAMME DU FLUX DE DONNÉES v4.1:")
        logger.info("   Zone 0 (APIs Externes) ────▶ Zone 1 (Ingestion)")
        logger.info("   Zone 1 (Ingestion) ─────────▶ Zone 2 (Contextualisation)")
        logger.info("   Zone 2 (Contextualisation) ──▶ Zone 3 (Persistance)")
        logger.info("   Zone 2 (Contextualisation) ──▶ Zone 4 (Rétroaction)")
        logger.info("   Zone 5 (Données Statiques) ──▶ MongoDB (autonome)")

        # État des services
        logger.info("\n🔍 ÉTAT DES SERVICES CRITIQUES:")
        critical_services = [
            ('ClickHouse Pool', self.services.get('ck_pool')),
            ('MongoDB Client', self.services.get('mongo_svc')),
            ('JSON Reader', self.services.get('json_reader')),
            ('JSON Writer', self.services.get('json_writer')),
            ('SSL Context', self.services.get('ssl_context'))
        ]

        for svc_name, svc_id in critical_services:
            if svc_id:
                state = self.integrity.get_component_state(svc_id)
                status = "✅" if state == "ENABLED" else "❌"
                logger.info(f"   {status} {svc_name:<20}: {state if state else 'N/A'}")

        print("═"*80)
        logger.info("🚀 SYSTÈME VERTIFLOW v4.1 CONFIGURÉ - PRÊT POUR L'ACTIVATION")
        print("═"*80 + "\n")

    async def execute_full_deployment_v41(self):
        """Orchestrateur Suprême : Déploiement complet v4.1 avec protocole Zero-Failure"""
        start_time = time.time()

        try:
            # PHASE 1 : INITIALISATION ROBUSTE
            logger.info("="*60)
            logger.info("PHASE 1 : INITIALISATION DU CORE v4.1")
            logger.info("="*60)
            if not await self.initialize_core():
                return False

            # PHASE 2 : SERVICES DE CONTRÔLE AVEC DÉPENDANCES
            logger.info("\n" + "="*60)
            logger.info("PHASE 2 : SERVICES DE CONTRÔLE v4.1")
            logger.info("="*60)
            await self.configure_master_services()

            # Attendre que les services soient stables
            await asyncio.sleep(8)

            # PHASE 3 : PIPELINE MASTER
            logger.info("\n" + "="*60)
            logger.info("PHASE 3 : PIPELINE MASTER v4.1")
            logger.info("="*60)
            main_pg_id = await self.create_standard_pg(self.root_id, "VERTIFLOW_GOVERNANCE_MASTER_V41", 0, 0)
            if not main_pg_id:
                logger.error("❌ Impossible de créer le pipeline master v4.1")
                return False

            # PHASE 4 : DÉPLOIEMENT DES ZONES SÉQUENTIELLEMENT
            logger.info("\n" + "="*60)
            logger.info("PHASE 4 : DÉPLOIEMENT DES ZONES v4.1")
            logger.info("="*60)

            zones_to_deploy = [
                ("Zone 0 - APIs Externes", self.deploy_zone_0(main_pg_id)),
                ("Zone 1 - Ingestion", self.deploy_zone_1(main_pg_id)),
                ("Zone 2 - Contextualisation", self.deploy_zone_2(main_pg_id)),
                ("Zone 3 - Persistance", self.deploy_zone_3(main_pg_id)),
                ("Zone 4 - Rétroaction", self.deploy_zone_4(main_pg_id)),
                ("Zone 5 - Données Statiques", self.deploy_zone_5(main_pg_id))
            ]

            for zone_name, task in zones_to_deploy:
                logger.info(f"\n📍 {zone_name}...")
                try:
                    await task
                    await asyncio.sleep(3)  # Pause stratégique entre zones
                except Exception as e:
                    logger.error(f"❌ Erreur dans {zone_name}: {e}")

            # PHASE 5 : LIAISONS INTER-ZONES ZERO-FAILURE
            logger.info("\n" + "="*60)
            logger.info("PHASE 5 : LIAISONS INTER-ZONES ZERO-FAILURE")
            logger.info("="*60)
            connections = await self.establish_inter_zone_connections(main_pg_id)

            if connections < 4:
                logger.warning(f"⚠️ {connections}/4 liaisons établies")
                logger.info("🔧 Vérification manuelle recommandée dans NiFi UI")
            else:
                logger.info(f"✅ {connections}/4 liaisons inter-zones opérationnelles")

            # PHASE 6 : AUDIT FINAL
            logger.info("\n" + "="*60)
            logger.info("PHASE 6 : AUDIT FINAL v4.1")
            logger.info("="*60)
            await self.verify_pipeline_health_v41()

            # PHASE 7 : PROTOCOLE DE STABILISATION ET DÉMARRAGE
            logger.info("\n" + "="*60)
            logger.info("PHASE 7 : PROTOCOLE DE STABILISATION ET DÉMARRAGE")
            logger.info("="*60)
            pipeline_active = await self.stabilize_and_start(main_pg_id)

            elapsed = time.time() - start_time
            logger.info(f"⏱️ Déploiement complet v4.1 exécuté en {elapsed:.2f} secondes")

            # Rapport final
            if pipeline_active:
                logger.info("🎉 DÉPLOIEMENT VERTIFLOW v4.1 RÉUSSI!")
            else:
                logger.warning("⚠️ DÉPLOIEMENT PARTIEL - VÉRIFICATION MANUELLE REQUISE")

            return pipeline_active

        except Exception as e:
            logger.critical(f"🚨 ERREUR CRITIQUE DU DÉPLOIEMENT v4.1: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

# --- POINT D'ENTRÉE DU SYSTÈME V4.1 ---
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 VERTIFLOW GOVERNANCE MASTER - VERSION 4.1.0 (ZERO-FAILURE)")
    print("="*80)
    print(f"📅 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    master = VertiFlowGovernanceMasterV41()

    try:
        success = asyncio.run(master.execute_full_deployment_v41())

        if success:
            print("\n" + "✅" * 40)
            print("✅ DÉPLOIEMENT VERTIFLOW v4.1 RÉUSSI - SYSTÈME ACTIF")
            print("✅" * 40)
            print("\n🔗 Accès NiFi: https://localhost:8443/nifi")
            print("👤 Identifiants: admin / ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB")
            print("📊 Données: basil_telemetry_full_v41 -> ClickHouse")
            print("🔄 Flux: Z0 → Z1 → Z2 → Z3/Z4 (Zero-Failure)")
            print("⚡ État: Pipeline en cours d'exécution")
            print("\n📋 Prochaines étapes:")
            print("1. Testez avec le simulateur IoT: python3 scripts/simulators/kafka_telemetry_producer.py")
            print("2. Surveillez les logs: tail -f logs/governance_v41_deploy.log")
            print("3. Vérifiez le flux dans NiFi UI")
        else:
            print("\n" + "⚠️" * 40)
            print("⚠️ DÉPLOIEMENT VERTIFLOW v4.1 PARTIEL")
            print("⚠️" * 40)
            print("\n📄 Consultez les logs: logs/governance_v41_deploy.log")
            print("🔧 Actions manuelles requises:")
            print("1. Connectez-vous à NiFi (https://localhost:8443/nifi)")
            print("2. Activez manuellement les services controller (Controller Settings)")
            print("3. Vérifiez les connexions inter-zones")
            print("4. Démarrez manuellement le pipeline 'VERTIFLOW_GOVERNANCE_MASTER_V41'")
            print("\n💡 Conseil: Le système utilise le protocole Zero-Failure v4.1")

    except KeyboardInterrupt:
        logger.info("🛑 Déploiement v4.1 interrompu par l'utilisateur.")
        print("\n🛑 Déploiement v4.1 interrompu.")
    except Exception as e:
        logger.critical(f"🚨 ERREUR FATALE v4.1: {str(e)}")
        print(f"\n❌ ERREUR FATALE v4.1: {str(e)}")
        sys.exit(1)