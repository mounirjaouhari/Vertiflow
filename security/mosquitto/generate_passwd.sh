#!/bin/bash
# ============================================================================
# VERTIFLOW - Génération des mots de passe Mosquitto
# ============================================================================

PASSWD_FILE="$(dirname "$0")/passwd"

# Supprimer le fichier existant
rm -f "$PASSWD_FILE"
touch "$PASSWD_FILE"

echo "Génération des utilisateurs Mosquitto..."

# Fonction pour ajouter un utilisateur
add_user() {
    local username=$1
    local password=$2
    mosquitto_passwd -b "$PASSWD_FILE" "$username" "$password"
    echo "  - Utilisateur ajouté: $username"
}

# Utilisateurs par défaut (changez les mots de passe en production!)
add_user "vertiflow_admin" "AdminSecure2025!"
add_user "nifi_connector" "NiFiConnect2025!"
add_user "iot_sensors" "IoTSensors2025!"
add_user "iot_actuators" "IoTActuators2025!"
add_user "monitoring" "Monitoring2025!"
add_user "stream_processor" "StreamProc2025!"
add_user "ml_inference" "MLInference2025!"

echo ""
echo "Fichier généré: $PASSWD_FILE"
echo "ATTENTION: Changez ces mots de passe en production!"
