#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      VERTIFLOW™ DATA PLATFORM - CLICKHOUSE                   ║
║                          SCRIPT: scripts/init_clickhouse.py                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-04                                                 ║
║ Version         : 1.0.0                                                      ║
║ Ticket          : TICKET-134 (DB Bootstrap Automation)                       ║
║ Squad           : Core Platform Operations                                   ║
║ Maintainer      : @Imrane (DevOps)                                           ║
║ Contributors    : @Mounir (Data Science), @Mouhammed (Data Eng)              ║
║ Classification  : Interne - Confidentiel                                     ║
║ Purpose         : Rejouer les scripts SQL ClickHouse et vérifier le schéma.  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Iterator, List

try:
    from clickhouse_driver import Client as ClickHouseClient
except ImportError:  # pragma: no cover - dependency missing seulement en doc build
    ClickHouseClient = None  # type: ignore[assignment]

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQL_DIR = ROOT_DIR / "infrastructure" / "init_scripts" / "clickhouse"
LOGGER = logging.getLogger("vertiflow.init_clickhouse")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap ClickHouse schema using the official SQL scripts."
    )
    parser.add_argument("--host", default=os.getenv("CLICKHOUSE_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("CLICKHOUSE_PORT", "9000")))
    parser.add_argument("--user", default=os.getenv("CLICKHOUSE_USER", "default"))
    parser.add_argument(
        "--password",
        default=os.getenv("CLICKHOUSE_PASSWORD", ""),
        help="Leave blank if you rely on the default user with no password.",
    )
    parser.add_argument("--database", default=os.getenv("CLICKHOUSE_DB", "vertiflow"))
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=DEFAULT_SQL_DIR,
        help="Folder containing *.sql files (executed alphabetically).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List statements without executing them.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logs for troubleshooting.",
    )
    return parser.parse_args(argv)


def _strip_inline_comment(line: str) -> str:
    if "--" in line:
        return line.split("--", 1)[0]
    return line


def iter_statements(sql_text: str) -> Iterator[str]:
    """Yield SQL statements separated by ';' while ignoring comments."""

    cleaned_text = "\n".join(_strip_inline_comment(line) for line in sql_text.splitlines())
    buffer: List[str] = []
    in_single = False
    in_double = False

    for char in cleaned_text:
        if char == "'" and not in_double:
            backslash_escaped = buffer and buffer[-1] == "\\"
            if not backslash_escaped:
                in_single = not in_single
        elif char == '"' and not in_single:
            backslash_escaped = buffer and buffer[-1] == "\\"
            if not backslash_escaped:
                in_double = not in_double
        if char == ";" and not in_single and not in_double:
            statement = "".join(buffer).strip()
            if statement:
                yield statement
            buffer = []
        else:
            buffer.append(char)

    tail = "".join(buffer).strip()
    if tail:
        yield tail


def execute_sql_file(client: ClickHouseClient, sql_file: Path, *, dry_run: bool = False) -> int:
    """Execute every statement contained in *sql_file* and return the count."""

    sql_text = sql_file.read_text(encoding="utf-8")
    statements = [stmt for stmt in iter_statements(sql_text) if stmt]

    if not statements:
        LOGGER.warning("No executable statements detected in %s", sql_file)
        return 0

    LOGGER.info("▶ Executing %s (%d statements)", sql_file.name, len(statements))
    executed = 0
    for idx, statement in enumerate(statements, start=1):
        LOGGER.debug("SQL #%d from %s:\n%s", idx, sql_file.name, statement)
        if dry_run:
            executed += 1
            continue
        client.execute(statement)
        executed += 1
    return executed


def discover_sql_files(folder: Path) -> List[Path]:
    if not folder.exists():
        raise FileNotFoundError(f"SQL directory not found: {folder}")
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".sql")
    if not files:
        raise FileNotFoundError(f"No .sql files found in {folder}")
    return files


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if ClickHouseClient is None:
        LOGGER.error("clickhouse-driver is not installed. Run 'pip install clickhouse-driver'.")
        return 2

    sql_files = discover_sql_files(args.scripts_dir)
    LOGGER.info("Preparing to run %d SQL files from %s", len(sql_files), args.scripts_dir)

    client = ClickHouseClient(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password if args.password is not None else None,
        database=args.database,
        connect_timeout=5,
    )

    if not args.dry_run:
        client.execute(f"CREATE DATABASE IF NOT EXISTS {args.database}")
        LOGGER.info("Database '%s' ensured.", args.database)

    total_statements = 0
    for sql_file in sql_files:
        total_statements += execute_sql_file(client, sql_file, dry_run=args.dry_run)

    LOGGER.info("Completed execution (%d statements).", total_statements)

    if not args.dry_run:
        tables = client.execute(f"SHOW TABLES IN {args.database}")
        table_list = ", ".join(row[0] for row in tables)
        LOGGER.info("Current tables in %s: %s", args.database, table_list or "<none>")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
