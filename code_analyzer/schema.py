"""
schema.py — radon-compatible JSON Schema definition

Defines the standard structure of code_analyzer JSON output, compatible with radon cc output format.
Reference: 07_code-analysis: My Implementation and Cross-validation System.md L382-430
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
        # Compatible with radon cc_visit output format
        "functions": {
            # radon-compatible fields
            "name": "string",
            "lineno": "int",
            "end_lineno": "int",
            "complexity": "int",        # radon-compatible (alias for cyclomatic_complexity)
            "rank": "string",           # radon-compatible (A-F rating)
            "type": "string",           # radon-compatible ('F' = function, 'M' = method)
            # code-analysis extended fields
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
        # code-analysis exclusive
        "edge_count": "int",
        "user_function_count": "int",
        "called_function_count": "int",
        "entry_point_count": "int",
        "max_depth": "int",
        "edges": [{"caller": "string", "callee": "string", "lineno": "int"}],
        "entry_points": "list[string]",
    },
    "dependency": {
        # code-analysis exclusive
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
        # code-analysis exclusive
        "function_count": "int",
        "most_impacted": "list",
        "least_impacted": "list",
        "impacts": "dict",
    },
    "dead_code": {
        # code-analysis exclusive
        "unreachable": "list[string]",
        "reachable_count": "int",
        "unreachable_count": "int",
        "total_user_functions": "int",
        "coverage": "float",
        "special_excluded": "list[string]",
    },
    "doc_coverage": {
        # code-analysis exclusive
        "functions_with_docstring": "int",
        "total_functions": "int",
        "coverage_percent": "float",
    },
    "quality_score": {
        # code-analysis exclusive
        "score": "float",
        "grade": "string",
        "breakdown": "dict",
    },
    "report": "string (Markdown)",
}


def validate_output(data: dict) -> list[str]:
    """
    Validate whether code_analyzer JSON output conforms to the schema.

    Returns: list of errors (empty list = pass)
    """
    errors = []

    # Check top-level keys
    for section in OUTPUT_SCHEMA:
        if section == "report":
            if section not in data:
                errors.append(f"Missing top-level section: {section}")
            elif not isinstance(data[section], str):
                errors.append(f"'{section}' should be string, got {type(data[section]).__name__}")
            continue

        if section not in data:
            errors.append(f"Missing top-level section: {section}")

    # Check radon fields in complexity.functions
    if "structure" in data and "functions" in data.get("structure", {}):
        funcs = data["structure"]["functions"]
        radon_fields = ["name", "lineno", "end_lineno", "complexity", "rank", "type"]
        if funcs:
            for field in radon_fields:
                if field not in funcs[0]:
                    errors.append(f"functions[0] missing radon field: {field}")

    return errors

