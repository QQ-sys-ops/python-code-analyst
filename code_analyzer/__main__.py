"""
code_analyzer CLI — Command Line Entry Point
Usage:
  python3 -m code_analyzer <file.py>              # Analyze single file, JSON output
  python3 -m code_analyzer <file.py> --report     # Analyze single file, Markdown report
  python3 -m code_analyzer <file.py> --json       # Analyze single file, JSON output (same as default)
  python3 -m code_analyzer <dir/>  --batch        # Batch analyze directory
"""

import sys
import json
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Python Static Code Analysis Tool",
        prog="code_analyzer",
    )
    parser.add_argument("target", help="Python file or directory")
    parser.add_argument("--json", action="store_true", default=True,
                        help="Output JSON format (default)")
    parser.add_argument("--report", action="store_true",
                        help="Output Markdown report")
    parser.add_argument("--batch", action="store_true",
                        help="Batch analyze all .py files in directory")
    parser.add_argument("-o", "--output", help="output file path")
    parser.add_argument("--lang", choices=["en", "zh"], default="en",
                        help="Report language (default: en)")

    args = parser.parse_args()
    target = Path(args.target)

    if not target.exists():
        print(f"Error: path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    if args.batch or target.is_dir():
        # Batch mode
        results = batch_analyze(target)
        output = json.dumps(results, indent=2, ensure_ascii=False, default=str)
    else:
        # Single file mode
        result = single_analyze(str(target), lang=args.lang)

        if args.report:
            output = result.get("report", "Report generation failed")
        else:
            output = json.dumps(result, indent=2, ensure_ascii=False, default=str)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Results saved to: {args.output}")
    else:
        print(output)


def single_analyze(file_path: str, lang: str = "en") -> dict:
    """Analyze a single Python file"""
    from .ast_analyzer import analyze_file
    from .call_graph import build_call_graph
    from .dependency import analyze_dependencies
    from .impact_analyzer import analyze_impact
    from .dead_code import detect_dead_code
    from .report import generate_report

    # 1. Structure analysis
    structure = analyze_file(file_path)

    # 2. Call graph
    call_graph = build_call_graph(
        _parse_file(file_path),
        structure.all_functions,
    )

    # 3. Dependency analysis
    dependency = analyze_dependencies(structure.imports)

    # 4. Impact analysis
    impact = analyze_impact(call_graph)

    # 5. Dead code detection
    dead_code = detect_dead_code(call_graph, structure.all_functions)

    # 6. Generate report
    report = generate_report(
        structure=structure,
        call_graph=call_graph,
        impact_analysis=impact,
        dead_code_result=dead_code,
        dependency_result=dependency,
        lang=lang,
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
    """Batch analyze all Python files in directory"""
    results = {}
    py_files = list(directory.rglob("*.py"))

    # Exclude common non-source directories
    exclude_dirs = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".eggs"}
    py_files = [f for f in py_files if not any(ex in f.parts for ex in exclude_dirs)]

    print(f"Found {len(py_files)} Python files", file=sys.stderr)

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
    """Parse Python file to AST"""
    import ast
    path = Path(file_path)
    for encoding in ('utf-8', 'gbk', 'latin-1'):
        try:
            source = path.read_text(encoding=encoding)
            return ast.parse(source, filename=str(path))
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"Cannot read file: {file_path}")


if __name__ == "__main__":
    main()
