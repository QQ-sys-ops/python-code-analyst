"""radon 交叉验证测试 — 与 radon 实际输出对比验证复杂度一致性

需要安装 radon: /tmp/radon-env/bin/pip install radon
"""
import json
import subprocess
import sys
import os

# radon 安装在临时 venv 中
RADON_BIN = "/tmp/radon-env/bin/radon"
PYTHON_BIN = sys.executable
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_radon_output(filepath):
    """获取 radon cc 的 JSON 输出"""
    result = subprocess.run(
        [RADON_BIN, "cc", filepath, "-j"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def _get_our_output(filepath):
    """获取 code_analyzer 的 JSON 输出"""
    result = subprocess.run(
        [PYTHON_BIN, "-m", "code_analyzer", filepath],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)


def _extract_radon_functions(radon_data, filepath):
    """从 radon 输出中提取所有函数（含类方法）"""
    funcs = {}
    for entry in radon_data.get(filepath, []):
        if entry["type"] == "function":
            funcs[entry["name"]] = entry
        elif entry["type"] == "class":
            for method in entry.get("methods", []):
                key = f"{entry['name']}.{method['name']}"
                funcs[key] = method
    return funcs


def _extract_our_functions(our_data):
    """从 code_analyzer 输出中提取所有函数"""
    funcs = {}
    for f in our_data["structure"]["all_functions"]:
        funcs[f["qualified_name"]] = f
    return funcs


# 测试文件列表
TEST_FILES = [
    "tests/fixtures/simple.py",
]


def test_radon_available():
    """radon 必须可用"""
    result = subprocess.run(
        [RADON_BIN, "--version"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"radon not available: {result.stderr}"


def test_complexity_matches_radon():
    """code_analyzer 的复杂度输出必须与 radon 一致"""
    for rel_path in TEST_FILES:
        filepath = os.path.join(PROJECT_DIR, rel_path)

        radon_data = _get_radon_output(filepath)
        assert radon_data is not None, f"radon failed for {rel_path}"

        our_data = _get_our_output(filepath)

        radon_funcs = _extract_radon_functions(radon_data, filepath)
        our_funcs = _extract_our_functions(our_data)

        for name, radon_f in radon_funcs.items():
            # 尝试匹配（qualified name vs short name）
            matched = None
            for our_name, our_f in our_funcs.items():
                if our_f["name"] == radon_f["name"] or our_name == name:
                    matched = our_f
                    break

            assert matched is not None, \
                f"Function '{name}' found in radon but not in our output"

            assert matched["complexity"] == radon_f["complexity"], \
                f"{name}: radon CC={radon_f['complexity']}, ours={matched['complexity']}"


def test_rank_matches_radon():
    """code_analyzer 的 rank 必须与 radon 一致"""
    for rel_path in TEST_FILES:
        filepath = os.path.join(PROJECT_DIR, rel_path)

        radon_data = _get_radon_output(filepath)
        our_data = _get_our_output(filepath)

        radon_funcs = _extract_radon_functions(radon_data, filepath)
        our_funcs = _extract_our_functions(our_data)

        for name, radon_f in radon_funcs.items():
            matched = None
            for our_name, our_f in our_funcs.items():
                if our_f["name"] == radon_f["name"] or our_name == name:
                    matched = our_f
                    break

            assert matched is not None, \
                f"Function '{name}' not found in our output"

            assert matched["rank"] == radon_f["rank"], \
                f"{name}: radon rank={radon_f['rank']}, ours={matched['rank']}"


def test_type_matches_radon():
    """code_analyzer 的 type 必须与 radon 一致"""
    for rel_path in TEST_FILES:
        filepath = os.path.join(PROJECT_DIR, rel_path)

        radon_data = _get_radon_output(filepath)
        our_data = _get_our_output(filepath)

        radon_funcs = _extract_radon_functions(radon_data, filepath)
        our_funcs = _extract_our_functions(our_data)

        for name, radon_f in radon_funcs.items():
            matched = None
            for our_name, our_f in our_funcs.items():
                if our_f["name"] == radon_f["name"] or our_name == name:
                    matched = our_f
                    break

            assert matched is not None, \
                f"Function '{name}' not found in our output"

            # radon: 'function'/'method'/'class' → ours: 'F'/'M'
            expected_type = "M" if radon_f["type"] == "method" else "F"
            assert matched["type"] == expected_type, \
                f"{name}: radon type={radon_f['type']}, ours={matched['type']}"
