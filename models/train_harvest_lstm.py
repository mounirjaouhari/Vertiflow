#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM                              ║
║          HARVEST ORACLE LSTM TRAINING PIPELINE (MODEL A9) - TICKET-129       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-03                                                 ║
║ Version         : 1.0.0                                                      ║
║ Author(s)       : @Mounir (ML Lead), @Mouhammed (Data Eng)                   ║
║ Reviewer(s)     : @Imrane (MLOps), @Asama (Domain)                           ║
║ Product Owner   : @MrZakaria                                                 ║
║ Classification  : Internal - Confidential                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ PURPOSE                                                                     ║
║ -------                                                                      ║
║ Train the LSTM sequence model consumed by cloud_citadel/nervous_system/      ║
║ nervous_system.py for predicting harvest dates (days remaining). Pipeline:   ║
║   • Extracts rolling growth tensors from ClickHouse (growth_time_series).     ║
║   • Builds (samples, timesteps, features) arrays with scaling.               ║
║   • Trains Keras LSTM + Dense head with early stopping.                      ║
║   • Saves weights (models/lstm_harvest_v1.h5) + scaler (models/telemetry_scaler.pkl).║
║   • Logs MAE/MAPE metrics for governance.                                    ║
║                                                                              ║
║ TICKET / TEAM                                                                ║
║ ---------------                                                              ║
║ - Ticket: TICKET-129                                                          ║
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
from typing import Iterable, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

try:
    from clickhouse_driver import Client as ClickHouseClient
except ImportError:  # pragma: no cover
    ClickHouseClient = None  # type: ignore[misc]

LOGGER = logging.getLogger("harvest.training")
logging.basicConfig(
    level=os.getenv("HARVEST_TRAINING_LOG", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@dataclass
class TrainingConfig:
    clickhouse_host: Optional[str]
    clickhouse_port: int
    clickhouse_db: str
    clickhouse_user: Optional[str]
    clickhouse_password: Optional[str]
    csv_path: Optional[pathlib.Path]
    sequence_length: int
    features: Tuple[str, ...]
    target: str
    batch_size: int
    epochs: int
    patience: int
    output_model: pathlib.Path
    output_scaler: pathlib.Path
    output_metrics: pathlib.Path
    validation_split: float

    def safe(self) -> dict:
        return {
            "clickhouse_host": self.clickhouse_host or "(csv mode)",
            "sequence_length": self.sequence_length,
            "features": self.features,
            "target": self.target,
            "output_model": str(self.output_model),
        }


# ---------------------------------------------------------------------------
# DATA EXTRACTION
# ---------------------------------------------------------------------------
def load_dataframe(cfg: TrainingConfig) -> pd.DataFrame:
    if cfg.csv_path:
        LOGGER.info("Loading growth time series from CSV: %s", cfg.csv_path)
        return pd.read_csv(cfg.csv_path)
    if ClickHouseClient is None or cfg.clickhouse_host is None:
        raise RuntimeError("ClickHouse driver missing; supply --csv or install dependency")
    LOGGER.info("Querying ClickHouse growth_time_series view")
    client = ClickHouseClient(
        host=cfg.clickhouse_host,
        port=cfg.clickhouse_port,
        database=cfg.clickhouse_db,
        user=cfg.clickhouse_user,
        password=cfg.clickhouse_password,
    )
    query = """
        SELECT batch_id,
               rack_id,
               event_ts,
               fresh_biomass_est,
               nutrient_solution_ec,
               vapor_pressure_deficit,
               light_ppfd,
               canopy_temperature_c,
               co2_ppm,
               days_until_harvest
        FROM analytics.harvest_training_view
        ORDER BY batch_id, event_ts
    """
    rows = client.execute(query)
    cols = [
        "batch_id",
        "rack_id",
        "event_ts",
        "fresh_biomass_est",
        "nutrient_solution_ec",
        "vapor_pressure_deficit",
        "light_ppfd",
        "canopy_temperature_c",
        "co2_ppm",
        "days_until_harvest",
    ]
    df = pd.DataFrame(rows, columns=cols)
    LOGGER.info("Fetched %d records", len(df))
    return df


# ---------------------------------------------------------------------------
# DATASET BUILDER
# ---------------------------------------------------------------------------
def build_sequences(df: pd.DataFrame, cfg: TrainingConfig) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    sequences = []
    targets = []
    scaler = StandardScaler()

    grouped = df.groupby("batch_id")
    for batch_id, group in grouped:
        group = group.sort_values("event_ts")
        values = group[list(cfg.features)].to_numpy(dtype=np.float32)
        labels = group[cfg.target].to_numpy(dtype=np.float32)
        if len(values) < cfg.sequence_length:
            continue
        for i in range(len(values) - cfg.sequence_length):
            seq = values[i : i + cfg.sequence_length]
            target = labels[i + cfg.sequence_length]
            sequences.append(seq)
            targets.append(target)

    data = np.array(sequences)
    target_vec = np.array(targets).reshape(-1, 1)

    flattened = data.reshape(-1, data.shape[-1])
    scaler.fit(flattened)
    scaled = scaler.transform(flattened).reshape(data.shape)
    LOGGER.info("Built dataset: samples=%d, timesteps=%d, features=%d", scaled.shape[0], scaled.shape[1], scaled.shape[2])
    return scaled, target_vec, scaler


# ---------------------------------------------------------------------------
# MODEL DEFINITION
# ---------------------------------------------------------------------------
def build_model(input_shape: tuple[int, int]) -> tf.keras.Model:
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=input_shape),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1, activation="relu"),
        ]
    )
    model.compile(optimizer="adam", loss="mae", metrics=["mape", "mae"])
    model.summary(print_fn=lambda x: LOGGER.info(x))
    return model


# ---------------------------------------------------------------------------
# TRAINING
# ---------------------------------------------------------------------------
def train_model(data: np.ndarray, targets: np.ndarray, cfg: TrainingConfig) -> tuple[tf.keras.Model, dict]:
    model = build_model((cfg.sequence_length, len(cfg.features)))
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=cfg.patience, restore_best_weights=True
        )
    ]
    history = model.fit(
        data,
        targets,
        batch_size=cfg.batch_size,
        epochs=cfg.epochs,
        validation_split=cfg.validation_split,
        callbacks=callbacks,
        verbose=1,
    )
    metrics = {
        "train_loss": history.history["loss"][-1],
        "train_mae": history.history.get("mae", [None])[-1],
        "train_mape": history.history.get("mape", [None])[-1],
        "val_loss": history.history["val_loss"][-1],
        "val_mae": history.history.get("val_mae", [None])[-1],
        "val_mape": history.history.get("val_mape", [None])[-1],
    }
    return model, metrics


# ---------------------------------------------------------------------------
# PERSISTENCE
# ---------------------------------------------------------------------------
def persist(model: tf.keras.Model, scaler: StandardScaler, metrics: dict, cfg: TrainingConfig) -> None:
    cfg.output_model.parent.mkdir(parents=True, exist_ok=True)
    model.save(cfg.output_model)
    LOGGER.info("Saved LSTM weights to %s", cfg.output_model)

    cfg.output_scaler.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, cfg.output_scaler)
    LOGGER.info("Saved scaler to %s", cfg.output_scaler)

    cfg.output_metrics.parent.mkdir(parents=True, exist_ok=True)
    with cfg.output_metrics.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    LOGGER.info("Saved metrics to %s", cfg.output_metrics)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train VertiFlow Harvest LSTM")
    parser.add_argument("--clickhouse-host", type=str, default=os.getenv("CLICKHOUSE_HOST"))
    parser.add_argument("--clickhouse-port", type=int, default=int(os.getenv("CLICKHOUSE_PORT", "9000")))
    parser.add_argument("--clickhouse-db", type=str, default=os.getenv("CLICKHOUSE_DB", "vertiflow"))
    parser.add_argument("--clickhouse-user", type=str, default=os.getenv("CLICKHOUSE_USER"))
    parser.add_argument("--clickhouse-password", type=str, default=os.getenv("CLICKHOUSE_PASSWORD"))
    parser.add_argument("--csv", type=pathlib.Path, default=None)
    parser.add_argument("--sequence-length", type=int, default=14)
    parser.add_argument(
        "--features",
        type=str,
        default="fresh_biomass_est,nutrient_solution_ec,vapor_pressure_deficit,light_ppfd,canopy_temperature_c",
        help="Comma-separated feature list",
    )
    parser.add_argument("--target", type=str, default="days_until_harvest")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--validation-split", type=float, default=0.2)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("models/lstm_harvest_v1.h5"))
    parser.add_argument(
        "--scaler-output",
        type=pathlib.Path,
        default=pathlib.Path("models/telemetry_scaler.pkl"),
    )
    parser.add_argument(
        "--metrics-output",
        type=pathlib.Path,
        default=pathlib.Path("models/lstm_harvest_v1.metrics.json"),
    )
    return parser.parse_args(argv)


def build_config(args: argparse.Namespace) -> TrainingConfig:
    return TrainingConfig(
        clickhouse_host=args.clickhouse_host,
        clickhouse_port=args.clickhouse_port,
        clickhouse_db=args.clickhouse_db,
        clickhouse_user=args.clickhouse_user,
        clickhouse_password=args.clickhouse_password,
        csv_path=args.csv,
        sequence_length=args.sequence_length,
        features=tuple(args.features.split(",")),
        target=args.target,
        batch_size=args.batch_size,
        epochs=args.epochs,
        patience=args.patience,
        output_model=args.output,
        output_scaler=args.scaler_output,
        output_metrics=args.metrics_output,
        validation_split=args.validation_split,
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    cfg = build_config(args)
    LOGGER.info("Training config: %s", cfg.safe())

    df = load_dataframe(cfg)
    data, targets, scaler = build_sequences(df, cfg)
    model, metrics = train_model(data, targets, cfg)
    persist(model, scaler, metrics, cfg)
    LOGGER.info("Harvest LSTM training complete")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 FOOTER                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Component        : models/train_harvest_lstm.py                              ║
║ Ticket           : TICKET-129                                                ║
║ Squad            : Core Data Foundation                                      ║
║ Owner            : @Mounir                                                   ║
║ Support          : @Mouhammed (Data), @Imrane (MLOps), @Asama (Domain)       ║
║ Contact          : data@vertiflow.ai                                         ║
║ Runtime          : Airflow DAG `train_harvest_lstm` / Notebook               ║
║ Dependencies     : tensorflow 2.x, pandas, numpy, scikit-learn, clickhouse-driver║
║ Last Updated     : 2026-01-03                                                ║
║ Next Review      : 2026-02-15                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
