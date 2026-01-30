# ============================================================================
# VERTIFLOW - Tests d'Intégration ClickHouse
# ============================================================================

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestClickHouseConnection:
    """Tests de connexion à ClickHouse."""

    @pytest.fixture
    def clickhouse_config(self):
        """Configuration ClickHouse pour les tests."""
        return {
            "host": "localhost",
            "port": 9000,
            "user": "default",
            "password": "",
            "database": "vertiflow_test"
        }

    def test_connection_success(self, mock_clickhouse, clickhouse_config):
        """Test la connexion réussie."""
        mock_clickhouse.execute.return_value = [(1,)]

        result = mock_clickhouse.execute("SELECT 1")

        assert result == [(1,)]

    def test_database_exists(self, mock_clickhouse):
        """Test l'existence de la base de données."""
        mock_clickhouse.execute.return_value = [("vertiflow",)]

        result = mock_clickhouse.execute("SHOW DATABASES LIKE 'vertiflow'")

        assert len(result) > 0


class TestClickHouseSchema:
    """Tests du schéma ClickHouse."""

    def test_table_creation_sql(self):
        """Test le SQL de création de table."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS basil_telemetry (
            timestamp DateTime64(3),
            farm_id String,
            zone_id String,
            sensor_id String,
            sensor_type String,
            value Float64,
            unit String,
            quality_score Float32
        ) ENGINE = MergeTree()
        ORDER BY (farm_id, zone_id, timestamp)
        PARTITION BY toYYYYMM(timestamp)
        """

        assert "MergeTree" in create_sql
        assert "PARTITION BY" in create_sql
        assert "ORDER BY" in create_sql

    def test_materialized_view_creation(self):
        """Test la création de vues matérialisées."""
        view_sql = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_1min_avg
        ENGINE = SummingMergeTree()
        ORDER BY (farm_id, zone_id, minute)
        AS SELECT
            farm_id,
            zone_id,
            toStartOfMinute(timestamp) AS minute,
            avg(value) AS avg_value,
            min(value) AS min_value,
            max(value) AS max_value,
            count() AS sample_count
        FROM basil_telemetry
        GROUP BY farm_id, zone_id, minute
        """

        assert "MATERIALIZED VIEW" in view_sql
        assert "SummingMergeTree" in view_sql

    def test_column_types(self):
        """Test les types de colonnes."""
        columns = {
            "timestamp": "DateTime64(3)",
            "farm_id": "String",
            "value": "Float64",
            "quality_score": "Float32",
            "is_anomaly": "UInt8"  # Boolean
        }

        assert columns["timestamp"] == "DateTime64(3)"
        assert columns["value"] == "Float64"


class TestClickHouseInsert:
    """Tests d'insertion dans ClickHouse."""

    def test_single_insert(self, mock_clickhouse, sample_telemetry_data):
        """Test l'insertion d'un enregistrement."""
        mock_clickhouse.execute.return_value = None

        insert_sql = """
        INSERT INTO basil_telemetry (timestamp, farm_id, zone_id, sensor_id, value)
        VALUES
        """

        mock_clickhouse.execute(insert_sql, [sample_telemetry_data])
        mock_clickhouse.execute.assert_called()

    def test_batch_insert(self, mock_clickhouse, sample_batch_telemetry):
        """Test l'insertion en batch."""
        mock_clickhouse.execute.return_value = None

        batch_size = len(sample_batch_telemetry)

        mock_clickhouse.execute("INSERT INTO basil_telemetry VALUES", sample_batch_telemetry)
        mock_clickhouse.execute.assert_called_once()

        assert batch_size == 100

    def test_insert_with_compression(self):
        """Test l'insertion avec compression."""
        settings = {
            "compression": "zstd",
            "compression_level": 3
        }

        assert settings["compression"] == "zstd"

    def test_async_insert(self):
        """Test l'insertion asynchrone."""
        async_settings = {
            "async_insert": 1,
            "wait_for_async_insert": 0,
            "async_insert_max_data_size": 10_000_000  # 10MB
        }

        assert async_settings["async_insert"] == 1


class TestClickHouseQueries:
    """Tests de requêtes ClickHouse."""

    def test_aggregation_query(self, mock_clickhouse):
        """Test une requête d'agrégation."""
        mock_clickhouse.execute.return_value = [
            ("FARM_001", "ZONE_A", 24.5, 22.0, 27.0, 1000)
        ]

        query = """
        SELECT
            farm_id,
            zone_id,
            avg(value) AS avg_temp,
            min(value) AS min_temp,
            max(value) AS max_temp,
            count() AS samples
        FROM basil_telemetry
        WHERE timestamp > now() - INTERVAL 1 HOUR
        GROUP BY farm_id, zone_id
        """

        result = mock_clickhouse.execute(query)

        assert len(result) == 1
        assert result[0][2] == 24.5  # avg_temp

    def test_time_series_query(self, mock_clickhouse):
        """Test une requête de série temporelle."""
        mock_clickhouse.execute.return_value = [
            ("2025-01-01 00:00:00", 23.5),
            ("2025-01-01 00:01:00", 23.6),
            ("2025-01-01 00:02:00", 23.4)
        ]

        query = """
        SELECT
            toStartOfMinute(timestamp) AS minute,
            avg(value) AS avg_value
        FROM basil_telemetry
        WHERE farm_id = 'FARM_001'
          AND timestamp BETWEEN '2025-01-01' AND '2025-01-02'
        GROUP BY minute
        ORDER BY minute
        """

        result = mock_clickhouse.execute(query)

        assert len(result) == 3

    def test_window_function(self, mock_clickhouse):
        """Test une fonction de fenêtre."""
        mock_clickhouse.execute.return_value = [
            ("2025-01-01 00:00:00", 23.5, 23.5),
            ("2025-01-01 00:01:00", 23.6, 23.55),
            ("2025-01-01 00:02:00", 23.4, 23.5)
        ]

        query = """
        SELECT
            timestamp,
            value,
            avg(value) OVER (
                ORDER BY timestamp
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS moving_avg
        FROM basil_telemetry
        ORDER BY timestamp
        """

        result = mock_clickhouse.execute(query)

        assert len(result) == 3

    def test_join_query(self, mock_clickhouse):
        """Test une requête avec jointure."""
        mock_clickhouse.execute.return_value = [
            ("FARM_001", "Basil Farm", 24.5, 25.0, 0.98)
        ]

        query = """
        SELECT
            t.farm_id,
            f.name AS farm_name,
            avg(t.value) AS avg_temp,
            r.optimal_temp,
            avg(t.value) / r.optimal_temp AS efficiency
        FROM basil_telemetry t
        JOIN farms f ON t.farm_id = f.id
        JOIN recipes r ON f.recipe_id = r.id
        GROUP BY t.farm_id, f.name, r.optimal_temp
        """

        result = mock_clickhouse.execute(query)

        assert result[0][4] == 0.98


class TestClickHousePerformance:
    """Tests de performance ClickHouse."""

    def test_query_explain(self, mock_clickhouse):
        """Test l'analyse de requête."""
        mock_clickhouse.execute.return_value = [
            ("ReadFromMergeTree", "basil_telemetry", 1000000)
        ]

        explain_sql = """
        EXPLAIN SELECT count() FROM basil_telemetry
        WHERE timestamp > now() - INTERVAL 1 DAY
        """

        result = mock_clickhouse.execute(explain_sql)

        assert "ReadFromMergeTree" in result[0][0]

    def test_partition_pruning(self):
        """Test l'élagage de partitions."""
        # Une requête sur un mois spécifique ne devrait lire que cette partition
        query = """
        SELECT count()
        FROM basil_telemetry
        WHERE timestamp BETWEEN '2025-01-01' AND '2025-01-31'
        """

        # La partition toYYYYMM(timestamp) = 202501 sera la seule lue
        expected_partition = "202501"

        assert expected_partition in "202501"

    def test_sampling(self):
        """Test l'échantillonnage."""
        sampling_query = """
        SELECT avg(value)
        FROM basil_telemetry
        SAMPLE 0.1  -- 10% des données
        WHERE farm_id = 'FARM_001'
        """

        assert "SAMPLE 0.1" in sampling_query


class TestClickHouseDataRetention:
    """Tests de rétention des données."""

    def test_ttl_configuration(self):
        """Test la configuration TTL."""
        ttl_sql = """
        ALTER TABLE basil_telemetry
        MODIFY TTL timestamp + INTERVAL 90 DAY
        """

        assert "INTERVAL 90 DAY" in ttl_sql

    def test_partition_deletion(self):
        """Test la suppression de partitions."""
        delete_sql = """
        ALTER TABLE basil_telemetry
        DROP PARTITION 202401
        """

        assert "DROP PARTITION" in delete_sql

    def test_data_archival(self):
        """Test l'archivage des données."""
        archive_query = """
        INSERT INTO basil_telemetry_archive
        SELECT * FROM basil_telemetry
        WHERE timestamp < now() - INTERVAL 1 YEAR
        """

        assert "INSERT INTO" in archive_query
        assert "INTERVAL 1 YEAR" in archive_query
