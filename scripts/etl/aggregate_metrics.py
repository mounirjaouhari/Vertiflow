#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║                DAILY METRICS AGGREGATION PIPELINE (TICKET-125)               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-03                                                 ║
║ Version         : 1.0.0                                                      ║
║ Author(s)       : @Mouhammed (Data Engineering Lead)                         ║
║ Reviewer(s)     : @Imrane (DevOps), @MrZakaria (Finance)                     ║
║ Product Owner   : @Mounir                                                    ║
║ Classification  : Internal - Confidential                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PURPOSE                                                                     ║
║ -------                                                                      ║
║ Batch job that computes daily KPIs for dashboards from ClickHouse tables:    ║
║   - Operational telemetry summaries (temperature, humidity, CO₂, VPD).       ║
║   - Agronomic indicators (growth score, biomass gain, disease risk proxy).   ║
║   - Business KPIs (revenue, COGS, gross/EBITDA margin, yield).               ║
║ Results are written into curated tables consumed by Grafana & ML pipelines.  ║
║                                                                              ║
║ KEY OUTPUT TABLES                                                            ║
║ ------------------                                                           ║
║ 1. analytics.daily_environment_summary                                       ║
║ 2. analytics.daily_growth_metrics                                            ║
║ 3. analytics.daily_financial_kpis                                            ║
║                                                                              ║
║ TICKET / TEAM                                                                ║
║ ---------------                                                              ║
║ - Ticket: TICKET-125                                                          ║
║ - Squad : Core Data Foundation                                                ║
║ - Members: @Mouhammed (owner), @Imrane (ops), @MrZakaria (finance QA)         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Optional

import requests

LOGGER = logging.getLogger("metrics.aggregator")
logging.basicConfig(
    level=os.getenv("AGGREGATE_METRICS_LOG", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@dataclass(frozen=True)
class AggregationConfig:
    clickhouse_url: str = os.getenv("CLICKHOUSE_URL", "http://clickhouse:8123")
    clickhouse_user: Optional[str] = os.getenv("CLICKHOUSE_USER")
    clickhouse_password: Optional[str] = os.getenv("CLICKHOUSE_PASSWORD")
    days_back: int = int(os.getenv("AGGREGATE_DAYS_BACK", "1"))
    dry_run: bool = os.getenv("AGGREGATE_DRY_RUN", "false").lower() == "true"

    def date_window(self) -> tuple[date, date]:
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=self.days_back - 1)
        return start, end


class ClickHouseClient:
    def __init__(self, config: AggregationConfig) -> None:
        self.url = config.clickhouse_url.rstrip("/")
        self.auth = None
        if config.clickhouse_user and config.clickhouse_password:
            self.auth = (config.clickhouse_user, config.clickhouse_password)

    def execute(self, statement: str) -> requests.Response:
        response = requests.post(f"{self.url}/", data=statement.encode("utf-8"), auth=self.auth, timeout=25)
        response.raise_for_status()
        return response


AGG_ENVIRONMENT = """
INSERT INTO analytics.daily_environment_summary
SELECT
    toDate(event_ts) AS metric_date,
    facility_id,
    AVG(metric__temperature_c) AS avg_temperature_c,
    MAX(metric__temperature_c) AS max_temperature_c,
    MIN(metric__temperature_c) AS min_temperature_c,
    AVG(metric__humidity_pct) AS avg_humidity_pct,
    AVG(metric__vpd_kpa) AS avg_vpd_kpa,
    AVG(metric__co2_ppm) AS avg_co2_ppm,
    AVG(metric__growth_score) AS avg_growth_score,
    COUNT() AS sample_count
FROM telemetry_enriched
WHERE event_ts >= '{start}' AND event_ts < addDays('{end}', 1)
GROUP BY metric_date, facility_id
"""

AGG_GROWTH = """
INSERT INTO analytics.daily_growth_metrics
SELECT
    toDate(event_ts) AS metric_date,
    facility_id,
    zone_id,
    AVG(metric__growth_score) AS avg_growth_score,
    AVG(metric__light_ppfd) AS avg_light_ppfd,
    quantileExact(0.95)(metric__growth_score) AS p95_growth_score,
    quantileExact(0.05)(metric__growth_score) AS p05_growth_score,
    anyHeavy(cultivar) AS dominant_cultivar,
    COUNT() AS observations
FROM telemetry_enriched
WHERE event_ts >= '{start}' AND event_ts < addDays('{end}', 1)
GROUP BY metric_date, facility_id, zone_id
"""

AGG_FINANCIAL = """
INSERT INTO analytics.daily_financial_kpis
SELECT
    sale_date,
    SUM(revenue_usd) AS revenue_usd,
    SUM(cogs_usd) AS cogs_usd,
    SUM(gross_margin_usd) AS gross_margin_usd,
    SUM(ebitda_usd) AS ebitda_usd,
    AVG(yield_kg_m2_year) AS yield_kg_m2_year,
    AVG(cost_per_kg_usd) AS cost_per_kg_usd,
    SUM(plants_harvested) AS plants_harvested
FROM financial.daily_summary
WHERE sale_date >= '{start}' AND sale_date <= '{end}'
GROUP BY sale_date
"""


class MetricsAggregator:
    def __init__(self, config: AggregationConfig) -> None:
        self.config = config
        self.client = ClickHouseClient(config)
        self.start_date, self.end_date = config.date_window()

    def run(self) -> None:
        LOGGER.info("Aggregating metrics for window %s → %s", self.start_date, self.end_date)
        statements = [
            ("environment", AGG_ENVIRONMENT.format(start=self.start_date, end=self.end_date)),
            ("growth", AGG_GROWTH.format(start=self.start_date, end=self.end_date)),
            ("financial", AGG_FINANCIAL.format(start=self.start_date, end=self.end_date)),
        ]
        for name, stmt in statements:
            if self.config.dry_run:
                LOGGER.info("[dry-run] Would execute %s aggregation", name)
                continue
            LOGGER.info("Executing %s aggregation", name)
            self.client.execute(stmt)
        LOGGER.info("Daily aggregations complete")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VertiFlow daily metrics aggregator")
    parser.add_argument("--days", type=int, default=int(os.getenv("AGGREGATE_DAYS_BACK", "1")), help="Days back")
    parser.add_argument("--dry-run", action="store_true", help="Log statements without execution")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    config = AggregationConfig(days_back=args.days, dry_run=args.dry_run)
    aggregator = MetricsAggregator(config)
    aggregator.run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 FOOTER                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Component        : scripts/etl/aggregate_metrics.py                          ║
║ Ticket           : TICKET-125                                                ║
║ Squad            : Core Data Foundation                                      ║
║ Owner            : @Mouhammed                                                ║
║ Support          : @Imrane (DevOps), @MrZakaria (Finance), @Mounir (Arch)    ║
║ Contact          : data@vertiflow.ai                                         ║
║ Runtime          : Cron 01:15 UTC / Airflow DAG `daily_metrics`               ║
║ Dependencies     : ClickHouse HTTP API, requests                             ║
║ Exit Codes       : 0 success, raises on ClickHouse error                     ║
║ Last Updated     : 2026-01-03                                                ║
║ Next Review      : 2026-02-15                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
