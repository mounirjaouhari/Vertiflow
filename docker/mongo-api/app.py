import subprocess
import re
import json
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import json_util
from datetime import datetime, timedelta

app = Flask(__name__)

# MongoDB Connection
MONGO_URI = "mongodb://mongodb:27017"
DB_NAME = "vertiflow_ops"

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def parse_json(data):
    """Convert MongoDB BSON to JSON-serializable format"""
    return json.loads(json_util.dumps(data))

# ============================================================================
# REST API ENDPOINTS FOR GRAFANA INFINITY
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "mongo-api"})

# --- ALERTS COUNT ENDPOINTS ---
@app.route('/api/alerts/count', methods=['GET'])
def alerts_count_total():
    """Total count of all alerts"""
    db = get_db()
    count = db.alerts.count_documents({})
    return jsonify([{"metric": "total", "count": count}])

@app.route('/api/alerts/count/<severity>', methods=['GET'])
def alerts_count_by_severity(severity):
    """Count alerts by severity (CRITICAL, HIGH, MEDIUM, LOW)"""
    db = get_db()
    resolved = request.args.get('resolved', 'false').lower() == 'true'
    count = db.alerts.count_documents({"severity": severity.upper(), "resolved": resolved})
    return jsonify([{"severity": severity.upper(), "count": count, "resolved": resolved}])

@app.route('/api/alerts/count/unresolved', methods=['GET'])
def alerts_count_unresolved():
    """Count of unresolved alerts"""
    db = get_db()
    count = db.alerts.count_documents({"resolved": False})
    return jsonify([{"metric": "unresolved", "count": count}])

# --- ALERTS GROUPING ENDPOINTS ---
@app.route('/api/alerts/by-severity', methods=['GET'])
def alerts_by_severity():
    """Group alerts by severity"""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
        {"$project": {"severity": "$_id", "count": 1, "_id": 0}}
    ]
    results = list(db.alerts.aggregate(pipeline))
    return jsonify(results)

@app.route('/api/alerts/by-type', methods=['GET'])
def alerts_by_type():
    """Group alerts by alert type"""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$metadata.alert_type", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$ne": None}}},
        {"$project": {"alert_type": "$_id", "count": 1, "_id": 0}}
    ]
    results = list(db.alerts.aggregate(pipeline))
    return jsonify(results)

@app.route('/api/alerts/by-module', methods=['GET'])
def alerts_by_module():
    """Group alerts by module_id"""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$module_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {"module": "$_id", "count": 1, "_id": 0}}
    ]
    results = list(db.alerts.aggregate(pipeline))
    return jsonify(results)

@app.route('/api/alerts/by-status', methods=['GET'])
def alerts_by_status():
    """Group alerts by resolution status"""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$resolved", "count": {"$sum": 1}}},
        {"$project": {"status": {"$cond": [{"$eq": ["$_id", True]}, "Résolu", "Non résolu"]}, "count": 1, "_id": 0}}
    ]
    results = list(db.alerts.aggregate(pipeline))
    return jsonify(results)

# --- ALERTS LIST ENDPOINTS ---
@app.route('/api/alerts/critical', methods=['GET'])
def alerts_critical():
    """List critical unresolved alerts"""
    db = get_db()
    limit = int(request.args.get('limit', 50))
    alerts = list(db.alerts.find(
        {"severity": "CRITICAL", "resolved": False},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit))
    return jsonify(parse_json(alerts))

@app.route('/api/alerts/high', methods=['GET'])
def alerts_high():
    """List high severity unresolved alerts"""
    db = get_db()
    limit = int(request.args.get('limit', 20))
    alerts = list(db.alerts.find(
        {"severity": "HIGH", "resolved": False},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit))
    return jsonify(parse_json(alerts))

@app.route('/api/alerts/recent', methods=['GET'])
def alerts_recent():
    """List recent alerts (last 100)"""
    db = get_db()
    limit = int(request.args.get('limit', 100))
    alerts = list(db.alerts.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return jsonify(parse_json(alerts))

@app.route('/api/alerts/parameters', methods=['GET'])
def alerts_parameters():
    """List parameter issue alerts"""
    db = get_db()
    limit = int(request.args.get('limit', 50))
    alerts = list(db.alerts.find(
        {"metadata.alert_type": "PARAMETER_ISSUE"},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit))
    return jsonify(parse_json(alerts))

# --- TIME SERIES ENDPOINTS ---
@app.route('/api/alerts/timeseries', methods=['GET'])
def alerts_timeseries():
    """Alerts count per hour for time series"""
    db = get_db()
    hours = int(request.args.get('hours', 168))  # Default to 7 days
    severity = request.args.get('severity', None)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    match_stage = {"timestamp": {"$gte": start_time}}
    if severity:
        match_stage["severity"] = severity.upper()
    
    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {
                "$dateToString": {"format": "%Y-%m-%dT%H:00:00Z", "date": "$timestamp"}
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {"time": "$_id", "value": "$count", "_id": 0}}
    ]
    results = list(db.alerts.aggregate(pipeline))
    return jsonify(results)

@app.route('/api/alerts/criticality-avg', methods=['GET'])
def alerts_criticality_avg():
    """Average criticality score per hour"""
    db = get_db()
    hours = int(request.args.get('hours', 168))  # Default to 7 days
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_time}}},
        {"$group": {
            "_id": {
                "$dateToString": {"format": "%Y-%m-%dT%H:00:00Z", "date": "$timestamp"}
            },
            "avg_score": {"$avg": "$metadata.criticality_score"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {"time": "$_id", "value": {"$round": ["$avg_score", 3]}, "_id": 0}}
    ]
    results = list(db.alerts.aggregate(pipeline))
    return jsonify(results)

# --- VARIABLE ENDPOINTS FOR DROPDOWNS ---
@app.route('/api/variables/severities', methods=['GET'])
def variables_severities():
    """Distinct severity values"""
    db = get_db()
    values = db.alerts.distinct("severity")
    return jsonify([{"__text": v, "__value": v} for v in sorted(values) if v])

@app.route('/api/variables/modules', methods=['GET'])
def variables_modules():
    """Distinct module_id values"""
    db = get_db()
    values = db.alerts.distinct("module_id")
    return jsonify([{"__text": v, "__value": v} for v in sorted(values) if v])

# ============================================================================
# LEGACY POST ENDPOINT (pour compatibilité)
# ============================================================================

def force_strict_json(raw_str):
    """
    Uses regex to wrap unquoted keys in double quotes.
    Example: { timestamp: ISODate(...) } -> { "timestamp": "ISODate(...)" }
    """
    quoted_keys = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*):', r'\1"\2"\3:', raw_str)
    quoted_vals = re.sub(r'(ISODate|ObjectId)\((.*?)\)', r'"\1(\2)"', quoted_keys)
    return quoted_vals

@app.route('/', methods=['POST'])
@app.route('/<dbname>', methods=['POST'])
def run_query(dbname=""):
    query = request.data.decode('utf-8').strip()
    print(f"--- EXECUTING ---", flush=True)
    print(f"Query: {query}", flush=True)
    
    try:
        process = subprocess.run(
            ['mongosh', f"mongodb://mongodb:27017/{dbname}", '--quiet', '--eval', query],
            capture_output=True, 
            text=True
        )
        output = process.stdout.strip()
        cleaned_output = force_strict_json(output)
        
        if process.returncode == 0:
            return cleaned_output, 200, {'Content-Type': 'application/json'}
        else:
            return f"Mongo Shell Error: {process.stderr}\n", 400
            
    except Exception as e:
        return f"System Error: {str(e)}\n", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
