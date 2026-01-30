#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        VERTIFLOW™ DATA PLATFORM - KAFKA                      ║
║                        SCRIPT: scripts/init_kafka_topics.py                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Date            : 2026-01-04                                                 ║
║ Version         : 1.0.0                                                      ║
║ Ticket          : TICKET-136 (Streaming Backbone Hardening)                  ║
║ Squad           : Core Platform Operations                                   ║
║ Maintainer      : @Imrane (DevOps)                                           ║
║ Reviewers       : @Mounir (ML), @Mouhammed (Data)                             ║
║ Classification  : Interne - Confidentiel                                     ║
║ Purpose         : Créer et valider les topics Kafka critiques VertiFlow.     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError

LOGGER = logging.getLogger("vertiflow.init_kafka")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create VertiFlow Kafka topics.")
    parser.add_argument(
        "--bootstrap-servers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        help="Comma-separated list of brokers accessible from this host.",
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=5.0,
        help="Kafka request timeout in seconds (default: 5).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retries per topic before failing (default: 3).",
    )
    parser.add_argument(
        "--api-version",
        help="Force Kafka API version (ex: 2.6.0) to skip auto negotiation.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logs.",
    )
    return parser.parse_args(argv)


@dataclass(frozen=True)
class TopicPlan:
    name: str
    partitions: int
    replication_factor: int
    config: dict[str, str] | None = None


TOPICS: Sequence[TopicPlan] = (
    TopicPlan("basil_telemetry_full", partitions=6, replication_factor=1),
    TopicPlan("vertiflow.commands", partitions=3, replication_factor=1),
    TopicPlan("vertiflow.alerts", partitions=3, replication_factor=1),
    TopicPlan("dead_letter_queue", partitions=1, replication_factor=1, config={"retention.ms": str(7 * 24 * 60 * 60 * 1000)}),
    TopicPlan("vertiflow.quality_predictions", partitions=3, replication_factor=1),
    TopicPlan("vertiflow.recipe_updates", partitions=1, replication_factor=1),
)


def build_admin_client(args: argparse.Namespace) -> KafkaAdminClient:
    kwargs = {
        "bootstrap_servers": args.bootstrap_servers.split(","),
        "client_id": "vertiflow-init",
        "request_timeout_ms": int(args.request_timeout * 1000),
        "retry_backoff_ms": 250,
    }
    if args.api_version:
        kwargs["api_version"] = tuple(int(part) for part in args.api_version.split("."))
    return KafkaAdminClient(**kwargs)


def create_topic(admin: KafkaAdminClient, plan: TopicPlan, retries: int) -> None:
    new_topic = NewTopic(
        name=plan.name,
        num_partitions=plan.partitions,
        replication_factor=plan.replication_factor,
        topic_configs=plan.config,
    )
    for attempt in range(1, retries + 1):
        try:
            admin.create_topics(new_topics=[new_topic], validate_only=False)
            LOGGER.info("✓ Created topic %s (%d partitions)", plan.name, plan.partitions)
            return
        except TopicAlreadyExistsError:
            LOGGER.info("✓ Topic already exists: %s", plan.name)
            return
        except KafkaError as exc:  # pragma: no cover - network dependent
            if attempt >= retries:
                LOGGER.error("✗ Failed to create %s after %d attempts: %s", plan.name, attempt, exc)
                raise
            LOGGER.warning(
                "Topic %s creation failed (%s). Retrying %d/%d...",
                plan.name,
                exc,
                attempt,
                retries,
            )
            time.sleep(1.5 * attempt)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    admin = build_admin_client(args)
    LOGGER.info("Connected to Kafka via %s", args.bootstrap_servers)

    failures: List[str] = []
    for plan in TOPICS:
        try:
            create_topic(admin, plan, retries=args.retries)
        except KafkaError:
            failures.append(plan.name)

    if failures:
        LOGGER.error("Topic creation finished with failures: %s", ", ".join(failures))
        return 1

    LOGGER.info("Kafka topic bootstrap complete.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
