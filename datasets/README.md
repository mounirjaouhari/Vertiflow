# Datasets - Donnees de recherche

Ce dossier contient les datasets de recherche pour VertiFlow.

## Structure

```
datasets/
├── Basil Data.zip                   # Dataset principal basil
└── basil_research/                  # Recherches sur le basilic
    ├── *.zip                        # Datasets compresses
    ├── *.pdf                        # Articles scientifiques
    ├── *.xlsx, *.xls                # Donnees experimentales
    └── *.docx                       # Documentation
```

## Sources de donnees

### MIT OpenAg / Food Computer
- **Volume:** 73,000+ datapoints
- **Contenu:** Environnement controle, capteurs IoT
- **Usage:** Entrainement modeles ML

### Frontiers in Plant Science
Articles et datasets sur :
- Tolerance au froid du basilic
- Effets du spectre lumineux
- Stress salin et hydrique
- Metabolites secondaires

### Etudes Wageningen
- Optimisation LED
- DLI et photoperiode
- Spectres Red/Blue/Far-Red

## Fichiers cles

| Fichier | Description | Volume |
|---------|-------------|--------|
| `Basil Data.zip` | Dataset principal | ~50 MB |
| `fpls-*.pdf` | Articles Frontiers | Reference |
| `Table_*.xlsx` | Donnees experimentales | ~5 MB |

## Utilisation

```python
import pandas as pd
import zipfile

# Extraire et charger un dataset
with zipfile.ZipFile("datasets/Basil Data.zip") as z:
    with z.open("data.csv") as f:
        df = pd.read_csv(f)
```

## Integration VertiFlow

Ces datasets sont utilises pour :
1. **Entrainement Oracle (A9)** - Prediction rendement
2. **Calibration Simulator** - Modeles bio-physiques
3. **Validation Cortex (A11)** - Optimisation recettes
