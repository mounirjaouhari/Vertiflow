#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Lanceur de Tous les Simulateurs
================================================================================
Date de creation    : 04/01/2026
Equipe              : VertiFlow Core Team

--------------------------------------------------------------------------------
MODULE: run_all_simulators.py
DESCRIPTION: Script pour lancer tous les simulateurs en parallele

Fonctionnalites:
    - Lance les simulateurs IoT, LED, Nutriments en processus separes
    - Gestion des signaux d'arret propre
    - Logging centralise
    - Mode daemon disponible

Usage:
    python run_all_simulators.py                    # Mode interactif
    python run_all_simulators.py --duration 3600   # 1 heure
    python run_all_simulators.py --once            # Une seule iteration

================================================================================
2025-2026 VertiFlow Core Team
================================================================================
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from datetime import datetime
from typing import List, Optional
import threading

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIMULATORS_DIR = os.path.join(SCRIPT_DIR, "simulators")

SIMULATORS = [
    {
        "name": "IoT Sensors",
        "script": os.path.join(SIMULATORS_DIR, "iot_sensor_simulator.py"),
        "enabled": True
    },
    {
        "name": "LED Spectrum",
        "script": os.path.join(SIMULATORS_DIR, "led_spectrum_simulator.py"),
        "enabled": True
    },
    {
        "name": "Nutrient Sensors",
        "script": os.path.join(SIMULATORS_DIR, "nutrient_sensor_simulator.py"),
        "enabled": True
    }
]

# Variables globales pour gestion des processus
processes: List[subprocess.Popen] = []
running = True


def signal_handler(signum, frame):
    """Gestionnaire de signaux pour arret propre."""
    global running
    print("\n[MAIN] Signal d'arret recu, fermeture des simulateurs...")
    running = False
    stop_all_simulators()


def start_simulator(sim_config: dict) -> Optional[subprocess.Popen]:
    """Demarre un simulateur individuel."""
    if not sim_config["enabled"]:
        return None

    script_path = sim_config["script"]
    if not os.path.exists(script_path):
        print(f"[ERROR] Script non trouve: {script_path}")
        return None

    try:
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"[OK] {sim_config['name']} demarre (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"[ERROR] Impossible de demarrer {sim_config['name']}: {e}")
        return None


def monitor_process(process: subprocess.Popen, name: str):
    """Monitore la sortie d'un processus."""
    try:
        for line in process.stdout:
            print(f"[{name}] {line.strip()}")
    except:
        pass


def stop_all_simulators():
    """Arrete tous les simulateurs."""
    global processes
    for proc in processes:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    processes = []


def run_once():
    """Execute une seule iteration de generation de donnees."""
    print("=" * 70)
    print("VERTIFLOW - Generation de Donnees (Mode Single)")
    print("=" * 70)

    # Importer et executer le generateur de donnees de test
    test_data_script = os.path.join(SCRIPT_DIR, "generate_nifi_test_data.py")

    if os.path.exists(test_data_script):
        print("Execution du generateur de donnees de test...")
        result = subprocess.run([sys.executable, test_data_script], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Erreur: {result.stderr}")
    else:
        print(f"Script non trouve: {test_data_script}")


def main():
    """Point d'entree principal."""
    global processes, running

    parser = argparse.ArgumentParser(description="VertiFlow Simulators Launcher")
    parser.add_argument("--duration", "-d", type=int, default=0,
                       help="Duree d'execution en secondes (0 = indefini)")
    parser.add_argument("--once", "-1", action="store_true",
                       help="Executer une seule fois et quitter")
    parser.add_argument("--list", "-l", action="store_true",
                       help="Lister les simulateurs disponibles")

    args = parser.parse_args()

    # Mode liste
    if args.list:
        print("Simulateurs disponibles:")
        for sim in SIMULATORS:
            status = "actif" if sim["enabled"] else "inactif"
            exists = "OK" if os.path.exists(sim["script"]) else "MANQUANT"
            print(f"  - {sim['name']}: {status} [{exists}]")
        return

    # Mode single
    if args.once:
        run_once()
        return

    # Mode continu
    print("=" * 70)
    print("VERTIFLOW - Lanceur de Simulateurs")
    print("=" * 70)
    print(f"Demarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.duration > 0:
        print(f"Duree: {args.duration} secondes")
    else:
        print("Duree: Indefinie (Ctrl+C pour arreter)")
    print("-" * 70)

    # Configuration des signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Demarrer les simulateurs
    threads = []
    for sim in SIMULATORS:
        proc = start_simulator(sim)
        if proc:
            processes.append(proc)

            # Thread de monitoring
            t = threading.Thread(target=monitor_process, args=(proc, sim["name"][:3].upper()))
            t.daemon = True
            t.start()
            threads.append(t)

    if not processes:
        print("[ERROR] Aucun simulateur demarre!")
        return

    print("-" * 70)
    print(f"{len(processes)} simulateur(s) actif(s)")

    # Boucle principale
    start_time = time.time()
    try:
        while running:
            # Verifier si les processus sont toujours actifs
            for i, proc in enumerate(processes):
                if proc and proc.poll() is not None:
                    print(f"[WARNING] Simulateur {i} termine (code: {proc.returncode})")

            # Verifier la duree
            if args.duration > 0:
                elapsed = time.time() - start_time
                if elapsed >= args.duration:
                    print(f"\n[MAIN] Duree atteinte ({args.duration}s)")
                    break

            time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        print("\n[MAIN] Arret des simulateurs...")
        stop_all_simulators()
        print("[MAIN] Termine.")


if __name__ == "__main__":
    main()
