# VertiFlow AI Chat App (app_merged.py)

## Description
VertiFlow AI Chat App est une interface intelligente basée sur Streamlit, conçue pour le projet d'agriculture verticale VertiFlow au Maroc. Elle permet d'interagir avec les données de la ferme, d'obtenir des analyses, des graphiques, des tableaux, et des recommandations agronomiques grâce à l'intégration de Google Gemini, BigQuery, et ClickHouse.

## Fonctionnalités principales
- ** UI** : Interface conversationnelle moderne.
- **Génération de graphiques et tableaux** : Visualisation des données de production, capteurs, et analyses.
- **Support multilingue** : Français, Anglais, Arabe, et Darija (dialecte marocain).
- **Mode expert** : Réponses détaillées avec références scientifiques et statistiques.
- **Historique de conversation** : Suivi des échanges.
- **Dashboard interactif** : Vue globale des indicateurs clés.
- **Thème clair/sombre** : Personnalisation de l'apparence.
- **Intégration ClickHouse** : Contexte complet des données Golden Record.
- **Requêtes SQL Gemini** : Génération et exécution de requêtes SQL via Google Gemini.
- **Détection Darija** : Adaptation automatique des réponses au dialecte marocain.

## Usage
1. Lancer l'application :
   ```bash
   cd ~/vertiflow_cloud_release/agents
   source venv/bin/activate
   streamlit run app_merged.py --server.port 8501 --server.address 0.0.0.0
   ```
2. Accéder à l'interface via [http://localhost:8501](http://localhost:8501)
3. Poser vos questions, demander des analyses, des graphiques, ou des recommandations.

## Technologies utilisées
- **Streamlit** : Interface web interactive
- **Google Gemini (genai)** : Génération de réponses et requêtes SQL
- **BigQuery** : Accès aux données cloud
- **Plotly, Pandas** : Visualisation et traitement des données
- **ClickHouse** : Contexte agronomique

## Structure du dossier
- `app_merged.py` : Script principal de l'application
- `README.md` : Ce fichier
- Autres scripts et utilitaires

## Contact

