// =============================================================================
// PROJET VERTIFLOW - INITIALISATION MONGODB (OPS & TEMPS RÉEL)
// =============================================================================
// Ticket JIRA : TICKET-025 (Algorithme A5 - Règles Métier & Initialisation)
// Auteur: @Imrane (DevOps) & @Mouhammed (Data Engineer)
// Date: 25/12/2025
// Description: Configuration de la base opérationnelle 'vertiflow_ops'.
//              Crée les collections, les validateurs de schéma et les index.
// =============================================================================

// Sélection de la base de données
db = db.getSiblingDB('vertiflow_ops');

// -----------------------------------------------------------------------------
// 1. COLLECTION : LIVE STATE (État Temps Réel des Bacs)
// Rôle : Stocker le dernier état connu de chaque module (Digital Twin).
// Usage : Alimente le Dashboard "Cockpit" et les Algorithmes Réflexes (A4, A5).
// -----------------------------------------------------------------------------

// Création avec Validation de Schéma (Qualité des Données)
db.createCollection("live_state", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: [ "farm_id", "rack_id", "module_id", "last_update", "telemetry" ],
         properties: {
            farm_id: {
               bsonType: "string",
               description: "Identifiant de la ferme requis"
            },
            rack_id: {
               bsonType: "string",
               description: "Identifiant du rack requis"
            },
            module_id: {
               bsonType: "string",
               description: "Identifiant unique du module (Bac)"
            },
            last_update: {
               bsonType: "date",
               description: "Horodatage de la dernière mesure reçue"
            },
            telemetry: {
               bsonType: "object",
               required: ["air_temp_internal", "nutrient_n_total"],
               properties: {
                  air_temp_internal: { bsonType: ["double", "int"] },
                  nutrient_n_total: { bsonType: ["double", "int"] }
               }
            },
            status: {
               bsonType: "object",
               properties: {
                  is_active: { bsonType: "bool" },
                  alert_level: { enum: ["NORMAL", "WARNING", "CRITICAL"] }
               }
            }
         }
      }
   }
});

// Indexation Stratégique
// 1. Index Unique Composite : Un seul document par module (C'est le Digital Twin)
db.live_state.createIndex({ "farm_id": 1, "rack_id": 1, "module_id": 1 }, { unique: true });

// 2. Index TTL (Time To Live) : Supprime les états "zombies" non mis à jour depuis 7 jours
// Cela permet de garder la base propre si un capteur est retiré.
db.live_state.createIndex({ "last_update": 1 }, { expireAfterSeconds: 604800 }); // 7 jours

// 3. Index Géospatial (Pour les requêtes de proximité dans la ferme)
// Utile pour dire : "Donne-moi tous les bacs proches du capteur défaillant"
// db.live_state.createIndex({ "location": "2dsphere" }); // Optionnel si coordonnées GPS présentes


// -----------------------------------------------------------------------------
// 2. COLLECTION : INCIDENT LOGS (Journal d'Alertes)
// Rôle : Historique des décisions prises par l'Algo A5 (Règles Métier).
// Usage : Audit et Analyse post-mortem des pannes.
// -----------------------------------------------------------------------------
db.createCollection("incident_logs");

// Index pour la recherche rapide par date et par sévérité
db.incident_logs.createIndex({ "timestamp": -1 });
db.incident_logs.createIndex({ "severity": 1, "status": 1 }); // Pour filtrer les incidents "OPEN" et "CRITICAL"


// -----------------------------------------------------------------------------
// 3. COLLECTION : PLANT RECIPES (Référentiel Cibles)
// Rôle : Stocke les paramètres idéaux (Algo A11 optimise ces valeurs).
// Usage : Les Algos A4 (Seuillage) lisent cette collection pour savoir si c'est une alerte.
// -----------------------------------------------------------------------------
db.createCollection("plant_recipes");

db.plant_recipes.createIndex({ "recipe_id": 1 }, { unique: true });
db.plant_recipes.createIndex({ "species_variety": 1, "growth_stage": 1 });

// Insertion d'une Recette par défaut (Bootstrap)
db.plant_recipes.insertOne({
    recipe_id: "BASIL_GENOVESE_STD_V1",
    species_variety: "Genovese",
    growth_stage: "Végétatif",
    targets: {
        temp_min: 18,
        temp_max: 28,
        humidity_min: 50,
        humidity_max: 80,
        n_target_ppm: 150
    },
    version: 1,
    is_active: true,
    created_at: new Date()
});

print(" Initialisation MongoDB terminée avec succès.");
print("   Collections créées : live_state, incident_logs, plant_recipes");