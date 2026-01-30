#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de creation    : 15/01/2026
Equipe              : VertiFlow Core Team

--------------------------------------------------------------------------------
MODULE: blockchain_hash_processor.py
DESCRIPTION: Processeur NiFi pour generer blockchain_hash et audit_trail_signature

Ce script est concu pour etre utilise avec le processeur ExecuteScript de NiFi.
Il ajoute deux champs de tracabilite a chaque enregistrement JSON:
    - blockchain_hash: Hash SHA-256 du contenu (preuve d'integrite)
    - audit_trail_signature: Signature HMAC pour verification d'origine

Usage dans NiFi:
    1. Ajouter un processeur ExecuteScript (Python)
    2. Pointer vers ce script
    3. Placer AVANT le processeur PutDatabaseRecord (ClickHouse)

Developpe par        : @VertiFlow Core Team
Ticket(s) associe(s): TICKET-BLOCKCHAIN-001
================================================================================
"""

import json
import hashlib
import hmac
import sys
from datetime import datetime, timezone

# ============================================================================
# CONFIGURATION
# ============================================================================

# Cle secrete pour HMAC (en production, utiliser une variable d'environnement)
# Cette cle doit etre la meme sur tous les noeuds pour verification
HMAC_SECRET_KEY = b'vertiflow_audit_key_2026_maroc'

# Version du schema de hash (pour evolution future)
HASH_SCHEMA_VERSION = "v1.0"


# ============================================================================
# FONCTIONS DE HASH
# ============================================================================

def generate_blockchain_hash(data: dict) -> str:
    """
    Genere un hash SHA-256 deterministe pour un enregistrement.

    Le hash est calcule sur les donnees triees par cle pour garantir
    la reproductibilite (meme donnees = meme hash).

    Args:
        data: Dictionnaire des donnees a hasher

    Returns:
        Hash SHA-256 en hexadecimal (64 caracteres)
    """
    # Exclure les champs de hash existants pour eviter la recursion
    data_to_hash = {k: v for k, v in data.items()
                    if k not in ('blockchain_hash', 'audit_trail_signature')}

    # Serialiser de maniere deterministe (cles triees, separateurs fixes)
    content = json.dumps(data_to_hash, sort_keys=True, separators=(',', ':'))

    # Generer le hash SHA-256
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def generate_audit_signature(data: dict, blockchain_hash: str) -> str:
    """
    Genere une signature HMAC-SHA256 pour l'audit trail.

    Cette signature permet de verifier que les donnees proviennent
    bien du pipeline VertiFlow et n'ont pas ete alterees.

    Args:
        data: Dictionnaire des donnees originales
        blockchain_hash: Hash SHA-256 deja calcule

    Returns:
        Signature HMAC en hexadecimal (64 caracteres)
    """
    # Construire le message a signer
    # Inclut: hash + timestamp + farm_id + version
    timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
    farm_id = data.get('farm_id', 'UNKNOWN')

    message = f"{HASH_SCHEMA_VERSION}:{blockchain_hash}:{timestamp}:{farm_id}"

    # Generer la signature HMAC-SHA256
    signature = hmac.new(
        HMAC_SECRET_KEY,
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


def process_record(record: dict) -> dict:
    """
    Traite un enregistrement et ajoute les champs de tracabilite.

    Args:
        record: Enregistrement JSON original

    Returns:
        Enregistrement enrichi avec blockchain_hash et audit_trail_signature
    """
    # Generer le hash blockchain
    blockchain_hash = generate_blockchain_hash(record)

    # Generer la signature d'audit
    audit_signature = generate_audit_signature(record, blockchain_hash)

    # Ajouter les champs
    record['blockchain_hash'] = blockchain_hash
    record['audit_trail_signature'] = audit_signature

    return record


# ============================================================================
# INTEGRATION NIFI - ExecuteScript
# ============================================================================

def nifi_process(flowfile):
    """
    Point d'entree pour le processeur ExecuteScript de NiFi.

    Cette fonction est appelee par NiFi pour chaque FlowFile.
    Elle lit le contenu JSON, ajoute les hash, et ecrit le resultat.
    """
    from org.apache.nifi.processor.io import StreamCallback
    from java.io import BufferedReader, InputStreamReader, OutputStreamWriter

    class HashCallback(StreamCallback):
        def process(self, inputStream, outputStream):
            # Lire le contenu JSON
            reader = BufferedReader(InputStreamReader(inputStream, 'UTF-8'))
            content = ''
            line = reader.readLine()
            while line is not None:
                content += line
                line = reader.readLine()
            reader.close()

            # Parser et enrichir
            try:
                record = json.loads(content)
                enriched = process_record(record)
                output = json.dumps(enriched, ensure_ascii=False)
            except json.JSONDecodeError:
                # En cas d'erreur, retourner le contenu original
                output = content

            # Ecrire le resultat
            writer = OutputStreamWriter(outputStream, 'UTF-8')
            writer.write(output)
            writer.flush()
            writer.close()

    return flowfile.write(HashCallback())


# ============================================================================
# MODE STANDALONE - Pour tests et batch processing
# ============================================================================

def process_file(input_path: str, output_path: str = None) -> dict:
    """
    Traite un fichier JSON et ajoute les hash de tracabilite.

    Args:
        input_path: Chemin du fichier JSON d'entree
        output_path: Chemin de sortie (optionnel, ecrase l'original si non fourni)

    Returns:
        Enregistrement enrichi
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        record = json.load(f)

    enriched = process_record(record)

    output = output_path or input_path
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    return enriched


def process_csv_batch(input_csv: str, output_csv: str) -> int:
    """
    Traite un fichier CSV en batch et ajoute les hash.

    Cette fonction est utile pour traiter des exports existants
    comme basil_ultimate_realtime1.csv.

    Args:
        input_csv: Chemin du CSV d'entree
        output_csv: Chemin du CSV de sortie

    Returns:
        Nombre de lignes traitees
    """
    import csv

    count = 0

    with open(input_csv, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['blockchain_hash', 'audit_trail_signature']

        with open(output_csv, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                enriched = process_record(dict(row))
                writer.writerow(enriched)
                count += 1

    return count


def verify_hash(record: dict) -> bool:
    """
    Verifie l'integrite d'un enregistrement via son hash.

    Args:
        record: Enregistrement avec blockchain_hash

    Returns:
        True si le hash est valide, False sinon
    """
    stored_hash = record.get('blockchain_hash', '')
    if not stored_hash:
        return False

    # Recalculer le hash
    computed_hash = generate_blockchain_hash(record)

    return hmac.compare_digest(stored_hash, computed_hash)


def verify_signature(record: dict) -> bool:
    """
    Verifie la signature d'audit d'un enregistrement.

    Args:
        record: Enregistrement avec audit_trail_signature

    Returns:
        True si la signature est valide, False sinon
    """
    stored_sig = record.get('audit_trail_signature', '')
    stored_hash = record.get('blockchain_hash', '')

    if not stored_sig or not stored_hash:
        return False

    # Recalculer la signature
    computed_sig = generate_audit_signature(record, stored_hash)

    return hmac.compare_digest(stored_sig, computed_sig)


# ============================================================================
# MAIN - Demo et tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("VERTIFLOW - Blockchain Hash Processor")
    print("=" * 70)

    # Donnees de test
    test_record = {
        "timestamp": "2026-01-15T12:00:00.000Z",
        "farm_id": "VERT-MAROC-01",
        "parcel_id": "830-AB-123",
        "rack_id": "R01",
        "level_index": 1,
        "air_temp_internal": 24.5,
        "health_score": 0.92,
        "lineage_uuid": "test-uuid-12345"
    }

    print("\n[1] Donnees originales:")
    print(json.dumps(test_record, indent=2))

    # Ajouter les hash
    enriched = process_record(test_record.copy())

    print("\n[2] Donnees enrichies:")
    print(f"  blockchain_hash:        {enriched['blockchain_hash']}")
    print(f"  audit_trail_signature:  {enriched['audit_trail_signature']}")

    # Verification
    print("\n[3] Verification:")
    print(f"  Hash valide:      {verify_hash(enriched)}")
    print(f"  Signature valide: {verify_signature(enriched)}")

    # Test de tampering
    print("\n[4] Test de tampering (modification air_temp):")
    tampered = enriched.copy()
    tampered['air_temp_internal'] = 30.0  # Modification malveillante
    print(f"  Hash valide apres modification: {verify_hash(tampered)}")

    print("\n" + "=" * 70)
    print("Script pret pour integration NiFi ExecuteScript")
    print("=" * 70)
