#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║                   ORACLE YIELD MODEL TRAINING (TICKET-127)                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-03                                                 ║
║ Version         : 1.0.0                                                      ║
║ Author(s)       : @Mounir (ML Lead), @Mouhammed (Data Eng)                   ║
║ Reviewer(s)     : @Imrane (MLOps)                                            ║
║ Product Owner   : @MrZakaria                                                 ║
║ Classification  : Internal - Confidential                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PURPOSE                                                                     ║
║ -------                                                                      ║
║ Train and register the RandomForest-based Oracle yield predictor referenced  ║
║ by cloud_citadel/nervous_system/oracle.py. Script handles:                   ║
║   1. Feature extraction from ClickHouse or CSV fallback.                     ║
║   2. Pre-processing pipeline (impute + scale).                               ║
║   3. Hyperparameter sweep (grid search) with validation metrics.             ║
║   4. Model persistence to models/oracle_rf.pkl + checksum logging.           ║
║   5. Metadata emission (metrics.json) for governance.                        ║
║                                                                              ║
║ BUSINESS IMPACT                                                              ║
║ ----------------                                                              ║
║ Ensures agronomists receive trustworthy yield forecasts powering production  ║
║ planning, harvest scheduling, and revenue projections.                       ║
║                                                                              ║
║ EXECUTION                                                                    ║
║ ---------                                                                    ║
║ Run locally or inside the ML Docker image:                                   ║
║   $ poetry run python models/train_oracle_model.py \                         ║
║       --clickhouse-host clickhouse \                                        ║
║       --start '2025-11-01' --end '2025-12-31'                                ║
║                                                                              ║
║ OUTPUTS                                                                      ║
║ -------                                                                      ║
║   • models/oracle_rf.pkl                (joblib serialized RandomForest)      ║
║   • models/oracle_rf.metrics.json       (R², RMSE, feature importances)       ║
║   • stdout logs suitable for CI/CD pipelines                                 ║
║                                                                              ║
║ TICKET / TEAM                                                                ║
║ ---------------                                                              ║
║ - Ticket: TICKET-127                                                          ║
║ - Squad : Core Data Foundation                                                ║
║ - Members: @Mounir (owner), @Mouhammed (data), @Imrane (ops)                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import sys
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from clickhouse_driver import Client as ClickHouseClient
except ImportError:  # pragma: no cover - optional dependency
    ClickHouseClient = None  # type: ignore[misc]

LOGGER = logging.getLogger("oracle.training")
logging.basicConfig(
    level=os.getenv("ORACLE_TRAINING_LOG", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

FEATURES = [
    "temp_mean_24h",
    "par_mean_24h",
    "humidity_mean_24h",
    "co2_mean_24h",
    "temp_stddev_24h",
]
TARGET = "yield_g"


@dataclass
class TrainingConfig:
    clickhouse_host: Optional[str]
    clickhouse_port: int
    clickhouse_db: str
    clickhouse_user: Optional[str]
    clickhouse_password: Optional[str]
    csv_path: Optional[pathlib.Path]
    start_date: Optional[date]
    end_date: Optional[date]
    output_model: pathlib.Path
    output_metrics: pathlib.Path
    test_size: float
    random_state: int
    n_jobs: int

    def to_safe_dict(self) -> dict[str, str]:
        return {
            "clickhouse_host": self.clickhouse_host or "(csv mode)",
            "clickhouse_db": self.clickhouse_db,
            "csv_path": str(self.csv_path) if self.csv_path else "(none)",
            "start_date": str(self.start_date) if self.start_date else "(min)",
            "end_date": str(self.end_date) if self.end_date else "(max)",
            "output_model": str(self.output_model),
            "test_size": str(self.test_size),
        }


# ---------------------------------------------------------------------------
# DATA EXTRACTION
# ---------------------------------------------------------------------------
def load_dataset(cfg: TrainingConfig) -> pd.DataFrame:
    if cfg.csv_path:
        LOGGER.info("Loading dataset from CSV: %s", cfg.csv_path)
        return pd.read_csv(cfg.csv_path)
    if ClickHouseClient is None or cfg.clickhouse_host is None:
        raise RuntimeError("ClickHouse driver unavailable; provide --csv or install clickhouse-driver")
    LOGGER.info("Querying ClickHouse host=%s db=%s", cfg.clickhouse_host, cfg.clickhouse_db)
    client = ClickHouseClient(
        host=cfg.clickhouse_host,
        port=cfg.clickhouse_port,
        user=cfg.clickhouse_user,
        password=cfg.clickhouse_password,
        database=cfg.clickhouse_db,
    )
    sql = [
        "SELECT * FROM analytics.oracle_training_view WHERE 1=1",
    ]
    params = {}
    if cfg.start_date:
        sql.append("AND event_date >= %(start_date)s")
        params["start_date"] = cfg.start_date
    if cfg.end_date:
        sql.append("AND event_date <= %(end_date)s")
        params["end_date"] = cfg.end_date
    query = " ".join(sql)
    data = client.execute(query, params, with_column_types=True)
    columns = [col[0] for col in data[1]] if isinstance(data, tuple) else []
    if isinstance(data, tuple):
        rows = data[0]
    else:
        rows = data
        columns = ["temp_mean_24h", "par_mean_24h", "humidity_mean_24h", "co2_mean_24h", "temp_stddev_24h", "yield_g"]
    frame = pd.DataFrame(rows, columns=columns)
    LOGGER.info("Loaded %d rows from ClickHouse", len(frame))
    return frame


# ---------------------------------------------------------------------------
# TRAINING ROUTINE
# ---------------------------------------------------------------------------
def train_model(df: pd.DataFrame, cfg: TrainingConfig) -> tuple[Pipeline, dict]:
    LOGGER.info("Preparing dataset; checking required columns")
    missing_cols = [col for col in FEATURES + [TARGET] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing columns: {missing_cols}")

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=cfg.test_size, random_state=cfg.random_state
    )

    numeric_transformer = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    preprocessor = ColumnTransformer(transformers=[("num", numeric_transformer, FEATURES)])

    rf = RandomForestRegressor(random_state=cfg.random_state)
    pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", rf)])

    param_grid = {
        "model__n_estimators": [200, 400],
        "model__max_depth": [10, 20, None],
        "model__min_samples_leaf": [1, 3, 5],
    }

    LOGGER.info("Launching GridSearch: %d combinations", len(param_grid["model__n_estimators"]) * len(param_grid["model__max_depth"]) * len(param_grid["model__min_samples_leaf"]))
    search = GridSearchCV(
        pipe,
        param_grid,
        cv=3,
        scoring="neg_root_mean_squared_error",
        n_jobs=cfg.n_jobs,
        verbose=1,
    )
    search.fit(X_train, y_train)

    LOGGER.info("Best params: %s", search.best_params_)
    best_pipe = search.best_estimator_
    y_pred = best_pipe.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    r2 = r2_score(y_test, y_pred)

    importances = (
        best_pipe.named_steps["model"].feature_importances_.tolist()  # type: ignore[attr-defined]
    )
    metrics = {
        "rmse_g": float(rmse),
        "r2_score": float(r2),
        "rows": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "feature_importances": dict(zip(FEATURES, importances)),
        "grid_search_params": search.best_params_,
        "timestamp": datetime.utcnow().isoformat(),
    }
    LOGGER.info("Validation RMSE=%.3f g, R²=%.3f", rmse, r2)
    return best_pipe, metrics


# ---------------------------------------------------------------------------
# SERIALIZATION
# ---------------------------------------------------------------------------
def persist_outputs(model: Pipeline, metrics: dict, cfg: TrainingConfig) -> None:
    cfg.output_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, cfg.output_model)
    LOGGER.info("Model artifact saved to %s", cfg.output_model)

    cfg.output_metrics.parent.mkdir(parents=True, exist_ok=True)
    with cfg.output_metrics.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    LOGGER.info("Metrics saved to %s", cfg.output_metrics)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Oracle RandomForest model")
    parser.add_argument("--clickhouse-host", type=str, default=os.getenv("CLICKHOUSE_HOST"))
    parser.add_argument("--clickhouse-port", type=int, default=int(os.getenv("CLICKHOUSE_PORT", "9000")))
    parser.add_argument("--clickhouse-db", type=str, default=os.getenv("CLICKHOUSE_DB", "vertiflow"))
    parser.add_argument("--clickhouse-user", type=str, default=os.getenv("CLICKHOUSE_USER"))
    parser.add_argument("--clickhouse-password", type=str, default=os.getenv("CLICKHOUSE_PASSWORD"))
    parser.add_argument("--csv", type=pathlib.Path, default=None, help="Optional CSV fallback")
    parser.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("models/oracle_rf.pkl"))
    parser.add_argument(
        "--metrics-output",
        type=pathlib.Path,
        default=pathlib.Path("models/oracle_rf.metrics.json"),
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    return parser.parse_args(argv)


def build_config(args: argparse.Namespace) -> TrainingConfig:
    start_dt = date.fromisoformat(args.start) if args.start else None
    end_dt = date.fromisoformat(args.end) if args.end else None
    return TrainingConfig(
        clickhouse_host=args.clickhouse_host,
        clickhouse_port=args.clickhouse_port,
        clickhouse_db=args.clickhouse_db,
        clickhouse_user=args.clickhouse_user,
        clickhouse_password=args.clickhouse_password,
        csv_path=args.csv,
        start_date=start_dt,
        end_date=end_dt,
        output_model=args.output,
        output_metrics=args.metrics_output,
        test_size=args.test_size,
        random_state=args.random_state,
        n_jobs=args.n_jobs,
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    cfg = build_config(args)
    LOGGER.info("Training config: %s", cfg.to_safe_dict())

    data = load_dataset(cfg)
    model, metrics = train_model(data, cfg)
    persist_outputs(model, metrics, cfg)
    LOGGER.info("Training complete")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 FOOTER                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Component        : models/train_oracle_model.py                              ║
║ Ticket           : TICKET-127                                                ║
║ Squad            : Core Data Foundation                                      ║
║ Owner            : @Mounir                                                   ║
║ Support          : @Mouhammed (Data), @Imrane (MLOps)                        ║
║ Contact          : data@vertiflow.ai                                         ║
║ Runtime          : On-demand / Airflow task `train_oracle_rf`                ║
║ Dependencies     : pandas, scikit-learn, joblib, clickhouse-driver (optional)║
║ Last Updated     : 2026-01-03                                                ║
║ Next Review      : 2026-02-15                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
