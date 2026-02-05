#!/usr/bin/env python3
"""
Import Basil Vance recipes to ClickHouse
Transform MongoDB format to ClickHouse format
"""
import json
import requests
from datetime import datetime

# Read recipes from file
with open('/home/mounirjaouhari/vertiflow_cloud_release/basil_recipes.json', 'r') as f:
    recipes = json.load(f)

print(f"📊 Importing {len(recipes)} recipes to ClickHouse...\n")

# Create ClickHouse table for basil_recipes if not exists
create_table_sql = """
CREATE TABLE IF NOT EXISTS vertiflow.basil_vance_recipes (
    recipe_id String,
    species_variety String,
    growth_stage String,
    target_temp_day Float32,
    target_temp_night Float32,
    target_humidity_min Float32,
    target_humidity_max Float32,
    target_vpd Float32,
    target_dli Float32,
    target_photoperiod_hours UInt8,
    target_spectrum_ratio_rb Float32,
    target_n_ppm Float32,
    target_p_ppm Float32,
    target_k_ppm Float32,
    target_ec Float32,
    target_ph Float32,
    author String,
    validation_date Date,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (recipe_id, created_date)
"""

try:
    # Create table
    response = requests.post(
        'http://localhost:8123/?database=vertiflow',
        data=create_table_sql,
        headers={'Content-Type': 'text/plain'}
    )
    if response.status_code != 200:
        print(f"⚠️ Create table response: {response.status_code}")
    else:
        print("✅ Table verified/created")
    
    # Insert recipes
    insert_sql = "INSERT INTO vertiflow.basil_vance_recipes FORMAT JSONEachRow\n"
    
    for recipe in recipes:
        # Transform to ClickHouse format
        ch_recipe = {
            'recipe_id': recipe.get('recipe_id', 'UNKNOWN'),
            'species_variety': recipe.get('species_variety', 'Basil'),
            'growth_stage': recipe.get('growth_stage', 'Unknown'),
            'target_temp_day': float(recipe.get('target_temp_day', 0)),
            'target_temp_night': float(recipe.get('target_temp_night', 0)),
            'target_humidity_min': float(recipe.get('target_humidity_min', 0)),
            'target_humidity_max': float(recipe.get('target_humidity_max', 0)),
            'target_vpd': float(recipe.get('target_vpd', 0)),
            'target_dli': float(recipe.get('target_dli', 0)),
            'target_photoperiod_hours': int(recipe.get('target_photoperiod_hours', 0)),
            'target_spectrum_ratio_rb': float(recipe.get('target_spectrum_ratio_rb', 0)),
            'target_n_ppm': float(recipe.get('target_n_ppm', 0)),
            'target_p_ppm': float(recipe.get('target_p_ppm', 0)),
            'target_k_ppm': float(recipe.get('target_k_ppm', 0)),
            'target_ec': float(recipe.get('target_ec', 0)),
            'target_ph': float(recipe.get('target_ph', 0)),
            'author': recipe.get('author', 'Unknown'),
            'validation_date': recipe.get('validation_date', '2026-02-01')
        }
        insert_sql += json.dumps(ch_recipe) + "\n"
    
    # Send to ClickHouse
    response = requests.post(
        'http://localhost:8123/?database=vertiflow',
        data=insert_sql,
        headers={'Content-Type': 'text/plain'}
    )
    
    if response.status_code == 200:
        print(f"✅ {len(recipes)} recipes inserted to ClickHouse")
        
        # Verify count
        verify_sql = "SELECT COUNT(*) FROM vertiflow.basil_vance_recipes"
        response = requests.get(
            'http://localhost:8123/?database=vertiflow',
            params={'query': verify_sql}
        )
        if response.status_code == 200:
            count = int(response.text.strip())
            print(f"✅ ClickHouse verification: {count} recipes stored")
        
    else:
        print(f"❌ Insert failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Basil Vance recipes import complete!")
