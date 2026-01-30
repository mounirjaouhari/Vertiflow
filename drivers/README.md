# Drivers - Drivers JDBC

Ce dossier contient les drivers JDBC pour les connexions bases de donnees.

## Structure

```
drivers/
├── clickhouse-jdbc-*.jar            # Driver JDBC ClickHouse
├── clickhouse-client-*.jar          # Client natif ClickHouse
├── clickhouse-data-*.jar            # Serialisation donnees
├── clickhouse-http-client-*.jar     # Client HTTP
├── guava-*.jar                      # Dependance Google
├── httpclient5-*.jar                # Client HTTP Apache
├── lz4-java-*.jar                   # Compression LZ4
└── slf4j-api-*.jar                  # Logging SLF4J
```

## Drivers principaux

### ClickHouse JDBC
| Fichier | Version | Usage |
|---------|---------|-------|
| `clickhouse-jdbc-0.6.0-all.jar` | 0.6.0 | Driver complet (tout-en-un) |
| `clickhouse-jdbc-0.9.3.jar` | 0.9.3 | Driver leger |

### Dependances
| Fichier | Usage |
|---------|-------|
| `guava-33.4.6-jre.jar` | Collections Google |
| `lz4-java-1.8.0.jar` | Compression |
| `commons-compress-1.27.1.jar` | Compression |

## Utilisation

### Power BI
1. Copier `clickhouse-jdbc-0.6.0-all.jar` dans le dossier drivers Power BI
2. Configurer la connexion JDBC :
   ```
   jdbc:clickhouse://localhost:8123/vertiflow
   ```

### Java
```java
Class.forName("com.clickhouse.jdbc.ClickHouseDriver");
Connection conn = DriverManager.getConnection(
    "jdbc:clickhouse://localhost:8123/vertiflow",
    "default", ""
);
```

### NiFi
1. Ajouter les JARs au classpath NiFi
2. Configurer un DBCPConnectionPool :
   - Driver Class: `com.clickhouse.jdbc.ClickHouseDriver`
   - URL: `jdbc:clickhouse://clickhouse:8123/vertiflow`
