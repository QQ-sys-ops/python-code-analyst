"""
code_analyzer CLI — 命令行入口
用法:
  python3 -m code_analyzer <file.py>              # 分析单文件，JSON输出
  python3 -m code_analyzer <file.py> --report     # 分析单文件，Markdown报告
  python3 -m code_analyzer <file.py> --json       # 分析单文件，JSON输出(同默认)
  python3 -m code_analyzer <dir/>  --batch        # 批量分析目录
"""

import sys
import json
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Python代码静态分析工具",
        prog="code_analyzer",
    )
    parser.add_argument("target", help="Python文件或目录")
    parser.add_argument("--json", action="store_true", default=True,
                        help="输出JSON格式（默认）")
    parser.add_argument("--report", action="store_true",
                        help="输出Markdown报告")
    parser.add_argument("--batch", action="store_true",
                        help="批量分析目录中的所有.py文件")
    parser.add_argument("-o", "--output", help="输出文件路径")

    args = parser.parse_args()
    target = Path(args.target)

    if not target.exists():
        print(f"错误: 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)

    if args.batch or target.is_dir():
        # 批量模式
        results = batch_analyze(target)
        output = json.dumps(results, indent=2, ensure_ascii=False, default=str)
    else:
        # 单文件模式
        result = single_analyze(str(target))

        if args.report:
            output = result.get("report", "报告生成失败")
        else:
            output = json.dumps(result, indent=2, ensure_ascii=False, default=str)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"结果已保存到: {args.output}")
    else:
        print(output)


def single_analyze(file_path: str) -> dict:
    """分析单个Python文件"""
    from .ast_analyzer import analyze_file
    from .call_graph import build_call_graph
    from .dependency import analyze_dependencies
    from .impact_analyzer import analyze_impact
    from .dead_code import detect_dead_code
    from .report import generate_report

    # 1. 结构分析
    structure = analyze_file(file_path)

    # 2. 调用图
    call_graph = build_call_graph(
        _parse_file(file_path),
        structure.all_functions,
    )

    # 3. 依赖分析
    dependency = analyze_dependencies(structure.imports)

    # 4. 影响面分析
    impact = analyze_impact(call_graph)

    # 5. 死代码检测
    dead_code = detect_dead_code(call_graph, structure.all_functions)

    # 6. 生成报告
    report = generate_report(
        structure=structure,
        call_graph=call_graph,
        impact_analysis=impact,
        dead_code_result=dead_code,
        dependency_result=dependency,
    )

    return {
        "structure": structure.to_dict(),
        "call_graph": call_graph.to_dict(),
        "dependency": dependency.to_dict(),
        "impact": impact.to_dict(),
        "dead_code": dead_code.to_dict(),
        "report": report,
    }


def batch_analyze(directory: Path) -> dict:
    """批量分析目录中的所有Python文件"""
    results = {}
    py_files = list(directory.rglob("*.py"))

    # 排除常见非源码目录
    exclude_dirs = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".eggs"}
    py_files = [f for f in py_files if not any(ex in f.parts for ex in exclude_dirs)]

    print(f"找到 {len(py_files)} 个Python文件", file=sys.stderr)

    for py_file in py_files:
        try:
            result = single_analyze(str(py_file))
            results[str(py_file)] = {
                "status": "ok",
                "structure": result["structure"],
                "dead_code": result["dead_code"],
                "dependency": result["dependency"],
            }
        except Exception as e:
            results[str(py_file)] = {
                "status": "error",
                "error": str(e),
            }

    return results


def _parse_file(file_path: str):
    """解析Python文件为AST"""
    import ast
    path = Path(file_path)
    for encoding in ('utf-8', 'gbk', 'latin-1'):
        try:
            source = path.read_text(encoding=encoding)
            return ast.parse(source, filename=str(path))
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"无法读取文件: {file_path}")


if __name__ == "__main__":
    main()
