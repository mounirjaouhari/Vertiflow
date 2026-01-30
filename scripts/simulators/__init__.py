#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Simulateurs de Donnees
================================================================================
Package contenant les simulateurs de donnees pour tests et developpement.

Simulateurs disponibles:
    - iot_sensor_simulator: Capteurs environnementaux (temperature, humidite, CO2)
    - led_spectrum_simulator: Spectres LED et metriques lumineuses
    - nutrient_sensor_simulator: Capteurs nutrition (EC, pH, NPK)
    - lab_data_generator: Donnees d'analyses laboratoire
    - vision_system_simulator: Systeme de vision (biomasse, sante)

Usage:
    # Lancer un simulateur individuel
    python -m scripts.simulators.iot_sensor_simulator

    # Ou importer dans un script
    from scripts.simulators import iot_sensor_simulator
    iot_sensor_simulator.main()

================================================================================
2025-2026 VertiFlow Core Team
================================================================================
"""

from . import iot_sensor_simulator
from . import led_spectrum_simulator
from . import nutrient_sensor_simulator
from . import lab_data_generator

__all__ = [
    'iot_sensor_simulator',
    'led_spectrum_simulator',
    'nutrient_sensor_simulator',
    'lab_data_generator'
]

__version__ = "1.0.0"
