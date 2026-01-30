📝 Rapport d'Incident  Initialisation Infrastructure VertiFlow

Date : 31 Décembre 2025

Rapporteur : Imrane (DevOps & Infrastructure)

Statut : ✅ Résolu (Workaround appliqué)

1. Description de l'Erreur

Lors de l'exécution du script infrastructure/init_infrastructure.py, le système ne parvenait pas à initialiser la connexion avec le cluster Kafka. L'erreur principale était liée à l'incompatibilité de la bibliothèque kafka-python avec les versions récentes de Python (notamment Python 3.12+), provoquant des erreurs d'importation (ModuleNotFoundError ou erreurs internes de types).

2. Analyse Technique

La bibliothèque kafka-python (version 2.0.2) spécifiée dans le fichier requirements.txt est devenue obsolète et ne supporte pas nativement les évolutions récentes du langage. Cela bloquait la vérification de l'état du broker et la création automatique des topics.

3. Solution Appliquée

La transition vers la version communautaire maintenue kafka-python-ng (Next Generation) a été effectuée.

Actions correctives immédiates :

Désinstallation de l'ancienne version.

Installation de la nouvelle version :

pip install kafka-python-ng


Test de validation réussi via la console :

python -c "from kafka import KafkaAdminClient; print('Import réussi !')"


4. Résultats

Après l'installation de kafka-python-ng, le script d'initialisation a pu :

✅ Détecter le broker Kafka sur 127.0.0.1:9092.

✅ Identifier la version du broker (2.6.0).

✅ Vérifier/Créer les topics : basil_telemetry_full, vertiflow.commands, dead_letter_queue, etc.

5. Recommandations

Il est impératif de mettre à jour le fichier source requirements.txt pour éviter que cette erreur ne se reproduise lors du déploiement par d'autres membres de l'équipe.

🎫 Ticket Jira/Trello : VF-089

Titre : Correction de la dépendance Kafka pour compatibilité Python 3.12+

Assigné à : 🧙‍♂️ @Mounir

Priorité : 🔴 Haute

Description :

Remplacer la bibliothèque obsolète kafka-python par kafka-python-ng dans les fichiers de configuration du projet.

Tâches à effectuer :

[ ] Modifier requirements.txt : Remplacer kafka-python==2.0.2 par kafka-python-ng>=2.2.3.

[ ] Vérifier si des imports spécifiques dans cortex.py nécessitent des ajustements (normalement transparent).

[ ] Pousser la modification sur la branche main.