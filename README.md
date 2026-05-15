# Python Code Analyst

Python code analysis toolkit designed for AI agents.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

- **AST-based code structure analysis** - Extract imports, classes, functions, and variables
- **Complexity calculation** - Cyclomatic complexity and cognitive complexity metrics
- **Call graph construction** - Two-pass scanning for accurate function call relationships
- **Impact analysis** - Transitive closure calculation for modification impact
- **Dead code detection** - Entry point traversal to identify unreachable functions
- **Dependency classification** - Automatic categorization (stdlib/third-party/local)
- **12-section standard report** - Comprehensive analysis with Markdown output
- **Three-dimensional assessment** - Code quality + domain quality + project value
- **CLI tool** - Easy-to-use command-line interface

## Quick Start

### Installation

```bash
pip install python-code-analyst
```

### Basic Usage

```bash
# Analyze a single file
python -m code_analyzer your_file.py

# Generate Markdown report
python -m code_analyzer your_file.py --report

# Batch analysis of a directory
python -m code_analyzer ./src/ --batch
```

### Python API

```python
from code_analyzer import analyze_file

# Analyze a file
result = analyze_file('your_file.py')
data = result.to_dict()

# Access analysis results
print(f"Complexity: {data['complexity']}")
print(f"Dependencies: {data['dependencies']}")
print(f"Quality score: {data['quality_score']}")
```

## Documentation

- [Architecture](ARCHITECTURE.md) - Technical architecture and design decisions
- [Contributing](CONTRIBUTING.md) - How to contribute to the project
- [Changelog](CHANGELOG.md) - Version history and updates
- [API Reference](docs/api.md) - Detailed API documentation

## Examples

### Single File Analysis

```python
from code_analyzer import analyze_file, generate_report

# Analyze and get structured data
result = analyze_file('example.py')
data = result.to_dict()

# Generate 12-section report
report = generate_report(data)
print(report)
```

### Multi-file Project Analysis

```python
from code_analyzer import analyze_directory

# Analyze entire directory
results = analyze_directory('./src/', recursive=True)

# Get summary statistics
total_files = len(results)
avg_complexity = sum(r.complexity for r in results) / total_files
print(f"Analyzed {total_files} files, avg complexity: {avg_complexity:.2f}")
```

## Development

### Setup

```bash
git clone https://github.com/QQ-sys-ops/python-code-analyst.git
cd python-code-analyst
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
pytest --cov=code_analyzer  # With coverage
```

### Code Quality

```bash
black .
isort .
flake8 .
mypy .
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python's `ast` module for accurate static analysis
- Inspired by tools like `radon`, `vulture`, and `pylint`
- Designed for AI agent integration with structured output formats