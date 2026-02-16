# Contributing to Agri-Copilot Pro

Thank you for your interest in contributing to Agri-Copilot Pro! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and professional in all interactions. We're committed to providing a welcoming and inclusive environment.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title describing the bug
   - Detailed description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment info (OS, Python version, etc.)
   - Screenshots if applicable

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear title
   - Detailed description of the feature
   - Use cases and benefits
   - Possible implementation approach
   - Any related context

### Submitting Code

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/agri-copilot-pro.git
   cd agri-copilot-pro
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   make dev
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **Make your changes**
   - Follow code style guidelines (see below)
   - Add tests for new functionality
   - Update documentation as needed
   - Write clear commit messages

6. **Run tests and linters**
   ```bash
   make test
   make lint
   make format
   ```

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**
   - Clear title describing changes
   - Link to related issues
   - Explanation of changes
   - Screenshots/demos if applicable

## Development Guidelines

### Code Style

We follow PEP 8 with some customizations:

- **Line length**: 88 characters (use Black formatter)
- **Quotes**: Single quotes for strings
- **Imports**: Use isort for import ordering

### Formatting & Linting

```bash
# Format code
black src/ tests/
isort src/ tests/

# Run linters
flake8 src/ tests/
pylint src/

# Type checking
mypy src/
```

### Testing

- Write tests for all new features
- Maintain >80% code coverage
- Tests should be in `tests/` directory
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Documentation

- Add docstrings to all functions and classes
- Use Google-style docstrings
- Update README.md if adding features
- Add inline comments for complex logic

Example docstring:
```python
def calculate_yield(plants: int, harvest_weight: float) -> float:
    """
    Calculate yield per plant.
    
    Args:
        plants: Number of plants
        harvest_weight: Total harvest weight in kg
        
    Returns:
        Yield per plant in kg
        
    Raises:
        ValueError: If plants is zero or negative
    """
```

## Directory Structure

```
src/
├── api/           # API clients and utilities
├── core/          # Core functionality
├── models/        # Data models and schemas
├── services/      # Business logic services
└── utils/         # Helper utilities

tests/
├── unit/          # Unit tests
└── integration/   # Integration tests
```

## Adding New Features

1. **Create service** in `src/services/`
2. **Create models** in `src/models/`
3. **Add API endpoints** in `main.py` if needed
4. **Write tests** in `tests/`
5. **Update documentation**

## Database Migrations

If adding new database schema:

1. Create migration with Alembic
2. Test migration up and down
3. Document schema changes
4. Include migration in PR

## Security Considerations

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Validate and sanitize all inputs
- Review security guidelines in code comments
- Report security issues privately to security@vertiflow.io

## Commit Messages

Follow conventional commits:

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(auth): add OAuth2 support`
- `fix(query): handle empty result sets correctly`
- `docs(readme): update installation instructions`

## Pull Request Process

1. Ensure all tests pass
2. Include test coverage for new code
3. Update documentation
4. Add entry to CHANGELOG.md
5. Request review from maintainers
6. Address feedback and comments
7. Squash commits if requested
8. Merge will be done by maintainers

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

## Getting Help

- **Questions**: Open discussion in GitHub Discussions
- **Issues**: Use GitHub Issues for bugs/features
- **Email**: dev@vertiflow.io for direct contact
- **Slack**: Join our community Slack workspace

## Development Tips

### Using the Development Environment

```bash
# Run API server
make run-api

# Run UI
make run-ui

# Run both
make run-both

# Run with Docker
make docker-up
```

### Common Tasks

```bash
# Create virtual environment
make setup

# Installation
make install

# Running tests
make test
make test-cov

# Code quality
make lint
make format

# Cleaning
make clean
```

### Debugging

Set environment variable for verbose logging:
```bash
export LOG_LEVEL=DEBUG
```

## Code Review Guidelines

When reviewing code:
- Be constructive and respectful
- Ask questions to understand intent
- Suggest improvements, don't demand
- Approve when satisfied
- Re-request changes if needed

## Attribution

Contributors will be credited in:
- CHANGELOG.md
- GitHub contributors page
- Project documentation

## Questions?

Feel free to reach out:
- Create an issue with `[question]` label
- Start a discussion in GitHub Discussions
- Email dev@vertiflow.io

Thank you for contributing! 🌿
