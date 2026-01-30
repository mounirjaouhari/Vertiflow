# Data Sources - Recuperation de donnees externes

Ce dossier contient les scripts de recuperation des donnees externes pour VertiFlow.

## Structure

```
data_sources/
├── download_all_sources.sh          # Orchestrateur shell (tous les datasets)
├── download_nasa_power.py           # API NASA POWER (climat)
├── fetch_all_external_data.py       # Orchestrateur Python (toutes les APIs)
├── fetch_open_meteo.py              # API Open-Meteo (meteo gratuite)
├── handlers/                        # Handlers d'APIs
│   ├── electricity_maps_handler.py  # Intensite carbone electrique
│   ├── fao_fpma_handler.py          # Prix alimentaires FAO
│   ├── openaq_handler.py            # Qualite de l'air
│   ├── openfarm_handler.py          # Base de donnees cultures
│   └── rte_eco2mix_handler.py       # Reseau electrique francais
└── scrapers/                        # Web scrapers
    ├── onee_tarifs_scraper.py       # Tarifs electricite Maroc
    └── rnm_prices_scraper.py        # Prix marche agricole
```

## Sources de donnees

### Meteo (GRATUIT)
| Source | Script | Cle API | Description |
|--------|--------|---------|-------------|
| NASA POWER | `download_nasa_power.py` | Non | Climat agricole, radiation solaire |
| Open-Meteo | `fetch_open_meteo.py` | Non | Meteo temps reel, ET0 |

### Energie
| Source | Script | Cle API | Description |
|--------|--------|---------|-------------|
| Electricity Maps | `handlers/electricity_maps_handler.py` | Oui | Intensite carbone |
| RTE ECO2MIX | `handlers/rte_eco2mix_handler.py` | Oui | Reseau electrique FR |
| ONEE | `scrapers/onee_tarifs_scraper.py` | Non | Tarifs Maroc |

### Marche & Agronomie
| Source | Script | Cle API | Description |
|--------|--------|---------|-------------|
| FAO FPMA | `handlers/fao_fpma_handler.py` | Non | Prix alimentaires |
| OpenFarm | `handlers/openfarm_handler.py` | Non | Base de cultures |
| RNM | `scrapers/rnm_prices_scraper.py` | Non | Prix marche FR |

## Utilisation

### Recuperer toutes les sources
```bash
# Via shell (datasets academiques)
./scripts/data_sources/download_all_sources.sh all

# Via Python (APIs temps reel)
python scripts/data_sources/fetch_all_external_data.py
```

### Recuperer une source specifique
```bash
# NASA POWER
python scripts/data_sources/download_nasa_power.py

# Open-Meteo
python scripts/data_sources/fetch_open_meteo.py

# Avec filtre par categorie
python scripts/data_sources/fetch_all_external_data.py --category weather
```

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `ELECTRICITY_MAPS_TOKEN` | Token API Electricity Maps |
| `RTE_CLIENT_ID` | Client ID RTE |
| `RTE_CLIENT_SECRET` | Client Secret RTE |
| `OPENWEATHER_API_KEY` | Cle API OpenWeather (optionnel) |
