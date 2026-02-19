# Contributing to BIST30 AI Trader

Thank you for your interest in contributing to BIST30 AI Trader! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Git
- PostgreSQL with TimescaleDB
- Basic understanding of machine learning and trading concepts

### Setting Up Development Environment

1. **Fork and clone the repository**
```bash
git clone https://github.com/yourusername/bist30_ai_trader.git
cd bist30_ai_trader
```

2. **Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Set up pre-commit hooks**
```bash
pre-commit install
```

5. **Run tests to verify setup**
```bash
pytest
```

## 🔄 Development Process

### Branching Strategy

We use a simplified Git Flow:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Workflow

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
- Write code
- Add tests
- Update documentation

3. **Commit your changes**
```bash
git add .
git commit -m "feat: add amazing feature"
```

4. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

5. **Open a Pull Request**

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(models): add CatBoost ranking model
fix(backtest): correct slippage calculation
docs(readme): update installation instructions
test(ranking): add property-based tests
```

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- Line length: 100 characters (not 79)
- Use double quotes for strings
- Use type hints for function signatures

### Code Formatting

We use `black` for code formatting:

```bash
# Format all files
black .

# Check formatting
black --check .
```

### Import Organization

Use `isort` for import sorting:

```bash
# Sort imports
isort .

# Check import sorting
isort --check .
```

### Linting

We use `flake8` for linting:

```bash
# Run linter
flake8 .
```

### Type Checking

We use `mypy` for type checking:

```bash
# Run type checker
mypy .
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_sharpe_ratio(returns: pd.Series) -> float:
    """Calculate annualized Sharpe ratio.
    
    Args:
        returns: Series of daily returns
        
    Returns:
        Annualized Sharpe ratio
        
    Raises:
        ValueError: If returns series is empty
        
    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03])
        >>> sharpe = calculate_sharpe_ratio(returns)
        >>> print(f"Sharpe: {sharpe:.2f}")
    """
    if returns.std() == 0:
        return 0.0
    return np.sqrt(252) * returns.mean() / returns.std()
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── property/          # Property-based tests
└── fixtures/          # Test fixtures
```

### Writing Tests

1. **Unit Tests**
```python
def test_calculate_sharpe_ratio():
    """Test Sharpe ratio calculation."""
    returns = pd.Series([0.01, -0.01, 0.02])
    sharpe = calculate_sharpe_ratio(returns)
    assert isinstance(sharpe, float)
    assert sharpe > 0
```

2. **Property-Based Tests**
```python
from hypothesis import given, strategies as st

@given(st.lists(st.floats(min_value=-0.1, max_value=0.1), min_size=10))
def test_sharpe_ratio_properties(returns):
    """Test Sharpe ratio properties."""
    sharpe = calculate_sharpe_ratio(pd.Series(returns))
    assert -10 <= sharpe <= 10  # Reasonable bounds
```

3. **Integration Tests**
```python
def test_backtest_integration():
    """Test full backtest pipeline."""
    engine = BacktestEngine()
    results = engine.run(start_date="2023-01-01", end_date="2023-12-31")
    assert "total_return" in results
    assert "sharpe_ratio" in results
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ranking_model.py

# Run specific test
pytest tests/test_ranking_model.py::test_train_model

# Run property-based tests
pytest tests/ -k "property"

# Run with verbose output
pytest -v
```

### Test Coverage

- Aim for >80% code coverage
- All new features must include tests
- Bug fixes should include regression tests

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include type hints
- Provide usage examples
- Document exceptions

### User Documentation

- Update README.md for user-facing changes
- Add examples to docs/ directory
- Update API documentation
- Include screenshots for UI changes

### Inline Comments

- Use comments sparingly
- Explain "why", not "what"
- Keep comments up-to-date

## 🔀 Pull Request Process

### Before Submitting

1. **Update your branch**
```bash
git fetch upstream
git rebase upstream/main
```

2. **Run all checks**
```bash
# Format code
black .
isort .

# Run linter
flake8 .

# Run tests
pytest

# Check types
mypy .
```

3. **Update documentation**
- Update README if needed
- Add docstrings
- Update CHANGELOG.md

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added
- [ ] CHANGELOG.md updated
```

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. All comments must be resolved
4. Branch must be up-to-date with main

### After Merge

- Delete your feature branch
- Update your local repository
- Close related issues

## 🐛 Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.12.0]
- Package versions: [from requirements.txt]

**Additional context**
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of desired solution

**Describe alternatives you've considered**
Alternative solutions or features

**Additional context**
Any other relevant information
```

## 🎯 Areas for Contribution

### High Priority

- Performance optimizations
- Additional ML models
- Enhanced risk management
- Better documentation
- More test coverage

### Good First Issues

Look for issues labeled `good-first-issue`:
- Documentation improvements
- Code cleanup
- Simple bug fixes
- Test additions

### Advanced Contributions

- New trading strategies
- Advanced ML models
- System architecture improvements
- Performance profiling

## 💬 Communication

### Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions

### Response Times

- Issues: Within 48 hours
- Pull Requests: Within 1 week
- Security Issues: Within 24 hours

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## ❓ Questions?

If you have questions, please:
1. Check existing documentation
2. Search closed issues
3. Open a new issue with the `question` label

Thank you for contributing to BIST30 AI Trader! 🚀
