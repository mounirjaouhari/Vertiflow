#!/usr/bin/env python3
"""Seed research/reference tables in ClickHouse from Basil Data and OpenAG datasets."""
from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
import subprocess
import pandas as pd

BASE_DIR = Path("/home/mounirjaouhari/vertiflow_cloud_release")
BASIL_ZIP = BASE_DIR / "datasets" / "Basil Data.zip"
OPENAG_DIR = BASE_DIR / "datasets" / "openag-basil-viability-experiment-foodserver-2-master" / "openag-basil-viability-experiment-foodserver-2-master"

EXTRACT_DIR = Path("/tmp/basil_data_extract")
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = datetime.utcnow().strftime("%Y-%m-%d")


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


def to_str(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")


def to_float(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "0"
    try:
        return str(float(value))
    except Exception:
        return "0"


def to_uint8(value) -> str:
    try:
        v = int(round(float(value)))
        if v < 0:
            v = 0
        if v > 255:
            v = 255
        return str(v)
    except Exception:
        return "0"


def extract_basil_zip() -> None:
    if BASIL_ZIP.exists():
        with zipfile.ZipFile(BASIL_ZIP, "r") as zf:
            zf.extractall(EXTRACT_DIR)


def seed_aroma_profiles() -> int:
    gcms_path = EXTRACT_DIR / "Basil GCMS data 1.xlsx"
    df = pd.read_excel(gcms_path, sheet_name=0)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    # Exclude RT and RI if present
    numeric_cols = [c for c in numeric_cols if c not in {"RT", "RI", "Match Factor"}]

    rows = []
    for idx, row in df.iterrows():
        aroma_id = f"GCMS_{idx + 1}"
        compound_name = to_str(row.get("Compound"))
        cas_number = to_str(row.get("CAS Number"))
        retention = to_float(row.get("RT"))
        mass_spec = to_str(row.get("Molecular Formula") or row.get("Match Factor"))
        if numeric_cols:
            rel_ab = pd.to_numeric(row[numeric_cols], errors="coerce").mean()
        else:
            rel_ab = 0
        relative_abundance = to_float(rel_ab)
        sensory_desc = ""
        basil_variety = "Basil"
        detection_method = "GC-MS"
        rows.append(
            "\t".join(
                [
                    aroma_id,
                    compound_name,
                    cas_number,
                    retention,
                    mass_spec,
                    relative_abundance,
                    sensory_desc,
                    basil_variety,
                    detection_method,
                ]
            )
        )

    run_insert(
        "INSERT INTO vertiflow.ref_aroma_profiles (aroma_id,compound_name,cas_number,retention_time_min,mass_spec_pattern,relative_abundance_percent,sensory_descriptor,basil_variety,detection_method) FORMAT TabSeparated",
        rows,
    )
    return len(rows)


def seed_photosynthesis_curves() -> int:
    dark_path = EXTRACT_DIR / "licor_dark_R.xlsx"
    light_path = EXTRACT_DIR / "licor_light_R.xlsx"

    rows = []
    # Dark
    df_dark = pd.read_excel(dark_path, sheet_name=0)
    for idx, row in df_dark.iterrows():
        curve_id = f"LICOR_DARK_{idx + 1}"
        light_condition = "dark"
        ppfd_level = "0"
        net_photo = "0"
        stomatal = to_float(row.get("gsw"))
        transp = to_float(row.get("E_apparent"))
        intercellular = "0"
        temp = "0"
        basil_variety = to_str(row.get("Cultivar"))
        measurement_date = TODAY
        rows.append(
            "\t".join(
                [
                    curve_id,
                    light_condition,
                    ppfd_level,
                    net_photo,
                    stomatal,
                    transp,
                    intercellular,
                    temp,
                    basil_variety,
                    measurement_date,
                ]
            )
        )

    # Light
    df_light = pd.read_excel(light_path, sheet_name=0)
    for idx, row in df_light.iterrows():
        curve_id = f"LICOR_LIGHT_{idx + 1}"
        light_condition = "light"
        ppfd_level = "0"
        net_photo = to_float(row.get("ETR"))
        stomatal = to_float(row.get("gsw"))
        transp = to_float(row.get("E_apparent"))
        intercellular = "0"
        temp = "0"
        basil_variety = to_str(row.get("Cultivar"))
        measurement_date = TODAY
        rows.append(
            "\t".join(
                [
                    curve_id,
                    light_condition,
                    ppfd_level,
                    net_photo,
                    stomatal,
                    transp,
                    intercellular,
                    temp,
                    basil_variety,
                    measurement_date,
                ]
            )
        )

    run_insert(
        "INSERT INTO vertiflow.ref_photosynthesis_curves (curve_id,light_condition,ppfd_level,net_photosynthesis_umol_m2s,stomatal_conductance,transpiration_mmol_m2s,intercellular_co2,temperature_celcius,basil_variety,measurement_date) FORMAT TabSeparated",
        rows,
    )
    return len(rows)


def seed_sensory_evaluation() -> int:
    sensory_path = EXTRACT_DIR / "Basil_sensory_R.csv"
    df = pd.read_csv(sensory_path)

    aroma_cols = [c for c in df.columns if c.endswith("_Aroma")]
    rows = []
    for idx, row in df.iterrows():
        eval_id = f"SENS_{idx + 1}"
        basil_variety = to_str(row.get("Sample_Name"))
        evaluator_id = "panel"
        leaf_color = "0"
        leaf_texture = to_uint8(row.get("Leaf_Thickness"))
        aroma_intensity = to_uint8(pd.to_numeric(row[aroma_cols], errors="coerce").mean())

        # Flavor profile = top 3 aroma descriptors
        aroma_scores = row[aroma_cols].to_dict() if aroma_cols else {}
        top_aromas = sorted(aroma_scores.items(), key=lambda x: (x[1] if pd.notna(x[1]) else 0), reverse=True)[:3]
        flavor_profile = ", ".join([a[0].replace("_Aroma", "") for a in top_aromas])

        overall_quality = to_uint8((float(aroma_intensity) + float(leaf_texture)) / 2 if aroma_intensity or leaf_texture else 0)
        notes = ""
        evaluation_date = TODAY

        rows.append(
            "\t".join(
                [
                    eval_id,
                    basil_variety,
                    evaluator_id,
                    leaf_color,
                    leaf_texture,
                    aroma_intensity,
                    flavor_profile,
                    overall_quality,
                    notes,
                    evaluation_date,
                ]
            )
        )

    run_insert(
        "INSERT INTO vertiflow.ref_sensory_evaluation (eval_id,basil_variety,evaluator_id,leaf_color_score,leaf_texture_score,aroma_intensity_score,flavor_profile,overall_quality_score,notes,evaluation_date) FORMAT TabSeparated",
        rows,
    )
    return len(rows)


def seed_openag_experiments() -> int:
    meta = pd.read_excel(OPENAG_DIR / "META_BV_FS2.xlsx", sheet_name=0)
    manual = pd.read_excel(OPENAG_DIR / "MANUAL_data_BV_FS2.xlsx", sheet_name=0)

    # Group by container + crop
    grouped = manual.groupby(["container", "crop"], dropna=False)
    rows = []
    for (container, crop), g in grouped:
        experiment_id = f"OPENAG_FS2_{container}"
        experiment_name = f"OpenAG FS2 {container}"
        basil_variety = to_str(crop)
        crop_cycle_days = g["date"].nunique() if "date" in g else 0
        plant_count = g["plant"].nunique() if "plant" in g else 0
        yield_g_per_plant = g["harvest_fresh_mass_g"].mean() if "harvest_fresh_mass_g" in g else 0
        final_fresh_weight_g = g["harvest_fresh_mass_g"].mean() if "harvest_fresh_mass_g" in g else 0
        final_dry_weight_g = g["harvest_dry_mass_g"].mean() if "harvest_dry_mass_g" in g else 0
        water_use_efficiency = 0
        co2_uptake_rate = 0

        meta_row = meta[meta["container"] == container].head(1)
        if not meta_row.empty:
            bay = meta_row.iloc[0].get("bay", "")
            res_design = meta_row.iloc[0].get("res_design", "")
            notes = f"bay={bay}, res_design={res_design}"
        else:
            notes = ""

        # experiment_date = min date
        if "date" in g:
            try:
                exp_date = pd.to_datetime(g["date"].min()).strftime("%Y-%m-%d")
            except Exception:
                exp_date = TODAY
        else:
            exp_date = TODAY

        rows.append(
            "\t".join(
                [
                    to_str(experiment_id),
                    to_str(experiment_name),
                    to_str(basil_variety),
                    str(int(crop_cycle_days) if crop_cycle_days else 0),
                    str(int(plant_count) if plant_count else 0),
                    to_float(yield_g_per_plant),
                    to_float(final_fresh_weight_g),
                    to_float(final_dry_weight_g),
                    to_float(water_use_efficiency),
                    to_float(co2_uptake_rate),
                    to_str(notes),
                    exp_date,
                ]
            )
        )

    run_insert(
        "INSERT INTO vertiflow.ref_mit_openag_experiments (experiment_id,experiment_name,basil_variety,crop_cycle_days,plant_count,yield_g_per_plant,final_fresh_weight_g,final_dry_weight_g,water_use_efficiency,co2_uptake_rate,notes,experiment_date) FORMAT TabSeparated",
        rows,
    )
    return len(rows)


def main() -> None:
    extract_basil_zip()

    aroma = seed_aroma_profiles()
    photo = seed_photosynthesis_curves()
    sensory = seed_sensory_evaluation()
    openag = seed_openag_experiments()

    print(f"✅ ref_aroma_profiles: {aroma}")
    print(f"✅ ref_photosynthesis_curves: {photo}")
    print(f"✅ ref_sensory_evaluation: {sensory}")
    print(f"✅ ref_mit_openag_experiments: {openag}")


if __name__ == "__main__":
    main()
