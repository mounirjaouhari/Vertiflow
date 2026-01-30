#!/bin/bash
# ============================================================================
# VERTIFLOW - Script de génération des certificats TLS
# ============================================================================
# Ce script génère tous les certificats nécessaires pour sécuriser
# les communications entre les services de la plateforme.
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="${SCRIPT_DIR}/certs"
VALIDITY_DAYS=365
KEY_SIZE=4096

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Créer le répertoire des certificats
mkdir -p "${CERTS_DIR}"
cd "${CERTS_DIR}"

log_info "=== Génération des certificats TLS VertiFlow ==="

# ============================================================================
# 1. Certificate Authority (CA) Root
# ============================================================================
log_info "Génération de la CA Root..."

if [ ! -f ca.key ]; then
    openssl genrsa -out ca.key ${KEY_SIZE}
    openssl req -new -x509 -days ${VALIDITY_DAYS} -key ca.key -out ca.crt \
        -subj "/C=MA/ST=Casablanca/L=Casablanca/O=VertiFlow/OU=Infrastructure/CN=VertiFlow Root CA"
    log_info "CA Root générée: ca.key, ca.crt"
else
    log_warn "CA Root existe déjà, skip..."
fi

# ============================================================================
# 2. Certificats Kafka
# ============================================================================
log_info "Génération des certificats Kafka..."

# Kafka Broker
openssl genrsa -out kafka-broker.key ${KEY_SIZE}
openssl req -new -key kafka-broker.key -out kafka-broker.csr \
    -subj "/C=MA/ST=Casablanca/L=Casablanca/O=VertiFlow/OU=Kafka/CN=kafka"

cat > kafka-broker.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = kafka
DNS.2 = localhost
DNS.3 = kafka.vertiflow-network
IP.1 = 127.0.0.1
EOF

openssl x509 -req -in kafka-broker.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out kafka-broker.crt -days ${VALIDITY_DAYS} -extfile kafka-broker.ext

# Créer le keystore et truststore Kafka (format JKS)
log_info "Création des keystores Kafka..."
KEYSTORE_PASSWORD="vertiflow2025secure"

# Convertir en PKCS12 puis JKS
openssl pkcs12 -export -in kafka-broker.crt -inkey kafka-broker.key \
    -out kafka-broker.p12 -name kafka -CAfile ca.crt -caname root \
    -password pass:${KEYSTORE_PASSWORD}

keytool -importkeystore -deststorepass ${KEYSTORE_PASSWORD} -destkeypass ${KEYSTORE_PASSWORD} \
    -destkeystore kafka.keystore.jks -srckeystore kafka-broker.p12 -srcstoretype PKCS12 \
    -srcstorepass ${KEYSTORE_PASSWORD} -alias kafka 2>/dev/null || true

keytool -keystore kafka.truststore.jks -alias CARoot -import -file ca.crt \
    -storepass ${KEYSTORE_PASSWORD} -noprompt 2>/dev/null || true

log_info "Certificats Kafka générés"

# ============================================================================
# 3. Certificats MQTT (Mosquitto)
# ============================================================================
log_info "Génération des certificats MQTT..."

openssl genrsa -out mosquitto.key ${KEY_SIZE}
openssl req -new -key mosquitto.key -out mosquitto.csr \
    -subj "/C=MA/ST=Casablanca/L=Casablanca/O=VertiFlow/OU=MQTT/CN=mosquitto"

cat > mosquitto.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = mosquitto
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

openssl x509 -req -in mosquitto.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out mosquitto.crt -days ${VALIDITY_DAYS} -extfile mosquitto.ext

log_info "Certificats MQTT générés"

# ============================================================================
# 4. Certificats NiFi
# ============================================================================
log_info "Génération des certificats NiFi..."

openssl genrsa -out nifi.key ${KEY_SIZE}
openssl req -new -key nifi.key -out nifi.csr \
    -subj "/C=MA/ST=Casablanca/L=Casablanca/O=VertiFlow/OU=NiFi/CN=nifi"

cat > nifi.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = nifi
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

openssl x509 -req -in nifi.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out nifi.crt -days ${VALIDITY_DAYS} -extfile nifi.ext

# Créer le keystore NiFi
openssl pkcs12 -export -in nifi.crt -inkey nifi.key \
    -out nifi.p12 -name nifi -CAfile ca.crt -caname root \
    -password pass:${KEYSTORE_PASSWORD}

log_info "Certificats NiFi générés"

# ============================================================================
# 5. Certificats ClickHouse
# ============================================================================
log_info "Génération des certificats ClickHouse..."

openssl genrsa -out clickhouse.key ${KEY_SIZE}
openssl req -new -key clickhouse.key -out clickhouse.csr \
    -subj "/C=MA/ST=Casablanca/L=Casablanca/O=VertiFlow/OU=ClickHouse/CN=clickhouse"

cat > clickhouse.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = clickhouse
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

openssl x509 -req -in clickhouse.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out clickhouse.crt -days ${VALIDITY_DAYS} -extfile clickhouse.ext

# Combiner pour ClickHouse
cat clickhouse.crt clickhouse.key > clickhouse-combined.pem

log_info "Certificats ClickHouse générés"

# ============================================================================
# 6. Certificats MongoDB
# ============================================================================
log_info "Génération des certificats MongoDB..."

openssl genrsa -out mongodb.key ${KEY_SIZE}
openssl req -new -key mongodb.key -out mongodb.csr \
    -subj "/C=MA/ST=Casablanca/L=Casablanca/O=VertiFlow/OU=MongoDB/CN=mongodb"

cat > mongodb.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = mongodb
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

openssl x509 -req -in mongodb.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out mongodb.crt -days ${VALIDITY_DAYS} -extfile mongodb.ext

# MongoDB PEM (cert + key combinés)
cat mongodb.crt mongodb.key > mongodb.pem

log_info "Certificats MongoDB générés"

# ============================================================================
# 7. Nettoyage et permissions
# ============================================================================
log_info "Nettoyage et configuration des permissions..."

# Supprimer les fichiers temporaires
rm -f *.csr *.ext *.srl

# Configurer les permissions
chmod 600 *.key *.pem *.p12 2>/dev/null || true
chmod 644 *.crt 2>/dev/null || true
chmod 644 *.jks 2>/dev/null || true

# ============================================================================
# 8. Résumé
# ============================================================================
log_info "=== Génération terminée ==="
echo ""
echo "Fichiers générés dans ${CERTS_DIR}:"
ls -la "${CERTS_DIR}"
echo ""
log_info "Mot de passe des keystores: ${KEYSTORE_PASSWORD}"
log_warn "IMPORTANT: Changez ce mot de passe en production!"
log_warn "Stockez les clés privées de manière sécurisée (Vault, KMS, etc.)"
