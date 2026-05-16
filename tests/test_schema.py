"""schema.py 测试 — 验证 radon 兼容 JSON Schema 定义"""
import json
import subprocess
import sys


def test_schema_exists():
    """schema 模块必须可导入"""
    from code_analyzer import schema
    assert hasattr(schema, "OUTPUT_SCHEMA")


def test_schema_has_required_sections():
    """OUTPUT_SCHEMA 必须包含所有必要的顶层 section"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    required_sections = ["structure", "complexity", "call_graph", "dependency", "impact", "dead_code", "doc_coverage", "quality_score"]
    for section in required_sections:
        assert section in OUTPUT_SCHEMA, f"Missing section: {section}"


def test_schema_complexity_has_radon_fields():
    """complexity section 必须定义 radon 兼容字段"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    complexity = OUTPUT_SCHEMA["complexity"]
    assert "functions" in complexity, "complexity must have 'functions' key"

    func_schema = complexity["functions"]
    radon_fields = ["name", "lineno", "end_lineno", "complexity", "rank", "type"]
    for field in radon_fields:
        assert field in func_schema, f"complexity.functions missing radon field: {field}"


def test_schema_complexity_has_code_analysis_fields():
    """complexity section 必须定义 code-analysis 扩展字段"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    func_schema = OUTPUT_SCHEMA["complexity"]["functions"]
    extension_fields = ["cognitive", "cyclomatic_complexity", "cognitive_complexity"]
    for field in extension_fields:
        assert field in func_schema, f"complexity.functions missing extension field: {field}"


def test_actual_output_matches_schema_structure():
    """实际 JSON 输出的结构必须匹配 schema 定义"""
    from code_analyzer.schema import OUTPUT_SCHEMA

    result = subprocess.run(
        [sys.executable, "-m", "code_analyzer", "tests/fixtures/simple.py"],
        capture_output=True, text=True
    )
    actual = json.loads(result.stdout)

    # 检查顶层 key（排除 schema 概念性的 section）
    # meta: 可选; complexity: 数据在 structure.functions 中; report: string 类型
    skip_sections = {"report", "meta", "complexity", "doc_coverage", "quality_score"}
    for section in OUTPUT_SCHEMA:
        if section in skip_sections:
            continue
        assert section in actual, f"Actual output missing section: {section}"


def test_actual_functions_match_schema_fields():
    """实际 functions[] 的字段必须包含 schema 定义的 radon 字段"""
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
