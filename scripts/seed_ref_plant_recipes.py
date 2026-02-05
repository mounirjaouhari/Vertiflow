#!/usr/bin/env python3
"""Seed ref_plant_recipes from basil_recipes.json."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import subprocess

BASE_DIR = Path("/home/mounirjaouhari/vertiflow_cloud_release")
RECIPES_JSON = BASE_DIR / "basil_recipes.json"

STAGE_MAP = {
    "Semis": "Semis",
    "Jeunes plantules": "Végétatif",
    "Croissance vegetative": "Végétatif",
    "Pré-recolte": "Bouton",
    "Pre-recolte": "Bouton",
    "Recolte": "Récolte",
    "Récolte": "Récolte",
    "Post-recolte": "Récolte",
}


def to_float(value) -> str:
    if value is None or value == "":
        return "0"
    try:
        return str(float(value))
    except Exception:
        return "0"


def to_str(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")


def run_insert(rows: list[str]) -> None:
    if not rows:
        return
    payload = "\n".join(rows) + "\n"
    cmd = [
        "docker",
        "exec",
        "-i",
        "clickhouse",
        "clickhouse-client",
        "--query",
        "INSERT INTO vertiflow.ref_plant_recipes (recipe_id,species_variety,growth_stage,target_temp_day,target_temp_night,target_humidity_min,target_humidity_max,target_vpd,target_dli,target_photoperiod_hours,target_spectrum_ratio_rb,target_n_ppm,target_p_ppm,target_k_ppm,target_ec,target_ph,author,validation_date,version) FORMAT TabSeparated",
    ]
    result = subprocess.run(cmd, input=payload.encode(), capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="ignore")[:200])


def main() -> None:
    with open(RECIPES_JSON, "r") as f:
        data = json.load(f)

    rows = []
    for rec in data:
        recipe_id = to_str(rec.get("recipe_id"))
        species_variety = to_str(rec.get("species_variety"))
        stage_raw = rec.get("growth_stage", "")
        growth_stage = STAGE_MAP.get(stage_raw, "Végétatif")

        row = "\t".join(
            [
                recipe_id,
                species_variety,
                growth_stage,
                to_float(rec.get("target_temp_day")),
                to_float(rec.get("target_temp_night")),
                to_float(rec.get("target_humidity_min")),
                to_float(rec.get("target_humidity_max")),
                to_float(rec.get("target_vpd")),
                to_float(rec.get("target_dli")),
                to_float(rec.get("target_photoperiod_hours")),
                to_float(rec.get("target_spectrum_ratio_rb")),
                to_float(rec.get("target_n_ppm")),
                to_float(rec.get("target_p_ppm")),
                to_float(rec.get("target_k_ppm")),
                to_float(rec.get("target_ec")),
                to_float(rec.get("target_ph")),
                to_str(rec.get("author")),
                to_str(rec.get("validation_date", datetime.utcnow().strftime("%Y-%m-%d"))),
                "1",
            ]
        )
        rows.append(row)

    run_insert(rows)
    print(f"✅ ref_plant_recipes inserted: {len(rows)}")


if __name__ == "__main__":
    main()
