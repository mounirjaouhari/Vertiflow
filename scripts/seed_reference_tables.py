#!/usr/bin/env python3
"""Seed ClickHouse reference tables from agronomic_parameters.yaml."""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
import yaml

BASE_DIR = Path("/home/mounirjaouhari/vertiflow_cloud_release")
CONFIG_PATH = BASE_DIR / "config" / "agronomic_parameters.yaml"


def run_insert(query: str, rows: list[str]) -> None:
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
        query,
    ]
    result = subprocess.run(cmd, input=payload.encode(), capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="ignore")[:200])


def to_float(value) -> str:
    if value is None:
        return "0"
    try:
        return str(float(value))
    except Exception:
        return "0"


def to_str(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")


def seed_light_spectra(crop: dict) -> int:
    spectrum = crop.get("spectrum", {})
    photoperiod = crop.get("photoperiod", {})
    par_opt = crop.get("optimal_ranges", {}).get("par_umol", {}).get("optimal", 0)

    rows = []
    for stage, spec in spectrum.items():
        spectrum_id = f"BASIL_GENOVESE_{stage.upper()}"
        name = f"Basil Genovese {stage}"
        red_ratio = spec.get("red_pct", 0)
        blue_ratio = spec.get("blue_pct", 0)
        green_ratio = spec.get("white_pct", 0)
        ir_ratio = spec.get("far_red_pct", 0)
        ppfd_target = par_opt
        photoperiod_h = photoperiod.get(stage, 0)
        notes = "agronomic_parameters.yaml"
        row = "\t".join(
            [
                spectrum_id,
                name,
                to_float(red_ratio),
                to_float(blue_ratio),
                to_float(green_ratio),
                to_float(ir_ratio),
                to_float(ppfd_target),
                str(int(photoperiod_h) if photoperiod_h else 0),
                notes,
            ]
        )
        rows.append(row)

    run_insert(
        "INSERT INTO vertiflow.ref_light_spectra (spectrum_id,name,red_ratio,blue_ratio,green_ratio,ir_ratio,ppfd_target,daily_photoperiod_hours,spectrum_notes) FORMAT TabSeparated",
        rows,
    )
    return len(rows)


def seed_nutrient_measurements(crop: dict) -> int:
    nutrition = crop.get("nutrition", {})
    rows = []
    for stage, nutrients in nutrition.items():
        for nutrient, target in nutrients.items():
            if nutrient in {"ec_target"}:
                continue
            nutrient_name = f"{nutrient.upper()} ({stage})"
            element_symbol = nutrient.upper()
            target_ppm = float(target)
            min_ppm = target_ppm * 0.8
            max_ppm = target_ppm * 1.2
            safety_range_percent = 20.0
            optimal_ratio = 1.0
            source = "agronomic_parameters.yaml"
            deficiency = ""
            measurement_id = f"BASIL_{stage.upper()}_{element_symbol}"
            row = "\t".join(
                [
                    measurement_id,
                    nutrient_name,
                    element_symbol,
                    to_float(target_ppm),
                    to_float(min_ppm),
                    to_float(max_ppm),
                    to_float(safety_range_percent),
                    to_float(optimal_ratio),
                    source,
                    deficiency,
                ]
            )
            rows.append(row)

    run_insert(
        "INSERT INTO vertiflow.ref_nutrient_measurements (measurement_id,nutrient_name,element_symbol,target_ppm,min_ppm,max_ppm,safety_range_percent,optimal_ratio,nutrient_source,deficiency_symptoms) FORMAT TabSeparated",
        rows,
    )
    return len(rows)


def seed_quality_thresholds(crop: dict) -> int:
    ranges = crop.get("optimal_ranges", {})
    quality = crop.get("quality_targets", {})

    def add_threshold(parameter, optimal_min, optimal_max, unit, description):
        warning_min = optimal_min * 0.9
        warning_max = optimal_max * 1.1
        critical_min = optimal_min * 0.8
        critical_max = optimal_max * 1.2
        threshold_id = f"BASIL_{parameter.upper()}"
        row = "\t".join(
            [
                threshold_id,
                parameter,
                to_float(optimal_min),
                to_float(optimal_max),
                to_float(warning_min),
                to_float(warning_max),
                to_float(critical_min),
                to_float(critical_max),
                unit,
                description,
            ]
        )
        return row

    rows = []
    if "temperature_c" in ranges:
        t = ranges["temperature_c"]
        rows.append(add_threshold("temperature_c", t["min"], t["max"], "C", "Basil Genovese temperature range"))
    if "humidity_pct" in ranges:
        h = ranges["humidity_pct"]
        rows.append(add_threshold("humidity_pct", h["min"], h["max"], "%", "Basil Genovese humidity range"))
    if "co2_ppm" in ranges:
        c = ranges["co2_ppm"]
        rows.append(add_threshold("co2_ppm", c["min"], c["max"], "ppm", "Basil Genovese CO2 range"))
    if "par_umol" in ranges:
        p = ranges["par_umol"]
        rows.append(add_threshold("par_umol", p["min"], p["max"], "umol/m2/s", "Basil Genovese PAR range"))
    if "ph" in ranges:
        ph = ranges["ph"]
        rows.append(add_threshold("ph", ph["min"], ph["max"], "pH", "Basil Genovese pH range"))
    if "ec_ms" in ranges:
        ec = ranges["ec_ms"]
        rows.append(add_threshold("ec_ms", ec["min"], ec["max"], "mS/cm", "Basil Genovese EC range"))

    if "fresh_weight_g" in quality:
        rows.append(add_threshold("fresh_weight_g", quality["fresh_weight_g"] * 0.9, quality["fresh_weight_g"] * 1.1, "g", "Target fresh weight"))
    if "essential_oil_pct" in quality:
        rows.append(add_threshold("essential_oil_pct", quality["essential_oil_pct"] * 0.8, quality["essential_oil_pct"] * 1.2, "%", "Target essential oil"))
    if "chlorophyll_spad" in quality:
        rows.append(add_threshold("chlorophyll_spad", quality["chlorophyll_spad"] * 0.9, quality["chlorophyll_spad"] * 1.1, "SPAD", "Target chlorophyll"))
    if "brix_degree" in quality:
        rows.append(add_threshold("brix_degree", quality["brix_degree"] * 0.9, quality["brix_degree"] * 1.1, "Brix", "Target brix"))
    if "shelf_life_days" in quality:
        rows.append(add_threshold("shelf_life_days", quality["shelf_life_days"] * 0.8, quality["shelf_life_days"] * 1.2, "days", "Target shelf life"))

    run_insert(
        "INSERT INTO vertiflow.ref_quality_thresholds (threshold_id,parameter_name,optimal_min,optimal_max,warning_min,warning_max,critical_min,critical_max,unit,description) FORMAT TabSeparated",
        rows,
    )
    return len(rows)


def main() -> None:
    with open(CONFIG_PATH, "r") as f:
        data = yaml.safe_load(f)

    crop = data.get("crops", {}).get("basil_genovese")
    if not crop:
        raise SystemExit("basil_genovese not found in agronomic_parameters.yaml")

    light_count = seed_light_spectra(crop)
    nutrient_count = seed_nutrient_measurements(crop)
    quality_count = seed_quality_thresholds(crop)

    print(f"✅ ref_light_spectra: {light_count}")
    print(f"✅ ref_nutrient_measurements: {nutrient_count}")
    print(f"✅ ref_quality_thresholds: {quality_count}")


if __name__ == "__main__":
    main()
