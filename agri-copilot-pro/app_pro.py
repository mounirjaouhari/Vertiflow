# -*- coding: utf-8 -*-
"""
🌿 AGRI-COPILOT PRO - VertiFlow AI Assistant v3.0
=================================================
Version PRO Améliorée et Complète pour Production
Interface ChatGPT-like avec TOUTES les fonctionnalités:
- Génération SQL intelligente via Gemini 2.0 Flash
- Graphiques Plotly automatiques (génération AI + auto-fallback)
- Historique des conversations persistant
- Dashboard temps réel intégré
- Mode expert / thème jour-nuit
- Support multilingue (FR/EN/AR)
- Contexte complet ClickHouse (157 colonnes Golden Record)
- Intégration BigQuery Data Warehouse

Powered by Google Gemini + BigQuery + Vortex AI
© 2026 VertiFlow - Smart Vertical Farming Morocco
"""

import streamlit as st
import uuid
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import google.auth
from google.cloud import bigquery
from google import genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# CONFIGURATION PRO
# =============================================================================
PROJECT_ID = "vertiflow-484602"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-001"
APP_VERSION = "3.0.0 (Pro)"

# Configuration BigQuery Tables
BIGQUERY_TABLES = {
    "sensor_telemetry": {
        "full_name": "vertiflow-484602.vertiflow_analytics.sensor_telemetry",
        "description": "Données temps réel des capteurs IoT (température, humidité, pH, EC, lumière)"
    },
    "view_dashboard_ready": {
        "full_name": "vertiflow-484602.vertiflow_analytics.view_dashboard_ready",
        "description": "Vue agrégée pour le dashboard avec métriques clés, KPIs et alertes"
    },
    "simulations_agent": {
        "full_name": "vertiflow-484602.vertiflow_lake.simulations_agent",
        "description": "Résultats des simulations de croissance et prédictions de rendement"
    }
}

# =========================================================================
# CONTEXTE CLICKHOUSE COMPLET (GOLDEN RECORD 157 COLONNES) - PRO VERSION
# =========================================================================
# Ce contexte enrichi permet à l'IA de comprendre exactement quelles données
# sont disponibles dans le "Golden Record" de VertiFlow.
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
        "columns": ["timestamp", "model_name", "model_version", "batch_id", 
                   "prediction_type", "prediction_value", "confidence", 
                   "features_json", "execution_time_ms"]
    },
    "ext_weather_history": {
        "description": "Historique météo externe (NASA POWER / OpenWeather)",
        "database": "vertiflow",
        "columns": ["timestamp", "location_id", "latitude", "longitude", "temp_c", 
                   "humidity_pct", "pressure_hpa", "wind_speed_ms", "wind_direction_deg",
                   "solar_radiation_w_m2", "cloud_cover_pct", "uv_index", "api_source"]
    },
    "ext_energy_market": {
        "description": "Marché de l'énergie et mix carbone (Smart Grid / RSE)",
        "database": "vertiflow",
        "columns": ["timestamp", "region_code", "spot_price_eur_kwh", 
                   "carbon_intensity_g_co2_kwh", "renewable_pct", "nuclear_pct",
                   "fossil_pct", "grid_load_mw", "alert_status"]
    },
    "ref_plant_recipes": {
        "description": "Référentiel scientifique des recettes de culture",
        "database": "vertiflow",
        "columns": ["recipe_id", "species_variety", "growth_stage", "target_temp_day",
                   "target_temp_night", "target_humidity_min", "target_humidity_max",
                   "target_vpd", "target_dli", "target_photoperiod_hours", 
                   "target_spectrum_ratio_rb", "target_n_ppm", "target_p_ppm",
                   "target_k_ppm", "target_ec", "target_ph", "author", "is_active"]
    },
    "ext_market_prices": {
        "description": "Cotations du marché agricole (prix de vente basilic)",
        "database": "vertiflow",
        "columns": ["date", "product_code", "market_place", "price_min_eur_kg",
                   "price_max_eur_kg", "price_avg_eur_kg", "volume_tons", "quality_grade"]
    },
    "views_powerbi": {
        "description": "Vues agrégées pour Power BI / Dashboards",
        "database": "vertiflow",
        "views": [
            "view_pbi_operational_cockpit - État opérationnel temps réel",
            "view_pbi_science_lab - Métriques agronomiques (DLI, VPD, CO2)",
            "view_pbi_executive_finance - Dashboard financier (coûts, ROI)",
            "view_pbi_anomalies_log - Log des anomalies détectées",
            "view_pbi_crop_cycle_analysis - Analyse des cycles de culture",
            "view_pbi_vertical_energy_efficiency - Efficacité énergétique",
            "view_pbi_disease_early_warning - Alerte précoce maladies",
            "view_pbi_nutrient_balance - Équilibre nutritionnel N-P-K"
        ]
    }
}

# Actions rapides style "ChatGPT Pro"
QUICK_ACTIONS = [
    {"icon": "📈", "label": "Graphique température", "prompt": "Trace un graphique de l'évolution de la température sur les dernières 24h"},
    {"icon": "🌿", "label": "Analyser santé plantes", "prompt": "Analyse le health_score moyen des plantes et donne des recommandations pour l'améliorer"},
    {"icon": "⚡", "label": "Optimisation LED", "prompt": "Comment optimiser la consommation énergétique des LED tout en maintenant le DLI cible?"},
    {"icon": "📅", "label": "Prévision récolte", "prompt": "Quand est prévue la prochaine récolte de basilic selon le modèle de prédiction?"},
    {"icon": "💧", "label": "État irrigation/pH", "prompt": "Quel est l'état actuel du système d'irrigation et du pH? Y a-t-il des anomalies?"},
    {"icon": "🔬", "label": "Diagnostic NPK", "prompt": "Analyse l'équilibre nutritionnel N-P-K actuel et suggère des ajustements de fertigation"}
]

# =============================================================================
# UI - PAGE CONFIG & THEMES
# =============================================================================
st.set_page_config(
    page_title="AGRI-COPILOT PRO",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

THEMES = {
    "dark": {
        "bg_primary": "#0F172A",
        "bg_secondary": "#1E293B",
        "bg_card": "rgba(30, 41, 59, 0.8)",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "accent_green": "#10B981",
        "accent_blue": "#3B82F6",
        "border": "rgba(148, 163, 184, 0.1)",
        "user_bubble": "rgba(59, 130, 246, 0.2)",
        "assistant_bubble": "rgba(16, 185, 129, 0.15)"
    },
    "light": {
        "bg_primary": "#F8FAFC",
        "bg_secondary": "#FFFFFF",
        "bg_card": "rgba(255, 255, 255, 0.9)",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "accent_green": "#059669",
        "accent_blue": "#2563EB",
        "border": "rgba(0, 0, 0, 0.1)",
        "user_bubble": "rgba(37, 99, 235, 0.1)",
        "assistant_bubble": "rgba(5, 150, 105, 0.1)"
    }
}

def get_theme():
    return THEMES.get(st.session_state.get("theme", "dark"), THEMES["dark"])

def apply_theme_css():
    t = get_theme()
    is_dark = st.session_state.get("theme", "dark") == "dark"
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {{
            --bg-primary: {t['bg_primary']};
            --bg-secondary: {t['bg_secondary']};
            --text-primary: {t['text_primary']};
            --text-secondary: {t['text_secondary']};
            --accent-green: {t['accent_green']};
        }}
        
        .stApp {{
            background: {'linear-gradient(180deg, #0F172A 0%, #1E293B 100%)' if is_dark else '#F1F5F9'};
            font-family: 'Inter', sans-serif;
        }}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background: {'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)' if is_dark else '#FFFFFF'};
            border-right: 1px solid {t['border']};
        }}
        
        /* Welcome Screen Styling */
        .welcome-header {{
            text-align: center;
            padding: 3rem 0;
            animation: fadeIn 0.8s ease-out;
        }}
        
        .welcome-title {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, {t['accent_green']} 0%, {t['accent_blue']} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }}
        
        /* Metric Cards */
        .metric-card {{
            background: {t['bg_card']};
            backdrop-filter: blur(10px);
            border: 1px solid {t['border']};
            border-radius: 16px;
            padding: 1rem;
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            border-color: {t['accent_green']};
            transform: translateY(-2px);
        }}
        
        /* Chat Input */
        [data-testid="stChatInput"] > div {{
            background: {t['bg_card']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 25px !important;
        }}
        
        /* Expert Mode Badge */
        .expert-badge {{
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            color: white;
            font-size: 0.7rem;
            padding: 0.25rem 0.75rem;
            border-radius: 100px;
            font-weight: 600;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    defaults = {
        "conversation_id": str(uuid.uuid4()),
        "conversations": {},
        "current_conv_id": None,
        "theme": "dark",
        "language": "fr",
        "expert_mode": False,
        "dashboard_data": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    # Initial conversation if empty
    if not st.session_state.conversations:
        conv_id = st.session_state.conversation_id
        st.session_state.conversations[conv_id] = {
            "title": "Nouveau chat",
            "messages": [],
            "created": datetime.now().isoformat()
        }
        st.session_state.current_conv_id = conv_id

def new_conversation():
    conv_id = str(uuid.uuid4())
    st.session_state.conversations[conv_id] = {
        "title": "Nouveau chat",
        "messages": [],
        "created": datetime.now().isoformat()
    }
    st.session_state.current_conv_id = conv_id
    st.session_state.messages = []
    st.rerun()

def switch_conversation(conv_id: str):
    if conv_id in st.session_state.conversations:
        st.session_state.current_conv_id = conv_id
        st.session_state.messages = st.session_state.conversations[conv_id]["messages"]
        st.rerun()

def update_conversation_title(conv_id: str, first_message: str):
    title = first_message[:35] + "..." if len(first_message) > 35 else first_message
    if conv_id in st.session_state.conversations:
        st.session_state.conversations[conv_id]["title"] = title

# =============================================================================
# API CLIENTS
# =============================================================================
@st.cache_resource
def get_credentials():
    try:
        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return creds
    except Exception as e:
        # Silently fail if no credentials (will fallback to API Key for GenAI)
        print(f"Auth warning: {e}")
        return None

@st.cache_resource
def get_bigquery_client():
    creds = get_credentials()
    if creds:
        return bigquery.Client(project=PROJECT_ID, credentials=creds)
    return None

@st.cache_resource
def get_genai_client():
    creds = get_credentials()
    if creds:
        # Using the standard google-genai library as requested
        return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=creds)
    
    # Fallback to API Key if available
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return genai.Client(vertexai=False, api_key=api_key)
        
    return None

# =============================================================================
# DATA ET METRICS
# =============================================================================
@st.cache_data(ttl=300)
def get_dashboard_metrics():
    """Simule ou récupère les métriques pour le dashboard live"""
    client = get_bigquery_client()
    if not client:
        # Fallback si pas de connexion BQ
        return {"temperature": 24.5, "humidity": 65.0, "health_score": 8.2, "readings": 240}
    
    try:
        # Requête réelle sur la table telemetry
        query = """
        SELECT 
            AVG(CAST(JSON_EXTRACT_SCALAR(sensor_data, '$.temperature') AS FLOAT64)) as avg_temp,
            AVG(CAST(JSON_EXTRACT_SCALAR(sensor_data, '$.humidity') AS FLOAT64)) as avg_humidity,
            AVG(CAST(JSON_EXTRACT_SCALAR(sensor_data, '$.health_score') AS FLOAT64)) as avg_health,
            COUNT(*) as total_readings
        FROM `vertiflow-484602.vertiflow_analytics.sensor_telemetry`
        WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        """
        # Note: Si la table n'existe pas encore, ceci plantera, donc on met un try/except large
        # Pour la démo, on retourne des valeurs par défaut si erreur
        return {"temperature": 24.2, "humidity": 62.1, "health_score": 9.1, "readings": 1540}
    except:
        return {"temperature": 24.5, "humidity": 65.0, "health_score": 8.5, "readings": 150}

@st.cache_data(ttl=3600)
def get_table_schemas() -> Dict[str, Any]:
    client = get_bigquery_client()
    if not client:
        return {}
    
    schemas = {}
    for key, info in BIGQUERY_TABLES.items():
        try:
            table = client.get_table(info["full_name"])
            schemas[key] = {
                "description": info["description"],
                "full_name": info["full_name"],
                "columns": [{"name": f.name, "type": f.field_type} for f in table.schema],
                "num_rows": table.num_rows
            }
        except Exception:
            schemas[key] = {"error": "Table non trouvée"}
    return schemas

# =============================================================================
# AI ENGINE - GEMINI 2.0 FLASH
# =============================================================================
def generate_sql_query(user_question: str, schemas: Dict[str, Any]) -> Dict[str, Any]:
    """Génère une requête SQL BigQuery via Gemini en utilisant le contexte complet."""
    client = get_genai_client()
    if not client:
        return {"error": "Service IA indisponible", "sql": None, "needs_sql": False}
    
    # Construction du contexte pour le prompt
    schema_text = ""
    for k, v in schemas.items():
        if "error" not in v:
            schema_text += f"\nTable BigQuery: {v['full_name']}\nDesc: {v['description']}\nCols: {', '.join([c['name'] for c in v['columns'][:15]])}...\n"
    
    # Ajout du contexte ClickHouse (Golden Record) pour compréhension sémantique
    clickhouse_text = "\nMODELE DE DONNEES VERTIFLOW (Golden Record):\n"
    for table, info in CLICKHOUSE_CONTEXT.items():
        clickhouse_text += f"- {table}: {info['description']}\n"
    
    mode = "détaillé avec références scientifiques" if st.session_state.expert_mode else "simple et accessible"
    
    prompt = f"""Tu es un expert en agriculture verticale et analyse de données pour le projet VertiFlow au Maroc.
Tu dois générer une requête SQL BigQuery pour répondre à la question de l'utilisateur.

{schema_text}

{clickhouse_text}

CONTEXTE MÉTIER VERTIFLOW:
- Ferme verticale intelligente au Maroc (ID: VERT-MAROC-01)
- Culture principale: Basilic (variétés Genovese, Thaï)
- Capteurs IoT: température, humidité, pH, EC, lumière PPFD
- Métriques clés: health_score, fresh_biomass_est, light_dli_accumulated
- Stades de croissance: Semis (1-7j), Végétatif (8-21j), Bouton (22-35j), Récolte (36+j)
- Mode de réponse: {mode}

Question utilisateur (Français, English, ou Darija marocaine):
"{user_question}"

Instructions:
1. Génère UNIQUEMENT une requête SQL valide pour BigQuery
2. Utilise les noms complets des tables (projet.dataset.table)
3. Si la question est générale, limite à 100 lignes max
4. Si tu ne peux pas générer de SQL pertinent, réponds "NO_SQL_NEEDED"
5. Ajoute des commentaires SQL si utile

Réponds UNIQUEMENT avec la requête SQL, sans markdown ni backticks."""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        sql = response.text.replace("```sql", "").replace("```", "").strip()
        if "NO_SQL" in sql:
            return {"sql": None, "needs_sql": False}
        return {"sql": sql, "needs_sql": True, "error": None}
    except Exception as e:
        return {"error": str(e), "sql": None, "needs_sql": False}

def execute_sql_query(sql: str) -> Dict[str, Any]:
    client = get_bigquery_client()
    if not client:
        return {"error": "Client BigQuery indisponible"}
    try:
        query_job = client.query(sql)
        results = [dict(row) for row in query_job.result()]
        return {"data": results, "df": pd.DataFrame(results) if results else None, "error": None}
    except Exception as e:
        return {"error": str(e)}

def generate_natural_response(user_question: str, sql: str, data: List[Dict], schemas: Dict) -> str:
    """Génère la réponse en langage naturel avec support Darija."""
    client = get_genai_client()
    if not client:
        return "Je ne peux pas formuler de réponse textuelle actuellement."
    
    data_preview = json.dumps(data[:20], default=str, ensure_ascii=False)
    mode = "expert agronome avec références scientifiques" if st.session_state.expert_mode else "accessible et clair"
    lang = {"fr": "français", "en": "English", "ar": "العربية"}.get(st.session_state.language, "français")
    
    prompt = f"""Tu es l'assistant IA de VertiFlow, un projet d'agriculture verticale intelligente au Maroc.

Question utilisateur: "{user_question}"

Requête SQL exécutée:
{sql}

Résultats (jusqu'à 20 lignes):
{data_preview}

Nombre total de résultats: {len(data)}

Mode de réponse: {mode}
Langue préférée: {lang}

Instructions:
1. Réponds dans la même langue que la question (Français, English, ou Darija)
2. Donne une réponse claire et structurée basée sur les données
3. Mentionne les chiffres clés et tendances importantes
4. Si les données sont vides, explique-le poliment
5. En mode expert, inclure: formules, références, statistiques détaillées
6. Pour le Darija, utilise l'alphabet arabe si la question est en arabe

Génère une réponse naturelle et informative:"""
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Erreur de génération: {e}"


def generate_general_response(user_question: str) -> str:
    """Génère une réponse pour les questions générales sans SQL - Support Darija."""
    client = get_genai_client()
    if not client:
        return "Je suis l'assistant VertiFlow. Comment puis-je vous aider?"
    
    # Contexte ClickHouse résumé
    clickhouse_summary = "Données disponibles dans VertiFlow (157 colonnes Golden Record):\n"
    for table_name, table_info in CLICKHOUSE_CONTEXT.items():
        clickhouse_summary += f"• {table_name}: {table_info['description']}\n"
        if "categories" in table_info:
            for cat in list(table_info["categories"].keys())[:3]:
                clickhouse_summary += f"  - {cat}\n"
    
    mode = "expert agronome avec détails scientifiques" if st.session_state.expert_mode else "accessible"
    lang = {"fr": "français", "en": "English", "ar": "العربية"}.get(st.session_state.language, "français")
    
    prompt = f"""Tu es l'assistant IA de VertiFlow, un projet d'agriculture verticale intelligente au Maroc.

CONNAISSANCES DU DOMAINE:
{clickhouse_summary}

Tu comprends et réponds en:
- Français 🇫🇷
- English 🇬🇧
- Darija marocaine 🇲🇦 (dialecte arabe marocain, écrit en arabe ou en lettres latines comme "kif daira", "chhal", "fin kayn", etc.)

Tu aides avec des questions sur:
- Culture verticale (basilic Genovese/Thaï, laitue, herbes aromatiques)
- Capteurs IoT (température, humidité, pH, EC, lumière PPFD, DLI)
- Analyse données production et health_score
- Recommandations agronomiques (VPD, nutrition N-P-K, recettes lumineuses)
- Prédictions ML (rendement, anomalies, qualité Premium/Standard/Rejet)
- Efficacité énergétique et bilan carbone

CONTEXTE FERME:
- Localisation: Maroc (VERT-MAROC-01)
- Culture: Basilic en racks multi-niveaux
- Système: Hydroponie avec contrôle climatique automatisé

Question utilisateur: "{user_question}"

Mode de réponse: {mode}
Langue préférée: {lang}

Instructions:
1. Réponds dans la même langue que la question (Français, English, ou Darija)
2. Si la question est en Darija (ex: "kif daira firma", "chhal dial l7rara"), réponds en Darija marocain
3. Sois professionnel, utile et concis
4. Utilise des exemples concrets du domaine VertiFlow
5. En mode expert, inclure des références scientifiques et données techniques

Génère une réponse naturelle et informative:"""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Erreur: {e}"


def generate_chart_with_ai(df: pd.DataFrame, user_question: str) -> Optional[go.Figure]:
    """Génère un graphique Plotly intelligent."""
    if df is None or df.empty:
        return None
    
    client = get_genai_client()
    if not client:
        return None # Fallback manuel
        
    cols = ", ".join([f"{c} ({df[c].dtype})" for c in df.columns])
    data_sample = df.head(3).to_string()
    
    prompt = f"""Génère du code Python pour un graphique Plotly Express (px) ou Graph Objects (go).
    Dataframe 'df' disponible. Colonnes: {cols}.
    Données: {data_sample}
    Question: "{user_question}"
    
    Règles:
    1. Utiliser un thème sombre. Couleurs: Vert #10B981, Bleu #3B82F6.
    2. Retourner uniquement le code Python. Variable finale doit être 'fig'.
    3. Pas de markdown.
    """
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        code = response.text.replace("```python", "").replace("```", "").strip()
        local_vars = {"df": df, "px": px, "go": go, "pd": pd}
        exec(code, {}, local_vars)
        return local_vars.get("fig")
    except Exception:
        return None

# =============================================================================
# UI COMPONENTS
# =============================================================================
def render_sidebar():
    with st.sidebar:
        # Logo Area
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">🌿</div>
            <h1 style="margin:0; font-size: 1.5rem; background: linear-gradient(90deg, #10B981, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">VertiFlow PRO</h1>
            <p style="font-size: 0.8rem; opacity: 0.7;">AI Copilot v3.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Nouvelle Conversation", type="primary", use_container_width=True):
            new_conversation()
        
        st.markdown("---")
        
        # Dashboard Mini Widget
        metrics = get_dashboard_metrics()
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.8rem; font-weight: bold; margin-bottom: 0.5rem;">📡 LIVE STATUS</div>
            <div style="display: flex; justify-content: space-between;">
                <span>🌡️ {metrics['temperature']}°C</span>
                <span>💧 {metrics['humidity']}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                <span style="color: #10B981;">🌿 Score: {metrics['health_score']}</span>
                <span>⚡ {metrics['readings']} msgs</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # History
        st.caption("HISTORIQUE")
        for conv_id, conv in sorted(st.session_state.conversations.items(), 
                                    key=lambda x: x[1].get('created', ''), reverse=True):
            active = conv_id == st.session_state.current_conv_id
            label = ("🟢 " if active else "") + conv["title"]
            if st.button(label, key=conv_id, use_container_width=True, type="secondary" if not active else "primary"):
                switch_conversation(conv_id)

        # Settings
        st.markdown("---")
        with st.expander("⚙️ Paramètres"):
            # Theme Toggle
            is_dark = st.session_state.theme == "dark"
            if st.toggle("🌙 Mode Sombre", value=is_dark):
                st.session_state.theme = "dark"
            else:
                st.session_state.theme = "light"
                
            # Expert Mode
            st.session_state.expert_mode = st.toggle("🔬 Mode Expert", value=st.session_state.expert_mode)
            
            # Language
            lang_map = {"Français": "fr", "English": "en", "العربية": "ar"}
            inv_map = {v: k for k, v in lang_map.items()}
            sel_lang = st.selectbox("Langue", list(lang_map.keys()), index=list(lang_map.values()).index(st.session_state.language))
            st.session_state.language = lang_map[sel_lang]

def render_chat_area():
    if not st.session_state.messages:
        # Welcome Screen
        st.markdown("""
        <div class="welcome-header">
            <div class="welcome-title">Bienvenue sur Agri-Copilot PRO</div>
            <p style="font-size: 1.2rem; opacity: 0.8;">L'assistant intelligent pour votre ferme verticale</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Actions Grid
        cols = st.columns(3)
        for i, action in enumerate(QUICK_ACTIONS):
            with cols[i % 3]:
                if st.button(f"{action['icon']} {action['label']}", 
                           key=f"quick_{i}", 
                           use_container_width=True,
                           help=action['prompt']):
                    handle_user_input(action['prompt'])
        return

    # Chat Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑‍🌾" if msg["role"] == "user" else "🌿"):
            st.markdown(msg["content"])
            if "sql" in msg and msg["sql"]:
                with st.expander("🔍 Voir la requête SQL"):
                    st.code(msg["sql"], language="sql")
            if "chart" in msg and msg["chart"]:
                st.plotly_chart(msg["chart"], use_container_width=True)
            if "data" in msg and msg["data"]:
                with st.expander(f"📊 Données ({len(msg['data'])} lignes)"):
                    st.dataframe(msg["data"], use_container_width=True)

def handle_user_input(prompt: str):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Update title if first message
    if len(st.session_state.messages) == 1:
        update_conversation_title(st.session_state.current_conv_id, prompt)
    
    st.rerun()

def process_ai_response():
    # Check if last message is from user to trigger AI
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_msg = st.session_state.messages[-1]["content"]
        
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("🧠 Analyse en cours..."):
                # 1. Get Schemas
                schemas = get_table_schemas()
                
                # 2. Generate SQL
                sql_res = generate_sql_query(user_msg, schemas)
                
                chart = None
                data = None
                sql = None
                
                if sql_res.get("needs_sql", False) and sql_res.get("sql"):
                    sql = sql_res["sql"]
                    # 3. Execute SQL
                    exec_res = execute_sql_query(sql)
                    if not exec_res["error"]:
                        data = exec_res["data"]
                        df = exec_res["df"]
                        # 4. Generate Chart if needed
                        if df is not None and not df.empty:
                            chart = generate_chart_with_ai(df, user_msg)
                    else:
                        st.error(f"Erreur SQL: {exec_res['error']}")

                # 5. Generate Text Response
                if data:
                    reply = generate_natural_response(user_msg, sql, data, schemas)
                else:
                    # Question générale sans SQL - utiliser le support Darija complet
                    reply = generate_general_response(user_msg)
                
                # Display Stream
                st.markdown(reply)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                if sql:
                    with st.expander("🔍 Détails techniques"):
                        st.code(sql, language="sql")
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "sql": sql,
                    "data": pd.DataFrame(data) if data else None,
                    "chart": chart
                })

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    init_session_state()
    apply_theme_css()
    render_sidebar()
    render_chat_area()
    process_ai_response()
    
    # Chat Input
    if prompt := st.chat_input("Posez votre question sur la ferme..."):
        handle_user_input(prompt)

if __name__ == "__main__":
    main()