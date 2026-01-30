#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "infrastructure" / "init_scripts" / "clickhouse" / "01_tables.sql"
MD_PATH = ROOT / "docs" / "CLICKHOUSE_COLUMN_DICTIONARY.md"
CSV_PATH = ROOT / "docs" / "CLICKHOUSE_COLUMN_DICTIONARY.csv"

CATEGORY_PATTERN = re.compile(r"--\s+([IVXLCDM]+)\.\s+([^\(]+)")


@dataclass
class Column:
    order: int
    name: str
    type: str
    category: str
    description: str


def humanize(name: str) -> str:
    words: list[str] = []
    for part in name.split("_"):
        if not part:
            continue
        if part.isupper():
            words.append(part)
        else:
            words.append(part.capitalize())
    return " ".join(words)


def synthesize_description(raw_comment: str, name: str, category: str) -> str:
    if raw_comment:
        return raw_comment.strip()
    base = humanize(name)
    return f"Mesure {base.lower()} pour le domaine {category.lower()}."


def parse_columns(sql_text: str) -> list[Column]:
    records: list[Column] = []
    in_table = False
    category = "Non catégorisé"
    order = 1

    for line in sql_text.splitlines():
        stripped = line.strip()

        if not in_table:
            if stripped.startswith("CREATE TABLE") and "basil_ultimate_realtime" in stripped:
                in_table = True
            continue

        if stripped.startswith(")") and "ENGINE" in stripped:
            break

        if stripped.startswith("--"):
            match = CATEGORY_PATTERN.match(stripped)
            if match:
                category = match.group(2).strip()
            continue

        if not stripped or stripped.startswith("("):
            continue

        # Exclude statements such as ALTER that appear after the table definition
        if stripped.upper().startswith("ALTER TABLE"):
            break

        column_section, _, comment = line.partition("--")
        column_section = column_section.strip().rstrip(",")
        if not column_section:
            continue

        parts = column_section.split(None, 1)
        if len(parts) < 2:
            continue

        name, type_part = parts[0].strip('`'), parts[1].strip().rstrip(",")
        description = synthesize_description(comment, name, category)
        records.append(Column(order, name, type_part, category, description))
        order += 1

    return records


def write_markdown(columns: list[Column]) -> None:
    count = len(columns)
    header = dedent(
        f"""
        # 📘 Dictionnaire des Colonnes ClickHouse

        Ce fichier est généré automatiquement à partir du schéma `basil_ultimate_realtime` afin de documenter les {count} mesures Golden Record.

        | # | Colonne | Type | Domaine | Description |
        | - | ------- | ---- | ------- | ----------- |
        """
    ).strip()

    lines = [header]
    for col in columns:
        description = col.description.replace("|", "\\|")
        lines.append(
            f"| {col.order} | `{col.name}` | `{col.type}` | {col.category} | {description} |"
        )

    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(columns: list[Column]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["order", "column", "type", "category", "description"])
        for col in columns:
            writer.writerow([col.order, col.name, col.type, col.category, col.description])


def main() -> None:
    sql_text = SQL_PATH.read_text(encoding="utf-8")
    columns = parse_columns(sql_text)
    expected = 157
    if len(columns) != expected:
        raise SystemExit(
            f"Le schéma devrait contenir {expected} colonnes d'après ClickHouse, trouvé {len(columns)}"
        )
    write_markdown(columns)
    write_csv(columns)
    print(f"✓ Dictionnaire généré ({len(columns)} colonnes)")


if __name__ == "__main__":
    main()
