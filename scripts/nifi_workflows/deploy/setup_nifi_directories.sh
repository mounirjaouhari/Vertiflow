#!/bin/bash
# ============================================================================
# PROJET VERTIFLOW - Setup NiFi Directories
# ============================================================================
# Ce script crée les dossiers nécessaires dans le conteneur NiFi
# pour que les processeurs GetFile/PutFile fonctionnent.
#
# Usage: bash scripts/nifi_workflows/deploy/setup_nifi_directories.sh
# ============================================================================

echo "=========================================="
echo "CRÉATION DES DOSSIERS NIFI"
echo "=========================================="

# Créer les dossiers dans le conteneur NiFi
docker exec -u root nifi bash -c "
    mkdir -p /opt/nifi/nifi-current/exchange/input
    mkdir -p /opt/nifi/nifi-current/exchange/output
    mkdir -p /opt/nifi/nifi-current/exchange/datasets
    mkdir -p /opt/nifi/nifi-current/exchange/lab_data
    mkdir -p /opt/nifi/nifi-current/exchange/recipes

    # Permissions
    chown -R nifi:nifi /opt/nifi/nifi-current/exchange
    chmod -R 755 /opt/nifi/nifi-current/exchange

    echo 'Dossiers créés:'
    ls -la /opt/nifi/nifi-current/exchange/
"

echo ""
echo "=========================================="
echo "VÉRIFICATION DU DRIVER JDBC"
echo "=========================================="

docker exec nifi bash -c "
    if [ -f /opt/nifi/nifi-current/drivers/clickhouse-jdbc-0.6.0-all.jar ]; then
        echo '[OK] Driver ClickHouse JDBC trouvé'
        ls -la /opt/nifi/nifi-current/drivers/clickhouse-jdbc-0.6.0-all.jar
    else
        echo '[MISSING] Driver ClickHouse JDBC non trouvé!'
        echo 'Contenu du dossier drivers:'
        ls -la /opt/nifi/nifi-current/drivers/ 2>/dev/null || echo 'Dossier drivers inexistant'
    fi
"

echo ""
echo "=========================================="
echo "VÉRIFICATION CONNECTIVITÉ RÉSEAU"
echo "=========================================="

# Test connexion Kafka
docker exec nifi bash -c "
    echo 'Test Kafka (kafka:29092)...'
    timeout 3 bash -c '</dev/tcp/kafka/29092' 2>/dev/null && echo '[OK] Kafka accessible' || echo '[FAIL] Kafka non accessible'
"

# Test connexion MongoDB
docker exec nifi bash -c "
    echo 'Test MongoDB (mongodb:27017)...'
    timeout 3 bash -c '</dev/tcp/mongodb/27017' 2>/dev/null && echo '[OK] MongoDB accessible' || echo '[FAIL] MongoDB non accessible'
"

# Test connexion ClickHouse
docker exec nifi bash -c "
    echo 'Test ClickHouse (clickhouse:8123)...'
    timeout 3 bash -c '</dev/tcp/clickhouse/8123' 2>/dev/null && echo '[OK] ClickHouse accessible' || echo '[FAIL] ClickHouse non accessible'
"

# Test connexion MQTT
docker exec nifi bash -c "
    echo 'Test MQTT (mosquitto:1883)...'
    timeout 3 bash -c '</dev/tcp/mosquitto/1883' 2>/dev/null && echo '[OK] MQTT accessible' || echo '[FAIL] MQTT non accessible'
"

echo ""
echo "=========================================="
echo "TERMINÉ"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "  1. git pull origin main"
echo "  2. python scripts/nifi_workflows/deploy/fix_nifi_processors.py"
echo "  3. Vérifier dans NiFi UI les processeurs encore invalides"
echo ""
