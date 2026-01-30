# Corrections Appliquees au Pipeline NiFi VertiFlow

## Date: 2026-01-13

## Probleme Initial
Plusieurs processeurs invalides empechaient le pipeline de fonctionner a 100%:
- 37 processeurs en cours d'execution (Running)
- 6 processeurs arretes (Stopped)
- 6+ processeurs invalides (Invalid)

## Erreurs Identifiees et Corrections

### 1. GetFile - Lab Data
**Erreur**: `Input Directory` valide contre `/opt/nifi/nifi-current/exchange/lab_data` est invalide car le repertoire n'existe pas.

**Correction**: Changer le repertoire en `/opt/nifi/nifi-current/exchange/input` et utiliser un filtre de fichier `.*lab.*\.json$`.

### 2. GetFile - Datasets CSV
**Erreur**: `Input Directory` valide contre `/opt/nifi/nifi-current/exchange/datasets` est invalide.

**Correction**: Changer le repertoire en `/opt/nifi/nifi-current/exchange/input`.

### 3. GetFile - Recipes
**Erreur**: `Input Directory` valide contre `/opt/nifi/nifi-current/exchange/recipes` est invalide.

**Correction**: Changer le repertoire en `/opt/nifi/nifi-current/exchange/input` et utiliser un filtre `.*recipe.*\.json$`.

### 4. PutMongo - Plant Recipes
**Erreur**: `Upsert Condition` valide contre `{"recipe_id": "${recipe_id}"}` est invalide (format Expression Language dans JSON).

**Correction**: Changer le mode de `upsert` a `insert` et supprimer la condition d'upsert.

### 5. DLQ_Logger
**Erreur**: `Log Prefix` et `Log Level` sont invalides car `LogMessage` n'a pas ces proprietes dans NiFi 1.23.2.

**Correction**: Remplacer `LogMessage` par `LogAttribute` qui supporte ces proprietes.

### 6. B1 - LookupRecord
**Erreur**: `User-Defined Properties` est invalide car au moins une propriete user-defined est requise.

**Correction**: Ajouter la propriete `key` avec la valeur `/plant_type` pour specifier la cle de lookup MongoDB.

### 7. B2 - ExecuteScript (VPD)
**Erreur**: Le script Groovy echoue avec `GroovyRuntimeException: Ambiguous method overloading for method java.math.BigDecimal#multiply. Cannot resolve which method to invoke for [null]`.

**Cause**: L'operateur Elvis (`?:`) en Groovy peut retourner des types mixtes (BigDecimal, null) qui causent des ambiguites lors des operations mathematiques.

**Correction**:
- Ajouter l'import `import org.apache.nifi.processor.io.StreamCallback`
- Utiliser des types explicites `double` avec le suffixe `d` (ex: `25.0d`)
- Convertir explicitement les valeurs avec `((Number) value).doubleValue()`

### 8. Zone 0 - PublishKafka (Weather, NASA, AirQuality) - ERREUR TEMPORAIRE
**Erreur**: `TimeoutException: Timeout expired after 5000milliseconds while awaiting InitProducerId`

**Cause**: Kafka n'etait pas encore pret quand NiFi a essaye de se connecter.

**Solution**:
- **Attendre que Kafka soit healthy** avant de demarrer les processeurs NiFi
- Les proprietes `max.block.ms` et `Delivery Guarantee` ne sont **PAS valides** pour PublishKafka_2_6 dans NiFi 1.23.2
- La configuration par defaut (`acks: "1"`) est suffisante

## Fichiers Modifies

1. **deploy_pipeline_v2_full.py** - Script de deploiement principal
   - Corrections des chemins GetFile
   - Correction du mode PutMongo
   - Remplacement de LogMessage par LogAttribute
   - Ajout de la propriete user-defined pour LookupRecord

2. **nifi_pipeline_manager.py** - Gestionnaire de pipeline
   - Ajout de la methode `fix_invalid_processors()`
   - Integration dans `fix_pipeline()`

3. **fix_invalid_processors.py** (NOUVEAU) - Script de correction dedie
   - Corrections automatisees pour les 6 erreurs
   - Peut etre execute independamment

## Comment Executer les Corrections

### Option 1: Script dedie
```bash
python scripts/nifi_workflows/deploy/fix_invalid_processors.py
```

### Option 2: Via le gestionnaire
```bash
python scripts/nifi_workflows/deploy/nifi_pipeline_manager.py --fix
```

### Option 3: Tout faire (fix + verify)
```bash
python scripts/nifi_workflows/deploy/nifi_pipeline_manager.py --all
```

## Structure des Repertoires NiFi

Le volume Docker monte:
```
./nifi_exchange  →  /opt/nifi/nifi-current/exchange
```

Sous-repertoires disponibles:
- `/opt/nifi/nifi-current/exchange/input` - Fichiers d'entree
- `/opt/nifi/nifi-current/exchange/output` - Fichiers de sortie
- `/opt/nifi/nifi-current/exchange/datasets` - Datasets CSV/JSON
- `/opt/nifi/nifi-current/exchange/lab_data` - Donnees laboratoire
- `/opt/nifi/nifi-current/exchange/recipes` - Recettes agronomiques

## Notes Importantes

1. **Idempotence**: Les scripts de correction sont idempotents - ils peuvent etre executes plusieurs fois sans effet negatif.

2. **Compatibilite NiFi 1.23.2**: Les corrections sont specifiques a cette version de NiFi.

3. **Preservation de la structure**: Aucune modification de l'architecture du pipeline (6 zones + DLQ).
