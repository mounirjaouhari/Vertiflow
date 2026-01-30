#!/usr/bin/env python3
# ============================================================================
# VERTIFLOW - Script de Vérification de Santé du Système
# ============================================================================
"""
Ce script vérifie la santé de tous les composants de la plateforme VertiFlow:
- Kafka (broker, topics)
- ClickHouse (connexion, tables)
- MongoDB (connexion, collections)
- MQTT (broker)
- NiFi (API)
"""

import os
import sys
import socket
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class HealthChecker:
    """Vérificateur de santé des services."""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.utcnow()

    def check_port(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """Vérifie si un port est accessible."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def check_kafka(self) -> Dict[str, Any]:
        """Vérifie la santé de Kafka."""
        host = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(":")[0]
        port = int(os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(":")[1])

        result = {
            "service": "kafka",
            "host": f"{host}:{port}",
            "status": "unknown",
            "details": {}
        }

        if self.check_port(host, port):
            result["status"] = "healthy"
            result["details"]["port_open"] = True

            # Vérifier avec kafka-python si disponible
            try:
                from kafka import KafkaAdminClient
                admin = KafkaAdminClient(
                    bootstrap_servers=f"{host}:{port}",
                    request_timeout_ms=5000
                )
                topics = admin.list_topics()
                result["details"]["topics_count"] = len(topics)
                result["details"]["topics"] = topics[:10]  # Premier 10
                admin.close()
            except ImportError:
                result["details"]["note"] = "kafka-python not installed"
            except Exception as e:
                result["details"]["error"] = str(e)
        else:
            result["status"] = "unhealthy"
            result["details"]["port_open"] = False

        return result

    def check_clickhouse(self) -> Dict[str, Any]:
        """Vérifie la santé de ClickHouse."""
        host = os.getenv("CLICKHOUSE_HOST", "localhost")
        http_port = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
        tcp_port = int(os.getenv("CLICKHOUSE_PORT", "9000"))

        result = {
            "service": "clickhouse",
            "host": host,
            "status": "unknown",
            "details": {}
        }

        result["details"]["http_port"] = self.check_port(host, http_port)
        result["details"]["tcp_port"] = self.check_port(host, tcp_port)

        if result["details"]["http_port"]:
            try:
                import requests
                response = requests.get(
                    f"http://{host}:{http_port}/?query=SELECT%201",
                    timeout=5
                )
                if response.status_code == 200:
                    result["status"] = "healthy"

                    # Vérifier les tables
                    tables_response = requests.get(
                        f"http://{host}:{http_port}/?query=SHOW%20TABLES%20FROM%20vertiflow",
                        timeout=5
                    )
                    if tables_response.status_code == 200:
                        tables = tables_response.text.strip().split('\n')
                        result["details"]["tables"] = tables
                else:
                    result["status"] = "degraded"
            except ImportError:
                result["details"]["note"] = "requests not installed"
            except Exception as e:
                result["status"] = "unhealthy"
                result["details"]["error"] = str(e)
        else:
            result["status"] = "unhealthy"

        return result

    def check_mongodb(self) -> Dict[str, Any]:
        """Vérifie la santé de MongoDB."""
        host = os.getenv("MONGODB_HOST", "localhost")
        port = int(os.getenv("MONGODB_PORT", "27017"))

        result = {
            "service": "mongodb",
            "host": f"{host}:{port}",
            "status": "unknown",
            "details": {}
        }

        if self.check_port(host, port):
            result["details"]["port_open"] = True

            try:
                from pymongo import MongoClient
                client = MongoClient(host, port, serverSelectionTimeoutMS=5000)
                # Test de ping
                client.admin.command('ping')
                result["status"] = "healthy"

                # Lister les bases de données
                dbs = client.list_database_names()
                result["details"]["databases"] = dbs

                # Collections dans vertiflow
                if "vertiflow" in dbs:
                    collections = client.vertiflow.list_collection_names()
                    result["details"]["collections"] = collections

                client.close()
            except ImportError:
                result["details"]["note"] = "pymongo not installed"
            except Exception as e:
                result["status"] = "unhealthy"
                result["details"]["error"] = str(e)
        else:
            result["status"] = "unhealthy"
            result["details"]["port_open"] = False

        return result

    def check_mqtt(self) -> Dict[str, Any]:
        """Vérifie la santé du broker MQTT."""
        host = os.getenv("MQTT_HOST", "localhost")
        port = int(os.getenv("MQTT_PORT", "1883"))
        tls_port = int(os.getenv("MQTT_TLS_PORT", "8883"))

        result = {
            "service": "mqtt",
            "host": f"{host}:{port}",
            "status": "unknown",
            "details": {}
        }

        result["details"]["port_1883"] = self.check_port(host, port)
        result["details"]["port_8883"] = self.check_port(host, tls_port)

        if result["details"]["port_1883"] or result["details"]["port_8883"]:
            result["status"] = "healthy"
        else:
            result["status"] = "unhealthy"

        return result

    def check_nifi(self) -> Dict[str, Any]:
        """Vérifie la santé de NiFi."""
        host = os.getenv("NIFI_HOST", "localhost")
        port = int(os.getenv("NIFI_PORT", "8443"))

        result = {
            "service": "nifi",
            "host": f"{host}:{port}",
            "status": "unknown",
            "details": {}
        }

        if self.check_port(host, port):
            result["details"]["port_open"] = True

            try:
                import requests
                import urllib3
                urllib3.disable_warnings()

                response = requests.get(
                    f"https://{host}:{port}/nifi-api/system-diagnostics",
                    verify=False,
                    timeout=10
                )
                if response.status_code in [200, 401, 403]:
                    result["status"] = "healthy"
                    result["details"]["api_accessible"] = True
                else:
                    result["status"] = "degraded"
            except ImportError:
                result["details"]["note"] = "requests not installed"
            except Exception as e:
                result["status"] = "degraded"
                result["details"]["error"] = str(e)
        else:
            result["status"] = "unhealthy"
            result["details"]["port_open"] = False

        return result

    def check_all(self) -> Dict[str, Any]:
        """Exécute toutes les vérifications."""
        logger.info("Starting health checks...")

        checks = [
            ("kafka", self.check_kafka),
            ("clickhouse", self.check_clickhouse),
            ("mongodb", self.check_mongodb),
            ("mqtt", self.check_mqtt),
            ("nifi", self.check_nifi),
        ]

        for name, check_func in checks:
            logger.info(f"Checking {name}...")
            self.results[name] = check_func()

        # Résumé global
        end_time = datetime.utcnow()
        healthy_count = sum(1 for r in self.results.values() if r["status"] == "healthy")
        total_count = len(self.results)

        summary = {
            "timestamp": end_time.isoformat(),
            "duration_ms": (end_time - self.start_time).total_seconds() * 1000,
            "overall_status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": self.results
        }

        return summary


def print_results(summary: Dict[str, Any]):
    """Affiche les résultats de manière lisible."""
    print("\n" + "=" * 60)
    print("VERTIFLOW - HEALTH CHECK REPORT")
    print("=" * 60)
    print(f"Timestamp: {summary['timestamp']}")
    print(f"Duration: {summary['duration_ms']:.0f}ms")
    print(f"Overall Status: {summary['overall_status'].upper()}")
    print(f"Services: {summary['healthy_services']}/{summary['total_services']} healthy")
    print("-" * 60)

    for name, result in summary["services"].items():
        status = result["status"]
        icon = "✓" if status == "healthy" else "✗" if status == "unhealthy" else "!"
        print(f"{icon} {name.upper():12} [{status:10}] - {result['host']}")

    print("=" * 60 + "\n")


def main():
    """Point d'entrée principal."""
    checker = HealthChecker()
    summary = checker.check_all()
    print_results(summary)

    # Écrire le résultat en JSON
    output_file = "health_check_result.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Results saved to {output_file}")

    # Exit code basé sur le statut global
    if summary["overall_status"] != "healthy":
        sys.exit(1)


if __name__ == "__main__":
    main()
