#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       VERTIFLOW™ DATA PLATFORM - MONGODB                     ║
║                         SCRIPT: scripts/init_mongodb.py                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-04                                                 ║
║ Version         : 1.0.0                                                      ║
║ Ticket          : TICKET-135 (Ops Datastore Bootstrap)                       ║
║ Squad           : Core Platform Operations                                   ║
║ Maintainer      : @Mouhammed (Data Eng)                                      ║
║ Reviewers       : @Imrane (DevOps), @Mounir (ML)                             ║
║ Classification  : Interne - Confidentiel                                     ║
║ Purpose         : Préparer la base vertiflow_ops avec schémas + données.     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Iterable, List

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure

LOGGER = logging.getLogger("vertiflow.init_mongodb")
DEFAULT_DB = os.getenv("MONGODB_DB", "vertiflow_ops")
TTL_SECONDS = 7 * 24 * 60 * 60  # 7 jours

PLANT_RECIPES = [
    {
        "recipe_id": "RECIPE_GENOVESE_STD_V1",
        "species_variety": "Genovese",
        "growth_stage": "VEGETATIVE",
        "targets": {
            "temp_min": 18,
            "temp_max": 24,
            "temp_opt": 22,
            "humidity_min": 50,
            "humidity_max": 70,
            "n_target_ppm": 150,
            "p_target_ppm": 50,
            "k_target_ppm": 200,
            "ec_target": 1.8,
            "ph_target": 6.0,
            "dli_target": 12.0,
        },
        "description": "Standard balanced recipe for biomass",
        "version": 1,
        "is_active": True,
    },
    {
        "recipe_id": "RECIPE_GENOVESE_BOOST_V1",
        "species_variety": "Genovese",
        "growth_stage": "FLOWERING_PREVENTION",
        "targets": {
            "temp_min": 20,
            "temp_max": 26,
            "temp_opt": 24,
            "humidity_min": 45,
            "humidity_max": 65,
            "n_target_ppm": 180,
            "p_target_ppm": 60,
            "k_target_ppm": 250,
            "ec_target": 2.2,
            "ph_target": 6.2,
            "dli_target": 16.0,
        },
        "description": "High light/nutrient recipe for oil production",
        "version": 1,
        "is_active": False,
    },
]


LIVE_STATE_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["farm_id", "rack_id", "module_id", "last_update", "telemetry"],
        "properties": {
            "farm_id": {"bsonType": "string"},
            "rack_id": {"bsonType": "string"},
            "module_id": {"bsonType": "string"},
            "last_update": {"bsonType": "date"},
            "telemetry": {
                "bsonType": "object",
                "required": ["air_temp_internal", "nutrient_n_total"],
                "properties": {
                    "air_temp_internal": {"bsonType": ["double", "int", "decimal"]},
                    "nutrient_n_total": {"bsonType": ["double", "int", "decimal"]},
                },
            },
            "status": {
                "bsonType": "object",
                "properties": {
                    "is_active": {"bsonType": "bool"},
                    "alert_level": {"enum": ["NORMAL", "WARNING", "CRITICAL"]},
                },
            },
        },
    }
}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap MongoDB vertiflow_ops data store.")
    parser.add_argument("--host", default=os.getenv("MONGODB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MONGODB_PORT", "27017")))
    parser.add_argument("--username", default=os.getenv("MONGODB_USER"))
    parser.add_argument("--password", default=os.getenv("MONGODB_PASSWORD"))
    parser.add_argument("--auth-db", default=os.getenv("MONGODB_AUTH_DB", "admin"))
    parser.add_argument("--database", default=DEFAULT_DB)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def get_database(args: argparse.Namespace) -> Database:
    client = MongoClient(
        host=args.host,
        port=args.port,
        username=args.username or None,
        password=args.password or None,
        authSource=args.auth_db,
        serverSelectionTimeoutMS=5_000,
    )
    client.admin.command("ping")
    LOGGER.info("Connected to MongoDB %s:%s", args.host, args.port)
    return client[args.database]


def ensure_collection(db: Database, name: str, validator: dict | None = None) -> Collection:
    if name not in db.list_collection_names():
        options = {"validator": validator} if validator else {}
        db.create_collection(name, **options)
        LOGGER.info("Created collection '%s'", name)
    elif validator:
        db.command("collMod", name, validator=validator, validationLevel="moderate")
        LOGGER.info("Updated validator for '%s'", name)
    return db[name]


def safe_create_index(collection: Collection, keys, **kwargs) -> None:
    try:
        collection.create_index(keys, **kwargs)
    except OperationFailure as exc:
        if exc.code == 85:
            LOGGER.info(
                "Index already exists on '%s' (keys=%s), skipping", collection.name, keys
            )
        else:
            raise


def configure_live_state(collection: Collection) -> None:
    safe_create_index(
        collection,
        [("farm_id", ASCENDING), ("rack_id", ASCENDING), ("module_id", ASCENDING)],
        unique=True,
        name="uq_farm_rack_module",
    )
    safe_create_index(
        collection,
        [("last_update", ASCENDING)],
        expireAfterSeconds=TTL_SECONDS,
        name="ttl_last_update_7d",
    )


def configure_incident_logs(collection: Collection) -> None:
    safe_create_index(collection, [("timestamp", DESCENDING)], name="idx_timestamp")
    safe_create_index(
        collection,
        [("severity", ASCENDING), ("status", ASCENDING)],
        name="idx_severity_status",
    )


def configure_plant_recipes(collection: Collection) -> None:
    safe_create_index(collection, "recipe_id", unique=True, name="uq_recipe_id")
    safe_create_index(
        collection,
        [("species_variety", ASCENDING), ("growth_stage", ASCENDING)],
        name="idx_species_stage",
    )


def upsert_recipes(collection: Collection, recipes: List[dict]) -> None:
    for recipe in recipes:
        recipe["updated_at"] = datetime.now(timezone.utc)
        collection.update_one(
            {"recipe_id": recipe["recipe_id"]},
            {"$set": recipe},
            upsert=True,
        )
    LOGGER.info("Upserted %d plant recipes", len(recipes))


def configure_support_collections(db: Database) -> None:
    quality = ensure_collection(db, "quality_predictions")
    safe_create_index(
        quality,
        [("batch_id", ASCENDING), ("prediction_date", DESCENDING)],
        name="idx_batch_prediction",
    )

    optim = ensure_collection(db, "recipe_optimizations")
    safe_create_index(
        optim,
        [("recipe_id", ASCENDING), ("optimization_date", DESCENDING)],
        name="idx_recipe_opt_date",
    )


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    db = get_database(args)
    LOGGER.info("Using database '%s'", db.name)

    live_state = ensure_collection(db, "live_state", validator=LIVE_STATE_VALIDATOR)
    configure_live_state(live_state)

    incident_logs = ensure_collection(db, "incident_logs")
    configure_incident_logs(incident_logs)

    plant_recipes = ensure_collection(db, "plant_recipes")
    configure_plant_recipes(plant_recipes)
    upsert_recipes(plant_recipes, PLANT_RECIPES)

    configure_support_collections(db)

    LOGGER.info("MongoDB bootstrap complete. Collections: %s", db.list_collection_names())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
