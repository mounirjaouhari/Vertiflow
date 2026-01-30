#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║              QUALITY CLASSIFIER TRAINING PIPELINE (TICKET-128)               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-03                                                 ║
║ Version         : 1.0.0                                                      ║
║ Author(s)       : @Mouhammed (Data Eng), @Mounir (ML Lead)                   ║
║ Reviewer(s)     : @Asama (Domain), @Imrane (MLOps)                           ║
║ Product Owner   : @MrZakaria                                                 ║
║ Classification  : Internal - Confidential                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PURPOSE                                                                     ║
║ -------                                                                      ║
║ Train and validate the RandomForest classifier powering cloud_citadel/        ║
║ nervous_system/classifier.py (A10 quality grading). The pipeline:             ║
║   • pulls labeled harvest samples (PREMIUM/STANDARD/REJECT) from ClickHouse   ║
║   • engineers agronomic features (VPD, cumulative DLI, EC stability, etc.)    ║
║   • performs class balancing + hyperparameter tuning                         ║
║   • exports joblib artifact + metrics summary for governance                  ║
║                                                                              ║
║ BUSINESS VALUE                                                               ║
║ ---------------                                                              ║
║ Ensures commercial contracts (premium basil deliveries) meet SLA by          ║
║ classifying batches early; reduces QA time & rejects.                        ║
║                                                                              ║
║ OUTPUTS                                                                      ║
║ -------                                                                      ║
║   • models/rf_quality_v1.pkl              (RandomForestClassifier)            ║
║   • models/rf_quality_v1.metrics.json     (F1, confusion matrix, drift stats) ║
║                                                                              ║
║ RUN                                                                          ║
║ ---                                                                          ║
║   $ python models/train_quality_classifier.py \                               ║
║       --clickhouse-host clickhouse --balance --class-weight                   ║
║                                                                              ║
║ TICKET / TEAM                                                                ║
║ ---------------                                                              ║
║ - Ticket: TICKET-128                                                          ║
║ - Squad : Core Data Foundation                                                ║
║ - Members: @Mouhammed (owner), @Mounir (ML), @Asama (QA rules)                ║
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
from typing import Iterable, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils import class_weight

try:  # Optional dependency for offline dev
    from clickhouse_driver import Client as ClickHouseClient
except ImportError:  # pragma: no cover
    ClickHouseClient = None  # type: ignore[misc]

LOGGER = logging.getLogger("quality.training")
logging.basicConfig(
    level=os.getenv("QUALITY_TRAINING_LOG", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

FEATURES = [
    "air_temp_internal",
    "vapor_pressure_deficit",
    "light_dli_accumulated",
    "nutrient_solution_ec",
    "days_since_planting",
]
TARGET = "quality_grade"


@dataclass
class TrainingConfig:
    clickhouse_host: Optional[str]
    clickhouse_port: int
    clickhouse_db: str
    clickhouse_user: Optional[str]
    clickhouse_password: Optional[str]
    csv_path: Optional[pathlib.Path]
    output_model: pathlib.Path
    output_metrics: pathlib.Path
    balance_data: bool
    use_class_weight: bool
    test_size: float
    random_state: int

    def safe_dict(self) -> dict[str, str]:
        return {
            "clickhouse_host": self.clickhouse_host or "(csv mode)",
            "csv_path": str(self.csv_path) if self.csv_path else "(none)",
            "balance_data": str(self.balance_data),
            "class_weight": str(self.use_class_weight),
            "output_model": str(self.output_model),
        }


# ---------------------------------------------------------------------------
# DATA EXTRACTION
# ---------------------------------------------------------------------------
def load_dataset(cfg: TrainingConfig) -> pd.DataFrame:
    if cfg.csv_path:
        LOGGER.info("Loading labeled data from CSV: %s", cfg.csv_path)
        return pd.read_csv(cfg.csv_path)
    if ClickHouseClient is None or cfg.clickhouse_host is None:
        raise RuntimeError("ClickHouse driver missing; supply --csv or install dependency")
    LOGGER.info("Querying ClickHouse for quality samples")
    client = ClickHouseClient(
        host=cfg.clickhouse_host,
        port=cfg.clickhouse_port,
        database=cfg.clickhouse_db,
        user=cfg.clickhouse_user,
        password=cfg.clickhouse_password,
    )
    query = """
        SELECT air_temp_internal,
               vapor_pressure_deficit,
               light_dli_accumulated,
               nutrient_solution_ec,
               days_since_planting,
               quality_grade
        FROM analytics.quality_training_view
        WHERE quality_grade IN ('PREMIUM','STANDARD','REJECT')
    """
    rows = client.execute(query)
    frame = pd.DataFrame(rows, columns=FEATURES + [TARGET])
    LOGGER.info("Fetched %d samples", len(frame))
    return frame


# ---------------------------------------------------------------------------
# BALANCING UTILITIES
# ---------------------------------------------------------------------------
def balance_dataset(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Applying simple upsampling to balance classes")
    max_size = df[TARGET].value_counts().max()
    balanced_frames = []
    for label, subset in df.groupby(TARGET):
        balanced_frames.append(subset.sample(max_size, replace=True, random_state=42))
    balanced = pd.concat(balanced_frames).sample(frac=1, random_state=42).reset_index(drop=True)
    LOGGER.info("Balanced dataset size: %d", len(balanced))
    return balanced


# ---------------------------------------------------------------------------
# TRAINING PIPELINE
# ---------------------------------------------------------------------------
def train(df: pd.DataFrame, cfg: TrainingConfig) -> tuple[Pipeline, dict]:
    df = df.dropna(subset=[TARGET])
    if cfg.balance_data:
        df = balance_dataset(df)

    X = df[FEATURES]
    y = df[TARGET]

    class_weights = None
    if cfg.use_class_weight:
        weights = class_weight.compute_class_weight("balanced", classes=np.unique(y), y=y)
        class_weights = dict(zip(np.unique(y), weights))
        LOGGER.info("Using class weights: %s", class_weights)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, test_size=cfg.test_size, random_state=cfg.random_state
    )

    numeric_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    preprocess = ColumnTransformer(transformers=[("num", numeric_pipeline, FEATURES)])

    classifier = RandomForestClassifier(random_state=cfg.random_state, class_weight=class_weights)

    pipe = Pipeline(steps=[("preprocess", preprocess), ("model", classifier)])
    param_grid = {
        "model__n_estimators": [200, 400],
        "model__max_depth": [8, 16, None],
        "model__min_samples_leaf": [1, 2, 4],
    }

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.random_state)
    search = GridSearchCV(
        pipe,
        param_grid,
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1,
    )
    search.fit(X_train, y_train)

    best_pipe = search.best_estimator_
    y_pred = best_pipe.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=["PREMIUM", "STANDARD", "REJECT"])
    f1_macro = f1_score(y_test, y_pred, average="macro")

    metrics = {
        "f1_macro": float(f1_macro),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "best_params": search.best_params_,
        "rows": int(len(df)),
        "class_distribution": df[TARGET].value_counts().to_dict(),
    }
    LOGGER.info("Validation F1_macro=%.3f", f1_macro)
    return best_pipe, metrics


# ---------------------------------------------------------------------------
# PERSISTENCE
# ---------------------------------------------------------------------------
def persist(model: Pipeline, metrics: dict, cfg: TrainingConfig) -> None:
    cfg.output_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, cfg.output_model)
    LOGGER.info("Saved model to %s", cfg.output_model)

    cfg.output_metrics.parent.mkdir(parents=True, exist_ok=True)
    with cfg.output_metrics.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    LOGGER.info("Saved metrics to %s", cfg.output_metrics)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train quality classifier (A10)")
    parser.add_argument("--clickhouse-host", type=str, default=os.getenv("CLICKHOUSE_HOST"))
    parser.add_argument("--clickhouse-port", type=int, default=int(os.getenv("CLICKHOUSE_PORT", "9000")))
    parser.add_argument("--clickhouse-db", type=str, default=os.getenv("CLICKHOUSE_DB", "vertiflow"))
    parser.add_argument("--clickhouse-user", type=str, default=os.getenv("CLICKHOUSE_USER"))
    parser.add_argument("--clickhouse-password", type=str, default=os.getenv("CLICKHOUSE_PASSWORD"))
    parser.add_argument("--csv", type=pathlib.Path, default=None)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("models/rf_quality_v1.pkl"))
    parser.add_argument(
        "--metrics-output",
        type=pathlib.Path,
        default=pathlib.Path("models/rf_quality_v1.metrics.json"),
    )
    parser.add_argument("--balance", action="store_true", help="Upsample classes")
    parser.add_argument("--class-weight", action="store_true", help="Enable class weights")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args(argv)


def build_config(args: argparse.Namespace) -> TrainingConfig:
    return TrainingConfig(
        clickhouse_host=args.clickhouse_host,
        clickhouse_port=args.clickhouse_port,
        clickhouse_db=args.clickhouse_db,
        clickhouse_user=args.clickhouse_user,
        clickhouse_password=args.clickhouse_password,
        csv_path=args.csv,
        output_model=args.output,
        output_metrics=args.metrics_output,
        balance_data=args.balance,
        use_class_weight=args.class_weight,
        test_size=args.test_size,
        random_state=args.random_state,
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    cfg = build_config(args)
    LOGGER.info("Training config: %s", cfg.safe_dict())
    data = load_dataset(cfg)
    model, metrics = train(data, cfg)
    persist(model, metrics, cfg)
    LOGGER.info("Quality classifier training complete")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 FOOTER                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Component        : models/train_quality_classifier.py                        ║
║ Ticket           : TICKET-128                                                ║
║ Squad            : Core Data Foundation                                      ║
║ Owner            : @Mouhammed                                                ║
║ Support          : @Mounir (ML), @Asama (QA), @Imrane (MLOps)                ║
║ Contact          : data@vertiflow.ai                                         ║
║ Runtime          : Airflow DAG `train_quality_classifier` / manual           ║
║ Dependencies     : pandas, scikit-learn, joblib, clickhouse-driver           ║
║ Last Updated     : 2026-01-03                                                ║
║ Next Review      : 2026-02-15                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
