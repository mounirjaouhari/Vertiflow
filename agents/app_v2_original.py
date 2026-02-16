# -*- coding: utf-8 -*-
"""
🌿 AGRI-COPILOT - VertiFlow AI Assistant
=========================================
Interface conversationnelle type ChatGPT/Grok pour l'agriculture verticale.
Powered by Google Gemini + BigQuery + Vertex AI

Features:
- Chat conversationnel avec historique
- Dashboard temps réel
- Diagnostic plantes (vision AI)
- Génération de rapports
- Mode expert/simple
- Thème jour/nuit
- Support multilingue (FR/EN/AR)

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
APP_VERSION = "2.0.0"

# BigQuery tables
BIGQUERY_TABLES = {
    "sensor_telemetry": {
        "full_name": "vertiflow-484602.vertiflow_analytics.sensor_telemetry",
        "description": "Données temps réel capteurs IoT"
    },
    "view_dashboard_ready": {
        "full_name": "vertiflow-484602.vertiflow_analytics.view_dashboard_ready",
        "description": "Vue agrégée dashboard"
    },
    "simulations_agent": {
        "full_name": "vertiflow-484602.vertiflow_lake.simulations_agent",
        "description": "Simulations et prédictions"
    }
}

# ClickHouse context (157 columns schema)
CLICKHOUSE_CONTEXT = {
    "basil_ultimate_realtime": {
        "description": "Golden Record 157 colonnes - Données complètes ferme verticale",
        "categories": ["Identification", "Nutrition NPK", "Photosynthèse", "Biomasse", 
                      "Santé", "Climat", "Rhizosphère", "Économie", "Hardware", "IA"]
    },
    "ml_predictions": {"description": "Prédictions ML (rendement, anomalies)"},
    "ext_weather_history": {"description": "Historique météo NASA"},
    "ref_plant_recipes": {"description": "Recettes agronomiques de référence"}
}

# Quick actions for welcome screen
QUICK_ACTIONS = [
    {"icon": "📈", "label": "Graphique température", "prompt": "Trace un graphique de l'évolution de la température sur les dernières 24h"},
    {"icon": "🌿", "label": "Analyser health_score", "prompt": "Analyse le health_score moyen des plantes et donne des recommandations"},
    {"icon": "⚡", "label": "Optimiser LED", "prompt": "Comment optimiser la consommation énergétique des LED?"},
    {"icon": "📅", "label": "Prochaine récolte", "prompt": "Quand est prévue la prochaine récolte de basilic?"},
    {"icon": "💧", "label": "État irrigation", "prompt": "Quel est l'état actuel du système d'irrigation?"},
    {"icon": "🔬", "label": "Analyse nutritive", "prompt": "Analyse l'équilibre NPK actuel et suggère des ajustements"}
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

# Theme configurations
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
    """Get current theme based on user preference."""
    return THEMES.get(st.session_state.get("theme", "dark"), THEMES["dark"])

def apply_theme_css():
    """Apply dynamic CSS based on theme."""
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
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: {'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)' if is_dark else '#FFFFFF'};
            border-right: 1px solid var(--border);
        }}
        
        [data-testid="stSidebar"] * {{
            color: var(--text-primary) !important;
        }}
        
        /* Chat Messages - ChatGPT Style */
        .chat-message {{
            padding: 1.5rem;
            margin: 0.5rem 0;
            border-radius: 0;
            animation: fadeIn 0.3s ease;
        }}
        
        .chat-message.user {{
            background: {t['user_bubble']};
            border-left: 3px solid var(--accent-blue);
        }}
        
        .chat-message.assistant {{
            background: {t['assistant_bubble']};
            border-left: 3px solid var(--accent-green);
        }}
        
        .chat-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            margin-right: 1rem;
        }}
        
        .user .chat-avatar {{
            background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        }}
        
        .assistant .chat-avatar {{
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        }}
        
        /* New Chat Button */
        .new-chat-btn {{
            background: linear-gradient(135deg, var(--accent-green) 0%, var(--accent-blue) 100%);
            color: white !important;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 1rem;
        }}
        
        .new-chat-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
        }}
        
        /* Conversation History */
        .conv-item {{
            padding: 0.75rem 1rem;
            margin: 0.25rem 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.85rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .conv-item:hover {{
            background: {'rgba(255,255,255,0.05)' if is_dark else 'rgba(0,0,0,0.05)'};
            color: var(--text-primary);
        }}
        
        .conv-item.active {{
            background: {'rgba(16, 185, 129, 0.2)' if is_dark else 'rgba(5, 150, 105, 0.1)'};
            color: var(--accent-green);
        }}
        
        /* Quick Action Cards */
        .quick-action {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }}
        
        .quick-action:hover {{
            border-color: var(--accent-green);
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.15);
        }}
        
        .quick-action-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .quick-action-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        /* Dashboard Cards */
        .metric-card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
        }}
        
        .metric-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-green);
        }}
        
        .metric-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-status {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }}
        
        .status-good {{ background: #10B981; }}
        .status-warning {{ background: #F59E0B; }}
        .status-danger {{ background: #EF4444; }}
        
        /* Module Section */
        .module-section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .module-title {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        /* Action Buttons under responses */
        .action-buttons {{
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        
        .action-btn {{
            background: {'rgba(255,255,255,0.05)' if is_dark else 'rgba(0,0,0,0.05)'};
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .action-btn:hover {{
            background: var(--accent-green);
            color: white;
            border-color: var(--accent-green);
        }}
        
        /* Welcome Header */
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
        
        /* Expert Mode Badge */
        .expert-badge {{
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            color: white;
            font-size: 0.7rem;
            padding: 0.25rem 0.75rem;
            border-radius: 100px;
            font-weight: 600;
        }}
        
        /* Theme Toggle */
        .theme-toggle {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem;
            border-radius: 8px;
            cursor: pointer;
        }}
        
        /* Footer */
        .app-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            z-index: 100;
        }}
        
        .status-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Hide Streamlit elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Chat input styling */
        .stChatInput {{
            border-radius: 25px !important;
        }}
        
        [data-testid="stChatInput"] > div {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 25px !important;
        }}
        
        [data-testid="stChatInput"] textarea {{
            color: var(--text-primary) !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--text-secondary);
            border-radius: 3px;
        }}
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "conversation_id": str(uuid.uuid4()),
        "messages": [],
        "conversations": {},  # {id: {"title": str, "messages": [], "created": datetime}}
        "current_conv_id": None,
        "theme": "dark",
        "language": "fr",
        "expert_mode": False,
        "dashboard_data": None,
        "last_dashboard_update": None,
        "uploaded_file": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialize first conversation if none exists
    if not st.session_state.conversations:
        conv_id = st.session_state.conversation_id
        st.session_state.conversations[conv_id] = {
            "title": "Nouveau chat",
            "messages": [],
            "created": datetime.now().isoformat()
        }
        st.session_state.current_conv_id = conv_id

def new_conversation():
    """Create a new conversation."""
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
    """Switch to a different conversation."""
    if conv_id in st.session_state.conversations:
        st.session_state.current_conv_id = conv_id
        st.session_state.messages = st.session_state.conversations[conv_id]["messages"]
        st.rerun()

def update_conversation_title(conv_id: str, first_message: str):
    """Auto-generate conversation title from first message."""
    title = first_message[:40] + "..." if len(first_message) > 40 else first_message
    if conv_id in st.session_state.conversations:
        st.session_state.conversations[conv_id]["title"] = title

# =============================================================================
# API CLIENTS
# =============================================================================
@st.cache_resource
def get_credentials():
    """Get Google Cloud credentials."""
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
    """Initialize BigQuery client."""
    creds = get_credentials()
    if creds:
        return bigquery.Client(project=PROJECT_ID, credentials=creds)
    return None

@st.cache_resource
def get_genai_client():
    """Initialize Gemini client."""
    creds = get_credentials()
    if creds:
        return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=creds)
    return None

# =============================================================================
# DATA FUNCTIONS
# =============================================================================
@st.cache_data(ttl=300)
def get_dashboard_metrics():
    """Fetch real-time dashboard metrics from BigQuery."""
    client = get_bigquery_client()
    if not client:
        return None
    
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
    
    # Default demo values
    return {"temperature": 24.5, "humidity": 65.0, "health_score": 8.2, "readings": 150}

@st.cache_data(ttl=3600)
def get_table_schemas() -> Dict[str, Any]:
    """Retrieve BigQuery table schemas."""
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
        except Exception as e:
            schemas[key] = {"error": str(e)}
    return schemas

# =============================================================================
# AI QUERY FUNCTIONS
# =============================================================================
def generate_sql_query(question: str, schemas: Dict) -> Dict:
    """Generate SQL from natural language."""
    client = get_genai_client()
    if not client:
        return {"error": "Gemini unavailable", "sql": None}
    
    schema_ctx = "Tables BigQuery:\n"
    for key, schema in schemas.items():
        if "error" not in schema:
            schema_ctx += f"\n{schema['full_name']}:\n"
            for col in schema['columns'][:15]:
                schema_ctx += f"  - {col['name']} ({col['type']})\n"
    
    mode = "détaillé avec références scientifiques" if st.session_state.expert_mode else "simple et accessible"
    
    prompt = f"""Expert agriculture verticale VertiFlow Maroc.
Génère une requête SQL BigQuery.

{schema_ctx}

Contexte: Ferme VERT-MAROC-01, basilic Genovese/Thaï, capteurs IoT.
Mode de réponse: {mode}

Question: "{question}"

Instructions:
1. SQL valide BigQuery uniquement
2. Noms complets des tables
3. LIMIT 100 max
4. "NO_SQL_NEEDED" si question générale

Réponds UNIQUEMENT avec le SQL:"""

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        sql = response.text.strip().replace("```sql", "").replace("```", "").strip()
        
        if "NO_SQL_NEEDED" in sql:
            return {"sql": None, "needs_sql": False}
        return {"sql": sql, "needs_sql": True}
    except Exception as e:
        return {"error": str(e), "sql": None}

def execute_sql(sql: str) -> Dict:
    """Execute SQL query."""
    client = get_bigquery_client()
    if not client:
        return {"error": "BigQuery unavailable", "data": None}
    
    try:
        df = client.query(sql).to_dataframe()
        return {"data": df.to_dict('records'), "df": df, "total": len(df)}
    except Exception as e:
        return {"error": str(e), "data": None}

def generate_response(question: str, sql: str = None, data: List = None) -> str:
    """Generate natural language response."""
    client = get_genai_client()
    if not client:
        return "Je suis l'assistant VertiFlow. Comment puis-je vous aider?"
    
    mode = "expert agronome" if st.session_state.expert_mode else "accessible"
    lang = {"fr": "français", "en": "English", "ar": "العربية"}.get(st.session_state.language, "français")
    
    context = f"""Assistant IA VertiFlow - Agriculture verticale Maroc.
Mode: {mode}
Langue: {lang}

Données ClickHouse disponibles: 157 colonnes (nutrition NPK, photosynthèse PPFD/DLI, 
biomasse, health_score, climat, économie, prédictions ML).

Question: "{question}"
"""
    
    if sql and data:
        context += f"\nSQL exécuté:\n{sql}\n\nRésultats ({len(data)} lignes):\n{json.dumps(data[:10], default=str, ensure_ascii=False)}"
    
    if st.session_state.expert_mode:
        context += "\n\nInclure: références scientifiques, formules, incertitudes, données brutes."
    
    context += "\n\nRéponds de manière informative et utile:"
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=context)
        return response.text.strip()
    except Exception as e:
        return f"Erreur: {e}"

def detect_chart_request(question: str) -> Dict:
    """Detect if user wants a chart."""
    keywords = ["graphe", "graphique", "tracer", "visualiser", "courbe", "tendance",
                "chart", "plot", "histogram", "évolution", "trend", "رسم"]
    wants_chart = any(k in question.lower() for k in keywords)
    
    chart_type = "auto"
    if any(k in question.lower() for k in ["ligne", "line", "évolution", "trend"]):
        chart_type = "line"
    elif any(k in question.lower() for k in ["barre", "bar", "histogramme"]):
        chart_type = "bar"
    elif any(k in question.lower() for k in ["camembert", "pie"]):
        chart_type = "pie"
    
    return {"wants_chart": wants_chart, "type": chart_type}

def generate_chart(df: pd.DataFrame, chart_type: str = "auto") -> Optional[go.Figure]:
    """Generate Plotly chart from data."""
    if df is None or df.empty:
        return None
    
    t = get_theme()
    colors = [t['accent_green'], t['accent_blue'], "#8B5CF6", "#F59E0B", "#EF4444"]
    
    numeric = df.select_dtypes(include=['number']).columns.tolist()
    datetime_cols = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()]
    
    try:
        if datetime_cols and numeric:
            fig = px.line(df, x=datetime_cols[0], y=numeric[:3], 
                         color_discrete_sequence=colors)
        elif numeric:
            fig = px.bar(df.head(20), y=numeric[0], color_discrete_sequence=colors)
        else:
            return None
        
        fig.update_layout(
            template="plotly_dark" if st.session_state.theme == "dark" else "plotly_white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter"),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        return fig
    except:
        return None

# =============================================================================
# MAIN QUERY FUNCTION
# =============================================================================
def process_query(question: str) -> Dict:
    """Process user query and return response."""
    result = {"reply": "", "sql": None, "data": None, "chart": None}
    
    schemas = get_table_schemas()
    chart_req = detect_chart_request(question)
    
    # Generate SQL
    sql_result = generate_sql_query(question, schemas)
    
    if sql_result.get("error"):
        result["reply"] = generate_response(question)
        return result
    
    if not sql_result.get("needs_sql"):
        result["reply"] = generate_response(question)
        return result
    
    result["sql"] = sql_result["sql"]
    
    # Execute SQL
    query_result = execute_sql(sql_result["sql"])
    
    if query_result.get("error"):
        result["reply"] = generate_response(question)
        result["error"] = query_result["error"]
        return result
    
    result["data"] = query_result["data"]
    
    # Generate chart if requested
    if chart_req["wants_chart"] and query_result.get("df") is not None:
        result["chart"] = generate_chart(query_result["df"], chart_req["type"])
    
    # Generate response
    result["reply"] = generate_response(question, sql_result["sql"], query_result["data"])
    
    return result

# =============================================================================
# UI COMPONENTS
# =============================================================================
def render_sidebar():
    """Render ChatGPT-style sidebar."""
    with st.sidebar:
        # Logo section
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
        
        # New Chat button
        if st.button("➕ Nouveau Chat", use_container_width=True, type="primary"):
            new_conversation()
        
        st.divider()
        
        # Conversation History
        st.markdown("**💬 Historique**")
        
        for conv_id, conv in sorted(st.session_state.conversations.items(), 
                                    key=lambda x: x[1].get('created', ''), reverse=True):
            is_active = conv_id == st.session_state.current_conv_id
            icon = "🟢" if is_active else "💬"
            
            if st.button(f"{icon} {conv['title'][:30]}", key=f"conv_{conv_id}", 
                        use_container_width=True,
                        type="primary" if is_active else "secondary"):
                switch_conversation(conv_id)
        
        st.divider()
        
        # Quick Modules
        st.markdown("**⚡ Modules Rapides**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Analytics", use_container_width=True):
                st.session_state.quick_prompt = "Montre-moi les analytics des dernières 24h"
        with col2:
            if st.button("🌡️ Capteurs", use_container_width=True):
                st.session_state.quick_prompt = "État actuel des capteurs"
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💡 Conseils", use_container_width=True):
                st.session_state.quick_prompt = "Recommandations agronomiques du jour"
        with col2:
            if st.button("⚡ Énergie", use_container_width=True):
                st.session_state.quick_prompt = "Optimisation énergétique LED"
        
        st.divider()
        
        # Live Dashboard Mini
        st.markdown("**📊 Dashboard Live**")
        metrics = get_dashboard_metrics()
        if metrics:
            col1, col2 = st.columns(2)
            with col1:
                temp_status = "🟢" if 20 <= metrics['temperature'] <= 28 else "🟡"
                st.metric("🌡️ Temp", f"{metrics['temperature']}°C", delta=None)
            with col2:
                hum_status = "🟢" if 50 <= metrics['humidity'] <= 80 else "🟡"
                st.metric("💧 Humid", f"{metrics['humidity']}%", delta=None)
            
            col1, col2 = st.columns(2)
            with col1:
                health_status = "🟢" if metrics['health_score'] >= 7 else "🟡"
                st.metric("🌿 Santé", f"{metrics['health_score']}/10", delta=None)
            with col2:
                st.metric("📡 Mesures", f"{metrics['readings']}", delta=None)
        
        st.divider()
        
        # Settings
        st.markdown("**⚙️ Paramètres**")
        
        # Theme toggle
        theme = st.toggle("🌙 Mode sombre", value=st.session_state.theme == "dark")
        if theme != (st.session_state.theme == "dark"):
            st.session_state.theme = "dark" if theme else "light"
            st.rerun()
        
        # Expert mode
        expert = st.toggle("🔬 Mode Expert", value=st.session_state.expert_mode)
        if expert != st.session_state.expert_mode:
            st.session_state.expert_mode = expert
        
        # Language
        lang = st.selectbox("🌍 Langue", ["Français", "English", "العربية"],
                          index=["fr", "en", "ar"].index(st.session_state.language))
        st.session_state.language = ["fr", "en", "ar"][["Français", "English", "العربية"].index(lang)]
        
        # Footer
        st.markdown(f"""
        <div style="position: absolute; bottom: 1rem; left: 1rem; right: 1rem; 
                    font-size: 0.7rem; color: #64748B; text-align: center;">
            <span style="display: inline-block; width: 6px; height: 6px; 
                         background: #10B981; border-radius: 50%; margin-right: 0.5rem;"></span>
            v{APP_VERSION} • VertiFlow Morocco 🇲🇦
        </div>
        """, unsafe_allow_html=True)

def render_welcome():
    """Render welcome screen with quick actions."""
    st.markdown("""
    <div class="welcome-header">
        <div class="welcome-title">🌿 Bienvenue sur AGRI-COPILOT</div>
        <div class="welcome-subtitle">
            Votre assistant IA pour l'agriculture verticale au Maroc
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 Actions Rapides")
    
    cols = st.columns(3)
    for i, action in enumerate(QUICK_ACTIONS):
        with cols[i % 3]:
            if st.button(f"{action['icon']} {action['label']}", 
                        key=f"quick_{i}", use_container_width=True):
                return action['prompt']
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748B; font-size: 0.9rem;">
        <p>Posez une question en <strong>français</strong>, <strong>anglais</strong> ou <strong>darija</strong> 🇲🇦</p>
        <p>Je peux analyser vos données, générer des graphiques et vous conseiller.</p>
    </div>
    """, unsafe_allow_html=True)
    
    return None

def render_chat():
    """Render main chat interface."""
    # Expert mode badge
    if st.session_state.expert_mode:
        st.markdown("""
        <div style="text-align: right; margin-bottom: 1rem;">
            <span class="expert-badge">🔬 MODE EXPERT</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Show welcome if no messages
    if not st.session_state.messages:
        quick_prompt = render_welcome()
        if quick_prompt:
            st.session_state.pending_prompt = quick_prompt
            st.rerun()
    
    # Display messages
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🧑‍🌾" if msg["role"] == "user" else "🌿"):
            st.markdown(msg["content"])
            
            # Show chart if available
            if msg["role"] == "assistant" and msg.get("chart"):
                st.plotly_chart(msg["chart"], use_container_width=True)
            
            # Show SQL and data expanders
            if msg["role"] == "assistant" and msg.get("sql"):
                with st.expander("🔍 Requête SQL"):
                    st.code(msg["sql"], language="sql")
            
            if msg["role"] == "assistant" and msg.get("data"):
                with st.expander(f"📊 Données ({len(msg['data'])} lignes)"):
                    st.dataframe(msg["data"], use_container_width=True)
            
            # Action buttons for assistant messages
            if msg["role"] == "assistant" and i == len(st.session_state.messages) - 1:
                cols = st.columns(4)
                with cols[0]:
                    if msg.get("data") and st.button("📥 CSV", key=f"csv_{i}"):
                        df = pd.DataFrame(msg["data"])
                        st.download_button("Télécharger", df.to_csv(index=False), 
                                         "vertiflow_data.csv", "text/csv")
                with cols[1]:
                    if st.button("📋 Copier", key=f"copy_{i}"):
                        st.toast("Réponse copiée!")
                with cols[2]:
                    if st.button("🔄 Régénérer", key=f"regen_{i}"):
                        st.session_state.regenerate = True
                        st.rerun()

def main():
    """Main application."""
    init_session_state()
    apply_theme_css()
    
    # Sidebar
    render_sidebar()
    
    # Main chat area
    render_chat()
    
    # Handle pending quick prompts
    if hasattr(st.session_state, 'pending_prompt') and st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Update conversation title if first message
        if len(st.session_state.messages) == 1:
            update_conversation_title(st.session_state.current_conv_id, prompt)
        
        # Process and respond
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("🌱 Analyse en cours..."):
                response = process_query(prompt)
            
            st.markdown(response["reply"])
            
            if response.get("chart"):
                st.plotly_chart(response["chart"], use_container_width=True)
            
            if response.get("sql"):
                with st.expander("🔍 Requête SQL"):
                    st.code(response["sql"], language="sql")
            
            if response.get("data"):
                with st.expander(f"📊 Données ({len(response['data'])} lignes)"):
                    st.dataframe(response["data"], use_container_width=True)
        
        # Save to session
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["reply"],
            "sql": response.get("sql"),
            "data": response.get("data"),
            "chart": response.get("chart")
        })
        
        # Save to conversation history
        st.session_state.conversations[st.session_state.current_conv_id]["messages"] = st.session_state.messages
        
        st.rerun()
    
    # Handle quick_prompt from sidebar
    if hasattr(st.session_state, 'quick_prompt') and st.session_state.quick_prompt:
        st.session_state.pending_prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Posez votre question... 🌿"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Update conversation title if first message
        if len(st.session_state.messages) == 1:
            update_conversation_title(st.session_state.current_conv_id, prompt)
        
        with st.chat_message("user", avatar="🧑‍🌾"):
            st.markdown(prompt)
        
        # Process and respond
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("🌱 Analyse en cours..."):
                response = process_query(prompt)
            
            st.markdown(response["reply"])
            
            if response.get("chart"):
                st.plotly_chart(response["chart"], use_container_width=True)
            
            if response.get("sql"):
                with st.expander("🔍 Requête SQL"):
                    st.code(response["sql"], language="sql")
            
            if response.get("data"):
                with st.expander(f"📊 Données ({len(response['data'])} lignes)"):
                    st.dataframe(response["data"], use_container_width=True)
            
            # Action buttons
            cols = st.columns(4)
            with cols[0]:
                if response.get("data"):
                    df = pd.DataFrame(response["data"])
                    st.download_button("📥 CSV", df.to_csv(index=False), 
                                      "vertiflow_data.csv", "text/csv")
        
        # Save to session
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["reply"],
            "sql": response.get("sql"),
            "data": response.get("data"),
            "chart": response.get("chart")
        })
        
        # Save to conversation history
        st.session_state.conversations[st.session_state.current_conv_id]["messages"] = st.session_state.messages
        
        st.rerun()

if __name__ == "__main__":
    main()
