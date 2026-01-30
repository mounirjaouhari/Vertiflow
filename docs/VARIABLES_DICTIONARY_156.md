🌿 Dictionnaire des Variables VertiFlow (156 Colonnes)

Ce document répertorie l'intégralité des champs de données circulant dans le pipeline NiFi, de la Zone 1 (Collection) à la Zone 4 (Publication).

1. Métadonnées d'Identification (8 variables)

system_id : Identifiant unique de l'installation.

tower_id : Identifiant de la tour de culture (ex: T-001).

floor_level : Étage dans la tour (1 à 12).

pod_id : Identifiant du module de culture spécifique.

crop_type : Type de culture (Basilic, Laitue, etc.).

batch_id : Numéro de lot de semences.

timestamp_utc : Horodatage de capture (ISO 8601).

firmware_version : Version du logiciel du capteur.

2. Atmosphère & Climat (25 variables)

air_temp_c : Température de l'air (°C).

air_humidity_pct : Humidité relative (%).

vapor_pressure_deficit : Déficit de pression de vapeur (VPD).

co2_ppm : Concentration en CO2.

o2_levels : Niveaux d'oxygène.

air_flow_velocity : Vitesse du flux d'air (m/s).

barometric_pressure : Pression atmosphérique.

voc_index : Index des composés organiques volatils.

(Variables 9-25: Moyennes mobiles, min/max sur 1h, 6h, 24h).

3. Système Nutritif & Hydroponie (30 variables)

water_temp_c : Température de la solution nutritive.

ph_level : Acidité de la solution (0-14).

ec_conductivity : Conductivité électrique (nutriments).

tds_ppm : Total des solides dissous.

dissolved_oxygen : Oxygène dissous dans l'eau.

orp_redox : Potentiel d'oxydoréduction.

water_level_tank : Niveau du réservoir principal (%).

flow_rate_main : Débit d'irrigation.

nutrient_a_level : Niveau du stock de solution A.

nutrient_b_level : Niveau du stock de solution B.

acid_buffer_level : Niveau du correcteur de pH.

(Variables 12-30: Ratios N-P-K mesurés, fréquences de pompage, alertes colmatage).

4. Spectrométrie & Éclairage (20 variables)

ppfd_current : Densité de flux de photons photosynthétiques.

dli_daily : Intégrale de lumière quotidienne.

lux_level : Intensité lumineuse globale.

spectrum_red_ratio : Intensité canal Rouge (660nm).

spectrum_blue_ratio : Intensité canal Bleu (450nm).

spectrum_far_red : Intensité canal Infra-rouge.

uv_index : Exposition aux ultraviolets.

photoperiod_status : État (On/Off).

(Variables 9-20: Énergie consommée par LED, température des dissipateurs).

5. Santé des Plantes - Imagerie (15 variables)

leaf_area_index : Indice de surface foliaire estimé.

ndvi_index : Indice de végétation (santé chlorophyllienne).

chlorophyll_fluorescence : Stress de la plante.

stomatal_conductance : Capacité de transpiration.

growth_rate_mm_day : Taux de croissance vertical.

(Variables 6-15: Scores de détection de maladies/parasites via Computer Vision).

6. Substrat & Racines (12 variables)

substrate_moisture : Humidité du substrat (laine de roche/coco).

substrate_temp : Température au niveau des racines.

substrate_salinity : Accumulation de sels.

(Variables 4-12: Capteurs multi-profondeurs).

7. Énergie & Consommables (15 variables)

power_consumption_kwh : Consommation électrique totale.

hvac_load : Charge du système de climatisation.

pump_energy_usage : Consommation des pompes.

backup_battery_pct : État des batteries de secours.

(Variables 5-15: Coût énergétique en temps réel, efficacité lumineuse).

8. Maintenance & Actionneurs (15 variables)

pump_status_1_4 : État binaire des 4 pompes.

valve_opening_pct : Ouverture des vannes.

fan_speed_rpm : Vitesse des ventilateurs.

last_maintenance_date : Date du dernier entretien.

(Variables 5-15: Cycles de vie restants, erreurs matérielles).

9. Analyse Chimique Avancée (10 variables)

nitrate_concentration : Concentration en Nitrates.

phosphate_concentration : Concentration en Phosphates.

potassium_concentration : Concentration en Potassium.

calcium_magnesium_ratio : Ratio Ca/Mg.

(Variables 5-10: Métaux lourds, pureté de l'eau entrante).

10. Audit & Qualité Data (6 variables)

data_integrity_score : Score de confiance de la donnée.

sensor_drift_offset : Décalage de calibration détecté.

processing_latency_ms : Temps de traitement dans NiFi.

source_ip : IP du gateway MQTT.

is_anomaly : Flag booléen de détection d'anomalie.

validation_schema_version : Version du contrat de donnée utilisé.

Total : 156 variables.