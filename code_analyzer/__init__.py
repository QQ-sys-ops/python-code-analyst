"""
code_analyzer — Python代码静态分析工具包
功能: 结构分析、调用图、影响面、死代码、依赖分析、12节报告
"""

__version__ = "1.0.0"

from .ast_analyzer import analyze_file, analyze_source, StructureAnalysis
from .call_graph import build_call_graph, CallGraph
from .dependency import analyze_dependencies, DependencyInfo
from .impact_analyzer import analyze_impact, ImpactAnalysis
from .dead_code import detect_dead_code, DeadCodeResult
from .report import generate_report

__all__ = [
    "analyze_file",
    "analyze_source",
    "StructureAnalysis",
    "build_call_graph",
    "CallGraph",
    "analyze_dependencies",
    "DependencyInfo",
    "analyze_impact",
    "ImpactAnalysis",
    "detect_dead_code",
    "DeadCodeResult",
    "generate_report",
]
