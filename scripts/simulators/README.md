# Simulators - Generateurs de donnees IoT

Ce dossier contient les simulateurs de capteurs IoT pour VertiFlow.

## Structure

```
simulators/
├── run_all_simulators.py            # Lanceur principal (tous les simulateurs)
├── iot_sensor_simulator.py          # Capteurs environnement (T, HR, CO2, PPFD)
├── led_spectrum_simulator.py        # Eclairage LED (spectre, DLI)
├── nutrient_sensor_simulator.py     # Solution nutritive (EC, pH, ions)
├── lab_data_generator.py            # Donnees experimentales (historique)
└── vision_system_simulator.py       # Vision (hauteur plante, LAI)
```

## Simulateurs disponibles

| Simulateur | Description | Metriques |
|------------|-------------|-----------|
| **IoT Sensors** | Environnement complet | Temp, Humidity, CO2, PPFD, VPD |
| **LED Spectrum** | Eclairage horticole | Blue/Red/Far-Red, DLI, PPFD |
| **Nutrient** | Solution hydroponique | EC, pH, N/P/K/Ca/Mg |
| **Lab Data** | Donnees experimentales | Biomasse, rendement, qualite |
| **Vision** | Computer vision | Hauteur, LAI, couleur |

## Utilisation

### Lancer tous les simulateurs
```bash
# Mode interactif (Ctrl+C pour arreter)
python scripts/simulators/run_all_simulators.py

# Duree limitee (1 heure)
python scripts/simulators/run_all_simulators.py --duration 3600

# Une seule iteration
python scripts/simulators/run_all_simulators.py --once
```

### Lancer un simulateur individuel
```bash
# Capteurs IoT
python scripts/simulators/iot_sensor_simulator.py

# LED Spectrum
python scripts/simulators/led_spectrum_simulator.py

# Solution nutritive
python scripts/simulators/nutrient_sensor_simulator.py
```

### Lister les simulateurs
```bash
python scripts/simulators/run_all_simulators.py --list
```

## Configuration

Les simulateurs publient sur MQTT (Mosquitto) :

| Variable | Defaut | Description |
|----------|--------|-------------|
| `MQTT_BROKER` | `localhost` | Adresse du broker |
| `MQTT_PORT` | `1883` | Port MQTT |
| `MQTT_TOPIC_BASE` | `vertiflow/telemetry` | Topic de base |

## Topics MQTT

```
vertiflow/telemetry/{rack_id}/{module_id}
vertiflow/telemetry/R01/M01  # Exemple
```

## Donnees generees

Les simulateurs generent des donnees realistes incluant :
- Cycles jour/nuit (temperature, lumiere)
- Variations gaussiennes (bruit de capteur)
- Anomalies aleatoires (1/500 messages)
- Alertes critiques (fuites, arrets d'urgence)
