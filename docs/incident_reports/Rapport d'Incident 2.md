📝 Rapport d'Incident : Authentification API NiFi

Date : 31 Décembre 2025

Rapporteur : Imrane (DevOps)

Composant : Apache NiFi / Pipeline Setup Script

1. Description de l'Erreur

L'exécution du script scripts/setup_nifi_pipeline.py échoue avec une erreur HTTP 401 Client Error: Unauthorized.
Le script parvient à vérifier que le service est "Up", mais est rejeté par l'API dès qu'il tente d'accéder aux ressources du flux (/flow/process-groups/root).

2. Analyse Technique

D'après le fichier docker-compose.yml, NiFi est sécurisé avec les paramètres suivants :

SINGLE_USER_CREDENTIALS_USERNAME: vertiflow_admin

SINGLE_USER_CREDENTIALS_PASSWORD: ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB

Le script actuel envoie des requêtes anonymes. Dans les versions récentes de NiFi (1.14+), l'accès à l'API nécessite un Header Authorization: Bearer <JWT_TOKEN>.

3. Solution de Résolution

Il faut modifier le script Python pour :

Envoyer une requête POST à /nifi-api/access/token avec les identifiants.

Récupérer le token JWT.

Injecter ce token dans les headers de toutes les requêtes suivantes.

🎫 Ticket Jira/Trello : VF-092

Titre : Implémentation de l'Auth JWT dans les scripts NiFi

Assigné à : 🐍 @Mouhammed (cc: @Mounir)

Priorité : 🔴 Critique

Statut : En attente de mise à jour du script

Instructions pour la correction :
Utiliser le bloc de code suivant pour la gestion du token dans setup_nifi_pipeline.py.

def get_nifi_token(base_url, username, password):
    auth_url = f"{base_url}/access/token"
    data = {'username': username, 'password': password}
    response = requests.post(auth_url, data=data, verify=False)
    if response.status_code == 201:
        return response.text
    else:
        raise Exception(f"Échec d'authentification: {response.status_code}")
