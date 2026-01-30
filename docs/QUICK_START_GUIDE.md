🚀 Guide de Démarrage Complet - Projet VertiFlow

Plateforme d'Intelligence Artificielle pour l'Agriculture Verticale

Ce guide vous accompagne de zéro jusqu'à une production complète, en utilisant l'infrastructure Docker, les pipelines NiFi, les bases de données ClickHouse/MongoDB et les algorithmes d'IA.

📋 Pré-requis Techniques

Avant de commencer, assurez-vous d'avoir :

Docker Desktop (ou Docker Engine + Docker Compose) installé et lancé.

Minimum : 4 CPU, 8 Go RAM alloués à Docker.

Python 3.9+ installé.

Git pour cloner le dépôt.

Accès internet (pour télécharger les images Docker et les libs Python).

🏗️ Phase 1 : Lancement de l'Infrastructure (Socle)

C'est la fondation. Nous allons lancer tous les serveurs (Kafka, NiFi, bases de données).

Ouvrez un terminal à la racine du projet vertiflow-data-platform/.

Lancez la stack principale :

docker-compose up -d


Attendez ~2 minutes que tous les conteneurs soient "Healthy" (surtout NiFi et ClickHouse).

Lancez la stack de monitoring (Optionnel mais recommandé) :

docker-compose -f infra/docker-compose.metrics.yml up -d


Vérifiez que vous avez accès à :

NiFi : https://localhost:8443/nifi (Attendez quelques minutes)

Grafana : http://localhost:3000 (Login: admin/admin)

📦 Phase 2 : Initialisation des Données

Maintenant que les serveurs tournent, nous devons créer les tables, les topics et les indexes.

Installez les dépendances Python :

pip install -r requirements.txt


Exécutez le script maître d'initialisation :

python infrastructure/init_infrastructure.py


Ce que ça fait :

Vérifie que Kafka, Mongo et ClickHouse répondent.

Crée le topic Kafka basil_telemetry_full.

Crée la base smart_farming dans ClickHouse.

Injecte les recettes de culture (plant_recipes) dans MongoDB.

Succès attendu : Des coches vertes ✅ partout dans le terminal.

Vérifiez la création des tables ClickHouse (Optionnel) :

Connectez-vous au conteneur ClickHouse ou utilisez un client DBeaver.

Vérifiez que la table smart_farming.basil_ultimate_realtime existe (elle est créée par le montage Docker des scripts .sql au démarrage).

🔄 Phase 3 : Construction de l'Usine NiFi (ETL)

C'est le moment de câbler le traitement des données.

Assurez-vous que le driver ClickHouse est en place :

Le fichier clickhouse-jdbc-0.4.6.jar doit être dans le dossier drivers/ à la racine du projet.

Lancez le déploiement automatique du pipeline :

python scripts/setup_nifi_pipeline.py


Ce que ça fait :

Se connecte à l'API NiFi.

Crée les 4 zones (Collection, Fusion, Qualité, Publication).

Configure la connexion MQTT, Kafka et ClickHouse.

Active les contrôleurs services.

Note : Si le script échoue (SSL error), attendez encore 1 minute que NiFi finisse son boot.

Démarrez les processeurs :

Allez sur https://localhost:8443/nifi.

Faites un clic droit sur le groupe principal "VERTIFLOW_DATA_PLATFORM_V1" -> Start.

📡 Phase 4 : Injection de Données (Simulation)

Le système est prêt mais vide. Injectons de la vie !

Lancez le Simulateur IoT (Le cœur du système) :
Ouvrez un nouveau terminal et lancez :

python scripts/simulators/iot_sensor_simulator.py


Vous verrez des logs d'envoi MQTT (📤 [MQTT] ...).

Laissez ce script tourner en fond.

Lancez le Connecteur Météo (Données réelles) :

python scripts/download_nasa_power.py


Cela va créer un fichier JSON dans data_ingestion/nasa_weather. NiFi le détectera automatiquement.

Simulez la Vision par Ordinateur (Croissance) :

python scripts/simulators/vision_system_simulator.py


🧠 Phase 5 : Activation de l'Intelligence Artificielle

Maintenant que les données coulent, activons les cerveaux.

Lancez l'Oracle (Prédiction Récolte) :

python cloud_citadel/nervous_system/oracle.py


Il va commencer à écouter Kafka, faire des prédictions, et renvoyer les résultats dans le topic vertiflow.predictions.

Lancez le Cortex (Optimisation) :

python cloud_citadel/nervous_system/cortex.py


Il va analyser les données ClickHouse et optimiser les recettes dans MongoDB.

📊 Phase 6 : Visualisation & Pilotage

Tout est en place. Voyons le résultat.

Ouvrez Power BI Desktop.

Connectez-vous à ClickHouse :

Source : ODBC.

Chaîne de connexion : Driver={ClickHouse ODBC Driver (Unicode)};Server=localhost;Port=8123;Database=smart_farming;

Connectez-vous au Streaming (Optionnel) :

Configurez un "Push Dataset" dans l'interface Power BI Service et mettez l'URL API dans le processeur NiFi correspondant (Zone 4).

🆘 Dépannage (Troubleshooting)

NiFi ne démarre pas ?

Vérifiez la RAM Docker (min 4Go).

docker logs nifi pour voir les erreurs Java.

Pas de données dans ClickHouse ?

Vérifiez que le simulateur tourne.

Vérifiez dans NiFi que les processeurs sont "Running" (Flèche verte).

Vérifiez les logs NiFi pour des erreurs JDBC ("Driver not found" = vérifiez le dossier drivers/).

Kafka est lent ?

C'est normal au premier lancement (création des fichiers logs).

Félicitations ! Vous avez maintenant