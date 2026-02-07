# Contributing to VertiFlow
## Document Reference: TICKET-116
**Date**: January 3, 2026  
**Version**: 1.0.0  
**Author/Team**: @MrZakaria (Project Lead), @Mounir (Architect)  
**Status**: Production  
**Classification**: Public  
**Last Modified**: 2026-01-03  

---

## Welcome to VertiFlow! 🌱

VertiFlow is an open-source industrial data platform for intelligent vertical farming. We welcome contributions from engineers, data scientists, agronomists, and enthusiasts worldwide. This guide provides everything you need to contribute effectively.

**Quick Links:**
- [Repository](https://github.com/J-Mounir/test-projet-agri)
- [Issues](https://github.com/J-Mounir/test-projet-agri/issues)
- [Discussions](https://github.com/J-Mounir/test-projet-agri/discussions)
- [Project Board](https://github.com/users/J-Mounir/projects/1)

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Commit Guidelines](#commit-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Coding Standards](#coding-standards)
8. [Testing Requirements](#testing-requirements)
9. [Documentation](#documentation)
10. [Review Process](#review-process)

---

## Code of Conduct

All contributors must adhere to our Code of Conduct:

**Our Pledge:**
We are committed to providing a welcoming and inclusive environment for all contributors regardless of age, body size, disability, ethnicity, gender identity, experience level, nationality, personal appearance, political belief, race, religion, sexual identity, or sexual orientation.

**Our Standards:**

✅ **Expected Behavior:**
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members
- Acknowledge and appreciate contributions

❌ **Unacceptable Behavior:**
- Harassment, intimidation, or discrimination
- Sexist, racist, or other derogatory language
- Unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, personal attacks
- Publishing others' private information without consent
- Violence, threats of violence, or violent language
- Advocating for or encouraging any of the above behaviors

**Enforcement:**
Violations of the Code of Conduct will be addressed by the project maintainers. Report violations to @MrZakaria or @Mounir. All complaints will be reviewed and investigated confidentially.

---

## Getting Started

### 1.1 Prerequisites

Before you begin, ensure you have:

```bash
# Required
- Python 3.11+
- Git 2.30+
- Docker & Docker Compose 2.0+
# Note: PostgreSQL n'est PAS requis - ClickHouse + MongoDB sont utilises
# - PostgreSQL 14+ (NON UTILISE - voir ARCHITECTURE_DECISIONS.md)
- Redis 7.0+ (for caching, optional)

# Recommended
- VS Code with Python extension
- Git extensions (GitLens, GitHub)
- Docker Desktop GUI
- Postman or curl (API testing)
```

### 1.2 Fork & Clone Repository

```bash
# 1. Fork the repository on GitHub
#    Click "Fork" button on https://github.com/J-Mounir/test-projet-agri

# 2. Clone your fork locally
git clone https://github.com/YOUR_USERNAME/test-projet-agri.git
cd test-projet-agri

# 3. Add upstream remote (sync with original)
git remote add upstream https://github.com/J-Mounir/test-projet-agri.git

# 4. Verify remotes
git remote -v
# Output:
# origin    https://github.com/YOUR_USERNAME/test-projet-agri.git (fetch)
# origin    https://github.com/YOUR_USERNAME/test-projet-agri.git (push)
# upstream  https://github.com/J-Mounir/test-projet-agri.git (fetch)
# upstream  https://github.com/J-Mounir/test-projet-agri.git (push)
```

### 1.3 Create Feature Branch

```bash
# Ensure you're on main and up-to-date
git checkout main
git pull upstream main

# Create a feature branch (naming convention below)
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b bugfix/issue-description

# Or for documentation:
git checkout -b docs/documentation-topic
```

**Branch Naming Convention:**
```
feature/<short-description>      # New features: feature/ml-model-optimization
bugfix/<issue-number>             # Bug fixes: bugfix/TICKET-105-kafka-lag
docs/<topic>                      # Documentation: docs/api-endpoints
refactor/<scope>                  # Refactoring: refactor/simulator-module
test/<area>                       # Test improvements: test/integration-suite
chore/<task>                      # Maintenance: chore/dependency-upgrade
```

---

## Development Setup

### 2.1 Local Environment Setup

```bash
# 1. Navigate to project root
cd vertiflow-data-platform

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# 5. Install dependencies
pip install -r requirements.txt

# 6. Install development dependencies
pip install -r requirements-dev.txt

# 7. Install pre-commit hooks (automatic linting/formatting on commit)
pre-commit install

# 8. Verify installation
python --version
python -c "import cloud_citadel; print('VertiFlow loaded successfully')"
```

### 2.2 Docker Compose Setup

```bash
# 1. Start all services (development environment)
docker-compose -f docker-compose.yml up -d

# 2. Verify services are running
docker-compose ps

# Output:
# NAME                    COMMAND                  SERVICE      STATUS      PORTS
# vertiflow-kafka         "/docker-entrypoint.s…" kafka        Up 2 mins   9092->9092/tcp
# vertiflow-zookeeper     "/docker-entrypoint.s…" zookeeper    Up 2 mins   2181->2181/tcp
# vertiflow-clickhouse    "/entrypoint.sh"        clickhouse   Up 2 mins   8123->8123/tcp, 9000->9000/tcp
# vertiflow-mongodb       "docker-entrypoint.s…" mongodb      Up 2 mins   27017->27017/tcp
# vertiflow-mosquitto     "/docker-entrypoint.s…" mosquitto    Up 2 mins   1883->1883/tcp
# vertiflow-nifi          "/opt/nifi/bin/nifi.…" nifi         Up 2 mins   8161->8161/tcp
# vertiflow-redis         "redis-server --appe…" redis        Up 2 mins   6379->6379/tcp

# 3. Check service logs
docker-compose logs -f kafka    # Follow Kafka logs
docker-compose logs clickhouse  # View ClickHouse logs

# 4. Stop services when done
docker-compose down

# 5. Remove volumes and restart fresh (careful!)
docker-compose down -v && docker-compose up -d
```

### 2.3 Database Initialization

```bash
# 1. Initialize ClickHouse schema
python scripts/init_clickhouse.py

# 2. Initialize MongoDB collections
python scripts/init_mongodb.py

# 3. Create Kafka topics
python scripts/init_kafka_topics.py

# 4. Verify connectivity
python scripts/validate_deployment.py

# Output:
# ✅ ClickHouse connection: OK
# ✅ MongoDB connection: OK
# ✅ Kafka broker: OK (3 brokers)
# ✅ Redis connection: OK
# ✅ MQTT broker: OK
# ✅ All systems operational
```

### 2.4 IDE Configuration

**VS Code settings (.vscode/settings.json):**

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ]
}
```

**Recommended Extensions:**
- Python (ms-python.python)
- GitLens (eamodio.gitlens)
- Docker (ms-azuretools.vscode-docker)
- Pylance (ms-python.vscode-pylance)
- Error Lens (usernamehw.errorlens)

---

## Making Changes

### 3.1 Code Areas & Ownership

**Core Modules (Contact for questions):**

```
cloud_citadel/
├── nervous_system/
│   ├── classifier.py          → @Asama (Quality classification)
│   ├── cortex.py              → @Mounir (Optimization algorithms)
│   ├── oracle.py              → @Mounir (ML predictions)
│   ├── simulator.py           → @Asama (Bio-physics simulations)
│   └── nervous_system.py      → @Mounir (Main coordination)
│
└── connectors/
    ├── feedback_loop.py       → @Mounir (Quality feedback)
    ├── stream_processor.py    → @Mouhammed (Kafka processing)
    └── mqtt_integration.py    → @Imrane (IoT connectivity)

tests/
├── unit/                      → @Mounir (Core logic tests)
├── integration/               → @Imrane (End-to-end tests)
└── performance/               → @Imrane (Stress tests)

scripts/
├── etl/                       → @Mouhammed (Data pipelines)
├── simulators/                → @Asama (Bio-physics simulators)
└── infrastructure/            → @Imrane (DevOps scripts)

docs/
├── 01_ARCHITECTURE.md         → @Mounir
├── 02_DATA_GOVERNANCE.md      → @Mounir
├── 03_DATA_CATALOG.md         → @Mouhammed
└── 05_EXTERNAL_DATA_CATALOG.md → @Mouhammed
```

### 3.2 Making Your Changes

```bash
# 1. Make your code changes in your editor
# 2. Run formatter before committing
black cloud_citadel/ tests/

# 3. Run linter to catch issues
pylint cloud_citadel/

# 4. Run type checker
mypy cloud_citadel/

# 5. Run tests (see Testing section below)
pytest tests/ -v

# 6. Check code coverage
pytest tests/ --cov=cloud_citadel

# 7. Stage changes
git add cloud_citadel/module/file.py
git add tests/unit/test_file.py

# 8. Commit with clear message (see Commit Guidelines below)
git commit -m "feat: add optimization algorithm for cortex module

- Implements Particle Swarm Optimization (PSO)
- Targets 15% improvement in yield vs baseline
- Adds 8 unit tests with parameterized inputs
- Fixes TICKET-105"

# 9. Push to your fork
git push origin feature/your-feature-name

# 10. Create Pull Request on GitHub
```

---

## Commit Guidelines

### 4.1 Commit Message Format

Follow the **Conventional Commits** standard for clear, automated change tracking:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Components:**

- **type**: Category of change
- **scope**: Which module/component affected
- **subject**: Brief summary (50 chars max, imperative mood)
- **body**: Detailed explanation (72 chars per line)
- **footer**: References to issues, breaking changes

### 4.2 Commit Types

```
feat      Feature (new capability)
fix       Bug fix
docs      Documentation only
style     Code style (formatting, missing semicolons)
refactor  Code refactoring (no feature/fix)
perf      Performance improvement
test      Test additions/modifications
chore     Build, dependency, tooling changes
ci        CI/CD configuration
```

### 4.3 Examples

**Good Commit:**

```
feat(cortex): implement particle swarm optimization

- Replace scipy.optimize with PSO algorithm
- Improves convergence speed by 20% on test suite
- Adds parameter bounds validation
- Increases computational efficiency for large datasets

Fixes TICKET-105
Related to TICKET-98, TICKET-102
```

**Bad Commits (avoid):**

```
❌ "Updated files"
❌ "Fix bug"
❌ "WIP: stuff"
❌ "asdf"
❌ "Updated cortex and simulator"
```

### 4.4 Commit Best Practices

```bash
# 1. Keep commits atomic (one logical change per commit)
✅ One commit: Add feature A
✅ One commit: Add tests for feature A
✅ One commit: Update documentation for feature A

❌ Avoid: Add feature A + fix unrelated bug + update docs

# 2. Write clear, detailed commit messages
git commit -m "Short summary" -m "Longer description here"

# 3. Sign commits (optional but recommended)
git commit -S -m "Signed commit"

# 4. Amend last commit if needed
git commit --amend --no-edit    # Add staged changes to last commit

# 5. View commit history
git log --oneline -10
git log --graph --oneline --all
```

---

## Pull Request Process

### 5.1 Creating a Pull Request

**Before Submitting:**

```bash
# 1. Update your branch with latest main
git fetch upstream
git rebase upstream/main

# 2. Run all checks locally
black --check cloud_citadel/ tests/
pylint cloud_citadel/
mypy cloud_citadel/
pytest tests/ -v

# 3. Ensure no conflicts
git status  # Should be clean

# 4. Push to your fork
git push origin feature/your-feature-name -f  # -f if rebased

# 5. Create PR on GitHub
#    - Go to https://github.com/YOUR_USERNAME/test-projet-agri
#    - Click "New Pull Request"
#    - Compare: upstream/main ← YOUR_FORK/feature/your-feature-name
```

### 5.2 PR Description Template

```markdown
## Description
Brief explanation of changes

## Type of Change
- [ ] New feature (TICKET-XXX)
- [ ] Bug fix (TICKET-XXX)
- [ ] Breaking change (TICKET-XXX)
- [ ] Documentation update

## Related Issue
Fixes #<issue-number>
Related to #<issue-number>

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Added tests for new features
- [ ] Commits follow conventional format

## Screenshots (if applicable)
[Images showing visual changes]

## Performance Impact
[If applicable: metrics showing performance effect]
```

### 5.3 PR Review Process

```
Your PR
  ↓
Automated Checks (GitHub Actions)
  ├─ ✅ Linting passed
  ├─ ✅ Tests passed
  ├─ ✅ Type checking passed
  └─ ✅ Code coverage ≥ 80%
  ↓
Manual Review (1-2 maintainers)
  ├─ Code quality assessment
  ├─ Architecture compliance
  ├─ Test adequacy
  ├─ Documentation completeness
  └─ Suggestions/approval
  ↓
Changes Requested? 
  ├─ YES: Make updates, reply to comments, push new commits
  └─ NO: Proceed to merge
  ↓
Merge to main
  ↓
Deploy (after all tests pass)
```

### 5.4 Review Expectations

**Timeline:**
- Feature PRs: Review within 48-72 hours
- Bug fixes: Review within 24 hours
- Documentation: Review within 48 hours
- Urgent/critical: Review ASAP (within 4 hours)

**Feedback Policy:**
- Be respectful and constructive
- Provide specific suggestions, not vague complaints
- Link relevant documentation/standards
- Acknowledge good work and improvements

---

## Coding Standards

### 6.1 Python Style Guide

We follow **PEP 8** with modifications:

```python
# Imports (alphabetical, grouped)
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from kafka import KafkaProducer
from sqlalchemy import create_engine

# Constants (UPPER_CASE)
MAX_BATCH_SIZE = 1000
DEFAULT_TIMEOUT_SECONDS = 30
SUPPORTED_CROPS = ["basil", "lettuce", "microgreens"]

# Type hints (mandatory for public functions)
def calculate_growth_rate(
    biomass_current: float,
    biomass_previous: float,
    hours_elapsed: float,
) -> float:
    """
    Calculate hourly biomass growth rate.
    
    Args:
        biomass_current: Current plant biomass in grams
        biomass_previous: Previous measurement in grams
        hours_elapsed: Hours between measurements
    
    Returns:
        Growth rate in grams per hour
    
    Raises:
        ValueError: If hours_elapsed <= 0
        TypeError: If inputs not numeric
    
    Example:
        >>> growth_rate = calculate_growth_rate(12.5, 10.2, 24)
        >>> growth_rate
        0.0958  # grams/hour
    """
    if hours_elapsed <= 0:
        raise ValueError("hours_elapsed must be positive")
    
    return (biomass_current - biomass_previous) / hours_elapsed


# Class definitions with docstrings
class PlantSimulator:
    """
    Simulates plant growth using Farquhar photosynthesis model.
    
    Attributes:
        crop_id (str): Identifier for crop type
        facility_id (str): Associated facility
        simulation_time (datetime): Current simulation timestamp
    """
    
    def __init__(self, crop_id: str, facility_id: str) -> None:
        """Initialize plant simulator."""
        self.crop_id = crop_id
        self.facility_id = facility_id
        self.simulation_time = datetime.utcnow()
    
    def simulate_photosynthesis(
        self,
        par: float,
        temp: float,
        humidity: float,
    ) -> Tuple[float, float]:
        """Calculate photosynthesis rate and transpiration."""
        # Implementation
        pass
```

**Key Standards:**
```
Line length: Maximum 100 characters
Indentation: 4 spaces (never tabs)
Naming:
  - Classes: PascalCase (PlantSimulator, QualityClassifier)
  - Functions: snake_case (calculate_growth_rate, validate_input)
  - Constants: UPPER_SNAKE_CASE (MAX_BATCH_SIZE, DEFAULT_TIMEOUT)
  - Private: _leading_underscore (_internal_method)
  
Docstrings: Google style (see example above)
Type hints: Always on public methods
Comments: Explain WHY, not WHAT (code shows what)
```

### 6.2 Testing Standards

**Pytest Conventions:**

```python
# tests/unit/test_simulator.py

import pytest
from cloud_citadel.nervous_system.simulator import PlantSimulator


class TestPlantSimulator:
    """Test suite for PlantSimulator module."""
    
    @pytest.fixture
    def simulator(self):
        """Create simulator instance for testing."""
        return PlantSimulator(crop_id="OCIM-BASI", facility_id="FAC-001")
    
    def test_initialization(self, simulator):
        """Test simulator initializes with correct values."""
        assert simulator.crop_id == "OCIM-BASI"
        assert simulator.facility_id == "FAC-001"
    
    @pytest.mark.parametrize("par,expected_min,expected_max", [
        (0, -0.5, 0),      # Dark respiration
        (500, 5, 8),       # Low light
        (1500, 15, 20),    # Optimal light
    ])
    def test_photosynthesis_par_response(
        self,
        simulator,
        par,
        expected_min,
        expected_max,
    ):
        """Test photosynthesis varies correctly with light intensity."""
        result = simulator.simulate_photosynthesis(
            par=par,
            temp=25,
            humidity=70,
        )
        assert expected_min <= result[0] <= expected_max
    
    def test_invalid_temperature_raises_error(self, simulator):
        """Test simulator rejects invalid temperatures."""
        with pytest.raises(ValueError):
            simulator.simulate_photosynthesis(
                par=1000,
                temp=-50,  # Below plant tolerance
                humidity=70,
            )
    
    @pytest.mark.slow
    def test_long_simulation(self, simulator):
        """Test extended simulation (marked slow for optional execution)."""
        # Expensive test
        pass
```

**Test Requirements:**
- Minimum 80% code coverage for new code
- All public methods tested
- Edge cases and error conditions tested
- Performance-critical code benchmarked

---

## Testing Requirements

### 7.1 Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_simulator.py

# Run specific test class
pytest tests/unit/test_simulator.py::TestPlantSimulator

# Run specific test
pytest tests/unit/test_simulator.py::TestPlantSimulator::test_initialization

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=cloud_citadel --cov-report=html

# Run only fast tests (skip slow)
pytest tests/ -m "not slow"

# Run with specific markers
pytest tests/ -m integration

# Run in parallel (faster)
pytest tests/ -n auto
```

### 7.2 Test Markers

```python
import pytest

# Mark slow tests (skip with: pytest -m "not slow")
@pytest.mark.slow
def test_extended_simulation():
    pass

# Mark integration tests
@pytest.mark.integration
def test_kafka_connectivity():
    pass

# Mark tests requiring docker
@pytest.mark.docker
def test_clickhouse_connection():
    pass
```

### 7.3 Coverage Requirements

```bash
# Minimum coverage standards:
# - Overall: 80%
# - Core modules: 90%
# - Tests themselves: No coverage requirement

# Generate coverage report
pytest tests/ --cov=cloud_citadel --cov-report=term-missing

# Example output:
# cloud_citadel/nervous_system/simulator.py   234   18   92%
# cloud_citadel/nervous_system/oracle.py      450   25   94%
# cloud_citadel/nervous_system/classifier.py  320   15   95%
# TOTAL                                       2104  120   94%
```

---

## Documentation

### 8.1 Code Documentation

**Module Docstring:**

```python
"""
VertiFlow Simulator Module - Bio-physics Growth Modeling

This module implements photosynthesis, transpiration, and growth simulations
using established agricultural science models:

- Farquhar model for photosynthesis (C3 plants)
- Penman-Monteith for transpiration
- Monod kinetics for nutrient uptake

References:
    Farquhar, G. D., et al. (1980). A biochemical model of photosynthetic 
    CO2 assimilation in leaves of C3 plants. Planta, 149(1), 78-90.

Example:
    Basic plant growth simulation::
    
        simulator = PlantSimulator("OCIM-BASI", "FAC-001")
        photosynthesis_rate = simulator.simulate_photosynthesis(
            par=1500,
            temp=24,
            humidity=70,
        )
"""
```

### 8.2 API Documentation

Update API docs in `docs/API_REFERENCE.md` for new endpoints:

```markdown
## POST /api/v1/facilities/{facility_id}/predictions

Generate crop growth predictions.

**Request:**
\`\`\`json
{
  "crop_id": "OCIM-BASI",
  "days_ahead": 14,
  "include_quality": true
}
\`\`\`

**Response:**
\`\`\`json
{
  "facility_id": "FAC-001",
  "predictions": [...],
  "confidence_interval": 0.95
}
\`\`\`

**Status Codes:**
- 200 OK: Prediction generated
- 400 Bad Request: Invalid parameters
- 404 Not Found: Facility not found
- 500 Internal Error: Processing failed
```

### 8.3 README Updates

Update relevant READMEs when adding features:

```markdown
## New Feature: Example Feature

### Overview
Brief explanation of the feature

### Usage
\`\`\`python
# Code example
\`\`\`

### Configuration
Document any config options

### Performance
Expected performance characteristics

### Testing
How to test the feature
```

---

## Review Process

### 9.1 Code Review Checklist

Reviewers will assess:

```
☐ Functionality
  ☐ Code implements stated requirements
  ☐ Fixes the reported issue
  ☐ No regressions introduced
  ☐ Edge cases handled

☐ Code Quality
  ☐ Follows style guide
  ☐ No obvious bugs or anti-patterns
  ☐ Clear variable/function names
  ☐ Proper error handling

☐ Testing
  ☐ Tests added for new code
  ☐ Tests cover edge cases
  ☐ All tests passing
  ☐ Coverage not decreased

☐ Documentation
  ☐ Code documented (docstrings)
  ☐ README/API docs updated
  ☐ Comments explain complex logic
  ☐ Examples provided if applicable

☐ Performance
  ☐ No significant performance regression
  ☐ Large O(n²) operations justified
  ☐ Memory usage reasonable
  ☐ Database queries optimized

☐ Security
  ☐ No hardcoded secrets
  ☐ Input validation present
  ☐ SQL injection not possible
  ☐ Auth/permissions checked
```

### 9.2 Feedback Types

**Request Changes** ❌
- Blocking issue that must be fixed before merge
- Example: Test coverage below 80%, syntax error, security issue

**Comment** 💬
- Non-blocking suggestion or question
- Example: "Consider using list comprehension here", "Does this handle X?"

**Approve** ✅
- Code ready to merge
- Example: "Looks great! LGTM"

### 9.3 After Review

```
If changes requested:
  1. Make the requested modifications
  2. Push new commits (don't force-push, shows iteration)
  3. Reply to reviewer comments
  4. Request re-review

If approved:
  1. Maintainer merges your PR
  2. Your branch is deleted
  3. Your code is live in main!
```

---

## Common Issues & Solutions

### 10.1 Pre-commit Hooks Failing

```bash
# Problem: Black/Pylint failing before commit
# Solution 1: Fix issues manually
black cloud_citadel/
pylint cloud_citadel/

# Solution 2: Skip pre-commit (not recommended)
git commit --no-verify

# Solution 3: Disable specific hook temporarily
git commit --no-verify -m "WIP: debugging"
```

### 10.2 Merge Conflicts

```bash
# Problem: Conflict when rebasing on main
# Solution:
git fetch upstream
git rebase upstream/main

# Resolve conflicts in editor, then:
git add <resolved-files>
git rebase --continue

# Or abort if too complex:
git rebase --abort
```

### 10.3 Lost Commits

```bash
# Problem: Accidentally reset commits
# Solution: Use reflog to find them
git reflog

# Output shows all your commits, even deleted ones
# Restore with:
git reset --hard abc1234
```

---

## Getting Help

- **Questions**: Use [GitHub Discussions](https://github.com/J-Mounir/test-projet-agri/discussions)
- **Bugs**: File an [Issue](https://github.com/J-Mounir/test-projet-agri/issues)
- **Chat**: Join our Slack/Discord (links in README)
- **Direct**: @MrZakaria (lead), @Mounir (architecture)

---

## Useful Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Google Docstring Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Pytest Documentation](https://docs.pytest.org/)
- [Git Documentation](https://git-scm.com/doc)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## Thank You! 🙏

Your contributions help make VertiFlow better. We appreciate:
- Code improvements
- Bug reports and fixes
- Documentation enhancements
- Performance optimizations
- Feature suggestions
- Testing efforts

Every contribution counts!

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-03 | @MrZakaria, @Mounir | Initial creation |

---

**Document Footer**

```
TICKET: TICKET-116
ASSIGNED TO: @MrZakaria (Project Lead), @Mounir (Architect)
TEAM: @MrZakaria, @Mounir, @Imrane, @Mouhammed, @Asama
PROJECT: VertiFlow Data Platform - Intelligent Vertical Farming
STATUS: Production Release
CLASSIFICATION: Public
NEXT REVIEW: 2026-04-03 (Quarterly)
REPOSITORY: J-Mounir/test-projet-agri (GitHub)
```

---

*This document is controlled and subject to change management procedures.*
*Last updated: 2026-01-03 | Next scheduled review: 2026-04-03*
