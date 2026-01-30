-- =============================================================================
-- PROJET VERTIFLOW - VUES OPTIMISÉES POUR POWER BI (DIRECTQUERY)
-- =============================================================================
-- Date de création    : 25/12/2025
-- Responsable         : VertiFlow Core Team
-- Ticket Associé      : TICKET-016
-- Description         : Couche sémantique pour l'alimentation des Dashboards.
--                       Ces vues agrègent les données pour garantir une latence < 1s.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS vertiflow;

-- =============================================================================
-- VUE 1 : COCKPIT OPÉRATIONNEL (Temps Réel & Alertes)
-- Cible : Techniciens de maintenance & Chef de culture
-- Fréquence : Rafraîchissement 5-10 secondes
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_operational_cockpit AS
SELECT
    -- Dimensions
    rack_id,
    level_index,
    zone_id,
    
    -- État Instantané (Dernière valeur connue via argMax)
    argMax(air_temp_internal, timestamp) as current_temp,
    argMax(air_humidity, timestamp) as current_humidity,
    argMax(nutrient_solution_ec, timestamp) as current_ec,
    argMax(water_ph, timestamp) as current_ph,
    
    -- Indicateurs de Santé Système
    argMax(maintenance_urgency_score, timestamp) as urgency_score,
    argMax(leak_detection_status, timestamp) as is_leaking,
    argMax(emergency_stop_status, timestamp) as is_emergency_stop,
    
    -- Traçabilité
    max(timestamp) as last_seen_utc,
    dateDiff('second', max(timestamp), now()) as latency_seconds

FROM vertiflow.basil_ultimate_realtime
WHERE timestamp >= now() - INTERVAL 1 HOUR -- Focus sur l'heure courante uniquement
GROUP BY
    rack_id,
    level_index,
    zone_id;

-- =============================================================================
-- VUE 1 Extention : SANTÉ DES RACKS (Grille Spatiale)
-- Date: 25/12/2025
-- Responsable: VertiFlow Core Team
-- Description: Vue dédiée pour la santé des racks en format grille X-Y
-- =============================================================================
CREATE VIEW vertiflow.v_rack_grid_health AS
SELECT 
    rack_id,
    level_index,
    -- Extracting numeric X from 'X10-Y13'
    toInt32(extract(position_x_y, 'X(\d+)')) AS pos_x,
    -- Extracting numeric Y from 'X10-Y13'
    toInt32(extract(position_x_y, 'Y(\d+)')) AS pos_y,
    -- Getting the most recent health and variety data per cell
    argMax(health_score, timestamp) AS latest_health,
    argMax(species_variety, timestamp) AS variety,
    max(timestamp) AS last_update
FROM vertiflow.basil_ultimate_realtime
WHERE farm_id = 'VERT-MAROC-01'
GROUP BY 
    rack_id, 
    level_index, 
    pos_x, 
    pos_y;

-- =============================================================================
-- VUE 2 : LABORATOIRE AGRONOMIQUE (Analyse Scientifique)
-- Cible : Agronomes & Chercheurs
-- Fréquence : Rafraîchissement 1 heure (Analyse de tendances)
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_science_lab AS
SELECT
    -- Dimensions Temporelles (Grain Horaire)
    toStartOfHour(timestamp) as time_bucket,
    farm_id,
    rack_id,
    spectral_recipe_id, -- Pour comparer les recettes lumineuses
    
    -- Métriques Environnementales (Moyennes)
    avg(light_dli_accumulated) as avg_dli,
    avg(vapor_pressure_deficit) as avg_vpd,
    avg(co2_level_ambient) as avg_co2,
    
    -- Métriques Biologiques (Croissance)
    avg(fresh_biomass_est) as biomass_est_g,
    avg(relative_growth_rate) as rgr,
    avg(chlorophyll_index_spad) as chlorophyll_index,
    
    -- Corrélations (Pré-calculées pour rapidité)
    -- Est-ce que la lumière (X) explique la biomasse (Y) sur cette heure ?
    corr(light_intensity_ppfd, net_assimilation_rate) as efficiency_correlation,
    
    -- Qualité
    avg(health_score) as health_score_avg,
    max(tip_burn_risk) as max_stress_risk

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag = 0 -- Exclure les erreurs de capteurs pour la science
GROUP BY
    toStartOfHour(timestamp),
    farm_id,
    rack_id,
    spectral_recipe_id;

-- =============================================================================
-- VUE 3 : DASHBOARD EXÉCUTIF (Rentabilité & Finance)
-- Cible : Investisseurs & Direction Financière
-- Fréquence : Rafraîchissement Journalier
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_executive_finance AS
SELECT
    -- Dimensions Temporelles (Grain Journalier)
    toDate(timestamp) as report_date,
    farm_id,
    parcel_id, -- Lien crucial avec le Bail
    
    -- Coûts (OPEX)
    sum(energy_footprint_hourly * energy_price_kwh) as total_energy_cost_eur,
    avg(daily_rent_cost) as daily_lease_cost_eur,
    sum(operational_cost_total) as total_opex_eur,
    
    -- Revenus Projetés
    avg(market_price_kg) as market_price_avg,
    sum(biomass_accumulation_daily / 1000) as production_kg_daily, -- Conversion g -> kg
    (sum(biomass_accumulation_daily / 1000) * avg(market_price_kg)) as potential_revenue_eur,
    
    -- KPIs Clés (ROI)
    avg(lease_profitability_index) as profitability_index,
    avg(master_compliance_index) as compliance_score_pct,
    
    -- Impact Environnemental (ESG)
    sum(carbon_credit_value) as carbon_credits_generated_eur,
    avg(water_recycled_rate) as water_efficiency_pct

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag IN (0, 1) -- On tolère les warnings pour la finance (vision macro)
GROUP BY
    toDate(timestamp),
    farm_id,
    parcel_id;

-- =============================================================================
-- VUE 4 : ANALYSE DES ANOMALIES (Maintenance Prédictive)
-- Cible : Ingénieurs DevOps & Maintenance
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_anomalies_log AS
SELECT
    timestamp,
    farm_id,
    rack_id,
    sensor_hardware_id,
    
    -- Détails de l'anomalie
    anomaly_confidence_score,
    data_integrity_flag,
    
    -- Valeurs suspectes (Pour investigation)
    air_temp_internal,
    nutrient_n_total,
    
    -- Source
    data_source_type

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag > 0 -- Uniquement les données problématiques
    OR anomaly_confidence_score > 0.5
ORDER BY 
    timestamp DESC
LIMIT 10000; -- Garder le dashboard léger

-- =============================================================================
-- VUE 5 : ANALYSE DES CYCLES DE CULTURE (A/B Testing & Performance Variétale)
-- Cible : Responsable R&D et Chef de Culture
-- Fréquence : Rafraîchissement Quotidien (Grain : Cycle complet)
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_crop_cycle_analysis AS
SELECT
    -- Dimensions de Cohorte
    species_variety,
    spectral_recipe_id, -- La recette lumineuse testée
    batch_id,           -- Le lot de semences spécifique
    
    -- Métriques Temporelles
    min(timestamp) as cycle_start_date,
    max(timestamp) as last_update_date,
    dateDiff('day', min(timestamp), max(timestamp)) as cycle_duration_days,
    
    -- Performance Biologique Cumulée
    max(fresh_biomass_est) as final_biomass_g,
    avg(fresh_biomass_est) / nullIf(dateDiff('day', min(timestamp), max(timestamp)), 0) as daily_growth_rate_g,
    avg(health_score) as avg_health_score,
    
    -- Efficacité des Ressources (Resource Use Efficiency)
    sum(light_dli_accumulated) as total_light_integral_mol,
    sum(energy_footprint_hourly) as total_energy_kwh,
    
    -- Indice de Performance Clé (Biomasse par kWh)
    max(fresh_biomass_est) / nullIf(sum(energy_footprint_hourly), 0) as energy_efficiency_g_per_kwh,
    
    -- Qualité Finale Estimée
    avg(essential_oil_yield) as avg_oil_yield_pct,
    argMax(quality_grade_prediction, timestamp) as predicted_final_grade

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag = 0 -- Données propres uniquement
GROUP BY
    species_variety,
    spectral_recipe_id,
    batch_id;

-- =============================================================================
-- VUE 6 : EFFICACITÉ ÉNERGÉTIQUE PAR ÉTAGE (Vertical Analysis)
-- Cible : Gestionnaire d'Énergie & Chef de Culture
-- Objectif : Détecter les micro-climats inefficaces par niveau (Haut vs Bas)
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_vertical_energy_efficiency AS
SELECT
    toStartOfHour(timestamp) as time_bucket,
    rack_id,
    level_index, -- L'étage est la dimension clé ici
    
    -- Consommation vs Production par étage
    sum(energy_footprint_hourly) as energy_consumed_kwh,
    avg(fresh_biomass_est) as avg_biomass_g,
    
    -- Indicateurs Thermiques
    avg(air_temp_internal) as avg_temp,
    avg(hvac_load_pct) as hvac_effort_pct,
    
    -- Ratio d'Efficacité Verticale
    -- Permet de voir si l'étage du haut consomme plus à cause de la chaleur montante
    sum(energy_footprint_hourly) / nullIf(avg(fresh_biomass_est), 0) as kwh_per_gram_biomass

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag = 0
GROUP BY
    toStartOfHour(timestamp),
    rack_id,
    level_index;

-- =============================================================================
-- VUE 7 : DÉTECTION PRÉCOCE MALADIES & STRESS (AI Insights)
-- Cible : Pathologiste Végétal
-- Objectif : Corréler les prédictions IA avec les conditions réelles
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_disease_early_warning AS
SELECT
    toStartOfHour(timestamp) as time_bucket,
    rack_id,
    species_variety,
    
    -- Facteurs de Risque Environnementaux
    avg(vapor_pressure_deficit) as avg_vpd, -- VPD bas = risque fongique
    avg(leaf_wetness_duration) as wetness_duration_min, -- Feuilles mouillées = Mildiou
    
    -- Signaux Biologiques
    avg(health_score) as ai_health_score,
    max(anthocyanin_index) as stress_pigment_level,
    
    -- Prédiction IA (Agrégée)
    countIf(risk_pest_outbreak > 0.7) as high_risk_alerts_count,
    
    -- Statut
    multiIf(
        avg(health_score) < 0.6, 'CRITICAL',
        avg(health_score) < 0.8, 'WARNING',
        'HEALTHY'
    ) as health_status_category

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag = 0
GROUP BY
    toStartOfHour(timestamp),
    rack_id,
    species_variety;

-- =============================================================================
-- VUE 8 : ANALYSE NUTRITIONNELLE COMPARATIVE (Chimie)
-- Cible : Chimiste / Responsable Fertigation
-- Objectif : Vérifier l'équilibre N-P-K réel vs cible
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_nutrient_balance AS
SELECT
    toStartOfDay(timestamp) as report_date,
    rack_id,
    
    -- Azote (N)
    avg(nutrient_n_total) as n_actual_ppm,
    avg(ref_n_target) as n_target_ppm,
    (avg(nutrient_n_total) - avg(ref_n_target)) as n_deviation,
    
    -- Phosphore (P)
    avg(nutrient_p_phosphorus) as p_actual_ppm,
    avg(ref_p_target) as p_target_ppm,
    
    -- Potassium (K)
    avg(nutrient_k_potassium) as k_actual_ppm,
    avg(ref_k_target) as k_target_ppm,
    
    -- Santé Racinaire associée
    avg(root_shoot_ratio) as root_health_indicator,
    avg(water_ph) as avg_ph

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag = 0
GROUP BY
    toStartOfDay(timestamp),
    rack_id;

-- =============================================================================
-- VUE 9 : SUIVI DE LA MAIN D'ŒUVRE & OPÉRATIONS
-- Cible : Chef d'Exploitation
-- Objectif : Optimiser le temps humain passé par zone
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_labor_efficiency AS
SELECT
    toStartOfMonth(timestamp) as report_month,
    zone_id,
    
    -- Coûts Humains
    sum(labor_cost_pro_rata) as total_labor_cost_eur,
    
    -- Production associée
    sum(fresh_biomass_est) as total_production_g,
    
    -- Ratio d'Efficacité Humaine
    sum(labor_cost_pro_rata) / (sum(fresh_biomass_est) / 1000) as labor_cost_per_kg,
    
    -- Maintenance
    sum(system_reboot_count) as intervention_count_est

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag = 0
GROUP BY
    toStartOfMonth(timestamp),
    zone_id;

-- =============================================================================
-- VUE 10 : RAPPORT DE CONFORMITÉ & RSE (Audit Bailleur)
-- Cible : Propriétaire Foncier / Auditeur Externe
-- Objectif : Prouver le respect des normes environnementales et contractuelles
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_compliance_audit AS
SELECT
    toStartOfMonth(timestamp) as audit_month,
    parcel_id,
    
    -- Conformité Contractuelle
    avg(is_compliant_lease) * 100 as lease_compliance_rate_pct,
    min(lease_index_value) as lease_index_applied,
    
    -- Impact Environnemental (Preuve RSE)
    sum(carbon_credit_value) as total_carbon_credits,
    avg(water_recycled_rate) as avg_water_recycling_pct,
    avg(renewable_energy_pct) as avg_green_energy_usage, -- Colonne à supposer existante ou dérivée
    
    -- Score Global
    avg(master_compliance_index) as global_compliance_score

FROM vertiflow.basil_ultimate_realtime
WHERE 
    data_integrity_flag = 0
GROUP BY
    toStartOfMonth(timestamp),
    parcel_id;

-- =============================================================================
-- VUE 11 : ANALYSE DU VIVANT (Plantes & Biodiversité)
-- Cible : Chef de Culture / Power BI Live
-- Objectif : Afficher dynamiquement le nombre de plantes vivantes par espèce
-- Fréquence : Rafraîchissement 1 min (quasi temps réel)
-- =============================================================================
CREATE OR REPLACE VIEW vertiflow.view_pbi_live_inventory AS
SELECT
    -- Grain Temporel : Minute (pour l'animation live)
    toStartOfMinute(timestamp) as time_bucket,
    
    -- Dimensions de Biodiversité
    species_variety, -- Ex: "Genovese", "Thaï"
    farm_id,
    
    -- Inventaire Instantané (Dernier état connu)
    -- On compte les modules uniques actifs
    uniqExact(module_id) as active_trays_count,
    
    -- Estimation du nombre de plantes (Hypothèse: ~20 plants/bac)
    -- Note: Pourrait être une colonne réelle si la vision IA compte les tiges
    uniqExact(module_id) * 20 as estimated_plant_count,
    
    -- État de Santé Global par Espèce
    avg(health_score) as avg_health,
    
    -- Répartition Spatiale
    uniqExact(rack_id) as active_racks_count,
    
    -- Indicateur de Diversité (Simulé)
    count(DISTINCT species_variety) OVER (PARTITION BY farm_id) as total_species_on_site

FROM vertiflow.basil_ultimate_realtime
WHERE 
    timestamp >= now() - INTERVAL 1 HOUR -- Fenêtre glissante courte
    AND data_integrity_flag = 0
GROUP BY
    toStartOfMinute(timestamp),
    species_variety,
    farm_id;
