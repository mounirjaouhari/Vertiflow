#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PROJET VERTIFLOW - Agriculture Verticale Intelligente
================================================================================
Date de création    : 25/12/2025
Équipe              : VertiFlow Core Team

Membres de l'équipe :
    🧙‍♂️ Mounir      - Architecte & Scientifique (Python Dev)
    🏗️ Imrane      - DevOps & Infrastructure (Python Dev)
    🐍 Mouhammed   - Data Engineer & Analyste ETL
    🧬 Asama       - Biologiste & Domain Expert (Python Dev)
    ⚖️ MrZakaria   - Encadrant & Architecte Data

--------------------------------------------------------------------------------
MODULE: validate_deployment.py
DESCRIPTION: Validation script to check deployment readiness

Fonctionnalités principales:
    - Verify all required files exist
    - Validate Python syntax
    - Check YAML/JSON configurations
    - Verify Docker Compose files
    - Test Python imports

Développé par       : @Imrane
Ticket(s) associé(s): TICKET-004, TICKET-080
Sprint              : Semaine 1 - Phase Deployment

Dépendances:
    - pathlib: File system operations
    - yaml: Configuration validation
    - json: Schema validation

================================================================================
© 2025 VertiFlow Core Team - Tous droits réservés
Développé dans le cadre de l'Initiative Nationale Marocaine JobInTech
au sein de l'École YNOV Maroc Campus
================================================================================
"""

import sys
import os
from pathlib import Path
import subprocess
import json
import yaml

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print section header."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} missing: {filepath}")
        return False

def validate_python_syntax(filepath):
    """Validate Python file syntax."""
    try:
        result = subprocess.run(
            ['python3', '-m', 'py_compile', filepath],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True
        else:
            print_error(f"Syntax error in {filepath}: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Failed to validate {filepath}: {e}")
        return False

def validate_yaml(filepath):
    """Validate YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        return True
    except Exception as e:
        print_error(f"YAML error in {filepath}: {e}")
        return False

def validate_json(filepath):
    """Validate JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except Exception as e:
        print_error(f"JSON error in {filepath}: {e}")
        return False

def main():
    """Main validation routine."""
    print_header("VertiFlow Deployment Validation")
    
    errors = 0
    warnings = 0
    
    # Check required files
    print_header("1. Checking Required Files")
    
    required_files = [
        ('docker-compose.yml', 'Main infrastructure'),
        ('docker-compose.metrics.yml', 'Monitoring stack'),
        ('.env.example', 'Environment template'),
        ('.gitignore', 'Git ignore'),
        ('requirements.txt', 'Python dependencies'),
        ('README.md', 'Documentation'),
        ('DEPLOYMENT_GUIDE.md', 'Deployment guide'),
    ]
    
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            errors += 1
    
    # Check Python services
    print_header("2. Validating Python Services")
    
    python_files = [
        'cloud_citadel/nervous_system/cortex.py',
        'cloud_citadel/nervous_system/oracle.py',
        'cloud_citadel/nervous_system/simulator.py',
        'infrastructure/init_infrastructure.py',
        'scripts/setup_nifi_pipeline.py',
        'scripts/download_nasa_power.py',
    ]
    
    for filepath in python_files:
        if Path(filepath).exists():
            if validate_python_syntax(filepath):
                print_success(f"Valid: {filepath}")
            else:
                errors += 1
        else:
            print_error(f"Missing: {filepath}")
            errors += 1
    
    # Check YAML configurations
    print_header("3. Validating YAML Configurations")
    
    yaml_files = [
        'docker-compose.yml',
        'docker-compose.metrics.yml',
        'config/nifi_pipeline_dev.yaml',
        'config/nifi_pipeline_prod.yaml',
        'config/prometheus.yml',
        'config/external_data_sources.yaml',
        'cloud_citadel/nervous_system/calibration/agronomic_parameters.yaml',
    ]
    
    for filepath in yaml_files:
        if Path(filepath).exists():
            if validate_yaml(filepath):
                print_success(f"Valid: {filepath}")
            else:
                errors += 1
        else:
            print_error(f"Missing: {filepath}")
            errors += 1
    
    # Check JSON schemas
    print_header("4. Validating JSON Schemas")
    
    json_files = [
        'docs/schemas/telemetry_v3.json',
        'docs/schemas/command_v3.json',
        'cloud_citadel/nervous_system/connectors/clickhouse_sink.json',
    ]
    
    for filepath in json_files:
        if Path(filepath).exists():
            if validate_json(filepath):
                print_success(f"Valid: {filepath}")
            else:
                errors += 1
        else:
            print_error(f"Missing: {filepath}")
            errors += 1
    
    # Check SQL scripts
    print_header("5. Checking SQL Scripts")
    
    sql_files = [
        'infrastructure/init_scripts/clickhouse/01_tables.sql',
        'infrastructure/init_scripts/clickhouse/02_powerbi_views.sql',
        'infrastructure/init_scripts/clickhouse/03_external_data.sql',
    ]
    
    for filepath in sql_files:
        if check_file_exists(filepath, 'SQL script'):
            pass
        else:
            errors += 1
    
    # Check documentation
    print_header("6. Checking Documentation")
    
    doc_files = [
        'docs/01_ARCHITECTURE.md',
        'docs/02_DATA_GOVERNANCE.md',
        'docs/03_DATA_CATALOG.md',
        'docs/05_EXTERNAL_DATA_CATALOG.md',
    ]
    
    for filepath in doc_files:
        if check_file_exists(filepath, 'Documentation'):
            pass
        else:
            warnings += 1
    
    # Test Python imports
    print_header("7. Testing Python Imports")
    
    try:
        import numpy
        print_success("numpy imported successfully")
    except ImportError:
        print_warning("numpy not installed (run: pip install -r requirements.txt)")
        warnings += 1
    
    try:
        import yaml
        print_success("pyyaml imported successfully")
    except ImportError:
        print_warning("pyyaml not installed")
        warnings += 1
    
    # Final summary
    print_header("Validation Summary")
    
    if errors == 0 and warnings == 0:
        print_success(f"All checks passed! ✓")
        print(f"\n{GREEN}Project is ready for deployment!{RESET}\n")
        print("Next steps:")
        print("  1. docker-compose up -d")
        print("  2. python3 infrastructure/init_infrastructure.py")
        print("  3. Access services (see DEPLOYMENT_GUIDE.md)")
        return 0
    elif errors == 0:
        print_success(f"All critical checks passed ✓")
        print_warning(f"{warnings} warning(s) found")
        print(f"\n{YELLOW}Project is ready but has warnings{RESET}\n")
        return 0
    else:
        print_error(f"{errors} error(s) found")
        print_warning(f"{warnings} warning(s) found")
        print(f"\n{RED}Project has issues that need to be fixed{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
