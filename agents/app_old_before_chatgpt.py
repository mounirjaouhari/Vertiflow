# -*- coding: utf-8 -*-
"""
VertiFlow AI Assistant - Streamlit Chat Interface
==================================================
A production-ready chat interface for querying VertiFlow's BigQuery data
using Google Gemini for natural language understanding.

Supports French, English, and Moroccan Darija (Arabic).
"""

import streamlit as st
import uuid
import json
import re
from typing import List, Dict, Any, Optional

import google.auth
from google.cloud import bigquery
from google import genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================
PROJECT_ID = "vertiflow-484602"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-001"

# BigQuery tables configuration
BIGQUERY_TABLES = {
    "sensor_telemetry": {
        "full_name": "vertiflow-484602.vertiflow_analytics.sensor_telemetry",
        "description": "Données temps réel des capteurs IoT (température, humidité, pH, EC, lumière)"
    },
    "view_dashboard_ready": {
        "full_name": "vertiflow-484602.vertiflow_analytics.view_dashboard_ready",
        "description": "Vue agrégée pour le dashboard avec métriques clés"
    },
    "simulations_agent": {
        "full_name": "vertiflow-484602.vertiflow_lake.simulations_agent",
        "description": "Résultats des simulations de croissance et prédictions"
    }
}

# ClickHouse tables context (schemas for AI context understanding)
# These tables are in ClickHouse database 'vertiflow' (not directly queryable from this app)
CLICKHOUSE_CONTEXT = {
    "basil_ultimate_realtime": {
        "description": "Table principale temps réel GOLDEN RECORD 157 colonnes - Données complètes de toute la ferme verticale",
        "database": "vertiflow",
        "categories": {
            "I. IDENTIFICATION & GÉOGRAPHIE (13 cols)": [
                "timestamp", "farm_id", "parcel_id", "latitude", "longitude", "zone_id", 
                "rack_id", "level_index", "module_id", "batch_id", "species_variety", 
                "position_x_y", "structural_weight_load"
            ],
            "II. NUTRITION MINÉRALE (15 cols)": [
                "nutrient_n_total", "nutrient_p_phosphorus", "nutrient_k_potassium", 
                "nutrient_ca_calcium", "nutrient_mg_magnesium", "nutrient_s_sulfur",
                "nutrient_fe_iron", "nutrient_mn_manganese", "nutrient_zn_zinc", 
                "nutrient_cu_copper", "nutrient_b_boron", "nutrient_mo_molybdenum",
                "nutrient_cl_chlorine", "nutrient_ni_nickel", "nutrient_solution_ec"
            ],
            "III. PHOTOSYNTHÈSE & LUMIÈRE (15 cols)": [
                "light_intensity_ppfd", "light_compensation_point", "light_saturation_point",
                "light_ratio_red_blue", "light_far_red_intensity", "light_dli_accumulated",
                "light_photoperiod", "quantum_yield_psii", "photosynthetic_rate_max",
                "co2_level_ambient", "co2_consumption_rate", "night_respiration_rate",
                "light_use_efficiency", "leaf_absorption_pct", "spectral_recipe_id"
            ],
            "IV. BIOMASSE & CROISSANCE (15 cols)": [
                "fresh_biomass_est", "dry_biomass_est", "leaf_area_index_lai", 
                "root_shoot_ratio", "relative_growth_rate", "net_assimilation_rate",
                "canopy_height", "harvest_index", "days_since_planting", 
                "thermal_sum_accumulated", "growth_stage", "predicted_yield_kg_m2",
                "expected_harvest_date", "biomass_accumulation_daily", "target_harvest_weight"
            ],
            "V. PHYSIOLOGIE & SANTÉ (15 cols)": [
                "health_score", "chlorophyll_index_spad", "stomatal_conductance",
                "anthocyanin_index", "tip_burn_risk", "leaf_temp_delta", 
                "stem_diameter_micro", "sap_flow_rate", "leaf_wetness_duration",
                "potential_hydrique_foliaire", "ethylene_level", "ascorbic_acid_content",
                "phenolic_content", "essential_oil_yield", "aroma_compounds_ratio"
            ],
            "VI. ENVIRONNEMENT & CLIMAT (16 cols)": [
                "air_temp_internal", "air_humidity", "vapor_pressure_deficit", 
                "airflow_velocity", "air_pressure", "fan_speed_pct",
                "ext_temp_nasa", "ext_humidity_nasa", "ext_solar_radiation",
                "oxygen_level", "dew_point", "hvac_load_pct", "co2_injection_status",
                "energy_footprint_hourly", "renewable_energy_pct", "ambient_light_pollution"
            ],
            "VII. RHIZOSPHÈRE & EAU (15 cols)": [
                "water_temp", "water_ph", "dissolved_oxygen", "water_turbidity",
                "wue_current", "water_recycled_rate", "coefficient_cultural_kc",
                "microbial_density", "beneficial_microbes_ratio", "root_fungal_pressure",
                "biofilm_thickness", "algae_growth_index", "redox_potential",
                "irrigation_line_pressure", "leaching_fraction"
            ],
            "VIII. ÉCONOMIE & BAIL (10 cols)": [
                "energy_price_kwh", "market_price_kg", "lease_index_value", 
                "daily_rent_cost", "lease_profitability_index", "is_compliant_lease",
                "labor_cost_pro_rata", "carbon_credit_value", "operational_cost_total",
                "carbon_footprint_per_kg"
            ],
            "IX. HARDWARE & INFRA (10 cols)": [
                "pump_vibration_level", "fan_current_draw", "led_driver_temp",
                "filter_differential_pressure", "ups_battery_health", "leak_detection_status",
                "emergency_stop_status", "network_latency_ms", "sensor_calibration_offset",
                "module_integrity_score"
            ],
            "X. INTELLIGENCE & DÉCISION (10 cols)": [
                "ai_decision_mode", "anomaly_confidence_score", "predicted_energy_need_24h",
                "risk_pest_outbreak", "irrigation_strategy_id", "master_compliance_index",
                "blockchain_hash", "audit_trail_signature", "quality_grade_prediction",
                "system_reboot_count"
            ],
            "XI. CIBLES RÉFÉRENTIELLES (15 cols)": [
                "ref_n_target", "ref_p_target", "ref_k_target", "ref_ca_target",
                "ref_mg_target", "ref_temp_opt", "ref_lai_target", "ref_oil_target",
                "ref_wue_target", "ref_microbial_target", "ref_photoperiod_opt",
                "ref_sum_thermal_target", "ref_brix_target", "ref_nitrate_limit",
                "ref_humidity_opt"
            ],
            "XII. TRAÇABILITÉ (8 cols)": [
                "data_source_type", "sensor_hardware_id", "api_endpoint_version",
                "source_reliability_score", "data_integrity_flag", "last_calibration_date",
                "maintenance_urgency_score", "lineage_uuid"
            ]
        }
    },
    "ml_predictions": {
        "description": "Prédictions des modèles ML (rendement, anomalies, qualité)",
        "database": "vertiflow",
        "columns": [
            "timestamp", "model_name", "model_version", "batch_id", 
            "prediction_type", "prediction_value", "confidence", 
            "features_json", "execution_time_ms"
        ]
    },
    "ext_weather_history": {
        "description": "Historique météo externe (NASA POWER / OpenWeather)",
        "database": "vertiflow",
        "columns": [
            "timestamp", "location_id", "latitude", "longitude", "temp_c", 
            "humidity_pct", "pressure_hpa", "wind_speed_ms", "wind_direction_deg",
            "solar_radiation_w_m2", "cloud_cover_pct", "uv_index", "api_source"
        ]
    },
    "ext_energy_market": {
        "description": "Marché de l'énergie et mix carbone (Smart Grid / RSE)",
        "database": "vertiflow",
        "columns": [
            "timestamp", "region_code", "spot_price_eur_kwh", 
            "carbon_intensity_g_co2_kwh", "renewable_pct", "nuclear_pct",
            "fossil_pct", "grid_load_mw", "alert_status"
        ]
    },
    "ref_plant_recipes": {
        "description": "Référentiel scientifique des recettes de culture (cibles agronomiques)",
        "database": "vertiflow",
        "columns": [
            "recipe_id", "species_variety", "growth_stage", "target_temp_day",
            "target_temp_night", "target_humidity_min", "target_humidity_max",
            "target_vpd", "target_dli", "target_photoperiod_hours", 
            "target_spectrum_ratio_rb", "target_n_ppm", "target_p_ppm",
            "target_k_ppm", "target_ec", "target_ph", "author", "is_active"
        ]
    },
    "ext_land_registry": {
        "description": "Données foncières et cadastrales (bail, parcelles)",
        "database": "vertiflow",
        "columns": [
            "parcel_id", "lease_contract_id", "surface_m2", "orientation_deg",
            "altitude_m", "base_rent_eur_m2", "lease_index_reference",
            "last_index_value", "zone_type", "lease_start_date", "lease_end_date"
        ]
    },
    "ext_market_prices": {
        "description": "Cotations du marché agricole (prix de vente basilic)",
        "database": "vertiflow",
        "columns": [
            "date", "product_code", "market_place", "price_min_eur_kg",
            "price_max_eur_kg", "price_avg_eur_kg", "volume_tons", "quality_grade"
        ]
    },
    "views_powerbi": {
        "description": "Vues agrégées pour Power BI / Dashboards",
        "database": "vertiflow",
        "views": [
            "view_pbi_operational_cockpit - État opérationnel temps réel (alertes, maintenance)",
            "view_pbi_science_lab - Métriques agronomiques (DLI, VPD, CO2, croissance)",
            "view_pbi_executive_finance - Dashboard financier (coûts, revenus, ROI)",
            "view_pbi_anomalies_log - Log des anomalies détectées",
            "view_pbi_crop_cycle_analysis - Analyse des cycles de culture (A/B testing)",
            "view_pbi_vertical_energy_efficiency - Efficacité énergétique par étage",
            "view_pbi_disease_early_warning - Alerte précoce maladies/stress",
            "view_pbi_nutrient_balance - Équilibre nutritionnel N-P-K",
            "view_pbi_labor_efficiency - Efficacité main d'œuvre",
            "view_pbi_compliance_audit - Conformité RSE/Bail",
            "view_pbi_live_inventory - Inventaire plantes en temps réel"
        ]
    }
}

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="VertiFlow AI Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logo URL (VertiFlow brand - Tech meets Nature: Digital Network + Green Leaf)
# Hosted on imgbb for reliability
LOGO_URL = "https://i.ibb.co/Lzp8hcSS/vertiflow-logo-digital-leaf.png"

# Base64 fallback logo (embedded for offline support)
LOGO_BASE64 = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MDAgMTIwIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjAlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjMTBCOTgxIi8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMEVBNUU5Ii8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PGNpcmNsZSBjeD0iNjAiIGN5PSI2MCIgcj0iNDUiIGZpbGw9InVybCgjZykiIG9wYWNpdHk9IjAuMiIvPjxwYXRoIGQ9Ik00NSA4MEMzNSA2MCA0MCA0MCA2MCAzNUM4MCAzMCA5MCA0NSA5MCA2NUM5MCA4NSA3MCA5NSA1NSA5MEM0MCA4NSA0MCA4NSA0NSA4MFoiIGZpbGw9IiMxMEI5ODEiLz48dGV4dCB4PSIxMzAiIHk9IjcwIiBmb250LWZhbWlseT0iSW50ZXIsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9InVybCgjZykiPlZlcnRpRmxvdzwvdGV4dD48dGV4dCB4PSIxMzAiIHk9Ijk1IiBmb250LWZhbWlseT0iSW50ZXIsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM5NEEzQjgiIGxldHRlci1zcGFjaW5nPSIycHgiPlNNQVJUIFZFUlRJQ0FMIEZBUK1JTkc8L3RleHQ+PC9zdmc+"

# =============================================================================
# MODERN UI DESIGN - CSS
# =============================================================================
st.markdown("""
<style>
    /* ===== IMPORT GOOGLE FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* ===== ROOT VARIABLES ===== */
    :root {
        --primary-green: #10B981;
        --primary-dark: #059669;
        --accent-blue: #0EA5E9;
        --accent-cyan: #06B6D4;
        --bg-dark: #0F172A;
        --bg-card: #1E293B;
        --bg-hover: #334155;
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --border-color: #334155;
        --gradient-main: linear-gradient(135deg, #10B981 0%, #0EA5E9 100%);
        --gradient-glass: linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(14,165,233,0.1) 100%);
        --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        --shadow-glow: 0 0 40px rgba(16, 185, 129, 0.15);
    }
    
    /* ===== GLOBAL STYLES ===== */
    .stApp {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ===== SIDEBAR STYLING ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: var(--text-primary);
    }
    
    /* ===== LOGO CONTAINER ===== */
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 1.5rem 1rem;
        margin-bottom: 1rem;
        background: var(--gradient-glass);
        border-radius: 16px;
        border: 1px solid rgba(16, 185, 129, 0.2);
        backdrop-filter: blur(10px);
    }
    
    .logo-container img {
        width: 100%;
        max-width: 220px;
        height: auto;
        border-radius: 12px;
        margin-bottom: 1rem;
        filter: drop-shadow(0 4px 20px rgba(16, 185, 129, 0.3));
    }
    
    .logo-title {
        font-size: 1.75rem;
        font-weight: 700;
        background: var(--gradient-main);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    
    .logo-subtitle {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.25rem;
    }
    
    /* ===== GLASSMORPHISM CARDS ===== */
    .glass-card {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }
    
    .glass-card h4 {
        color: var(--text-primary);
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .glass-card p {
        color: var(--text-secondary);
        font-size: 0.8rem;
        line-height: 1.6;
        margin: 0.25rem 0;
    }
    
    /* ===== METRIC BADGES ===== */
    .metric-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--gradient-glass);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 100px;
        padding: 0.5rem 1rem;
        font-size: 0.75rem;
        color: var(--primary-green);
        font-weight: 500;
    }
    
    /* ===== LANGUAGE PILLS ===== */
    .lang-pills {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }
    
    .lang-pill {
        background: rgba(14, 165, 233, 0.1);
        border: 1px solid rgba(14, 165, 233, 0.2);
        border-radius: 100px;
        padding: 0.35rem 0.75rem;
        font-size: 0.7rem;
        color: var(--accent-cyan);
        font-weight: 500;
    }
    
    /* ===== CHAT INTERFACE ===== */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 1rem;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: var(--gradient-main);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
    }
    
    /* ===== CHAT MESSAGES ===== */
    [data-testid="stChatMessage"] {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stChatMessage"][data-testid*="user"] {
        background: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.2);
    }
    
    /* ===== CHAT INPUT ===== */
    [data-testid="stChatInput"] {
        border-radius: 100px;
        background: var(--bg-card);
        border: 2px solid var(--border-color);
    }
    
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--primary-green);
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
    }
    
    [data-testid="stChatInput"] textarea {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: var(--gradient-main);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(16, 185, 129, 0.4);
    }
    
    /* ===== EXPANDERS ===== */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        overflow: hidden;
    }
    
    [data-testid="stExpander"] summary {
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    /* ===== DATAFRAMES ===== */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* ===== CODE BLOCKS ===== */
    .stCodeBlock {
        border-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* ===== SPINNERS ===== */
    .stSpinner > div {
        border-color: var(--primary-green) transparent transparent transparent;
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* ===== RTL SUPPORT ===== */
    .rtl-text {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', 'Arial', sans-serif;
    }
    
    /* ===== ANIMATIONS ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .animate-pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* ===== STATUS INDICATORS ===== */
    .status-online {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--primary-green);
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: var(--primary-green);
        border-radius: 50%;
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []


def reset_conversation():
    """Reset the conversation state."""
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()


# =============================================================================
# CLIENTS INITIALIZATION
# =============================================================================
@st.cache_resource
def get_credentials():
    """Get Google Cloud credentials with full cloud-platform scope."""
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return credentials
    except Exception as e:
        st.error(f"❌ Erreur d'authentification: {e}")
        return None


@st.cache_resource
def get_bigquery_client():
    """Initialize BigQuery client."""
    try:
        credentials = get_credentials()
        if credentials:
            return bigquery.Client(project=PROJECT_ID, credentials=credentials)
        return None
    except Exception as e:
        st.error(f"❌ Erreur BigQuery: {e}")
        return None


@st.cache_resource
def get_genai_client():
    """Initialize Google GenAI client for Vertex AI."""
    try:
        credentials = get_credentials()
        if credentials:
            client = genai.Client(
                vertexai=True,
                project=PROJECT_ID,
                location=LOCATION,
                credentials=credentials
            )
            return client
        return None
    except Exception as e:
        st.error(f"❌ Erreur Gemini: {e}")
        return None


# =============================================================================
# SCHEMA RETRIEVAL
# =============================================================================
@st.cache_data(ttl=3600)
def get_table_schemas() -> Dict[str, Any]:
    """Retrieve schemas for all configured BigQuery tables."""
    client = get_bigquery_client()
    if not client:
        return {}
    
    schemas = {}
    for table_key, table_info in BIGQUERY_TABLES.items():
        try:
            table = client.get_table(table_info["full_name"])
            schemas[table_key] = {
                "description": table_info["description"],
                "full_name": table_info["full_name"],
                "columns": [
                    {"name": field.name, "type": field.field_type, "description": field.description or ""}
                    for field in table.schema
                ],
                "num_rows": table.num_rows
            }
        except Exception as e:
            schemas[table_key] = {"error": str(e)}
    
    return schemas


# =============================================================================
# GEMINI QUERY GENERATION
# =============================================================================
def generate_sql_query(user_question: str, schemas: Dict[str, Any]) -> Dict[str, Any]:
    """Use Gemini to generate SQL query from natural language."""
    client = get_genai_client()
    if not client:
        return {"error": "Client Gemini non disponible", "sql": None}
    
    # Build BigQuery schema context
    schema_context = "=== TABLES BIGQUERY (Interrogeables directement) ===\n\n"
    for table_key, schema in schemas.items():
        if "error" not in schema:
            schema_context += f"Table: {schema['full_name']}\n"
            schema_context += f"Description: {schema['description']}\n"
            schema_context += f"Nombre de lignes: {schema['num_rows']}\n"
            schema_context += "Colonnes:\n"
            for col in schema['columns']:
                schema_context += f"  - {col['name']} ({col['type']})\n"
            schema_context += "\n"
    
    # Build ClickHouse context for understanding (not queryable from here)
    clickhouse_context = "\n=== CONTEXTE CLICKHOUSE (Pour ta compréhension du domaine) ===\n"
    clickhouse_context += "Ces tables sont dans ClickHouse et définissent le modèle de données VertiFlow:\n\n"
    
    for table_name, table_info in CLICKHOUSE_CONTEXT.items():
        clickhouse_context += f"📊 {table_name}: {table_info['description']}\n"
        if "categories" in table_info:
            for cat_name, cols in table_info["categories"].items():
                clickhouse_context += f"   {cat_name}: {', '.join(cols[:5])}...\n"
        elif "columns" in table_info:
            clickhouse_context += f"   Colonnes: {', '.join(table_info['columns'][:10])}...\n"
        elif "views" in table_info:
            for view in table_info["views"][:3]:
                clickhouse_context += f"   - {view}\n"
        clickhouse_context += "\n"
    
    prompt = f"""Tu es un expert en agriculture verticale et analyse de données pour le projet VertiFlow au Maroc.
Tu dois générer une requête SQL BigQuery pour répondre à la question de l'utilisateur.

{schema_context}

{clickhouse_context}

CONTEXTE MÉTIER VERTIFLOW:
- Ferme verticale intelligente au Maroc (ID: VERT-MAROC-01)
- Culture principale: Basilic (variétés Genovese, Thaï)
- Capteurs IoT: température, humidité, pH, EC, lumière PPFD
- Métriques clés: health_score, fresh_biomass_est, light_dli_accumulated
- Stades de croissance: Semis (1-7j), Végétatif (8-21j), Bouton (22-35j), Récolte (36+j)

Question de l'utilisateur (peut être en Français, English, ou Darija marocaine):
"{user_question}"

Instructions:
1. Génère UNIQUEMENT une requête SQL valide pour BigQuery
2. Utilise les noms complets des tables (projet.dataset.table)
3. Si la question est générale, limite les résultats à 10 lignes
4. Si tu ne peux pas générer de SQL pertinent, réponds "NO_SQL_NEEDED"
5. Ajoute des commentaires SQL pour expliquer la requête

Réponds UNIQUEMENT avec la requête SQL, sans markdown ni backticks."""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        sql = response.text.strip()
        
        if "NO_SQL_NEEDED" in sql or not sql:
            return {"sql": None, "needs_sql": False}
        
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return {"sql": sql, "needs_sql": True, "error": None}
        
    except Exception as e:
        return {"error": str(e), "sql": None}


def execute_sql_query(sql: str) -> Dict[str, Any]:
    """Execute SQL query on BigQuery."""
    client = get_bigquery_client()
    if not client:
        return {"error": "Client BigQuery non disponible", "data": None, "df": None}
    
    try:
        query_job = client.query(sql)
        results = query_job.result()
        data = [dict(row) for row in results]
        df = pd.DataFrame(data) if data else pd.DataFrame()
        return {"data": data, "df": df, "total_rows": len(data), "error": None}
    except Exception as e:
        return {"error": str(e), "data": None, "df": None}


def detect_chart_request(user_question: str) -> Dict[str, Any]:
    """Detect if user is requesting a chart/visualization."""
    chart_keywords = [
        # French
        "graphe", "graphique", "tracer", "visualiser", "courbe", "diagramme",
        "histogramme", "camembert", "barres", "ligne", "tendance", "évolution",
        "comparaison", "distribution", "série temporelle", "afficher",
        # English
        "chart", "graph", "plot", "visualize", "visualization", "trend",
        "histogram", "pie", "bar", "line", "scatter", "show me", "display",
        # Darija
        "رسم", "بياني", "شوف", "ورني"
    ]
    
    question_lower = user_question.lower()
    wants_chart = any(kw in question_lower for kw in chart_keywords)
    
    # Detect chart type
    chart_type = "auto"
    if any(kw in question_lower for kw in ["ligne", "line", "évolution", "trend", "temporelle", "time"]):
        chart_type = "line"
    elif any(kw in question_lower for kw in ["barre", "bar", "histogramme", "histogram", "comparaison"]):
        chart_type = "bar"
    elif any(kw in question_lower for kw in ["camembert", "pie", "répartition", "distribution"]):
        chart_type = "pie"
    elif any(kw in question_lower for kw in ["scatter", "nuage", "corrélation", "correlation"]):
        chart_type = "scatter"
    
    return {"wants_chart": wants_chart, "chart_type": chart_type}


def generate_chart(
    df: pd.DataFrame,
    user_question: str,
    chart_type: str = "auto"
) -> Optional[go.Figure]:
    """Generate a Plotly chart from DataFrame based on user question."""
    if df is None or df.empty:
        return None
    
    client = get_genai_client()
    if not client:
        return create_auto_chart(df, chart_type)
    
    columns_info = ", ".join([f"{col} ({df[col].dtype})" for col in df.columns])
    sample_data = df.head(3).to_string()
    
    prompt = f"""Analyse ces données et génère le code Python Plotly pour créer un graphique approprié.

Question utilisateur: "{user_question}"
Type de graphique suggéré: {chart_type}

Colonnes disponibles: {columns_info}
Échantillon de données:
{sample_data}

Nombre de lignes: {len(df)}

Instructions:
1. Le DataFrame s'appelle 'df' (déjà chargé)
2. Utilise plotly.express (importé comme 'px') ou plotly.graph_objects (importé comme 'go')
3. Crée un graphique clair et professionnel
4. Utilise des couleurs vertes (thème agriculture: #2E7D32, #4CAF50, #81C784)
5. Ajoute un titre en français décrivant les données
6. Le résultat final doit être stocké dans une variable 'fig'

Réponds UNIQUEMENT avec le code Python, sans markdown ni backticks.
Exemple de format attendu:
fig = px.line(df, x='col1', y='col2', title='Mon Titre')
fig.update_layout(template='plotly_white')"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        code = response.text.strip()
        code = code.replace("```python", "").replace("```", "").strip()
        
        # Execute the code safely
        local_vars = {"df": df, "px": px, "go": go, "pd": pd}
        exec(code, {"__builtins__": {}}, local_vars)
        
        if "fig" in local_vars and isinstance(local_vars["fig"], (go.Figure,)):
            return local_vars["fig"]
        
    except Exception as e:
        pass  # Fall back to auto chart
    
    return create_auto_chart(df, chart_type)


def create_auto_chart(df: pd.DataFrame, chart_type: str = "auto") -> Optional[go.Figure]:
    """Create an automatic chart based on data structure."""
    if df is None or df.empty:
        return None
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    string_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Try to find timestamp-like columns
    time_cols = [c for c in df.columns if any(t in c.lower() for t in ['time', 'date', 'timestamp'])]
    if time_cols and time_cols[0] not in datetime_cols:
        try:
            df[time_cols[0]] = pd.to_datetime(df[time_cols[0]])
            datetime_cols = time_cols
        except:
            pass
    
    fig = None
    colors = ["#2E7D32", "#4CAF50", "#81C784", "#A5D6A7", "#C8E6C9"]
    
    try:
        if chart_type == "line" or (chart_type == "auto" and datetime_cols and numeric_cols):
            x_col = datetime_cols[0] if datetime_cols else (time_cols[0] if time_cols else df.columns[0])
            y_cols = numeric_cols[:3] if numeric_cols else [df.columns[1]]
            fig = px.line(df, x=x_col, y=y_cols, title="📈 Évolution temporelle - VertiFlow",
                         color_discrete_sequence=colors)
        
        elif chart_type == "bar" or (chart_type == "auto" and string_cols and numeric_cols):
            x_col = string_cols[0] if string_cols else df.columns[0]
            y_col = numeric_cols[0] if numeric_cols else df.columns[1]
            fig = px.bar(df.head(20), x=x_col, y=y_col, 
                        title=f"📊 Comparaison - {y_col}",
                        color_discrete_sequence=colors)
        
        elif chart_type == "pie" and numeric_cols:
            value_col = numeric_cols[0]
            name_col = string_cols[0] if string_cols else df.columns[0]
            fig = px.pie(df.head(10), values=value_col, names=name_col,
                        title=f"🥧 Répartition - {value_col}",
                        color_discrete_sequence=colors)
        
        elif chart_type == "scatter" and len(numeric_cols) >= 2:
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1],
                           title=f"🔵 Corrélation {numeric_cols[0]} vs {numeric_cols[1]}",
                           color_discrete_sequence=colors)
        
        elif numeric_cols:
            # Default: bar chart with first numeric column
            y_col = numeric_cols[0]
            x_col = string_cols[0] if string_cols else df.index
            fig = px.bar(df.head(20), y=y_col, 
                        title=f"📊 Analyse - {y_col}",
                        color_discrete_sequence=colors)
        
        if fig:
            fig.update_layout(
                template="plotly_white",
                font=dict(family="Arial", size=12),
                title_font=dict(size=16, color="#1B5E20"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(l=40, r=40, t=60, b=40)
            )
    except Exception as e:
        return None
    
    return fig


def generate_natural_response(
    user_question: str,
    sql_query: str,
    query_results: List[Dict],
    schemas: Dict[str, Any]
) -> str:
    """Generate natural language response from query results."""
    client = get_genai_client()
    if not client:
        return "Je n'ai pas pu générer une réponse."
    
    results_str = json.dumps(query_results[:20], indent=2, default=str, ensure_ascii=False)
    
    prompt = f"""Tu es l'assistant IA de VertiFlow, un projet d'agriculture verticale intelligente au Maroc.

Question de l'utilisateur: "{user_question}"

Requête SQL exécutée:
{sql_query}

Résultats (jusqu'à 20 lignes):
{results_str}

Nombre total de résultats: {len(query_results)}

Instructions:
1. Réponds dans la même langue que la question (Français, English, ou Darija)
2. Donne une réponse claire et concise basée sur les données
3. Mentionne les chiffres clés et tendances importantes
4. Si les données sont vides, explique-le poliment
5. Sois professionnel mais accessible
6. Pour le Darija, utilise l'alphabet arabe si la question est en arabe

Génère une réponse naturelle et informative:"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Erreur lors de la génération de la réponse: {e}"


def generate_general_response(user_question: str) -> str:
    """Generate response for general questions without SQL."""
    client = get_genai_client()
    if not client:
        return "Je suis l'assistant VertiFlow. Comment puis-je vous aider?"
    
    # Build ClickHouse context summary
    clickhouse_summary = "Données disponibles dans le système VertiFlow:\n"
    for table_name, table_info in CLICKHOUSE_CONTEXT.items():
        clickhouse_summary += f"• {table_name}: {table_info['description']}\n"
    
    prompt = f"""Tu es l'assistant IA de VertiFlow, un projet d'agriculture verticale intelligente au Maroc.

CONNAISSANCES DU DOMAINE:
{clickhouse_summary}

Tu aides les agriculteurs et ingénieurs avec des questions sur:
- La culture verticale (basilic Genovese/Thaï, laitue, herbes aromatiques)
- Les capteurs IoT (température, humidité, pH, EC, lumière PPFD, DLI)
- L'analyse des données de production et health_score
- Les recommandations agronomiques (VPD, nutrition N-P-K, recettes lumineuses)
- Les prédictions ML (rendement, anomalies, qualité Premium/Standard/Rejet)
- L'efficacité énergétique et le bilan carbone

CONTEXTE FERME:
- Localisation: Maroc (VERT-MAROC-01)
- Culture: Basilic en racks multi-niveaux
- Système: Hydroponie avec contrôle climatique automatisé
- IA: Modèles ML pour prédiction rendement et détection anomalies

Question de l'utilisateur: "{user_question}"

Réponds dans la même langue que la question (Français, English, ou Darija marocaine).
Sois professionnel, utile et concis. Utilise des exemples concrets du domaine."""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Erreur: {e}"


# =============================================================================
# MAIN QUERY FUNCTION
# =============================================================================
def query_vertiflow(user_question: str) -> Dict[str, Any]:
    """Main function to process user questions."""
    result = {"reply": "", "sql": None, "data": None, "error": None, "chart": None, "df": None}
    
    # Detect if user wants a chart
    chart_request = detect_chart_request(user_question)
    
    schemas = get_table_schemas()
    if not schemas:
        result["error"] = "Impossible de récupérer les schémas des tables."
        return result
    
    sql_result = generate_sql_query(user_question, schemas)
    
    if sql_result.get("error"):
        result["error"] = sql_result["error"]
        return result
    
    if not sql_result.get("needs_sql") or not sql_result.get("sql"):
        result["reply"] = generate_general_response(user_question)
        return result
    
    result["sql"] = sql_result["sql"]
    
    query_result = execute_sql_query(sql_result["sql"])
    
    if query_result.get("error"):
        result["error"] = f"Erreur SQL: {query_result['error']}"
        result["reply"] = generate_general_response(user_question)
        return result
    
    result["data"] = query_result["data"]
    result["df"] = query_result.get("df")
    
    # Generate chart if requested or if data is suitable
    if chart_request["wants_chart"] and result["df"] is not None and not result["df"].empty:
        chart = generate_chart(result["df"], user_question, chart_request["chart_type"])
        if chart:
            result["chart"] = chart
    
    result["reply"] = generate_natural_response(
        user_question,
        sql_result["sql"],
        query_result["data"],
        schemas
    )
    
    return result


# =============================================================================
# UI COMPONENTS
# =============================================================================
def render_sidebar():
    """Render the sidebar with modern glassmorphism design."""
    with st.sidebar:
        # Logo and Brand Section with fallback
        st.markdown(f'''
        <div class="logo-container">
            <img src="{LOGO_URL}" alt="VertiFlow" 
                 style="width: 100%; max-width: 280px; height: auto; border-radius: 12px;"
                 onerror="this.onerror=null; this.src='{LOGO_BASE64}';">
            <div class="logo-title">VertiFlow</div>
            <div class="logo-subtitle">Smart Vertical Farming</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Status Indicator
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <span class="status-online">
                <span class="status-dot"></span>
                AI Assistant Online
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # About Card
        st.markdown("""
        <div class="glass-card">
            <h4>🚀 Powered By</h4>
            <p><span class="metric-badge">🧠 Google Gemini</span></p>
            <p><span class="metric-badge">📊 BigQuery</span></p>
            <p><span class="metric-badge">☁️ Vertex AI</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Data Sources
        st.markdown("""
        <div class="glass-card">
            <h4>📡 Sources de données</h4>
            <p>🌡️ Capteurs IoT temps réel</p>
            <p>🌿 157 métriques agricoles</p>
            <p>🤖 Prédictions ML</p>
            <p>📈 Analytics avancés</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Languages
        st.markdown("""
        <div class="glass-card">
            <h4>🌍 Langues supportées</h4>
            <div class="lang-pills">
                <span class="lang-pill">🇫🇷 Français</span>
                <span class="lang-pill">🇬🇧 English</span>
                <span class="lang-pill">🇲🇦 الدارجة</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Session Info
        st.markdown(f"""
        <div class="glass-card">
            <h4>💬 Session Active</h4>
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--text-muted);">
                ID: {st.session_state.conversation_id[:12]}...
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # New Conversation Button
        if st.button("🔄 Nouvelle Conversation", use_container_width=True, type="primary"):
            reset_conversation()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Examples
        with st.expander("💡 Exemples de questions"):
            st.markdown("""
**📊 Analytics & Graphiques:**
- "Trace l'évolution de la température"
- "Montre un graphique de l'humidité"
- "Fais une comparaison en barres"

**🔍 Requêtes data:**
- "Quelles sont les dernières mesures?"
- "Montre les alertes récentes"

**🌿 Questions métier:**
- "Comment optimiser le VPD?"
- "Explique le health_score"
            """)


def render_chat_interface():
    """Render the main chat interface with modern design."""
    # Header
    st.markdown("""
    <div class="main-header">
        <div class="main-title">🌱 VertiFlow AI Assistant</div>
        <div class="main-subtitle">
            Intelligence Artificielle pour l'Agriculture Verticale au Maroc
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            if message["role"] == "assistant" and message.get("chart"):
                st.plotly_chart(message["chart"], use_container_width=True)
            
            if message["role"] == "assistant" and message.get("sql"):
                with st.expander("🔍 Requête SQL", expanded=False):
                    st.code(message["sql"], language="sql")
            
            if message["role"] == "assistant" and message.get("data"):
                with st.expander(f"📊 Données ({len(message['data'])} lignes)", expanded=False):
                    st.dataframe(message["data"], use_container_width=True)
    
    if prompt := st.chat_input("Posez votre question... / Ask your question... / سول سؤالك..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Analyse en cours..."):
                response = query_vertiflow(prompt)
            
            if response.get("error") and not response.get("reply"):
                st.error(f"❌ {response['error']}")
                assistant_message = f"Désolé, une erreur s'est produite: {response['error']}"
            else:
                assistant_message = response.get("reply", "Je n'ai pas pu trouver de réponse.")
                st.markdown(assistant_message)
                
                # Display chart if generated
                if response.get("chart"):
                    st.plotly_chart(response["chart"], use_container_width=True)
                
                if response.get("sql"):
                    with st.expander("🔍 Requête SQL", expanded=False):
                        st.code(response["sql"], language="sql")
                
                if response.get("data"):
                    with st.expander(f"📊 Données ({len(response['data'])} lignes)", expanded=False):
                        st.dataframe(response["data"], use_container_width=True)
                
                if response.get("error"):
                    st.warning(f"⚠️ Note: {response['error']}")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_message,
                "sql": response.get("sql"),
                "data": response.get("data"),
                "chart": response.get("chart")
            })


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()
    render_chat_interface()


if __name__ == "__main__":
    main()
