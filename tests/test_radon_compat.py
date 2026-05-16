"""Radon compatibility field tests -- verify JSON output contains radon standard fields"""
import json
import subprocess
import sys


def test_functions_contain_radon_fields():
    """functions[] must contain radon-compatible fields: complexity, rank, type"""
    result = subprocess.run(
        [sys.executable, "-m", "code_analyzer", "tests/fixtures/simple.py"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    funcs = data["structure"]["functions"]

    assert len(funcs) > 0, "No functions found"

    for func in funcs:
        # radon-compatible fields must exist
        assert "complexity" in func, f"Missing 'complexity' in {func['name']}"
        assert "rank" in func, f"Missing 'rank' in {func['name']}"
        assert "type" in func, f"Missing 'type' in {func['name']}"

        # complexity must equal cyclomatic_complexity
        assert func["complexity"] == func["cyclomatic_complexity"], \
            f"{func['name']}: complexity({func['complexity']}) != cyclomatic_complexity({func['cyclomatic_complexity']})"

        # rank must be A-F
        assert func["rank"] in ("A", "B", "C", "D", "E", "F"), \
            f"{func['name']}: invalid rank '{func['rank']}'"

        # type must be 'F' or 'M'
        assert func["type"] in ("F", "M"), \
            f"{func['name']}: invalid type '{func['type']}'"


def test_rank_matches_complexity():
    """rank must correspond to complexity values (consistent with radon)"""
    result = subprocess.run(
        [sys.executable, "-m", "code_analyzer", "tests/fixtures/simple.py"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    funcs = data["structure"]["functions"]

    expected_ranks = {
        range(1, 6): "A",    # 1-5 → A
        range(6, 11): "B",   # 6-10 → B
        range(11, 16): "C",  # 11-15 → C
        range(16, 21): "D",  # 16-20 → D
        range(21, 26): "E",  # 21-25 → E
    }

    for func in funcs:
        cc = func["complexity"]
        rank = func["rank"]

        expected = "F"  # >25 → F
        for r, label in expected_ranks.items():
            if cc in r:
                expected = label
                break

        assert rank == expected, \
            f"{func['name']}: cc={cc}, expected rank={expected}, got rank={rank}"


def test_type_matches_is_method():
    """type must correspond to is_method: is_method=True -> 'M', False -> 'F'"""
    result = subprocess.run(
        [sys.executable, "-m", "code_analyzer", "tests/fixtures/simple.py"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    funcs = data["structure"]["functions"]

    for func in funcs:
        expected_type = "M" if func["is_method"] else "F"
        assert func["type"] == expected_type, \
            f"{func['name']}: is_method={func['is_method']}, expected type={expected_type}, got type={func['type']}"
