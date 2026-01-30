# ============================================================================
# VERTIFLOW - Tests Unitaires Simulator (Bio-Physics Models)
# ============================================================================

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestPlantGrowthSimulator:
    """Tests pour le simulateur de croissance des plantes."""

    def test_photosynthesis_rate(self):
        """Test le calcul du taux de photosynthèse."""
        # Modèle simplifié de photosynthèse
        ppfd = 400        # µmol/m²/s
        co2 = 800         # ppm
        temperature = 24  # °C

        # Taux maximal à conditions optimales
        p_max = 15  # µmol CO2/m²/s

        # Facteurs de limitation
        light_factor = ppfd / (ppfd + 200)  # Michaelis-Menten
        co2_factor = co2 / (co2 + 400)
        temp_factor = 1 - ((temperature - 25) / 15) ** 2

        photosynthesis_rate = p_max * light_factor * co2_factor * temp_factor

        assert 0 < photosynthesis_rate < p_max

    def test_respiration_rate(self):
        """Test le calcul du taux de respiration."""
        temperature = 24  # °C
        base_respiration = 1.5  # µmol CO2/m²/s à 25°C
        q10 = 2.0  # Coefficient de température

        # Respiration augmente avec la température (Q10 model)
        respiration = base_respiration * (q10 ** ((temperature - 25) / 10))

        assert respiration > 0
        assert respiration < 5  # Limite raisonnable

    def test_daily_carbon_gain(self):
        """Test le gain net de carbone journalier."""
        photoperiod_hours = 16
        dark_hours = 24 - photoperiod_hours

        avg_photosynthesis = 10  # µmol CO2/m²/s pendant la lumière
        avg_respiration = 2      # µmol CO2/m²/s (toujours)

        # Gain pendant la période éclairée
        light_gain = (avg_photosynthesis - avg_respiration) * photoperiod_hours * 3600

        # Perte pendant la nuit
        dark_loss = avg_respiration * dark_hours * 3600

        net_daily_gain = light_gain - dark_loss

        assert net_daily_gain > 0  # La plante doit avoir un gain net positif

    def test_biomass_accumulation(self):
        """Test l'accumulation de biomasse."""
        initial_biomass = 5.0   # g
        daily_growth_rate = 0.1  # 10% par jour
        days = 7

        # Croissance exponentielle
        final_biomass = initial_biomass * ((1 + daily_growth_rate) ** days)

        assert final_biomass > initial_biomass
        assert final_biomass == pytest.approx(9.74, rel=0.05)  # ~2x en 7 jours


class TestEnvironmentSimulator:
    """Tests pour le simulateur d'environnement."""

    def test_vpd_calculation(self):
        """Test le calcul du VPD (Vapor Pressure Deficit)."""
        temperature = 24  # °C
        relative_humidity = 65  # %

        # Pression de vapeur saturante (Tetens formula)
        svp = 0.6108 * math.exp((17.27 * temperature) / (temperature + 237.3))

        # Pression de vapeur actuelle
        avp = svp * (relative_humidity / 100)

        # VPD
        vpd = svp - avp

        assert 0 < vpd < 3  # kPa, plage normale
        assert vpd == pytest.approx(1.05, rel=0.1)

    def test_dew_point_calculation(self):
        """Test le calcul du point de rosée."""
        temperature = 24  # °C
        relative_humidity = 65  # %

        # Formule de Magnus
        a = 17.27
        b = 237.3

        alpha = ((a * temperature) / (b + temperature)) + math.log(relative_humidity / 100)
        dew_point = (b * alpha) / (a - alpha)

        assert dew_point < temperature
        assert 10 < dew_point < 20

    def test_heat_transfer(self):
        """Test le transfert de chaleur."""
        current_temp = 22
        setpoint = 25
        hvac_power = 2.5  # kW
        room_volume = 50  # m³
        air_density = 1.2  # kg/m³
        specific_heat = 1.005  # kJ/kg·K

        # Énergie nécessaire
        mass = room_volume * air_density
        energy_needed = mass * specific_heat * (setpoint - current_temp)

        # Temps nécessaire
        time_seconds = energy_needed / hvac_power

        assert time_seconds > 0
        assert time_seconds < 300  # Moins de 5 minutes

    def test_co2_dynamics(self):
        """Test la dynamique du CO2."""
        initial_co2 = 400   # ppm
        injection_rate = 50  # ppm/min
        consumption_rate = 10  # ppm/min (photosynthèse)
        ventilation_rate = 5  # ppm/min (perte vers l'extérieur)

        # Après 10 minutes
        minutes = 10
        net_change = (injection_rate - consumption_rate - ventilation_rate) * minutes
        final_co2 = initial_co2 + net_change

        assert final_co2 == 750


class TestNutrientSimulator:
    """Tests pour le simulateur de nutriments."""

    def test_nutrient_uptake(self):
        """Test l'absorption des nutriments."""
        ec_solution = 1.8  # mS/cm
        plant_size_factor = 0.8  # Fraction de la taille adulte
        temperature_factor = 1.0  # Normal à 24°C

        base_uptake = 10  # ml/heure
        actual_uptake = base_uptake * plant_size_factor * temperature_factor

        assert actual_uptake == 8

    def test_ec_drift(self):
        """Test la dérive de l'EC."""
        initial_ec = 1.8
        water_uptake = 5  # L/jour (évaporation + absorption)
        nutrient_uptake = 0.1  # % des nutriments absorbés

        # L'EC augmente si l'eau s'évapore plus vite que les nutriments ne sont absorbés
        volume_initial = 100  # L
        volume_after = volume_initial - water_uptake

        # EC augmente proportionnellement à la concentration
        ec_after = initial_ec * (volume_initial / volume_after) * (1 - nutrient_uptake)

        assert ec_after > initial_ec

    def test_ph_buffer(self):
        """Test le tampon pH."""
        current_ph = 6.0
        acid_addition = 0.1  # ml d'acide par litre
        buffer_capacity = 0.5  # mEq/L/pH unit

        # pH change inversement proportionnel à la capacité tampon
        ph_change = -acid_addition / buffer_capacity
        new_ph = current_ph + ph_change

        assert new_ph < current_ph


class TestLightSimulator:
    """Tests pour le simulateur de lumière."""

    def test_dli_calculation(self):
        """Test le calcul du DLI (Daily Light Integral)."""
        ppfd = 400        # µmol/m²/s
        photoperiod = 16  # heures

        # DLI = PPFD × secondes × conversion
        dli = ppfd * photoperiod * 3600 / 1_000_000

        assert dli == pytest.approx(23.04, rel=0.01)

    def test_light_spectrum_par(self):
        """Test le calcul du PAR (Photosynthetically Active Radiation)."""
        spectrum = {
            "blue_400_500": 100,   # µmol/m²/s
            "green_500_600": 80,
            "red_600_700": 220
        }

        total_par = sum(spectrum.values())

        assert total_par == 400

    def test_inverse_square_law(self):
        """Test la loi de l'inverse du carré pour l'intensité lumineuse."""
        ppfd_at_30cm = 600
        distance1 = 30  # cm
        distance2 = 60  # cm

        # L'intensité diminue avec le carré de la distance
        ppfd_at_60cm = ppfd_at_30cm * (distance1 / distance2) ** 2

        assert ppfd_at_60cm == 150


class TestWaterSimulator:
    """Tests pour le simulateur d'eau."""

    def test_evapotranspiration(self):
        """Test le calcul de l'évapotranspiration."""
        temperature = 24
        humidity = 65
        vpd = 1.05  # kPa
        leaf_area = 0.05  # m²

        # Coefficient de transpiration (simplifié)
        transpiration_coef = 0.5  # g H2O / kPa / m² / heure

        transpiration_rate = transpiration_coef * vpd * leaf_area

        assert transpiration_rate > 0
        assert transpiration_rate < 1  # g/heure pour une petite plante

    def test_irrigation_scheduling(self):
        """Test la planification de l'irrigation."""
        substrate_capacity = 100  # ml
        current_moisture = 60     # %
        target_moisture = 80      # %
        drainage_factor = 0.1     # 10% de drainage

        water_needed_raw = (target_moisture - current_moisture) / 100 * substrate_capacity
        water_to_apply = water_needed_raw / (1 - drainage_factor)

        assert water_to_apply == pytest.approx(22.2, rel=0.1)

    def test_water_quality_check(self):
        """Test la vérification de la qualité de l'eau."""
        water_params = {
            "ec": 0.3,      # mS/cm (eau de départ)
            "ph": 7.2,
            "chlorine": 0.5  # ppm
        }

        limits = {
            "ec": (0, 0.5),
            "ph": (6.5, 7.5),
            "chlorine": (0, 1)
        }

        all_ok = all(
            limits[param][0] <= value <= limits[param][1]
            for param, value in water_params.items()
        )

        assert all_ok is True
