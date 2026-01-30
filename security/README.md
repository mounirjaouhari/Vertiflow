# Security - Configuration securite

Ce dossier contient les configurations de securite pour VertiFlow.

## Structure

```
security/
├── generate_certs.sh                # Generation certificats TLS
├── clickhouse/
│   ├── config.xml                   # Config securisee ClickHouse
│   └── users.xml                    # Utilisateurs et roles
├── kafka/
│   ├── kafka_jaas.conf              # JAAS pour Kafka
│   └── zookeeper_jaas.conf          # JAAS pour Zookeeper
├── mosquitto/
│   ├── acl                          # Access Control List MQTT
│   ├── generate_passwd.sh           # Generation mots de passe
│   └── mosquitto-secure.conf        # Config securisee
└── vault/
    └── secrets-template.env         # Template secrets Vault
```

## Certificats TLS

### Generation
```bash
./security/generate_certs.sh

# Genere:
# - ca.crt / ca.key (Autorite de certification)
# - server.crt / server.key (Certificat serveur)
# - client.crt / client.key (Certificat client)
```

### Utilisation
```yaml
# docker-compose.secure.yml
services:
  clickhouse:
    volumes:
      - ./security/certs:/etc/clickhouse-server/certs
```

## ClickHouse

### Utilisateurs
```xml
<!-- users.xml -->
<users>
  <vertiflow_app>
    <password_sha256_hex>...</password_sha256_hex>
    <access_management>0</access_management>
    <databases>
      <database>vertiflow</database>
    </databases>
  </vertiflow_app>
</users>
```

### Roles
- `vertiflow_admin` - Administration complete
- `vertiflow_app` - Lecture/ecriture application
- `vertiflow_readonly` - Lecture seule (dashboards)

## Kafka

### SASL/SCRAM
```properties
# kafka_jaas.conf
KafkaServer {
  org.apache.kafka.common.security.scram.ScramLoginModule required
  username="admin"
  password="admin-secret";
};
```

## Mosquitto MQTT

### ACL
```
# acl
user vertiflow_sensors
topic write vertiflow/telemetry/#

user vertiflow_app
topic read vertiflow/telemetry/#
topic write vertiflow/commands/#
```

### Mots de passe
```bash
./security/mosquitto/generate_passwd.sh vertiflow_sensors
# Ajoute l'utilisateur au fichier passwords
```

## Vault (prevu)

### Secrets geres
```bash
# secrets-template.env
CLICKHOUSE_PASSWORD=vault:secret/data/vertiflow/clickhouse#password
KAFKA_PASSWORD=vault:secret/data/vertiflow/kafka#password
MQTT_PASSWORD=vault:secret/data/vertiflow/mqtt#password
```

## Bonnes pratiques

1. **Ne jamais committer** de secrets dans Git
2. Utiliser `.env.example` comme template
3. Rotation des certificats tous les 90 jours
4. Audit des acces regulier
