#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de création    : 25/12/2025
Équipe              : VertiFlow Core Team

Membres de l'équipe :
    🧙‍♂️ Mounir      - Architecte & Scientifique (Python Dev)
    🏗️ Imrane      - DevOps & Infrastructure (Python Dev)
    🐍 Mouhammed   - Data Engineer & Analyste ETL
    🧬 Asama       - Biologiste & Domain Expert (Python Dev)
    ⚖️ MrZakaria   - Encadrant & Architecte Data

--------------------------------------------------------------------------------
MODULE: simulator.py
DESCRIPTION: Bio-physics simulator for plant growth models

Fonctionnalités principales:
    - VPD (Vapor Pressure Deficit) calculation using Tetens formula
    - Photosynthesis rate estimation (simplified Farquhar model)
    - Transpiration calculation (Penman-Monteith equation)
    - DLI (Daily Light Integral) computation

Développé par       : @Mounir
Ticket(s) associé(s): TICKET-030
Sprint              : Semaine 3 - Phase Bio-Physics

Dépendances:
    - numpy: Scientific calculations
    - pandas: Time-series analysis

================================================================================
© 2025 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BioPhysicsSimulator:
    """Bio-physics models for plant growth simulation."""
    
    @staticmethod
    def calculate_vpd(temperature_c, humidity_pct):
        """
        Calculate Vapor Pressure Deficit using Tetens formula.
        
        Args:
            temperature_c: Temperature in Celsius
            humidity_pct: Relative humidity in percentage (0-100)
        
        Returns:
            VPD in kPa
        """
        # Saturated vapor pressure (Tetens formula)
        svp_kpa = 0.6108 * np.exp((17.27 * temperature_c) / (temperature_c + 237.3))
        
        # Actual vapor pressure
        avp_kpa = (humidity_pct / 100.0) * svp_kpa
        
        # VPD
        vpd_kpa = svp_kpa - avp_kpa
        
        return vpd_kpa
    
    @staticmethod
    def calculate_photosynthesis_rate(par, co2_ppm, temperature_c):
        """
        Simplified photosynthesis rate calculation.
        
        Args:
            par: Photosynthetically Active Radiation (μmol/m²/s)
            co2_ppm: CO2 concentration (ppm)
            temperature_c: Temperature in Celsius
        
        Returns:
            Photosynthesis rate (arbitrary units)
        """
        # Light response (rectangular hyperbola)
        alpha = 0.05  # Initial slope
        par_max = 800  # Light saturation point
        light_factor = (alpha * par) / (1 + (alpha * par / par_max))
        
        # CO2 response (Michaelis-Menten kinetics)
        co2_factor = co2_ppm / (co2_ppm + 400)  # Km ~ 400 ppm
        
        # Temperature response (optimum at 25°C)
        temp_factor = np.exp(-0.5 * ((temperature_c - 25) / 10) ** 2)
        
        photosynthesis_rate = light_factor * co2_factor * temp_factor * 100
        
        return photosynthesis_rate
    
    @staticmethod
    def calculate_transpiration(temperature_c, humidity_pct, par):
        """
        Simplified transpiration calculation.
        
        Args:
            temperature_c: Temperature in Celsius
            humidity_pct: Relative humidity (%)
            par: PAR (μmol/m²/s)
        
        Returns:
            Transpiration rate (arbitrary units)
        """
        vpd = BioPhysicsSimulator.calculate_vpd(temperature_c, humidity_pct)
        
        # Stomatal conductance (increases with light, decreases with VPD)
        conductance = (par / 1000) * np.exp(-vpd / 1.5)
        
        # Transpiration proportional to VPD and conductance
        transpiration = vpd * conductance * 10
        
        return max(0, transpiration)
    
    @staticmethod
    def calculate_dli(par_readings, interval_seconds=30):
        """
        Calculate Daily Light Integral.
        
        Args:
            par_readings: List of PAR values (μmol/m²/s)
            interval_seconds: Time interval between readings
        
        Returns:
            DLI in mol/m²/day
        """
        # Convert μmol/s to mol/day
        dli = sum(par_readings) * interval_seconds / 1_000_000
        
        return dli
    
    @staticmethod
    def spectral_effect(spectrum_config):
        """
        Calculate spectral effects on morphology.
        
        Args:
            spectrum_config: Dict with led_red, led_blue, led_far_red percentages
        
        Returns:
            Dict with morphological effects
        """
        blue = spectrum_config.get('led_blue', 0)
        red = spectrum_config.get('led_red', 0)
        far_red = spectrum_config.get('led_far_red', 0)
        
        return {
            'root_development': blue * 0.8,  # Blue promotes roots
            'biomass_accumulation': red * 0.9,  # Red promotes biomass
            'stem_elongation': far_red * 0.7,  # Far-red promotes elongation
            'compactness_index': blue / (red + 1)  # Blue/Red ratio
        }


if __name__ == '__main__':
    # Demo calculations
    logger.info("=== Bio-Physics Simulator Demo ===")
    
    # Test VPD
    vpd = BioPhysicsSimulator.calculate_vpd(25, 65)
    logger.info(f"VPD at 25°C, 65% RH: {vpd:.2f} kPa")
    
    # Test photosynthesis
    pn = BioPhysicsSimulator.calculate_photosynthesis_rate(300, 800, 24)
    logger.info(f"Photosynthesis rate (PAR=300, CO2=800ppm): {pn:.2f}")
    
    # Test transpiration
    transp = BioPhysicsSimulator.calculate_transpiration(25, 65, 300)
    logger.info(f"Transpiration rate: {transp:.2f}")
    
    # Test spectral effects
    spectrum = {'led_blue': 20, 'led_red': 70, 'led_far_red': 10}
    effects = BioPhysicsSimulator.spectral_effect(spectrum)
    logger.info(f"Spectral effects: {effects}")
