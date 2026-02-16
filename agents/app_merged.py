# -*- coding: utf-8 -*-
"""
🌿 AGRI-COPILOT - VertiFlow AI Assistant v2.1
==============================================
Interface ChatGPT-like avec TOUTES les fonctionnalités:
- Génération SQL intelligente via Gemini
- Graphiques Plotly (génération AI + auto-fallback)
- Historique conversations
- Dashboard temps réel
- Mode expert / thème jour-nuit
- Support multilingue (FR/EN/AR)
- Contexte complet ClickHouse (157 colonnes)

Powered by Google Gemini + BigQuery + Vertex AI
© 2026 VertiFlow - Smart Vertical Farming Morocco
"""

import streamlit as st
import uuid
import json
import re
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from io import BytesIO

import google.auth
from google.cloud import bigquery
from google import genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_ID = "vertiflow-484602"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-001"
APP_VERSION = "2.1.0"

# BigQuery tables
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

# =========================================================================
# CLICKHOUSE CONTEXT COMPLET (157 colonnes - Golden Record)
# =========================================================================
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

# Quick actions for welcome screen
QUICK_ACTIONS = [
    {"icon": "📈", "label": "Graphique température", "prompt": "Trace un graphique de l'évolution de la température sur les dernières 24h"},
    {"icon": "🌿", "label": "Analyser health_score", "prompt": "Analyse le health_score moyen des plantes et donne des recommandations"},
    {"icon": "⚡", "label": "Optimiser LED", "prompt": "Comment optimiser la consommation énergétique des LED?"},
    {"icon": "📅", "label": "Prochaine récolte", "prompt": "Quand est prévue la prochaine récolte de basilic?"},
    {"icon": "💧", "label": "État irrigation", "prompt": "Quel est l'état actuel du système d'irrigation et du pH?"},
    {"icon": "🔬", "label": "Analyse NPK", "prompt": "Analyse l'équilibre nutritionnel N-P-K actuel et suggère des ajustements"}
]

# =============================================================================
# PAGE CONFIG & THEMES
# =============================================================================
st.set_page_config(
    page_title="AGRI-COPILOT | VertiFlow AI",
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
            --bg-card: {t['bg_card']};
            --text-primary: {t['text_primary']};
            --text-secondary: {t['text_secondary']};
            --accent-green: {t['accent_green']};
            --accent-blue: {t['accent_blue']};
            --border: {t['border']};
        }}
        
        .stApp {{
            background: {'linear-gradient(180deg, #0F172A 0%, #1E293B 100%)' if is_dark else '#F1F5F9'};
            font-family: 'Inter', sans-serif;
        }}
        
        [data-testid="stSidebar"] {{
            background: {'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)' if is_dark else '#FFFFFF'};
            border-right: 1px solid var(--border);
        }}
        
        [data-testid="stSidebar"] * {{
            color: var(--text-primary) !important;
        }}
        
        .welcome-header {{
            text-align: center;
            padding: 3rem 0;
        }}
        
        .welcome-title {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-green) 0%, var(--accent-blue) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        
        .welcome-subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        .expert-badge {{
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            color: white;
            font-size: 0.7rem;
            padding: 0.25rem 0.75rem;
            border-radius: 100px;
            font-weight: 600;
        }}
        
        .glass-card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }}
        
        .metric-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: {'rgba(16,185,129,0.1)' if is_dark else 'rgba(5,150,105,0.1)'};
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 100px;
            padding: 0.4rem 0.8rem;
            font-size: 0.75rem;
            color: var(--accent-green);
            font-weight: 500;
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        [data-testid="stChatInput"] > div {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 25px !important;
        }}
        
        [data-testid="stChatInput"] textarea {{
            color: var(--text-primary) !important;
        }}
        
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: var(--text-secondary); border-radius: 3px; }}
        
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
    defaults = {
        "conversation_id": str(uuid.uuid4()),
        "messages": [],
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
    title = first_message[:40] + "..." if len(first_message) > 40 else first_message
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
        st.error(f"❌ Auth error: {e}")
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
        return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=creds)
    return None

# =============================================================================
# DATA FUNCTIONS
# =============================================================================
@st.cache_data(ttl=300)
def get_dashboard_metrics():
    client = get_bigquery_client()
    if not client:
        return {"temperature": 24.5, "humidity": 65.0, "health_score": 8.2, "readings": 150}
    
    try:
        query = """
        SELECT 
            AVG(CAST(JSON_EXTRACT_SCALAR(sensor_data, '$.temperature') AS FLOAT64)) as avg_temp,
            AVG(CAST(JSON_EXTRACT_SCALAR(sensor_data, '$.humidity') AS FLOAT64)) as avg_humidity,
            AVG(CAST(JSON_EXTRACT_SCALAR(sensor_data, '$.health_score') AS FLOAT64)) as avg_health,
            COUNT(*) as total_readings
        FROM `vertiflow-484602.vertiflow_analytics.sensor_telemetry`
        WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        """
        df = client.query(query).to_dataframe()
        if not df.empty:
            return {
                "temperature": round(df['avg_temp'].iloc[0] or 24.5, 1),
                "humidity": round(df['avg_humidity'].iloc[0] or 65.0, 1),
                "health_score": round(df['avg_health'].iloc[0] or 8.2, 1),
                "readings": int(df['total_readings'].iloc[0] or 0)
            }
    except:
        pass
    return {"temperature": 24.5, "humidity": 65.0, "health_score": 8.2, "readings": 150}

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
                "columns": [{"name": f.name, "type": f.field_type, "description": f.description or ""} 
                           for f in table.schema],
                "num_rows": table.num_rows
            }
        except Exception as e:
            schemas[key] = {"error": str(e)}
    return schemas

# =============================================================================
# AI QUERY FUNCTIONS (COMPLET)
# =============================================================================
def generate_sql_query(user_question: str, schemas: Dict[str, Any]) -> Dict[str, Any]:
    """Generate SQL from natural language using complete context."""
    client = get_genai_client()
    if not client:
        return {"error": "Client Gemini non disponible", "sql": None}
    
    # Build BigQuery schema context
    schema_context = "=== TABLES BIGQUERY (Interrogeables) ===\n\n"
    for table_key, schema in schemas.items():
        if "error" not in schema:
            schema_context += f"Table: {schema['full_name']}\n"
            schema_context += f"Description: {schema['description']}\n"
            schema_context += f"Lignes: {schema.get('num_rows', 'N/A')}\n"
            schema_context += "Colonnes:\n"
            for col in schema['columns'][:20]:
                schema_context += f"  - {col['name']} ({col['type']})\n"
            schema_context += "\n"
    
    # Build ClickHouse context
    clickhouse_context = "\n=== CONTEXTE CLICKHOUSE (157 colonnes - Golden Record) ===\n"
    clickhouse_context += "Ces données définissent le modèle de données VertiFlow:\n\n"
    
    for table_name, table_info in CLICKHOUSE_CONTEXT.items():
        clickhouse_context += f"📊 {table_name}: {table_info['description']}\n"
        if "categories" in table_info:
            for cat_name, cols in list(table_info["categories"].items())[:5]:
                clickhouse_context += f"   {cat_name}: {', '.join(cols[:5])}...\n"
        elif "columns" in table_info:
            clickhouse_context += f"   Colonnes: {', '.join(table_info['columns'][:8])}...\n"
        clickhouse_context += "\n"
    
    mode = "détaillé avec références scientifiques" if st.session_state.expert_mode else "simple et accessible"
    
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
    """Detect if user wants a chart with comprehensive keyword detection."""
    chart_keywords = [
        # French
        "graphe", "graphique", "tracer", "visualiser", "courbe", "diagramme",
        "histogramme", "camembert", "barres", "ligne", "tendance", "évolution",
        "comparaison", "distribution", "série temporelle", "afficher", "montre",
        # English
        "chart", "graph", "plot", "visualize", "visualization", "trend",
        "histogram", "pie", "bar", "line", "scatter", "show me", "display",
        # Darija
        "رسم", "بياني", "شوف", "ورني"
    ]
    
    question_lower = user_question.lower()
    wants_chart = any(kw in question_lower for kw in chart_keywords)
    
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


def generate_chart_with_ai(df: pd.DataFrame, user_question: str, chart_type: str = "auto") -> Optional[go.Figure]:
    """Generate chart using Gemini AI for intelligent visualization."""
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
4. Utilise des couleurs vertes (thème agriculture: #10B981, #059669, #34D399)
5. Ajoute un titre en français décrivant les données
6. Le résultat final doit être stocké dans une variable 'fig'
7. Utilise template='plotly_dark' pour le mode sombre

Réponds UNIQUEMENT avec le code Python, sans markdown ni backticks.
Exemple de format attendu:
fig = px.line(df, x='col1', y='col2', title='Mon Titre')
fig.update_layout(template='plotly_dark')"""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        code = response.text.strip()
        code = code.replace("```python", "").replace("```", "").strip()
        
        # Execute safely
        local_vars = {"df": df, "px": px, "go": go, "pd": pd}
        exec(code, {"__builtins__": {}}, local_vars)
        
        if "fig" in local_vars and isinstance(local_vars["fig"], go.Figure):
            # Apply theme
            is_dark = st.session_state.get("theme", "dark") == "dark"
            local_vars["fig"].update_layout(
                template="plotly_dark" if is_dark else "plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            return local_vars["fig"]
    except Exception as e:
        pass
    
    return create_auto_chart(df, chart_type)


def create_auto_chart(df: pd.DataFrame, chart_type: str = "auto") -> Optional[go.Figure]:
    """Fallback: Create automatic chart based on data structure."""
    if df is None or df.empty:
        return None
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    string_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Try to find timestamp columns
    time_cols = [c for c in df.columns if any(t in c.lower() for t in ['time', 'date', 'timestamp'])]
    if time_cols and time_cols[0] not in datetime_cols:
        try:
            df[time_cols[0]] = pd.to_datetime(df[time_cols[0]])
            datetime_cols = time_cols
        except:
            pass
    
    fig = None
    colors = ["#10B981", "#3B82F6", "#8B5CF6", "#F59E0B", "#EF4444"]
    is_dark = st.session_state.get("theme", "dark") == "dark"
    
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
            y_col = numeric_cols[0]
            fig = px.bar(df.head(20), y=y_col, 
                        title=f"📊 Analyse - {y_col}",
                        color_discrete_sequence=colors)
        
        if fig:
            fig.update_layout(
                template="plotly_dark" if is_dark else "plotly_white",
                font=dict(family="Inter", size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=40, t=60, b=40)
            )
    except:
        return None
    
    return fig


def generate_natural_response(user_question: str, sql_query: str, 
                            query_results: List[Dict], schemas: Dict[str, Any]) -> str:
    """Generate natural language response from query results."""
    client = get_genai_client()
    if not client:
        return "Je n'ai pas pu générer une réponse. Voici les données brutes."
    results_str = json.dumps(query_results[:20], indent=2, default=str, ensure_ascii=False)
    mode = "expert agronome avec références scientifiques" if st.session_state.expert_mode else "accessible et clair"
    lang = {"fr": "français", "en": "English", "ar": "العربية"}.get(st.session_state.language, "français")
    # Darija detection
    darija_keywords = ["شوف", "ورني", "بغيت", "عطيني", "شنو", "كيفاش", "فين", "علاش", "دابا", "بزاف", "مزيان", "خايب", "سميتو", "بلا", "ماشي", "واش", "عندك", "معاك", "دير", "سير", "جي", "حط", "خدم", "وقف", "زيد", "نقص", "سول", "جاوب", "سمع", "شحال", "بغيت", "عطيني"]
    user_lower = user_question.lower()
    is_darija = any(k in user_lower for k in darija_keywords) or st.session_state.language == "ar"
    prompt = f"""Tu es l'assistant IA de VertiFlow, un projet d'agriculture verticale intelligente au Maroc.\n\nQuestion utilisateur: \"{user_question}\"\n\nRequête SQL exécutée:\n{sql_query}\n\nRésultats (jusqu'à 20 lignes):\n{results_str}\n\nNombre total de résultats: {len(query_results)}\n\nMode de réponse: {mode}\nLangue préférée: {lang}\n\nInstructions:\n1. Si la question est en Darija (dialecte marocain), réponds en Darija (utilise l'alphabet arabe, style marocain, expressions locales, exemples concrets de la ferme).\n2. Sinon, réponds dans la même langue que la question (Français, English, ou Darija).\n3. Donne une réponse claire et structurée basée sur les données.\n4. Mentionne les chiffres clés et tendances importantes.\n5. Si les données sont vides, explique-le poliment.\n6. En mode expert, inclure: formules, références, statistiques détaillées.\n\nGénère une réponse naturelle et informative:"""
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Erreur lors de la génération de la réponse: {e}"


def generate_general_response(user_question: str) -> str:
    """Generate response for general questions without SQL."""
    client = get_genai_client()
    if not client:
        return "Je suis l'assistant VertiFlow. Comment puis-je vous aider?"
    # Build comprehensive ClickHouse context
    clickhouse_summary = "Données disponibles dans VertiFlow (157 colonnes Golden Record):\n"
    for table_name, table_info in CLICKHOUSE_CONTEXT.items():
        clickhouse_summary += f"• {table_name}: {table_info['description']}\n"
        if "categories" in table_info:
            for cat in list(table_info["categories"].keys())[:3]:
                clickhouse_summary += f"  - {cat}\n"
    mode = "expert agronome avec détails scientifiques" if st.session_state.expert_mode else "accessible"
    lang = {"fr": "français", "en": "English", "ar": "العربية"}.get(st.session_state.language, "français")
    # Darija detection
    darija_keywords = ["شوف", "ورني", "بغيت", "عطيني", "شنو", "كيفاش", "فين", "علاش", "دابا", "بزاف", "مزيان", "خايب", "سميتو", "بلا", "ماشي", "واش", "عندك", "معاك", "دير", "سير", "جي", "حط", "خدم", "وقف", "زيد", "نقص", "سول", "جاوب", "سمع", "شحال", "بغيت", "عطيني"]
    user_lower = user_question.lower()
    is_darija = any(k in user_lower for k in darija_keywords) or st.session_state.language == "ar"
    prompt = f"""Tu es l'assistant IA de VertiFlow, un projet d'agriculture verticale intelligente au Maroc.\n\nCONNAISSANCES DU DOMAINE:\n{clickhouse_summary}\n\nTu aides avec des questions sur:\n- Culture verticale (basilic Genovese/Thaï, laitue, herbes aromatiques)\n- Capteurs IoT (température, humidité, pH, EC, lumière PPFD, DLI)\n- Analyse données production et health_score\n- Recommandations agronomiques (VPD, nutrition N-P-K, recettes lumineuses)\n- Prédictions ML (rendement, anomalies, qualité Premium/Standard/Rejet)\n- Efficacité énergétique et bilan carbone\n\nCONTEXTE FERME:\n- Localisation: Maroc (VERT-MAROC-01)\n- Culture: Basilic en racks multi-niveaux\n- Système: Hydroponie avec contrôle climatique automatisé\n\nQuestion utilisateur: \"{user_question}\"\n\nMode de réponse: {mode}\nLangue préférée: {lang}\n\nInstructions:\n1. Si la question est en Darija (dialecte marocain), réponds en Darija (utilise l'alphabet arabe, style marocain, expressions locales, exemples concrets de la ferme).\n2. Sinon, réponds dans la même langue que la question (Français, English, ou Darija).\n3. Sois professionnel, utile et concis. Utilise des exemples concrets du domaine.\n4. En mode expert, inclure des références scientifiques et données techniques."""
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Erreur: {e}"


# =============================================================================
# MAIN QUERY FUNCTION (COMPLET)
# =============================================================================
def query_vertiflow(user_question: str) -> Dict[str, Any]:
    """Main function to process user questions with all features."""
    result = {"reply": "", "sql": None, "data": None, "error": None, "chart": None, "df": None}
    
    # Detect chart request
    chart_request = detect_chart_request(user_question)
    
    # Get schemas
    schemas = get_table_schemas()
    if not schemas:
        result["error"] = "Impossible de récupérer les schémas des tables."
        result["reply"] = generate_general_response(user_question)
        return result
    
    # Generate SQL
    sql_result = generate_sql_query(user_question, schemas)
    
    if sql_result.get("error"):
        result["error"] = sql_result["error"]
        result["reply"] = generate_general_response(user_question)
        return result
    
    if not sql_result.get("needs_sql") or not sql_result.get("sql"):
        result["reply"] = generate_general_response(user_question)
        return result
    
    result["sql"] = sql_result["sql"]
    
    # Execute SQL
    query_result = execute_sql_query(sql_result["sql"])
    
    if query_result.get("error"):
        result["error"] = f"Erreur SQL: {query_result['error']}"
        result["reply"] = generate_general_response(user_question)
        return result
    
    result["data"] = query_result["data"]
    result["df"] = query_result.get("df")
    
    # Generate chart if requested or data is suitable
    if chart_request["wants_chart"] and result["df"] is not None and not result["df"].empty:
        chart = generate_chart_with_ai(result["df"], user_question, chart_request["chart_type"])
        if chart:
            result["chart"] = chart
    
    # Generate natural response
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
    """Render ChatGPT-style sidebar with all features."""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 2.5rem;">🌿</div>
            <div style="font-size: 1.5rem; font-weight: 700; 
                 background: linear-gradient(135deg, #10B981, #3B82F6);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                AGRI-COPILOT
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; letter-spacing: 2px;">
                SMART VERTICAL FARMING
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # New Chat
        if st.button("➕ Nouveau Chat", use_container_width=True, type="primary"):
            new_conversation()
        
        st.divider()
        
        # Conversation History
        st.markdown("**💬 Historique**")
        for conv_id, conv in sorted(st.session_state.conversations.items(), 
                                    key=lambda x: x[1].get('created', ''), reverse=True):
            is_active = conv_id == st.session_state.current_conv_id
            if st.button(f"{'🟢' if is_active else '💬'} {conv['title'][:25]}", 
                        key=f"conv_{conv_id}", use_container_width=True,
                        type="primary" if is_active else "secondary"):
                switch_conversation(conv_id)
        
        st.divider()
        
        # Quick Modules
        st.markdown("**⚡ Modules**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📊 Analytics", use_container_width=True):
                st.session_state.quick_prompt = "Montre-moi un graphique des analytics des dernières 24h"
        with c2:
            if st.button("🌡️ Capteurs", use_container_width=True):
                st.session_state.quick_prompt = "Affiche l'état actuel des capteurs avec un tableau"
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💡 Conseils", use_container_width=True):
                st.session_state.quick_prompt = "Recommandations agronomiques du jour"
        with c2:
            if st.button("⚡ Énergie", use_container_width=True):
                st.session_state.quick_prompt = "Analyse de l'efficacité énergétique des LED avec graphique"
        
        st.divider()
        
        # Dashboard Live
        st.markdown("**📊 Dashboard Live**")
        metrics = get_dashboard_metrics()
        if metrics:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("🌡️ Temp", f"{metrics['temperature']}°C")
            with c2:
                st.metric("💧 Humid", f"{metrics['humidity']}%")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("🌿 Santé", f"{metrics['health_score']}/10")
            with c2:
                st.metric("📡 Mesures", f"{metrics['readings']}")
        
        st.divider()
        
        # Settings
        st.markdown("**⚙️ Paramètres**")
        
        theme = st.toggle("🌙 Mode sombre", value=st.session_state.theme == "dark")
        if theme != (st.session_state.theme == "dark"):
            st.session_state.theme = "dark" if theme else "light"
            st.rerun()
        
        expert = st.toggle("🔬 Mode Expert", value=st.session_state.expert_mode)
        if expert != st.session_state.expert_mode:
            st.session_state.expert_mode = expert
        
        lang = st.selectbox("🌍 Langue", ["Français", "English", "العربية"],
                          index=["fr", "en", "ar"].index(st.session_state.language))
        st.session_state.language = ["fr", "en", "ar"][["Français", "English", "العربية"].index(lang)]
        
        # Powered by
        st.markdown("""
        <div class="glass-card" style="margin-top: 1rem;">
            <div style="font-size: 0.8rem; font-weight: 600; margin-bottom: 0.5rem;">🚀 Powered By</div>
            <span class="metric-badge">🧠 Gemini</span>
            <span class="metric-badge">📊 BigQuery</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="font-size: 0.7rem; color: #64748B; text-align: center; margin-top: 1rem;">
            v{APP_VERSION} • VertiFlow Morocco 🇲🇦
        </div>
        """, unsafe_allow_html=True)


def render_welcome():
    """Render welcome screen."""
    st.markdown("""
    <div class="welcome-header">
        <div class="welcome-title">🌿 Bienvenue sur AGRI-COPILOT</div>
        <div class="welcome-subtitle">
            Votre assistant IA pour l'agriculture verticale au Maroc<br>
            Graphiques • Tables • Analyses • Recommandations
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 Actions Rapides")
    cols = st.columns(3)
    for i, action in enumerate(QUICK_ACTIONS):
        with cols[i % 3]:
            if st.button(f"{action['icon']} {action['label']}", key=f"quick_{i}", use_container_width=True):
                return action['prompt']
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #94A3B8; font-size: 0.9rem;">
        <p>Posez une question en <strong>français</strong>, <strong>anglais</strong> ou <strong>darija</strong> 🇲🇦</p>
        <p>Exemples: "Trace un graphique de température", "Montre les données dans une table"</p>
    </div>
    """, unsafe_allow_html=True)
    
    return None


def render_chat():
    """Render main chat interface."""
    if st.session_state.expert_mode:
        st.markdown("""
        <div style="text-align: right; margin-bottom: 1rem;">
            <span class="expert-badge">🔬 MODE EXPERT</span>
        </div>
        """, unsafe_allow_html=True)
    
    if not st.session_state.messages:
        quick_prompt = render_welcome()
        if quick_prompt:
            st.session_state.pending_prompt = quick_prompt
            st.rerun()
    
    # Display messages
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🧑‍🌾" if msg["role"] == "user" else "🌿"):
            st.markdown(msg["content"])
            
            if msg["role"] == "assistant":
                if msg.get("chart"):
                    st.plotly_chart(msg["chart"], use_container_width=True)
                
                if msg.get("sql"):
                    with st.expander("🔍 Requête SQL", expanded=False):
                        st.code(msg["sql"], language="sql")
                
                if msg.get("data"):
                    with st.expander(f"📊 Données ({len(msg['data'])} lignes)", expanded=False):
                        df = pd.DataFrame(msg["data"])
                        st.dataframe(df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button("📥 Télécharger CSV", csv, 
                                         "vertiflow_data.csv", "text/csv", key=f"dl_{i}")


def main():
    """Main application."""
    init_session_state()
    apply_theme_css()
    render_sidebar()
    render_chat()
    
    # Handle quick prompts
    if hasattr(st.session_state, 'pending_prompt') and st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        st.session_state.messages.append({"role": "user", "content": prompt})
        if len(st.session_state.messages) == 1:
            update_conversation_title(st.session_state.current_conv_id, prompt)
        
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("🌱 Analyse en cours..."):
                response = query_vertiflow(prompt)
            st.markdown(response["reply"])
            if response.get("chart"):
                st.plotly_chart(response["chart"], use_container_width=True)
            if response.get("sql"):
                with st.expander("🔍 Requête SQL"):
                    st.code(response["sql"], language="sql")
            if response.get("data"):
                with st.expander(f"📊 Données ({len(response['data'])} lignes)"):
                    st.dataframe(response["data"], use_container_width=True)
        
        st.session_state.messages.append({
            "role": "assistant", "content": response["reply"],
            "sql": response.get("sql"), "data": response.get("data"),
            "chart": response.get("chart")
        })
        st.session_state.conversations[st.session_state.current_conv_id]["messages"] = st.session_state.messages
        st.rerun()
    
    if hasattr(st.session_state, 'quick_prompt') and st.session_state.quick_prompt:
        st.session_state.pending_prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Posez votre question... 🌿"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        if len(st.session_state.messages) == 1:
            update_conversation_title(st.session_state.current_conv_id, prompt)
        
        with st.chat_message("user", avatar="🧑‍🌾"):
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("🌱 Analyse en cours..."):
                response = query_vertiflow(prompt)
            
            st.markdown(response["reply"])
            
            if response.get("chart"):
                st.plotly_chart(response["chart"], use_container_width=True)
            
            if response.get("sql"):
                with st.expander("🔍 Requête SQL"):
                    st.code(response["sql"], language="sql")
            
            if response.get("data"):
                with st.expander(f"📊 Données ({len(response['data'])} lignes)"):
                    df = pd.DataFrame(response["data"])
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 CSV", df.to_csv(index=False), 
                                      "vertiflow_data.csv", "text/csv")
            
            if response.get("error"):
                st.warning(f"⚠️ Note: {response['error']}")
        
        st.session_state.messages.append({
            "role": "assistant", "content": response["reply"],
            "sql": response.get("sql"), "data": response.get("data"),
            "chart": response.get("chart")
        })
        st.session_state.conversations[st.session_state.current_conv_id]["messages"] = st.session_state.messages
        st.rerun()


if __name__ == "__main__":
    main()
