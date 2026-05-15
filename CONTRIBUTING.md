# Contributing to python-code-analyst

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

Please be respectful and constructive in all interactions. We are committed to providing a welcoming and inclusive experience for everyone.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/python-code-analyst.git
cd python-code-analyst

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Project Structure

```
python-code-analyst/
├── code_analyzer/          # Main package
│   ├── __init__.py
│   ├── ast_analyzer.py     # AST analysis
│   ├── call_graph.py       # Call graph construction
│   ├── dependency.py       # Dependency analysis
│   ├── impact_analyzer.py  # Impact analysis
│   ├── dead_code.py        # Dead code detection
│   └── report.py           # Report generation
├── tests/                  # Test suite
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
└── README.md               # Project overview
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Write Code

Follow the code style guidelines below. Write clear, documented code.

### 3. Write Tests

Add tests for new functionality. Ensure all tests pass:

```bash
pytest tests/ -v
```

### 4. Update Documentation

If your change affects the API or adds features, update the relevant documentation.

### 5. Commit

Write clear, concise commit messages:

```bash
git commit -m "Add: description of your change"

# Or for fixes:
git commit -m "Fix: description of the fix"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=code_analyzer

# Run specific test file
pytest tests/test_ast_analyzer.py -v

# Run specific test
pytest tests/test_ast_analyzer.py::TestAnalyzeSource::test_basic_structure -v
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Name test functions `test_<description>`
- Use pytest fixtures for shared setup
- Aim for high coverage on new code

## Code Style

### Formatting

We use:
- **black** for code formatting
- **isort** for import sorting
- **flake8** for linting

```bash
# Format code
black .

# Sort imports
isort .

# Check for issues
flake8 .
```

### Guidelines

- Use type hints for function signatures
- Write docstrings for public functions
- Keep functions focused and small
- Use meaningful variable names
- Follow PEP 8 style guide

### Example

```python
def analyze_function(tree: ast.AST, func_name: str) -> FunctionInfo:
    """
    Analyze a specific function in the AST.
    
    Args:
        tree: The AST root node
        func_name: Name of the function to analyze
        
    Returns:
        FunctionInfo with analysis results
        
    Raises:
        ValueError: If function not found
    """
    # Implementation here
    pass
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass (`pytest`)
2. ✅ Code is formatted (`black .`)
3. ✅ Imports are sorted (`isort .`)
4. ✅ No linting errors (`flake8 .`)
5. ✅ Documentation is updated
6. ✅ Commit messages are clear

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Added tests for new functionality
- [ ] All existing tests pass

## Checklist

- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. Submit PR with clear description
2. Wait for CI to pass
3. Address review feedback
4. Get approval from maintainer
5. Merge

## Reporting Issues

### Bug Reports

Include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error traceback (if applicable)

### Feature Requests

Include:
- Clear description of the feature
- Use case / motivation
- Proposed solution (if any)

## Questions?

Feel free to open an issue for questions or discussions.

---

Thank you for contributing!