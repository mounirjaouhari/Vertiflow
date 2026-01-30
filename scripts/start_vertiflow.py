#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - ORCHESTRATEUR MAÎTRE CORRIGÉ
================================================================================
Description : Gère la santé de l'infra, le déploiement NiFi et le ML Engine.
Version : 2.3 - Correction des chemins et du changement de répertoire
================================================================================
"""

import os
import sys
import time
import logging
import subprocess
import signal
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Tentative d'import des drivers pour les tests de santé
try:
    from clickhouse_driver import Client
    from kafka import KafkaAdminClient
    from pymongo import MongoClient
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError as e:
    print(f"❌ Erreur : Dépendances manquantes: {e}")
    print("Lancez 'pip install clickhouse-driver kafka-python pymongo requests'")
    sys.exit(1)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler("logs/orchestrateur_master.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VertiFlow.Master")

# DÉFINIR LE RACINE ABSOLUE DU PROJET CORRECTEMENT
# Le script est dans scripts/start_vertiflow.py
# Donc PROJECT_ROOT = parent du parent = ~/vertiflow_cloud_release
SCRIPT_DIR = Path(__file__).parent.absolute()  # scripts/
PROJECT_ROOT = SCRIPT_DIR.parent.absolute()    # ~/vertiflow_cloud_release/

processes = []

# CONFIGURATION
NIFI_BASE_URL = "https://localhost:8443/nifi-api"
NIFI_USERNAME = "admin"
NIFI_PASSWORD = "ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB"

print(f"🔧 DEBUG: SCRIPT_DIR = {SCRIPT_DIR}")
print(f"🔧 DEBUG: PROJECT_ROOT = {PROJECT_ROOT}")

class PathResolver:
    """Résout les chemins de manière fiable"""

    @staticmethod
    def get_absolute_path(relative_path):
        """Retourne le chemin absolu depuis la racine du projet"""
        return PROJECT_ROOT / relative_path

    @staticmethod
    def check_path_exists(path_description, paths_to_check):
        """Vérifie l'existence de chemins et retourne le premier qui existe"""
        for path_desc in paths_to_check:
            if isinstance(path_desc, tuple):
                path, desc = path_desc
            else:
                path = path_desc
                desc = str(path)

            absolute_path = PROJECT_ROOT / path if not Path(path).is_absolute() else Path(path)

            if absolute_path.exists():
                logger.debug(f"✅ Chemin trouvé: {desc}")
                return absolute_path
            else:
                logger.debug(f"❌ Chemin introuvable: {desc}")

        return None

class DockerValidator:
    """Valide l'état Docker"""

    @staticmethod
    def validate_docker_services():
        """Valide les services Docker essentiels"""
        logger.info("🔍 Validation des services Docker...")

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}||{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.warning("⚠️ Docker non disponible")
                return False

            services = {}
            for line in result.stdout.strip().split('\n'):
                if '||' in line:
                    name, status = line.split('||', 1)
                    services[name] = status

            required_services = ['kafka', 'clickhouse', 'mongodb', 'nifi', 'mosquitto', 'zookeeper']
            found_services = []

            for service in required_services:
                if service in services:
                    status = services[service]
                    if '(healthy)' in status or not '(unhealthy)' in status:
                        logger.info(f"   ✅ {service}: {status}")
                        found_services.append(service)
                    else:
                        logger.warning(f"   ⚠️ {service}: {status}")
                else:
                    logger.warning(f"   ❌ {service}: non trouvé")

            logger.info(f"📊 {len(found_services)}/{len(required_services)} services Docker trouvés")

            # Requis minimum: Kafka, ClickHouse, MongoDB
            critical_services = ['kafka', 'clickhouse', 'mongodb']
            critical_found = all(svc in found_services for svc in critical_services)

            if critical_found:
                logger.info("✅ Services Docker critiques disponibles")
                return True
            else:
                logger.warning("⚠️ Services Docker critiques partiellement disponibles")
                return True  # On continue quand même

        except Exception as e:
            logger.warning(f"⚠️ Erreur validation Docker: {e}")
            return True  # On continue quand même

class ServiceConnector:
    """Teste la connectivité aux services"""

    @staticmethod
    async def test_kafka():
        """Test Kafka"""
        try:
            admin = KafkaAdminClient(
                bootstrap_servers='localhost:9092',
                request_timeout_ms=3000
            )
            admin.list_topics()
            admin.close()
            return True
        except Exception as e:
            logger.debug(f"Kafka test failed: {e}")
            return False

    @staticmethod
    async def test_clickhouse():
        """Test ClickHouse"""
        try:
            client = Client(
                host='localhost',
                port=9000,
                user='default',
                password='default',
                connect_timeout=3
            )
            client.execute('SELECT 1')
            return True
        except Exception as e:
            logger.debug(f"ClickHouse test failed: {e}")
            return False

    @staticmethod
    async def test_mongodb():
        """Test MongoDB"""
        try:
            client = MongoClient(
                'mongodb://localhost:27017/',
                serverSelectionTimeoutMS=3000
            )
            client.admin.command('ping')
            return True
        except Exception as e:
            logger.debug(f"MongoDB test failed: {e}")
            return False

    @staticmethod
    async def test_nifi():
        """Test NiFi (avec retries)"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{NIFI_BASE_URL}/flow/status",
                    verify=False,
                    timeout=10
                )
                if response.status_code == 200:
                    return True
                elif response.status_code == 401:
                    # NiFi est accessible mais besoin d'authentification
                    logger.debug(f"NiFi accessible mais auth requise (401)")
                    return True
            except Exception as e:
                logger.debug(f"NiFi attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)

        return False

    @staticmethod
    async def test_mosquitto():
        """Test Mosquitto"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 1883))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"Mosquitto test failed: {e}")
            return False

class InfrastructureTester:
    """Teste l'infrastructure complète"""

    @staticmethod
    async def run_comprehensive_test():
        """Exécute tous les tests"""
        print("\n" + "="*60)
        logger.info("Étape 0 : Test de Connectivité Réseau")
        print("="*60)

        # Valider Docker d'abord
        DockerValidator.validate_docker_services()

        # Tests parallèles
        tests = [
            ("Kafka", ServiceConnector.test_kafka()),
            ("ClickHouse", ServiceConnector.test_clickhouse()),
            ("MongoDB", ServiceConnector.test_mongodb()),
            ("NiFi", ServiceConnector.test_nifi()),
            ("Mosquitto", ServiceConnector.test_mosquitto())
        ]

        results = {}
        for name, task in tests:
            logger.info(f"   Testing {name}...")
            try:
                result = await task
                results[name] = result
                status = "✅" if result else "❌"
                logger.info(f"   {status} {name}")
            except Exception as e:
                results[name] = False
                logger.warning(f"   ❌ {name}: {e}")

        # Résumé
        print("\n" + "="*60)
        logger.info("RÉSUMÉ DE CONNECTIVITÉ")
        print("="*60)

        success_count = sum(1 for r in results.values() if r)
        total_count = len(results)

        for name, success in results.items():
            status = "✅ OK" if success else "❌ ÉCHEC"
            logger.info(f"   {name:<12} {status}")

        logger.info(f"\n📊 {success_count}/{total_count} services connectés")

        # Conditions minimales
        critical_services = ['Kafka', 'ClickHouse', 'MongoDB']
        critical_ok = all(results.get(service, False) for service in critical_services)

        if critical_ok:
            logger.info("✅ Connectivité minimale établie")
            return True
        else:
            logger.warning("⚠️ Connectivité minimale non atteinte, poursuite quand même")
            return True

class DataInitializer:
    """Initialise les données"""

    def __init__(self):
        self.resolver = PathResolver()

    def initialize(self):
        """Initialise les données de base"""
        print("\n" + "="*60)
        logger.info("Étape 1 : Initialisation des Données")
        print("="*60)

        # Le script d'initialisation a déjà été exécuté dans le premier script
        # Vérifier si les données sont déjà là
        logger.info("📊 Vérification des données existantes...")

        # Vérifier ClickHouse
        try:
            client = Client(
                host='localhost',
                port=9000,
                user='default',
                password='default',
                connect_timeout=3
            )
            tables = client.execute('SHOW TABLES FROM vertiflow')
            if tables:
                logger.info(f"✅ ClickHouse: {len(tables)} tables trouvées")
                for table in tables[:3]:  # Afficher les 3 premières
                    logger.info(f"   • {table[0]}")
                return True
            else:
                logger.warning("⚠️ ClickHouse: aucune table trouvée")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de vérifier ClickHouse: {e}")

        # Vérifier MongoDB
        try:
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
            db = client.vertiflow_ops
            collections = db.list_collection_names()
            if collections:
                logger.info(f"✅ MongoDB: {len(collections)} collections trouvées")
                for coll in collections[:3]:
                    logger.info(f"   • {coll}")
                return True
            else:
                logger.warning("⚠️ MongoDB: aucune collection trouvée")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de vérifier MongoDB: {e}")

        logger.info("ℹ️ Données déjà initialisées ou non vérifiables")
        return True

class NiFiDeployer:
    """Déploie le pipeline NiFi"""

    def __init__(self):
        self.resolver = PathResolver()

    def deploy(self):
        """Déploie le pipeline NiFi"""
        print("\n" + "="*60)
        logger.info("Étape 2 : Déploiement NiFi")
        print("="*60)

        # Chercher le script de déploiement
        deploy_script_paths = [
            ("scripts/nifi_workflows/deploy/deploy_pipeline_v2_full.py", "Script principal"),
            ("deploy_pipeline_v2_full.py", "Script à la racine"),
            ("../deploy_pipeline_v2_full.py", "Script parent"),
        ]

        deploy_script = self.resolver.check_path_exists("Script déploiement", deploy_script_paths)

        if not deploy_script:
            logger.error("❌ Script de déploiement NiFi introuvable")
            logger.info("💡 Essayez depuis la racine: python3 deploy_pipeline_v2_full.py")
            return False

        logger.info(f"📄 Script trouvé: {deploy_script}")
        logger.info("🚀 Lancement du déploiement NiFi...")

        try:
            # Garder une trace du répertoire actuel
            original_cwd = os.getcwd()

            # ALLER À LA RACINE DU PROJET pour exécuter le script
            os.chdir(PROJECT_ROOT)
            logger.debug(f"📁 Changement vers: {PROJECT_ROOT}")

            # Préparer l'environnement
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'

            # Chemin relatif depuis la racine
            if deploy_script.is_relative_to(PROJECT_ROOT):
                rel_path = deploy_script.relative_to(PROJECT_ROOT)
            else:
                rel_path = deploy_script

            logger.info(f"▶️ Exécution: python3 {rel_path}")

            # Lancer le processus
            process = subprocess.Popen(
                [sys.executable, str(rel_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1,
                universal_newlines=True
            )

            # Lire la sortie en temps réel
            logger.info("📝 Sortie du déploiement:")
            print("-" * 40)

            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    clean_line = line.rstrip('\n')
                    if clean_line:
                        print(f"  {clean_line}")
                        output_lines.append(clean_line)

            print("-" * 40)
            process.wait()

            # Revenir au répertoire original
            os.chdir(original_cwd)

            if process.returncode == 0:
                logger.info("✅ Déploiement NiFi terminé avec succès")

                # Vérifier si des erreurs sont dans la sortie
                if any("erreur" in line.lower() or "error" in line.lower() or "failed" in line.lower()
                       for line in output_lines[-10:]):
                    logger.warning("⚠️ Messages d'avertissement détectés")

                return True
            else:
                logger.error(f"❌ Déploiement NiFi échoué (code: {process.returncode})")
                if output_lines:
                    logger.error("   Dernières lignes de sortie:")
                    for line in output_lines[-5:]:
                        logger.error(f"     {line}")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur lors du déploiement NiFi: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

class MLEngineStarter:
    """Démarre les moteurs ML"""

    def __init__(self):
        self.resolver = PathResolver()
        self.ml_processes = []

    def start(self):
        """Démarre les services ML"""
        print("\n" + "="*60)
        logger.info("Étape 3 : Moteurs d'Intelligence Artificielle")
        print("="*60)

        # Définir les scripts ML
        ml_scripts = [
            ("A9 - Oracle", "cloud_citadel/nervous_system/oracle.py"),
            ("A10 - Classifier", "cloud_citadel/nervous_system/classifier.py"),
            ("A11 - Cortex", "cloud_citadel/nervous_system/cortex.py")
        ]

        started_count = 0
        logs_dir = PROJECT_ROOT / "logs"
        logs_dir.mkdir(exist_ok=True)

        for name, rel_path in ml_scripts:
            script_path = self.resolver.get_absolute_path(rel_path)

            if not script_path.exists():
                logger.warning(f"⚠️ {name}: {script_path} introuvable")
                continue

            logger.info(f"🚀 Lancement {name}...")

            try:
                # Créer le fichier log
                log_file = logs_dir / f"{name.lower().replace(' - ', '_').replace(' ', '_')}.log"

                # Exécuter depuis la racine du projet
                original_cwd = os.getcwd()
                os.chdir(PROJECT_ROOT)

                process = subprocess.Popen(
                    [sys.executable, str(rel_path)],
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT,
                    text=True
                )

                os.chdir(original_cwd)

                self.ml_processes.append((name, process, log_file))
                started_count += 1

                logger.info(f"   ✅ PID: {process.pid}, Logs: {log_file}")

                time.sleep(1)  # Pause entre les lancements

            except Exception as e:
                logger.error(f"❌ Erreur lancement {name}: {e}")

        # Vérification
        if started_count == 0:
            logger.warning("⚠️ Aucun service ML démarré")
            logger.info("💡 Vérifiez que les scripts ML existent dans cloud_citadel/nervous_system/")
            return False

        logger.info(f"\n📊 {started_count}/{len(ml_scripts)} services ML démarrés")

        # Attendre et vérifier
        time.sleep(3)
        active_count = 0
        for name, process, log_file in self.ml_processes:
            if process.poll() is None:
                active_count += 1
                logger.info(f"   🔄 {name} toujours actif")
            else:
                returncode = process.returncode
                status = "terminé proprement" if returncode == 0 else f"terminé (code: {returncode})"
                logger.info(f"   ℹ️ {name} {status}")

                # Lire les dernières lignes du log
                try:
                    if log_file.exists():
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            if lines:
                                logger.info(f"     Dernières lignes:")
                                for line in lines[-2:]:
                                    logger.info(f"       {line.strip()}")
                except:
                    pass

        if active_count > 0:
            logger.info(f"✅ {active_count} services ML actifs")
        else:
            logger.info("ℹ️ Services ML exécutés et terminés (mode batch probable)")

        return True

    def stop(self):
        """Arrête les services ML"""
        logger.info("🛑 Arrêt des services ML...")
        for name, process, _ in self.ml_processes:
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                    logger.info(f"   ✅ {name} arrêté")
                except:
                    try:
                        process.kill()
                        logger.warning(f"   ⚠️ {name} tué (force)")
                    except:
                        logger.error(f"   ❌ Erreur arrêt {name}")

class IoTSimulatorLauncher:
    """Démarre le simulateur IoT"""

    @staticmethod
    def start():
        """Démarre le simulateur IoT si demandé"""
        print("\n" + "="*60)
        logger.info("Étape 4 : Simulateur IoT (Optionnel)")
        print("="*60)

        if not ("--full" in sys.argv or "--iot" in sys.argv):
            logger.info("ℹ️ Simulateur IoT non demandé (utilisez --full ou --iot)")
            return None

        # Chercher le simulateur
        simulator_paths = [
            ("scripts/simulators/kafka_telemetry_producer.py", "Simulateur standard"),
            ("kafka_telemetry_producer.py", "Simulateur à la racine"),
        ]

        resolver = PathResolver()
        simulator_script = resolver.check_path_exists("Simulateur IoT", simulator_paths)

        if not simulator_script:
            logger.warning("⚠️ Script simulateur IoT introuvable")
            return None

        logger.info(f"🛰️ Lancement simulateur IoT: {simulator_script}")

        try:
            logs_dir = PROJECT_ROOT / "logs"
            logs_dir.mkdir(exist_ok=True)

            log_file = logs_dir / "iot_simulator.log"

            # Exécuter depuis la racine
            original_cwd = os.getcwd()
            os.chdir(PROJECT_ROOT)

            # Chemin relatif
            if simulator_script.is_relative_to(PROJECT_ROOT):
                rel_path = simulator_script.relative_to(PROJECT_ROOT)
            else:
                rel_path = simulator_script

            process = subprocess.Popen(
                [sys.executable, str(rel_path)],
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                text=True
            )

            os.chdir(original_cwd)

            logger.info(f"✅ Simulateur IoT lancé (PID: {process.pid}, Logs: {log_file})")
            return process

        except Exception as e:
            logger.error(f"❌ Erreur lancement simulateur: {e}")
            return None

def shutdown_handler(sig, frame):
    """Gestionnaire d'arrêt"""
    print("\n" + "="*60)
    logger.info("🛑 Arrêt orchestrateur VertiFlow...")
    print("="*60)

    global processes
    global ml_starter

    # Arrêter IoT
    for proc in processes:
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except:
                pass

    # Arrêter ML
    if 'ml_starter' in globals():
        ml_starter.stop()

    logger.info("✅ Arrêt terminé")
    sys.exit(0)

async def main_async():
    """Fonction principale asynchrone"""
    global processes, ml_starter

    # Configuration
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Créer logs
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)

    print("\n" + "="*70)
    print("🚀 ORCHESTRATEUR VERTIFLOW - EXÉCUTION CORRECTE")
    print("="*70)
    print(f"📅 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Répertoire racine: {PROJECT_ROOT}")
    print(f"📁 Script actuel: {SCRIPT_DIR}")
    print("="*70)

    # 1. Test infrastructure
    tester = InfrastructureTester()
    if not await tester.run_comprehensive_test():
        logger.warning("⚠️ Tests infrastructure échoués, poursuite quand même")

    # 2. Données (déjà fait par le script parent)
    data_init = DataInitializer()
    data_init.initialize()

    # 3. NiFi
    nifi_deployer = NiFiDeployer()
    nifi_success = nifi_deployer.deploy()

    # 4. ML
    ml_starter = MLEngineStarter()
    ml_success = ml_starter.start()

    # 5. IoT optionnel
    iot_process = IoTSimulatorLauncher.start()
    if iot_process:
        processes.append(iot_process)

    # 6. Dashboard final
    print("\n" + "="*70)
    logger.info("⭐ VERTIFLOW - SYSTÈME DÉPLOYÉ")
    print("="*70)

    logger.info("\n📊 ÉTAT FINAL:")
    logger.info(f"   • Pipeline NiFi: {'✅ DÉPLOYÉ' if nifi_success else '❌ ÉCHEC'}")
    logger.info(f"   • Services ML: {'✅ ACTIFS' if ml_success else '⚠️ PROBLÈMES'}")
    logger.info(f"   • Simulateur IoT: {'✅ ACTIF' if iot_process else '❌ INACTIF'}")

    logger.info("\n🌐 INTERFACES:")
    logger.info("   • NiFi: https://localhost:8443/nifi")
    logger.info("   • Kafka: localhost:9092")
    logger.info("   • ClickHouse: http://localhost:8123")
    logger.info("   • MongoDB: mongodb://localhost:27017")

    logger.info("\n📁 SURVEILLANCE:")
    logger.info(f"   • Logs: {PROJECT_ROOT / 'logs'}")
    logger.info("   • Commandes:")
    logger.info("     tail -f logs/*.log")
    logger.info("     docker compose logs --tail=20")

    logger.info("\n🛑 ARRÊT: Ctrl+C")
    print("="*70)

    return True

def main():
    """Point d'entrée"""
    print(f"🔧 Initialisation depuis: {os.getcwd()}")

    try:
        success = asyncio.run(main_async())

        if success:
            # Surveillance simple
            logger.info("\n👁️ Surveillance en cours... (Ctrl+C pour arrêter)")
            try:
                while True:
                    time.sleep(5)
                    # Vérification légère
                    pass
            except KeyboardInterrupt:
                logger.info("\n🎯 Arrêt demandé")
                shutdown_handler(None, None)

        return 0

    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # S'assurer qu'on exécute depuis le bon endroit
    current_dir = Path.cwd()
    expected_script_dir = PROJECT_ROOT / "scripts"

    if current_dir != expected_script_dir and SCRIPT_DIR == expected_script_dir:
        logger.debug(f"📁 On est dans {current_dir}, script est dans {SCRIPT_DIR}")
        logger.debug(f"📁 Racine projet: {PROJECT_ROOT}")

    sys.exit(main())