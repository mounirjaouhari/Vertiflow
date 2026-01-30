# Mapping - Utilitaires de mapping

Ce dossier contient les scripts de mapping des donnees VertiFlow.

## Structure

```
mapping/
└── mapping_156_parameters.py        # Mapping des 156 colonnes ClickHouse
```

## Scripts

### mapping_156_parameters.py
Genere et documente le mapping des 156 colonnes du schema ClickHouse :
- Identification des capteurs
- Metriques environnementales
- Nutrition minerale
- Photosynthese et lumiere
- Hardware et maintenance
- Donnees externes
- Metadonnees de gouvernance

```bash
python scripts/mapping/mapping_156_parameters.py
```

## Fichier de configuration associe

Le fichier `config/mapping.json` contient le mapping complet :

```json
{
  "sensor_id": "string",
  "zone": ["ZONE_A", "ZONE_B", "NURSERY"],
  "metric_type": ["temperature", "humidity", "co2", "par", "ph", "ec"],
  "timestamp": "ISO-8601"
}
```

## Categories de colonnes

| Categorie | Colonnes | Description |
|-----------|----------|-------------|
| I. Identification | 1-10 | IDs, timestamps |
| II. Nutrition | 11-30 | N, P, K, Ca, Mg, Fe, etc. |
| III. Photosynthese | 31-50 | PPFD, DLI, spectre |
| IV. Biomasse | 51-70 | Poids, hauteur, LAI |
| V. Qualite | 71-90 | Grade, defauts, couleur |
| VI. Environnement | 91-110 | Temp, HR, CO2, VPD |
| VII. Rhizosphere | 111-125 | pH, EC, DO, turbidite |
| VIII. Externe | 126-140 | Meteo, energie |
| IX. Hardware | 141-150 | Pompes, LED, filtres |
| X. Gouvernance | 151-156 | Lineage, flags |
