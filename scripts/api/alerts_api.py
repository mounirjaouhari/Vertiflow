#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VertiFlow Alerts REST API - For Grafana Infinity Datasource
"""
import os
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from pymongo import MongoClient

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "vertiflow_ops")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "alerts")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_mongo_client():
    """Create MongoDB client"""
    logger.info(f"Connecting to MongoDB: {MONGO_URI}")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    logger.info("MongoDB connection successful")
    return client

def get_collection():
    """Get the alerts collection"""
    client = get_mongo_client()
    db = client[DB_NAME]
    return db[COLLECTION_NAME]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        collection = get_collection()
        count = collection.count_documents({})
        return jsonify({
            "status": "healthy",
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "document_count": count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/alerts/count', methods=['GET'])
def get_alert_count():
    """Get total alert count"""
    try:
        collection = get_collection()
        count = collection.count_documents({})
        return jsonify({"count": count})
    except Exception as e:
        logger.error(f"Error getting count: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/count-by-severity', methods=['GET'])
def get_count_by_severity():
    """Get alert count grouped by severity"""
    try:
        resolved_param = request.args.get('resolved', None)
        
        collection = get_collection()
        match_filter = {}
        
        if resolved_param is not None:
            resolved = resolved_param.lower() == 'true'
            match_filter['resolved'] = resolved
        
        pipeline = [
            {"$match": match_filter} if match_filter else {"$match": {}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
        ]
        
        result = list(collection.aggregate(pipeline))
        
        # Convert to dict format
        data = {}
        for item in result:
            if item["_id"]:
                data[item["_id"]] = item["count"]
        
        # Ensure all severity levels are present
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if sev not in data:
                data[sev] = 0
        
        return jsonify({
            "data": data,
            "query": {"resolved": resolved_param}
        })
    except Exception as e:
        logger.error(f"Error getting count by severity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/stats', methods=['GET'])
def get_stats():
    """Get comprehensive alert statistics"""
    try:
        collection = get_collection()
        
        # Total counts
        total = collection.count_documents({})
        active = collection.count_documents({"resolved": False})
        resolved = collection.count_documents({"resolved": True})
        
        # By severity
        severity_pipeline = [
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
        ]
        severity_result = list(collection.aggregate(severity_pipeline))
        by_severity = {item["_id"]: item["count"] for item in severity_result if item["_id"]}
        
        # By type
        type_pipeline = [
            {"$group": {"_id": "$metadata.alert_type", "count": {"$sum": 1}}}
        ]
        type_result = list(collection.aggregate(type_pipeline))
        by_type = {item["_id"]: item["count"] for item in type_result if item["_id"]}
        
        # Resolution rate
        resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0
        
        return jsonify({
            "summary": {
                "total": total,
                "active": active,
                "resolved": resolved,
                "resolution_rate": resolution_rate
            },
            "by_severity": by_severity,
            "by_type": by_type
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/active', methods=['GET'])
def get_active_alerts():
    """Get active (unresolved) alerts"""
    try:
        limit = int(request.args.get('limit', 100))
        collection = get_collection()
        
        cursor = collection.find(
            {"resolved": False},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        alerts = list(cursor)
        total = collection.count_documents({"resolved": False})
        
        # Convert datetime objects to strings
        for alert in alerts:
            if 'timestamp' in alert and isinstance(alert['timestamp'], datetime):
                alert['timestamp'] = alert['timestamp'].isoformat()
        
        return jsonify({
            "data": alerts,
            "pagination": {
                "limit": limit,
                "total": total,
                "returned": len(alerts)
            }
        })
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/all', methods=['GET'])
def get_all_alerts():
    """Get all alerts with pagination"""
    try:
        limit = int(request.args.get('limit', 100))
        skip = int(request.args.get('skip', 0))
        
        collection = get_collection()
        
        cursor = collection.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit)
        
        alerts = list(cursor)
        total = collection.count_documents({})
        
        # Convert datetime objects to strings
        for alert in alerts:
            if 'timestamp' in alert and isinstance(alert['timestamp'], datetime):
                alert['timestamp'] = alert['timestamp'].isoformat()
        
        return jsonify({
            "data": alerts,
            "pagination": {
                "limit": limit,
                "skip": skip,
                "total": total,
                "returned": len(alerts)
            }
        })
    except Exception as e:
        logger.error(f"Error getting all alerts: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting Alerts API on 0.0.0.0:5000")
    logger.info(f"MongoDB: {DB_NAME}.{COLLECTION_NAME}")
    app.run(host='0.0.0.0', port=5000, debug=False)
