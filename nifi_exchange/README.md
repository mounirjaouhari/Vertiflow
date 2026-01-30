# NiFi Exchange - Repertoire d'echange NiFi

Ce dossier est utilise par Apache NiFi pour l'echange de fichiers.

## Structure

```
nifi_exchange/
├── input/                           # Fichiers entrants
│   ├── external/                    # Donnees externes
│   ├── telemetry/                   # Donnees capteurs
│   └── commands/                    # Commandes
├── output/                          # Fichiers sortants
│   ├── processed/                   # Donnees traitees
│   └── archive/                     # Archives
└── error/                           # Fichiers en erreur (DLQ)
```

## Utilisation

### GetFile Processor
NiFi surveille `input/` pour les nouveaux fichiers :
```
Input Directory: /nifi_exchange/input/telemetry
File Filter: *.json
```

### PutFile Processor
NiFi ecrit dans `output/` :
```
Output Directory: /nifi_exchange/output/processed
```

### Dead Letter Queue
Fichiers invalides dans `error/` :
```
Failure Directory: /nifi_exchange/error
```

## Permissions

```bash
# S'assurer que NiFi peut lire/ecrire
chmod -R 777 nifi_exchange/
```

## Nettoyage

Les fichiers sont archives apres traitement.
Nettoyage automatique des archives > 7 jours.
