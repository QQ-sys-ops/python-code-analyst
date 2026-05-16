"""
schema.py — radon 兼容的 JSON Schema 定义

定义 code_analyzer JSON 输出的标准结构，与 radon cc 输出格式兼容。
参考: 07_code-analysis：我的实现方案与交叉验证体系.md L382-430
"""

OUTPUT_SCHEMA = {
    "meta": {
        "analyzer": "code_analyzer",
        "version": "string",
        "file": "string",
        "timestamp": "string",
    },
    "structure": {
        "file_path": "string",
        "total_lines": "int",
        "sloc": "int",
        "class_count": "int",
        "function_count": "int",
        "method_count": "int",
        "import_count": "int",
        "avg_complexity": "float",
        "max_complexity": "int",
        "doc_coverage": "float",
        "total_arguments": "int",
    },
    "complexity": {
        # 与 radon cc_visit 输出格式兼容
        "functions": {
            # radon 兼容字段
            "name": "string",
            "lineno": "int",
            "end_lineno": "int",
            "complexity": "int",        # ← radon 兼容 (alias for cyclomatic_complexity)
            "rank": "string",           # ← radon 兼容 (A-F rating)
            "type": "string",           # ← radon 兼容 ('F' = function, 'M' = method)
            # code-analysis 扩展字段
            "cognitive": "int",         # ← cognitive complexity
            "cyclomatic_complexity": "int",
            "cognitive_complexity": "int",
            "qualified_name": "string",
            "args": "list[string]",
            "docstring_length": "int",
            "line_count": "int",
            "is_method": "bool",
            "parent_class": "string|null",
        }
    },
    "call_graph": {
        # code-analysis 独有
        "edge_count": "int",
        "user_function_count": "int",
        "called_function_count": "int",
        "entry_point_count": "int",
        "max_depth": "int",
        "edges": [{"caller": "string", "callee": "string", "lineno": "int"}],
        "entry_points": "list[string]",
    },
    "dependency": {
        # code-analysis 独有
        "standard_lib": "list[string]",
        "third_party": "list[string]",
        "local": "list[string]",
        "standard_lib_count": "int",
        "third_party_count": "int",
        "local_count": "int",
        "import_count": "int",
        "has_circular": "bool",
        "circular_cycles": "list",
        "fan_in": "dict",
        "fan_out": "dict",
    },
    "impact": {
        # code-analysis 独有
        "function_count": "int",
        "most_impacted": "list",
        "least_impacted": "list",
        "impacts": "dict",
    },
    "dead_code": {
        # code-analysis 独有
        "unreachable": "list[string]",
        "reachable_count": "int",
        "unreachable_count": "int",
        "total_user_functions": "int",
        "coverage": "float",
        "special_excluded": "list[string]",
    },
    "doc_coverage": {
        # code-analysis 独有
        "functions_with_docstring": "int",
        "total_functions": "int",
        "coverage_percent": "float",
    },
    "quality_score": {
        # code-analysis 独有
        "score": "float",
        "grade": "string",
        "breakdown": "dict",
    },
    "report": "string (Markdown)",
}


def validate_output(data: dict) -> list[str]:
    """
    验证 code_analyzer 的 JSON 输出是否符合 schema。

    返回: 错误列表（空列表 = 通过）
    """
    errors = []

    # 检查顶层 key
    for section in OUTPUT_SCHEMA:
        if section == "report":
            if section not in data:
                errors.append(f"Missing top-level section: {section}")
            elif not isinstance(data[section], str):
                errors.append(f"'{section}' should be string, got {type(data[section]).__name__}")
            continue

        if section not in data:
            errors.append(f"Missing top-level section: {section}")

    # 检查 complexity.functions 的 radon 字段
    if "structure" in data and "functions" in data.get("structure", {}):
        funcs = data["structure"]["functions"]
        radon_fields = ["name", "lineno", "end_lineno", "complexity", "rank", "type"]
        if funcs:
            for field in radon_fields:
                if field not in funcs[0]:
                    errors.append(f"functions[0] missing radon field: {field}")

    return errors
