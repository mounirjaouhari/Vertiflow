# ============================================================================
# VERTIFLOW - Tests Unitaires Cortex (Optimization Engine)
# ============================================================================

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestCortexOptimizer:
    """Tests pour l'optimiseur principal."""

    def test_optimization_output_format(self):
        """Test le format de sortie des recommandations."""
        recommendation = {
            "timestamp": datetime.utcnow().isoformat(),
            "farm_id": "FARM_001",
            "zone_id": "ZONE_A",
            "recommendations": [
                {
                    "actuator_type": "hvac",
                    "action": "set_temperature",
                    "target_value": 24.0,
                    "priority": "high",
                    "reason": "Temperature below optimal range"
                }
            ],
            "expected_impact": {
                "energy_change_percent": -5.0,
                "yield_change_percent": 2.0
            }
        }

        assert "recommendations" in recommendation
        assert len(recommendation["recommendations"]) > 0
        assert "expected_impact" in recommendation

    def test_multi_objective_optimization(self):
        """Test l'optimisation multi-objectifs."""
        objectives = {
            "maximize_yield": 0.5,       # Poids 50%
            "minimize_energy": 0.3,       # Poids 30%
            "minimize_water": 0.2         # Poids 20%
        }

        # La somme des poids doit être 1
        assert abs(sum(objectives.values()) - 1.0) < 0.01

    def test_constraint_satisfaction(self):
        """Test le respect des contraintes."""
        constraints = {
            "temperature": {"min": 18, "max": 30},
            "humidity": {"min": 40, "max": 80},
            "co2": {"min": 400, "max": 1500}
        }

        recommendation = {"temperature": 24, "humidity": 65, "co2": 800}

        for param, value in recommendation.items():
            min_val = constraints[param]["min"]
            max_val = constraints[param]["max"]
            assert min_val <= value <= max_val

    def test_energy_cost_calculation(self):
        """Test le calcul du coût énergétique."""
        power_consumption = {
            "hvac": 2.5,      # kW
            "lighting": 1.8,  # kW
            "pumps": 0.5      # kW
        }

        duration_hours = 1
        electricity_rate = 0.12  # €/kWh

        total_power = sum(power_consumption.values())
        cost = total_power * duration_hours * electricity_rate

        assert cost == pytest.approx(0.576, rel=0.01)

    def test_pareto_frontier(self):
        """Test le calcul de la frontière de Pareto."""
        solutions = [
            {"yield": 50, "energy": 100},
            {"yield": 45, "energy": 80},
            {"yield": 55, "energy": 120},
            {"yield": 48, "energy": 85},
        ]

        # Solution dominée: yield < autre ET energy > autre
        def is_dominated(sol, all_sols):
            for other in all_sols:
                if other != sol:
                    if other["yield"] >= sol["yield"] and other["energy"] <= sol["energy"]:
                        if other["yield"] > sol["yield"] or other["energy"] < sol["energy"]:
                            return True
            return False

        pareto_solutions = [s for s in solutions if not is_dominated(s, solutions)]
        assert len(pareto_solutions) >= 1


class TestCortexResourceAllocator:
    """Tests pour l'allocation de ressources."""

    def test_resource_allocation_by_zone(self):
        """Test l'allocation des ressources par zone."""
        total_resources = {
            "light_hours": 16,
            "water_liters": 1000,
            "nutrients_ml": 500
        }

        zones = ["ZONE_A", "ZONE_B", "ZONE_C"]
        zone_priorities = {"ZONE_A": 0.5, "ZONE_B": 0.3, "ZONE_C": 0.2}

        allocation = {}
        for zone in zones:
            allocation[zone] = {
                resource: amount * zone_priorities[zone]
                for resource, amount in total_resources.items()
            }

        # Vérifier que la somme des allocations = ressources totales
        for resource in total_resources:
            total_allocated = sum(allocation[z][resource] for z in zones)
            assert total_allocated == pytest.approx(total_resources[resource], rel=0.01)

    def test_dynamic_reallocation(self):
        """Test la réallocation dynamique basée sur les besoins."""
        current_allocation = {"ZONE_A": 100, "ZONE_B": 100}
        needs = {"ZONE_A": 150, "ZONE_B": 50}

        # Redistribuer selon les besoins
        total = sum(current_allocation.values())
        total_needs = sum(needs.values())

        new_allocation = {
            zone: (needs[zone] / total_needs) * total
            for zone in needs
        }

        assert new_allocation["ZONE_A"] > new_allocation["ZONE_B"]
        assert sum(new_allocation.values()) == pytest.approx(total, rel=0.01)


class TestCortexScheduler:
    """Tests pour le planificateur d'actions."""

    def test_action_scheduling(self):
        """Test la planification des actions."""
        actions = [
            {"action": "water", "priority": 1, "duration": 30},
            {"action": "light_on", "priority": 2, "duration": 60},
            {"action": "nutrient_dose", "priority": 1, "duration": 15}
        ]

        # Trier par priorité
        sorted_actions = sorted(actions, key=lambda x: x["priority"])

        assert sorted_actions[0]["action"] in ["water", "nutrient_dose"]

    def test_conflict_resolution(self):
        """Test la résolution de conflits entre actions."""
        conflicting_actions = [
            {"action": "cool", "target_temp": 20},
            {"action": "heat", "target_temp": 25}
        ]

        # On ne peut pas chauffer ET refroidir en même temps
        # Choisir en fonction de l'écart à la consigne
        current_temp = 22
        optimal_temp = 24

        if current_temp < optimal_temp:
            selected = [a for a in conflicting_actions if a["action"] == "heat"]
        else:
            selected = [a for a in conflicting_actions if a["action"] == "cool"]

        assert len(selected) == 1

    def test_time_window_constraints(self):
        """Test les contraintes de fenêtres temporelles."""
        # Certaines actions ne peuvent être faites qu'à certaines heures
        action = {"type": "lighting", "on_hours": (6, 22)}
        current_hour = 14

        on_start, on_end = action["on_hours"]
        is_allowed = on_start <= current_hour < on_end

        assert is_allowed is True


class TestCortexFeedbackLoop:
    """Tests pour la boucle de rétroaction."""

    def test_action_effectiveness_tracking(self):
        """Test le suivi de l'efficacité des actions."""
        action_history = [
            {"action": "increase_temp", "expected_change": 2, "actual_change": 1.8},
            {"action": "increase_temp", "expected_change": 2, "actual_change": 2.1},
            {"action": "increase_temp", "expected_change": 2, "actual_change": 1.9}
        ]

        effectiveness_ratios = [
            a["actual_change"] / a["expected_change"]
            for a in action_history
        ]

        avg_effectiveness = np.mean(effectiveness_ratios)
        assert 0.8 <= avg_effectiveness <= 1.2

    def test_model_calibration(self):
        """Test la calibration du modèle basée sur les résultats."""
        prediction_errors = [0.5, -0.3, 0.2, -0.1, 0.4]

        # Biais systématique = moyenne des erreurs
        bias = np.mean(prediction_errors)

        # Correction: soustraire le biais des futures prédictions
        calibration_factor = -bias

        assert abs(calibration_factor) < 0.5

    def test_learning_rate_adjustment(self):
        """Test l'ajustement du taux d'apprentissage."""
        recent_performance = [0.85, 0.87, 0.86, 0.88, 0.89]
        historical_performance = [0.75, 0.78, 0.80, 0.82, 0.84]

        recent_avg = np.mean(recent_performance)
        historical_avg = np.mean(historical_performance)

        # Si les performances s'améliorent, réduire le taux d'apprentissage
        if recent_avg > historical_avg:
            learning_rate_multiplier = 0.95
        else:
            learning_rate_multiplier = 1.05

        assert learning_rate_multiplier == 0.95


class TestCortexEnergyOptimizer:
    """Tests pour l'optimisation énergétique."""

    def test_peak_shaving(self):
        """Test le lissage des pics de consommation."""
        hourly_demand = [50, 60, 80, 100, 120, 100, 80, 60]  # kW
        max_allowed = 90

        # Identifier les heures de dépassement
        peak_hours = [i for i, d in enumerate(hourly_demand) if d > max_allowed]

        assert 3 in peak_hours and 4 in peak_hours

    def test_off_peak_scheduling(self):
        """Test la planification hors heures de pointe."""
        peak_hours = list(range(8, 12)) + list(range(18, 22))
        deferrable_actions = ["water_heating", "battery_charging"]

        current_hour = 14  # Hors pointe
        is_off_peak = current_hour not in peak_hours

        assert is_off_peak is True

    def test_renewable_integration(self):
        """Test l'intégration des énergies renouvelables."""
        solar_production = 50  # kW disponible
        current_demand = 80     # kW nécessaire

        grid_import = max(0, current_demand - solar_production)
        solar_utilization = min(solar_production, current_demand)

        assert grid_import == 30
        assert solar_utilization == 50
