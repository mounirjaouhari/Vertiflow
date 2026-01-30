📝 Rapport d'Incident : Authentification et Stabilité NiFi API

Date : 01 Janvier 2026

Rapporteur : Imrane (DevOps)

Système : Flux de données ETL / Apache NiFi

Statut : ✅ Résolu (Nécessite une action de synchronisation finale)

1. Description des Problèmes Rencontrés

A. Erreur 503 (Service Unavailable)

Lors des premières tentatives, le script de déploiement recevait une erreur 503.

Cause : NiFi est une application Java lourde. L'API REST démarre plusieurs minutes après le conteneur. Le script tentait de se connecter avant que le moteur d'authentification ne soit initialisé.

Résolution : Implémentation d'une fonction wait_for_nifi avec une stratégie de "Retry" (20 tentatives toutes les 15 secondes).

B. Erreur 400 (Bad Request / Invalid Credentials)

Une fois l'API en ligne, le script a été rejeté avec le message : The supplied username and password are not valid.

Cause : Conflit de persistance. NiFi conserve les premiers identifiants générés dans son volume nifi-conf. Si le mot de passe a été modifié dans le docker-compose.yml après le premier lancement, NiFi ignore la mise à jour et conserve l'ancien mot de passe.

Résolution : Identification de la nécessité de purger le volume de configuration pour forcer la prise en compte des identifiants vertiflow_admin.

2. Solutions Appliquées

Mise à jour du script setup_nifi_pipeline.py :

Ajout du support JWT (JSON Web Token).

Ajout de la gestion des certificats SSL auto-signés (verify=False).

Ajout de la boucle d'attente intelligente pour le démarrage du service.

Procédure de réinitialisation de la sécurité :

Arrêt du service.

Suppression du volume vertiflow-data-platform_nifi-conf.

Redémarrage pour forcer la synchronisation avec les credentials du projet.

🎫 Ticket Jira/Trello : VF-095

Titre : Stabilisation et Synchronisation des Accès NiFi

Assigné à : 🧙‍♂️ @Mounir

Priorité : 🔴 Critique

Description :

Suite aux erreurs 400 rencontrées par @Imrane, il est nécessaire de s'assurer que tous les environnements de développement utilisent les mêmes credentials pour l'automatisation.

Tâches à effectuer :

[ ] Purger la configuration locale : Exécuter docker-compose down, puis docker volume rm vertiflow-data-platform_nifi-conf.

[ ] Vérifier le fichier .env : S'assurer que le mot de passe ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB est bien celui utilisé partout.

[ ] Validation finale : Lancer le script setup_nifi_pipeline.py et confirmer la création des 4 zones (Collection, Fusion, Validation, Publication) dans l'interface NiFi.

Commentaire technique :
Attention, la suppression du volume nifi-conf réinitialise également les certificats. NiFi peut mettre jusqu'à 5 minutes pour régénérer son magasin de clés au premier boot.