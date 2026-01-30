# 📘 Dictionnaire des Colonnes ClickHouse

Ce fichier est généré automatiquement à partir du schéma `basil_ultimate_realtime` afin de documenter les 157 mesures Golden Record.

| # | Colonne | Type | Domaine | Description |
| - | ------- | ---- | ------- | ----------- |
| 1 | `timestamp` | `DateTime64(3, 'UTC')` | IDENTIFICATION & GÉOGRAPHIE | Précision milliseconde |
| 2 | `farm_id` | `LowCardinality(String)` | IDENTIFICATION & GÉOGRAPHIE | Ex: VERT-MAROC-01 |
| 3 | `parcel_id` | `LowCardinality(String)` | IDENTIFICATION & GÉOGRAPHIE | Ex: 830-AB-123 (Clé Bail) |
| 4 | `latitude` | `Float64` | IDENTIFICATION & GÉOGRAPHIE | Mesure latitude pour le domaine identification & géographie. |
| 5 | `longitude` | `Float64` | IDENTIFICATION & GÉOGRAPHIE | Mesure longitude pour le domaine identification & géographie. |
| 6 | `zone_id` | `LowCardinality(String)` | IDENTIFICATION & GÉOGRAPHIE | Ex: ZONE_A |
| 7 | `rack_id` | `LowCardinality(String)` | IDENTIFICATION & GÉOGRAPHIE | Ex: R01 |
| 8 | `level_index` | `UInt8` | IDENTIFICATION & GÉOGRAPHIE | Étage 1 à N |
| 9 | `module_id` | `String` | IDENTIFICATION & GÉOGRAPHIE | ID Unique du Bac |
| 10 | `batch_id` | `LowCardinality(String)` | IDENTIFICATION & GÉOGRAPHIE | Identifiant de lot (A/B testing) |
| 11 | `species_variety` | `LowCardinality(String)` | IDENTIFICATION & GÉOGRAPHIE | Ex: Ocimum basilicum 'Genovese' |
| 12 | `position_x_y` | `String` | IDENTIFICATION & GÉOGRAPHIE | Coordonnées locales |
| 13 | `structural_weight_load` | `Float32` | IDENTIFICATION & GÉOGRAPHIE | Charge au sol (kg) |
| 14 | `nutrient_n_total` | `Float32` | NUTRITION MINÉRALE RÉELLE | Azote (ppm) |
| 15 | `nutrient_p_phosphorus` | `Float32` | NUTRITION MINÉRALE RÉELLE | Phosphore |
| 16 | `nutrient_k_potassium` | `Float32` | NUTRITION MINÉRALE RÉELLE | Potassium |
| 17 | `nutrient_ca_calcium` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient ca calcium pour le domaine nutrition minérale réelle. |
| 18 | `nutrient_mg_magnesium` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient mg magnesium pour le domaine nutrition minérale réelle. |
| 19 | `nutrient_s_sulfur` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient s sulfur pour le domaine nutrition minérale réelle. |
| 20 | `nutrient_fe_iron` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient fe iron pour le domaine nutrition minérale réelle. |
| 21 | `nutrient_mn_manganese` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient mn manganese pour le domaine nutrition minérale réelle. |
| 22 | `nutrient_zn_zinc` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient zn zinc pour le domaine nutrition minérale réelle. |
| 23 | `nutrient_cu_copper` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient cu copper pour le domaine nutrition minérale réelle. |
| 24 | `nutrient_b_boron` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient b boron pour le domaine nutrition minérale réelle. |
| 25 | `nutrient_mo_molybdenum` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient mo molybdenum pour le domaine nutrition minérale réelle. |
| 26 | `nutrient_cl_chlorine` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient cl chlorine pour le domaine nutrition minérale réelle. |
| 27 | `nutrient_ni_nickel` | `Float32` | NUTRITION MINÉRALE RÉELLE | Mesure nutrient ni nickel pour le domaine nutrition minérale réelle. |
| 28 | `nutrient_solution_ec` | `Float32` | NUTRITION MINÉRALE RÉELLE | Conductivité (mS/cm) |
| 29 | `light_intensity_ppfd` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Flux Photons (µmol/m²/s) |
| 30 | `light_compensation_point` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure light compensation point pour le domaine photosynthèse & lumière. |
| 31 | `light_saturation_point` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure light saturation point pour le domaine photosynthèse & lumière. |
| 32 | `light_ratio_red_blue` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure light ratio red blue pour le domaine photosynthèse & lumière. |
| 33 | `light_far_red_intensity` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure light far red intensity pour le domaine photosynthèse & lumière. |
| 34 | `light_dli_accumulated` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Daily Light Integral |
| 35 | `light_photoperiod` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Heures |
| 36 | `quantum_yield_psii` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Efficacité Photosystème II |
| 37 | `photosynthetic_rate_max` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure photosynthetic rate max pour le domaine photosynthèse & lumière. |
| 38 | `co2_level_ambient` | `UInt16` | PHOTOSYNTHÈSE & LUMIÈRE | ppm |
| 39 | `co2_consumption_rate` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure co2 consumption rate pour le domaine photosynthèse & lumière. |
| 40 | `night_respiration_rate` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure night respiration rate pour le domaine photosynthèse & lumière. |
| 41 | `light_use_efficiency` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure light use efficiency pour le domaine photosynthèse & lumière. |
| 42 | `leaf_absorption_pct` | `Float32` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure leaf absorption pct pour le domaine photosynthèse & lumière. |
| 43 | `spectral_recipe_id` | `LowCardinality(String)` | PHOTOSYNTHÈSE & LUMIÈRE | Mesure spectral recipe id pour le domaine photosynthèse & lumière. |
| 44 | `fresh_biomass_est` | `Float32` | BIOMASSE & CROISSANCE | Grammes |
| 45 | `dry_biomass_est` | `Float32` | BIOMASSE & CROISSANCE | Mesure dry biomass est pour le domaine biomasse & croissance. |
| 46 | `leaf_area_index_lai` | `Float32` | BIOMASSE & CROISSANCE | Mesure leaf area index lai pour le domaine biomasse & croissance. |
| 47 | `root_shoot_ratio` | `Float32` | BIOMASSE & CROISSANCE | Mesure root shoot ratio pour le domaine biomasse & croissance. |
| 48 | `relative_growth_rate` | `Float32` | BIOMASSE & CROISSANCE | Mesure relative growth rate pour le domaine biomasse & croissance. |
| 49 | `net_assimilation_rate` | `Float32` | BIOMASSE & CROISSANCE | Mesure net assimilation rate pour le domaine biomasse & croissance. |
| 50 | `canopy_height` | `Float32` | BIOMASSE & CROISSANCE | cm |
| 51 | `harvest_index` | `Float32` | BIOMASSE & CROISSANCE | % |
| 52 | `days_since_planting` | `UInt16` | BIOMASSE & CROISSANCE | Mesure days since planting pour le domaine biomasse & croissance. |
| 53 | `thermal_sum_accumulated` | `Float32` | BIOMASSE & CROISSANCE | Degrés-Jours |
| 54 | `growth_stage` | `Enum8('Semis'=1, 'Végétatif'=2, 'Bouton'=3, 'Récolte'=4)` | BIOMASSE & CROISSANCE | Mesure growth stage pour le domaine biomasse & croissance. |
| 55 | `predicted_yield_kg_m2` | `Float32` | BIOMASSE & CROISSANCE | Mesure predicted yield kg m2 pour le domaine biomasse & croissance. |
| 56 | `expected_harvest_date` | `Date` | BIOMASSE & CROISSANCE | Mesure expected harvest date pour le domaine biomasse & croissance. |
| 57 | `biomass_accumulation_daily` | `Float32` | BIOMASSE & CROISSANCE | Mesure biomass accumulation daily pour le domaine biomasse & croissance. |
| 58 | `target_harvest_weight` | `Float32` | BIOMASSE & CROISSANCE | Mesure target harvest weight pour le domaine biomasse & croissance. |
| 59 | `health_score` | `Float32` | PHYSIOLOGIE & SANTÉ | 0.0 à 1.0 |
| 60 | `chlorophyll_index_spad` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure chlorophyll index spad pour le domaine physiologie & santé. |
| 61 | `stomatal_conductance` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure stomatal conductance pour le domaine physiologie & santé. |
| 62 | `anthocyanin_index` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure anthocyanin index pour le domaine physiologie & santé. |
| 63 | `tip_burn_risk` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure tip burn risk pour le domaine physiologie & santé. |
| 64 | `leaf_temp_delta` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure leaf temp delta pour le domaine physiologie & santé. |
| 65 | `stem_diameter_micro` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure stem diameter micro pour le domaine physiologie & santé. |
| 66 | `sap_flow_rate` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure sap flow rate pour le domaine physiologie & santé. |
| 67 | `leaf_wetness_duration` | `Float32` | PHYSIOLOGIE & SANTÉ | Minutes |
| 68 | `potential_hydrique_foliaire` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure potential hydrique foliaire pour le domaine physiologie & santé. |
| 69 | `ethylene_level` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure ethylene level pour le domaine physiologie & santé. |
| 70 | `ascorbic_acid_content` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure ascorbic acid content pour le domaine physiologie & santé. |
| 71 | `phenolic_content` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure phenolic content pour le domaine physiologie & santé. |
| 72 | `essential_oil_yield` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure essential oil yield pour le domaine physiologie & santé. |
| 73 | `aroma_compounds_ratio` | `Float32` | PHYSIOLOGIE & SANTÉ | Mesure aroma compounds ratio pour le domaine physiologie & santé. |
| 74 | `air_temp_internal` | `Float32` | ENVIRONNEMENT & CLIMAT | °C |
| 75 | `air_humidity` | `Float32` | ENVIRONNEMENT & CLIMAT | % |
| 76 | `vapor_pressure_deficit` | `Float32` | ENVIRONNEMENT & CLIMAT | kPa |
| 77 | `airflow_velocity` | `Float32` | ENVIRONNEMENT & CLIMAT | m/s |
| 78 | `air_pressure` | `Float32` | ENVIRONNEMENT & CLIMAT | hPa |
| 79 | `fan_speed_pct` | `Float32` | ENVIRONNEMENT & CLIMAT | % |
| 80 | `ext_temp_nasa` | `Float32` | ENVIRONNEMENT & CLIMAT | API NASA |
| 81 | `ext_humidity_nasa` | `Float32` | ENVIRONNEMENT & CLIMAT | Mesure ext humidity nasa pour le domaine environnement & climat. |
| 82 | `ext_solar_radiation` | `Float32` | ENVIRONNEMENT & CLIMAT | Mesure ext solar radiation pour le domaine environnement & climat. |
| 83 | `oxygen_level` | `Float32` | ENVIRONNEMENT & CLIMAT | Mesure oxygen level pour le domaine environnement & climat. |
| 84 | `dew_point` | `Float32` | ENVIRONNEMENT & CLIMAT | Mesure dew point pour le domaine environnement & climat. |
| 85 | `hvac_load_pct` | `Float32` | ENVIRONNEMENT & CLIMAT | Mesure hvac load pct pour le domaine environnement & climat. |
| 86 | `co2_injection_status` | `UInt8` | ENVIRONNEMENT & CLIMAT | 0/1 |
| 87 | `energy_footprint_hourly` | `Float32` | ENVIRONNEMENT & CLIMAT | kWh |
| 88 | `renewable_energy_pct` | `Float32` | ENVIRONNEMENT & CLIMAT | % d'énergie renouvelable consommée |
| 89 | `ambient_light_pollution` | `Float32` | ENVIRONNEMENT & CLIMAT | Mesure ambient light pollution pour le domaine environnement & climat. |
| 90 | `water_temp` | `Float32` | RHIZOSPHÈRE & EAU | Mesure water temp pour le domaine rhizosphère & eau. |
| 91 | `water_ph` | `Float32` | RHIZOSPHÈRE & EAU | Mesure water ph pour le domaine rhizosphère & eau. |
| 92 | `dissolved_oxygen` | `Float32` | RHIZOSPHÈRE & EAU | Mesure dissolved oxygen pour le domaine rhizosphère & eau. |
| 93 | `water_turbidity` | `Float32` | RHIZOSPHÈRE & EAU | Mesure water turbidity pour le domaine rhizosphère & eau. |
| 94 | `wue_current` | `Float32` | RHIZOSPHÈRE & EAU | Water Use Efficiency |
| 95 | `water_recycled_rate` | `Float32` | RHIZOSPHÈRE & EAU | Mesure water recycled rate pour le domaine rhizosphère & eau. |
| 96 | `coefficient_cultural_kc` | `Float32` | RHIZOSPHÈRE & EAU | Mesure coefficient cultural kc pour le domaine rhizosphère & eau. |
| 97 | `microbial_density` | `Float32` | RHIZOSPHÈRE & EAU | UFC |
| 98 | `beneficial_microbes_ratio` | `Float32` | RHIZOSPHÈRE & EAU | Mesure beneficial microbes ratio pour le domaine rhizosphère & eau. |
| 99 | `root_fungal_pressure` | `Float32` | RHIZOSPHÈRE & EAU | Mesure root fungal pressure pour le domaine rhizosphère & eau. |
| 100 | `biofilm_thickness` | `Float32` | RHIZOSPHÈRE & EAU | Mesure biofilm thickness pour le domaine rhizosphère & eau. |
| 101 | `algae_growth_index` | `Float32` | RHIZOSPHÈRE & EAU | Mesure algae growth index pour le domaine rhizosphère & eau. |
| 102 | `redox_potential` | `Float32` | RHIZOSPHÈRE & EAU | mV |
| 103 | `irrigation_line_pressure` | `Float32` | RHIZOSPHÈRE & EAU | Bar |
| 104 | `leaching_fraction` | `Float32` | RHIZOSPHÈRE & EAU | Mesure leaching fraction pour le domaine rhizosphère & eau. |
| 105 | `energy_price_kwh` | `Float32` | ÉCONOMIE & BAIL | API RTE |
| 106 | `market_price_kg` | `Float32` | ÉCONOMIE & BAIL | API RNM |
| 107 | `lease_index_value` | `Float32` | ÉCONOMIE & BAIL | Indice Fermages |
| 108 | `daily_rent_cost` | `Float32` | ÉCONOMIE & BAIL | Mesure daily rent cost pour le domaine économie & bail. |
| 109 | `lease_profitability_index` | `Float32` | ÉCONOMIE & BAIL | KPI Clé |
| 110 | `is_compliant_lease` | `UInt8` | ÉCONOMIE & BAIL | 0/1 |
| 111 | `labor_cost_pro_rata` | `Float32` | ÉCONOMIE & BAIL | Mesure labor cost pro rata pour le domaine économie & bail. |
| 112 | `carbon_credit_value` | `Float32` | ÉCONOMIE & BAIL | Mesure carbon credit value pour le domaine économie & bail. |
| 113 | `operational_cost_total` | `Float32` | ÉCONOMIE & BAIL | Mesure operational cost total pour le domaine économie & bail. |
| 114 | `carbon_footprint_per_kg` | `Float32` | ÉCONOMIE & BAIL | Mesure carbon footprint per kg pour le domaine économie & bail. |
| 115 | `pump_vibration_level` | `Float32` | HARDWARE & INFRA | Mesure pump vibration level pour le domaine hardware & infra. |
| 116 | `fan_current_draw` | `Float32` | HARDWARE & INFRA | Mesure fan current draw pour le domaine hardware & infra. |
| 117 | `led_driver_temp` | `Float32` | HARDWARE & INFRA | Mesure led driver temp pour le domaine hardware & infra. |
| 118 | `filter_differential_pressure` | `Float32` | HARDWARE & INFRA | Mesure filter differential pressure pour le domaine hardware & infra. |
| 119 | `ups_battery_health` | `Float32` | HARDWARE & INFRA | Mesure ups battery health pour le domaine hardware & infra. |
| 120 | `leak_detection_status` | `UInt8` | HARDWARE & INFRA | ALERTE CRITIQUE |
| 121 | `emergency_stop_status` | `UInt8` | HARDWARE & INFRA | ALERTE CRITIQUE |
| 122 | `network_latency_ms` | `UInt16` | HARDWARE & INFRA | Mesure network latency ms pour le domaine hardware & infra. |
| 123 | `sensor_calibration_offset` | `Float32` | HARDWARE & INFRA | Mesure sensor calibration offset pour le domaine hardware & infra. |
| 124 | `module_integrity_score` | `Float32` | HARDWARE & INFRA | Mesure module integrity score pour le domaine hardware & infra. |
| 125 | `ai_decision_mode` | `LowCardinality(String)` | INTELLIGENCE & DÉCISION | Mesure ai decision mode pour le domaine intelligence & décision. |
| 126 | `anomaly_confidence_score` | `Float32` | INTELLIGENCE & DÉCISION | Mesure anomaly confidence score pour le domaine intelligence & décision. |
| 127 | `predicted_energy_need_24h` | `Float32` | INTELLIGENCE & DÉCISION | Mesure predicted energy need 24h pour le domaine intelligence & décision. |
| 128 | `risk_pest_outbreak` | `Float32` | INTELLIGENCE & DÉCISION | Mesure risk pest outbreak pour le domaine intelligence & décision. |
| 129 | `irrigation_strategy_id` | `LowCardinality(String)` | INTELLIGENCE & DÉCISION | Mesure irrigation strategy id pour le domaine intelligence & décision. |
| 130 | `master_compliance_index` | `Float32` | INTELLIGENCE & DÉCISION | Mesure master compliance index pour le domaine intelligence & décision. |
| 131 | `blockchain_hash` | `String` | INTELLIGENCE & DÉCISION | Preuve Immuable (SHA-256) |
| 132 | `audit_trail_signature` | `String` | INTELLIGENCE & DÉCISION | Mesure audit trail signature pour le domaine intelligence & décision. |
| 133 | `quality_grade_prediction` | `Enum8('Premium'=1, 'Standard'=2, 'Rejet'=3)` | INTELLIGENCE & DÉCISION | Mesure quality grade prediction pour le domaine intelligence & décision. |
| 134 | `system_reboot_count` | `UInt8` | INTELLIGENCE & DÉCISION | Mesure system reboot count pour le domaine intelligence & décision. |
| 135 | `ref_n_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref n target pour le domaine cibles référentielles. |
| 136 | `ref_p_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref p target pour le domaine cibles référentielles. |
| 137 | `ref_k_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref k target pour le domaine cibles référentielles. |
| 138 | `ref_ca_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref ca target pour le domaine cibles référentielles. |
| 139 | `ref_mg_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref mg target pour le domaine cibles référentielles. |
| 140 | `ref_temp_opt` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref temp opt pour le domaine cibles référentielles. |
| 141 | `ref_lai_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref lai target pour le domaine cibles référentielles. |
| 142 | `ref_oil_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref oil target pour le domaine cibles référentielles. |
| 143 | `ref_wue_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref wue target pour le domaine cibles référentielles. |
| 144 | `ref_microbial_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref microbial target pour le domaine cibles référentielles. |
| 145 | `ref_photoperiod_opt` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref photoperiod opt pour le domaine cibles référentielles. |
| 146 | `ref_sum_thermal_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref sum thermal target pour le domaine cibles référentielles. |
| 147 | `ref_brix_target` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref brix target pour le domaine cibles référentielles. |
| 148 | `ref_nitrate_limit` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref nitrate limit pour le domaine cibles référentielles. |
| 149 | `ref_humidity_opt` | `Float32` | CIBLES RÉFÉRENTIELLES | Mesure ref humidity opt pour le domaine cibles référentielles. |
| 150 | `data_source_type` | `Enum8('IoT'=1, 'API'=2, 'ML'=3, 'Lab'=4)` | TRAÇABILITÉ | Mesure data source type pour le domaine traçabilité. |
| 151 | `sensor_hardware_id` | `LowCardinality(String)` | TRAÇABILITÉ | Mesure sensor hardware id pour le domaine traçabilité. |
| 152 | `api_endpoint_version` | `String` | TRAÇABILITÉ | Mesure api endpoint version pour le domaine traçabilité. |
| 153 | `source_reliability_score` | `Float32` | TRAÇABILITÉ | Mesure source reliability score pour le domaine traçabilité. |
| 154 | `data_integrity_flag` | `UInt8` | TRAÇABILITÉ | 0=OK, 1=Warning, 2=Error |
| 155 | `last_calibration_date` | `Date` | TRAÇABILITÉ | Mesure last calibration date pour le domaine traçabilité. |
| 156 | `maintenance_urgency_score` | `Float32` | TRAÇABILITÉ | Mesure maintenance urgency score pour le domaine traçabilité. |
| 157 | `lineage_uuid` | `UUID` | TRAÇABILITÉ | ID Unique NiFi |
