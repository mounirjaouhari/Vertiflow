# 🔑 Configuration des Identifiants (Agri-Copilot PRO)

Pour que l'IA fonctionne, vous devez configurer **UNE** des deux méthodes suivantes :

## Méthode 1 : Clé API (Recommandé pour test rapide)
Cette méthode active Gemini pour le chat et l'analyse, mais certaines fonctions avancées (BigQuery direct) peuvent être limitées.

1. Obtenez une clé API ici : [Google AI Studio](https://aistudio.google.com/)
2. Ouvrez le fichier `.env` à la racine du projet.
3. Remplacez la valeur placeholder :
   ```bash
   GEMINI_API_KEY=votre_cle_vraie_cle_api_ici
   ```
4. Redémarrez l'application.

## Méthode 2 : Compte de Service GCP (Production)
C'est la méthode complète qui permet l'accès à BigQuery et Vertex AI.

1. Téléchargez votre clé JSON GCP (Service Account).
2. Renommez le fichier en `vertiflow-gcp-key.json`.
3. Placez-le dans le dossier :
   ```
   security/gcp/vertiflow-gcp-key.json
   ```
   *(Créez le dossier s'il n'existe pas)*

## État actuel
Le fichier `.env` a été mis à jour avec les variables manquantes. Veuillez les remplir.
