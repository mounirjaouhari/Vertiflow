#!/usr/bin/env python3
"""Import LED spectrum and nutrient data into ClickHouse (TabSeparated)."""
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess

BASE_DIR = Path("/home/mounirjaouhari/vertiflow_cloud_release")
LED_DIR = BASE_DIR / "data_ingestion" / "led_spectrum"
NUTRIENT_DIR = BASE_DIR / "data_ingestion" / "nutrient_data"

BATCH_SIZE = 1000


def to_datetime_str(value: str) -> str:
    if not value:
        return "1970-01-01 00:00:00"
    try:
        # Handle ISO with timezone
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "1970-01-01 00:00:00"


def to_str(value) -> str:
    if value is None or value == "":
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")


def to_float(value) -> str:
    if value is None or value == "":
        return "0"
    try:
        return str(float(value))
    except Exception:
        return "0"


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


def import_led():
    print("📥 Import LED spectrum...")
    files = sorted(LED_DIR.glob("*.json"))
    rows = []
    inserted = 0
    for fp in files:
        with open(fp, "r") as f:
            data = json.load(f)
        # Ensure dict
        if isinstance(data, list):
            # If list, insert each record
            records = data
        else:
            records = [data]
        for rec in records:
            ts = to_datetime_str(rec.get("timestamp"))
            farm_id = to_str(rec.get("farm_id"))
            rack_id = to_str(rec.get("rack_id"))
            level_id = to_str(rec.get("level_id", rec.get("level_index")))
            ppfd = to_float(rec.get("light_intensity_ppfd"))
            ratio_rb = to_float(rec.get("light_ratio_red_blue"))
            spectral_id = to_str(rec.get("spectral_recipe_id"))
            row = "\t".join([ts, farm_id, rack_id, level_id, ppfd, ratio_rb, spectral_id])
            rows.append(row)
            if len(rows) >= BATCH_SIZE:
                run_insert(
                    "INSERT INTO vertiflow.led_spectrum_data (timestamp,farm_id,rack_id,level_id,light_intensity_ppfd,light_ratio_red_blue,spectral_recipe_id) FORMAT TabSeparated",
                    rows,
                )
                inserted += len(rows)
                rows = []
    if rows:
        run_insert(
            "INSERT INTO vertiflow.led_spectrum_data (timestamp,farm_id,rack_id,level_id,light_intensity_ppfd,light_ratio_red_blue,spectral_recipe_id) FORMAT TabSeparated",
            rows,
        )
        inserted += len(rows)
    print(f"✅ LED inserted: {inserted}")


def import_nutrient():
    print("📥 Import nutrient data...")
    files = sorted(NUTRIENT_DIR.glob("*.json"))
    rows = []
    inserted = 0
    for fp in files:
        with open(fp, "r") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else [data]
        for rec in records:
            ts = to_datetime_str(rec.get("timestamp"))
            zone_id = to_str(rec.get("zone_id"))
            tank_id = to_str(rec.get("tank_id"))
            n_val = to_float(rec.get("nutrient_n_total"))
            p_val = to_float(rec.get("nutrient_p_phosphorus"))
            row = "\t".join([ts, zone_id, tank_id, n_val, p_val])
            rows.append(row)
            if len(rows) >= BATCH_SIZE:
                run_insert(
                    "INSERT INTO vertiflow.iot_nutrient_measurements FORMAT TabSeparated",
                    rows,
                )
                inserted += len(rows)
                rows = []
    if rows:
        run_insert(
            "INSERT INTO vertiflow.iot_nutrient_measurements FORMAT TabSeparated",
            rows,
        )
        inserted += len(rows)
    print(f"✅ Nutrient inserted: {inserted}")


def main():
    if not LED_DIR.exists():
        raise SystemExit(f"LED dir not found: {LED_DIR}")
    if not NUTRIENT_DIR.exists():
        raise SystemExit(f"Nutrient dir not found: {NUTRIENT_DIR}")

    import_led()
    import_nutrient()


if __name__ == "__main__":
    main()
