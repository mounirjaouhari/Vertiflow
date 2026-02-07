# GitHub Codespaces - VertiFlow

Developpement a distance sur Codespaces avec acces aux services depuis votre laptop.

## Demarrage Rapide

### 1. Creer le Codespace
1. Allez sur https://github.com/mounirjaouhari/VertiflowMJ
2. Cliquez sur **Code** > **Codespaces** > **Create codespace on main**
3. Attendez la construction (~5 min le premier build)

### 2. Lancer l'infrastructure (dans le terminal Codespaces)
```bash
# Demarrer tous les services Docker
docker compose up -d

# Verifier que les services sont up
docker compose ps

# Initialiser les bases de donnees et Kafka
python infrastructure/init_infrastructure.py
```

### 3. Lancer le pipeline de donnees
```bash
# Option A: Lancer tout en une commande
python scripts/start_vertiflow.py

# Option B: Lancer etape par etape
python scripts/simulators/iot_sensor_simulator.py &   # Simulateur IoT
python scripts/etl/transform_telemetry.py &           # ETL Kafka->ClickHouse
```

---

## Acces aux Services depuis votre Laptop

Une fois les services lances, Codespaces expose automatiquement les ports.
Vous les verrez dans l'onglet **PORTS** de VS Code.

### Ports exposes

| Service | Port | URL Codespaces | Usage |
|---------|------|----------------|-------|
| **NiFi UI** | 8443 | `https://<codespace>-8443.app.github.dev` | Interface web pipeline |
| **ClickHouse HTTP** | 8123 | `https://<codespace>-8123.app.github.dev` | API REST / Play UI |
| **ClickHouse Native** | 9000 | Forwarde localement | DataGrip (TCP) |
| **MongoDB** | 27017 | Forwarde localement | DataGrip / Compass |
| **Kafka** | 9092 | Forwarde localement | Kafka clients |
| **MQTT Mosquitto** | 1883 | Forwarde localement | MQTT clients |
| **Grafana** | 3000 | `https://<codespace>-3000.app.github.dev` | Dashboards |

### Configuration DataGrip (depuis votre laptop)

#### Option 1: Port Forwarding Local (Recommande)

Dans VS Code Codespaces, cliquez sur l'onglet **PORTS**, puis:
1. Trouvez le port (ex: 9000 pour ClickHouse)
2. Clic droit > **Forward Port**
3. Choisissez **Local Address**: `localhost:9000`

Ensuite dans DataGrip:
- **Host**: `localhost`
- **Port**: `9000` (ou le port forwarde)
- **User**: `default`
- **Password**: `default`
- **Database**: `vertiflow`

#### Option 2: URL Publique (pour HTTP uniquement)

Pour ClickHouse HTTP (port 8123):
1. Dans l'onglet PORTS, clic droit sur 8123
2. Choisissez **Port Visibility** > **Public**
3. Copiez l'URL (ex: `https://xxx-8123.app.github.dev`)

Dans DataGrip, creez une connexion HTTP:
- **URL**: `https://xxx-8123.app.github.dev`
- **User**: `default`
- **Password**: `default`

---

## Acces NiFi UI

1. Dans l'onglet **PORTS** de Codespaces, trouvez le port **8443**
2. Clic droit > **Open in Browser**
3. Acceptez le certificat auto-signe
4. Connectez-vous:
   - **Username**: `admin`
   - **Password**: `ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB`

---

## Credentials Services

| Service | User | Password |
|---------|------|----------|
| NiFi | admin | ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB |
| ClickHouse | default | default |
| MongoDB | (no auth) | - |
| Kafka | (no auth) | - |
| Mosquitto | (no auth) | - |

---

## Verification des Donnees

### Dans ClickHouse (via DataGrip ou Play UI)
```sql
-- Nombre de lignes de telemetrie
SELECT count() FROM vertiflow.basil_ultimate_realtime;

-- Derniers enregistrements
SELECT * FROM vertiflow.basil_ultimate_realtime
ORDER BY timestamp DESC LIMIT 10;

-- Stats par rack
SELECT rack_id, count() as nb, avg(air_temp_internal) as temp_avg
FROM vertiflow.basil_ultimate_realtime
GROUP BY rack_id;
```

### Dans MongoDB (via DataGrip ou Compass)
```javascript
// Recettes de culture
db.plant_recipes.find()

// Predictions de qualite
db.quality_predictions.find().sort({prediction_date: -1}).limit(5)
```

---

## Commandes Utiles

```bash
# Voir les logs des services
docker compose logs -f kafka
docker compose logs -f clickhouse
docker compose logs -f nifi

# Redemarrer un service
docker compose restart clickhouse

# Arreter tout
docker compose down

# Tout nettoyer (volumes inclus)
docker compose down -v
```

---

## Troubleshooting

### Les ports ne sont pas visibles
- Verifiez que `docker compose up -d` a bien demarre les services
- Attendez 30-60 secondes que les healthchecks passent
- Rafraichissez l'onglet PORTS

### DataGrip ne peut pas se connecter
1. Verifiez que le port est bien forwarde (onglet PORTS)
2. Pour les ports TCP (9000, 27017), utilisez le forwarding local
3. Pour HTTP (8123), vous pouvez utiliser l'URL publique

### NiFi affiche une erreur de certificat
- C'est normal, le certificat est auto-signe
- Cliquez sur "Avance" > "Continuer vers le site"
