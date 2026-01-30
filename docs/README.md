# Docs - Documentation

Ce dossier contient toute la documentation du projet VertiFlow.

## Structure

```
docs/
├── 01_ARCHITECTURE.md               # Architecture systeme
├── 02_DATA_GOVERNANCE.md            # Protocole Vance (gouvernance)
├── 03_DATA_CATALOG.md               # Catalogue de donnees
├── 05_EXTERNAL_DATA_CATALOG.md      # Sources externes
├── CLICKHOUSE_COLUMN_DICTIONARY.md  # 156 colonnes documentees
├── GUIDE_SOURCES_DE_DONNEES.md      # Guide sources de donnees
├── PLAN_EXECUTION_SYSTEME.md        # Plan d'execution
├── QUICK_START_GUIDE.md             # Guide de demarrage rapide
├── RAPPORT_HARMONISATION.md         # Rapport harmonisation
├── RAPPORT_TECHNIQUE_COMPLET.md     # Rapport technique
├── VARIABLES_DICTIONARY_156.md      # Dictionnaire des variables
│
├── architecture/                    # Documentation architecture
│   ├── ABSTRACT_MATHEMATICAL_MODEL.md
│   ├── algorithmes.md
│   ├── algorithms_detail.md
│   ├── nifi_architecture.md
│   ├── RAPPORT_CLICKHOUSE_TABLES.md
│   └── RAPPORT_EXPLICATIF.md
│
├── deployment/                      # Guides de deploiement
│   ├── GUIDE_INSTALLATION_COMPLET.md
│   └── ORDRE_EXECUTION.md
│
├── diagrams/                        # Diagrammes Mermaid
│   ├── algorithmes.mmd
│   ├── architecture_globale.mmd
│   ├── kafka.mmd
│   ├── master_v2.mmd
│   ├── master_v3.mmd
│   └── nifi.mmd
│
├── incident_reports/                # Rapports d'incidents
│   ├── CHANGEMENTS_STANDARDISATION.md
│   ├── DIAGNOSTIC_ET_PLAN_ACTION.md
│   └── RAPPORT_AMELIORATION_TECHNIQUE.md
│
├── project/                         # Gestion de projet
│   ├── AI_PROMPT_SYSTEM_FOR_ARTICLE.md
│   ├── ARTICLE_OUTLINE_EN.md
│   ├── DONE.md
│   ├── MANIFEST.md
│   ├── TICKETS_TABLE.md
│   └── TODO.md
│
└── schemas/                         # Schemas JSON
    ├── command_v3.json
    ├── telemetry_v3.json
    └── telemetry_v3_complete.json
```

## Documents principaux

### Architecture
| Document | Description |
|----------|-------------|
| `01_ARCHITECTURE.md` | Vue d'ensemble du systeme |
| `architecture/nifi_architecture.md` | Pipeline NiFi detaille |
| `architecture/algorithms_detail.md` | Algorithmes A1-A11 |

### Gouvernance
| Document | Description |
|----------|-------------|
| `02_DATA_GOVERNANCE.md` | Protocole Vance complet |
| `03_DATA_CATALOG.md` | Catalogue des donnees |
| `CLICKHOUSE_COLUMN_DICTIONARY.md` | 156 colonnes |

### Deploiement
| Document | Description |
|----------|-------------|
| `QUICK_START_GUIDE.md` | Demarrage rapide |
| `deployment/GUIDE_INSTALLATION_COMPLET.md` | Installation complete |
| `deployment/ORDRE_EXECUTION.md` | Ordre des etapes |

## Diagrammes

Les diagrammes sont au format Mermaid (`.mmd`) :

```bash
# Visualiser avec mermaid-cli
mmdc -i docs/diagrams/architecture_globale.mmd -o architecture.png
```

## Schemas JSON

Schemas de validation pour NiFi :
- `telemetry_v3.json` - Format des messages IoT
- `command_v3.json` - Format des commandes actuateurs
