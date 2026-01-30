import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration des paramètres
num_cycles = 6
days_per_cycle = 35
groups = ['G1_Control', 'G3_VertiFlow']
frequency_minutes = 1  # Haute résolution pour atteindre ~50Mo

# Calcul du nombre total de lignes
total_rows = num_cycles * days_per_cycle * 24 * 60 * len(groups)
print(f"Génération de {total_rows} lignes...")

# Création des séquences temporelles
start_date = datetime(2025, 1, 1)
timestamps = [start_date + timedelta(minutes=i) for i in range(num_cycles * days_per_cycle * 24 * 60)]

data_list = []

for cycle in range(1, num_cycles + 1):
    for group in groups:
        for day in range(days_per_cycle):
            # Simulation des cycles circadiens (24h)
            for minute in range(1440):
                # Facteurs de base
                is_day = 6 <= (minute // 60) <= 18
                
                # Physique du groupe G1 (Statique)
                if group == 'G1_Control':
                    temp = 24.0 + np.random.normal(0, 0.5)
                    energy = 0.5 if is_day else 0.1
                    co2 = 400 + np.random.normal(0, 10)
                    yield_sim = 0.01 * (day + 1)**1.5 # Croissance basique
                
                # Physique du groupe G3 (Auto-adaptatif - Opti Energie & Bio)
                else:
                    # G3 adapte la température et optimise l'énergie (-31.8%)
                    temp = (22.0 if is_day else 18.0) + np.random.normal(0, 0.2)
                    energy = (0.34 if is_day else 0.07) # Réduction énergétique
                    co2 = 800 + (cycle * 20) # Apprentissage : augmentation CO2 par cycle
                    # Amélioration du rendement (+27.3% et +4.2% par cycle)
                    yield_boost = 1.273 + (0.042 * cycle)
                    yield_sim = 0.01 * (day + 1)**1.5 * yield_boost

                data_list.append({
                    'cycle_id': cycle,
                    'group_id': group,
                    'day': day,
                    'minute': minute,
                    'temp_c': round(temp, 2),
                    'co2_ppm': round(co2, 2),
                    'energy_kwh': round(energy, 4),
                    'cumulative_yield_g': round(yield_sim, 2),
                    'vps_kpa': round(np.random.uniform(0.8, 1.2), 3)
                })

# Création du DataFrame
df = pd.DataFrame(data_list)

# Sauvegarde en CSV (C'est ici que le fichier atteindra environ 50Mo)
filename = "vertiflow_high_res_dataset.csv"
df.to_csv(filename, index=False)

print(f"Fichier '{filename}' généré avec succès.")
print(f"Taille estimée : {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB en mémoire.")