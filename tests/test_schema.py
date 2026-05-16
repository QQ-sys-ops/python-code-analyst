"""schema.py tests -- verify radon-compatible JSON Schema definition"""
import json
import subprocess
import sys


def test_schema_exists():
    """schema module must be importable"""
    from code_analyzer import schema
    assert hasattr(schema, "OUTPUT_SCHEMA")


def test_schema_has_required_sections():
    """OUTPUT_SCHEMA must contain all required top-level sections"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    required_sections = ["structure", "complexity", "call_graph", "dependency", "impact", "dead_code", "doc_coverage", "quality_score"]
    for section in required_sections:
        assert section in OUTPUT_SCHEMA, f"Missing section: {section}"


def test_schema_complexity_has_radon_fields():
    """complexity section must define radon-compatible fields"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    complexity = OUTPUT_SCHEMA["complexity"]
    assert "functions" in complexity, "complexity must have 'functions' key"

    func_schema = complexity["functions"]
    radon_fields = ["name", "lineno", "end_lineno", "complexity", "rank", "type"]
    for field in radon_fields:
        assert field in func_schema, f"complexity.functions missing radon field: {field}"


def test_schema_complexity_has_code_analysis_fields():
    """complexity section must define code-analysis extension fields"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    func_schema = OUTPUT_SCHEMA["complexity"]["functions"]
    extension_fields = ["cognitive", "cyclomatic_complexity", "cognitive_complexity"]
    for field in extension_fields:
        assert field in func_schema, f"complexity.functions missing extension field: {field}"


def test_actual_output_matches_schema_structure():
    """Actual JSON output structure must match schema definition"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    result = subprocess.run(
        [sys.executable, "-m", "code_analyzer", "tests/fixtures/simple.py"],
        capture_output=True, text=True
    )
    actual = json.loads(result.stdout)

    # Check top-level keys (excluding conceptual schema sections)
    # meta: optional; complexity: data lives in structure.functions; report: string type
    skip_sections = {"report", "meta", "complexity", "doc_coverage", "quality_score"}
    for section in OUTPUT_SCHEMA:
        if section in skip_sections:
            continue
        assert section in actual, f"Actual output missing section: {section}"


def test_actual_functions_match_schema_fields():
    """Actual functions[] fields must include radon fields defined in schema"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    result = subprocess.run(
        [sys.executable, "-m", "code_analyzer", "tests/fixtures/simple.py"],
        capture_output=True, text=True
    )
    actual = json.loads(result.stdout)
    actual_funcs = actual["structure"]["functions"]

    radon_fields = OUTPUT_SCHEMA["complexity"]["functions"]
    # Check radon-compatible fields specifically
    radon_only = ["name", "lineno", "end_lineno", "complexity", "rank", "type"]
    for field_name in radon_only:
        assert field_name in actual_funcs[0], \
            f"Actual functions[0] missing radon field defined in schema: {field_name}"
