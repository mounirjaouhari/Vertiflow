#!/usr/bin/env python3
"""
Créer table plant_recipes compatible avec dashboard 11_plant_recipes.json
"""

import clickhouse_connect

CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = 'default'

def create_plant_recipes_table(client):
    """Créer table plant_recipes avec structure requise par dashboard 11"""
    print("🔨 Création de la table plant_recipes...")
    
    # Supprimer vue si existe
    client.command("DROP VIEW IF EXISTS vertiflow.plant_recipes")
    
    # Créer table avec colonnes requises par dashboard
    create_sql = """
    CREATE TABLE IF NOT EXISTS vertiflow.plant_recipes (
        recipe_id String,
        name String,
        plant_type String,
        type Enum8('initial' = 1, 'optimal' = 2),
        growth_stage String,
        temp_optimal Float64,
        humidity_optimal Float64,
        co2_optimal Float64,
        ph_optimal Float64,
        ec_optimal Float64,
        dli_optimal Float64,
        nitrogen_optimal Float64,
        phosphorus_optimal Float64,
        potassium_optimal Float64,
        optimization_score Float64 DEFAULT 0,
        yield_increase Float64 DEFAULT 0,
        quality_increase Float64 DEFAULT 0,
        energy_reduction Float64 DEFAULT 0,
        optimized_by String DEFAULT '',
        status String DEFAULT 'active',
        version String DEFAULT 'v1.0',
        created_at DateTime DEFAULT now(),
        updated_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY (plant_type, recipe_id);
    """
    
    client.command(create_sql)
    print("✅ Table créée avec succès")

def insert_sample_recipes(client):
    """Insérer recettes exemples (initial + optimal)"""
    print("📥 Insertion de recettes exemples...")
    
    recipes = [
        # Recettes INITIALES (baseline)
        {
            'recipe_id': 'INIT-BASIL-001',
            'name': 'Basilic Genovese Standard',
            'plant_type': 'Basilic Genovese',
            'type': 'initial',
            'growth_stage': 'Végétatif',
            'temp_optimal': 24.0,
            'humidity_optimal': 65.0,
            'co2_optimal': 800.0,
            'ph_optimal': 5.8,
            'ec_optimal': 1.8,
            'dli_optimal': 17.0,
            'nitrogen_optimal': 150.0,
            'phosphorus_optimal': 50.0,
            'potassium_optimal': 200.0,
            'optimization_score': 0,
            'yield_increase': 0,
            'quality_increase': 0,
            'energy_reduction': 0,
            'optimized_by': '',
            'status': 'baseline',
            'version': 'v1.0'
        },
        {
            'recipe_id': 'INIT-BASIL-002',
            'name': 'Basilic Thai Baseline',
            'plant_type': 'Basilic Thai',
            'type': 'initial',
            'growth_stage': 'Croissance',
            'temp_optimal': 25.0,
            'humidity_optimal': 60.0,
            'co2_optimal': 850.0,
            'ph_optimal': 6.0,
            'ec_optimal': 1.9,
            'dli_optimal': 18.0,
            'nitrogen_optimal': 160.0,
            'phosphorus_optimal': 55.0,
            'potassium_optimal': 210.0,
            'optimization_score': 0,
            'yield_increase': 0,
            'quality_increase': 0,
            'energy_reduction': 0,
            'optimized_by': '',
            'status': 'baseline',
            'version': 'v1.0'
        },
        {
            'recipe_id': 'INIT-BASIL-003',
            'name': 'Basilic Purple Standard',
            'plant_type': 'Basilic Purple',
            'type': 'initial',
            'growth_stage': 'Floraison',
            'temp_optimal': 23.0,
            'humidity_optimal': 70.0,
            'co2_optimal': 900.0,
            'ph_optimal': 5.9,
            'ec_optimal': 2.0,
            'dli_optimal': 19.0,
            'nitrogen_optimal': 140.0,
            'phosphorus_optimal': 60.0,
            'potassium_optimal': 220.0,
            'optimization_score': 0,
            'yield_increase': 0,
            'quality_increase': 0,
            'energy_reduction': 0,
            'optimized_by': '',
            'status': 'baseline',
            'version': 'v1.0'
        },
        # Recettes OPTIMALES (Cortex A11)
        {
            'recipe_id': 'OPT-BASIL-001',
            'name': 'Basilic Genovese Optimal - Cortex A11',
            'plant_type': 'Basilic Genovese',
            'type': 'optimal',
            'growth_stage': 'Végétatif',
            'temp_optimal': 23.2,
            'humidity_optimal': 68.5,
            'co2_optimal': 1050.0,
            'ph_optimal': 5.95,
            'ec_optimal': 1.65,
            'dli_optimal': 19.2,
            'nitrogen_optimal': 165.0,
            'phosphorus_optimal': 48.0,
            'potassium_optimal': 195.0,
            'optimization_score': 94.5,
            'yield_increase': 18.3,
            'quality_increase': 12.7,
            'energy_reduction': 8.4,
            'optimized_by': 'Cortex A11 ML Engine',
            'status': 'validated',
            'version': 'v2.3'
        },
        {
            'recipe_id': 'OPT-BASIL-002',
            'name': 'Basilic Thai Optimal - Cortex A11',
            'plant_type': 'Basilic Thai',
            'type': 'optimal',
            'growth_stage': 'Croissance',
            'temp_optimal': 24.8,
            'humidity_optimal': 63.2,
            'co2_optimal': 1120.0,
            'ph_optimal': 6.05,
            'ec_optimal': 1.78,
            'dli_optimal': 20.5,
            'nitrogen_optimal': 172.0,
            'phosphorus_optimal': 52.0,
            'potassium_optimal': 205.0,
            'optimization_score': 91.8,
            'yield_increase': 22.1,
            'quality_increase': 15.2,
            'energy_reduction': 6.9,
            'optimized_by': 'Cortex A11 ML Engine',
            'status': 'validated',
            'version': 'v2.1'
        },
        {
            'recipe_id': 'OPT-BASIL-003',
            'name': 'Basilic Purple Optimal - Cortex A11',
            'plant_type': 'Basilic Purple',
            'type': 'optimal',
            'growth_stage': 'Floraison',
            'temp_optimal': 22.5,
            'humidity_optimal': 72.8,
            'co2_optimal': 980.0,
            'ph_optimal': 5.92,
            'ec_optimal': 1.88,
            'dli_optimal': 21.3,
            'nitrogen_optimal': 148.0,
            'phosphorus_optimal': 58.0,
            'potassium_optimal': 215.0,
            'optimization_score': 89.2,
            'yield_increase': 16.9,
            'quality_increase': 10.5,
            'energy_reduction': 11.2,
            'optimized_by': 'Cortex A11 ML Engine',
            'status': 'production',
            'version': 'v2.0'
        }
    ]
    
    # Insérer recettes
    for recipe in recipes:
        client.insert('vertiflow.plant_recipes', [tuple(recipe.values())], column_names=list(recipe.keys()))
    
    print(f"✅ {len(recipes)} recettes insérées (3 initial + 3 optimal)")

def verify_data(client):
    """Vérifier données"""
    print("\n🔍 Vérification des données...")
    
    # Compter par type
    counts = client.query("""
        SELECT 
            toString(type) as recipe_type, 
            count() as total
        FROM vertiflow.plant_recipes 
        GROUP BY type
    """).result_rows
    
    for row in counts:
        print(f"  📊 {row[0]}: {row[1]} recettes")
    
    # Score moyen
    avg_score = client.query("""
        SELECT round(avg(optimization_score), 1) as avg_score
        FROM vertiflow.plant_recipes
        WHERE toString(type) = 'optimal'
    """).first_row[0]
    
    print(f"  💚 Score optimisation moyen: {avg_score}%")
    
    # Échantillon
    print("\n  📋 Recettes optimales:")
    samples = client.query("""
        SELECT 
            name,
            plant_type,
            round(optimization_score, 1) as score,
            round(yield_increase, 1) as yield_up,
            round(quality_increase, 1) as quality_up
        FROM vertiflow.plant_recipes
        WHERE toString(type) = 'optimal'
        ORDER BY optimization_score DESC
    """).result_rows
    
    for row in samples:
        print(f"    • {row[0]}: Score={row[2]}%, Rendement+{row[3]}%, Qualité+{row[4]}%")

def main():
    print("=" * 80)
    print("🌱 CRÉATION TABLE PLANT_RECIPES POUR DASHBOARD 11")
    print("=" * 80)
    
    # Connexion
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD
    )
    print("✅ Connecté à ClickHouse\n")
    
    # Créer table
    create_plant_recipes_table(client)
    print()
    
    # Insérer données
    insert_sample_recipes(client)
    
    # Vérifier
    verify_data(client)
    
    print("\n" + "=" * 80)
    print("✅ TERMINÉ - Dashboard 11_plant_recipes.json débloqué")
    print("=" * 80)

if __name__ == '__main__':
    main()
