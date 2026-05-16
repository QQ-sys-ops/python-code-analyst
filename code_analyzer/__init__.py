"""
code_analyzer — Python Static Code Analysis Toolkit
Features: structure analysis, call graph, impact analysis, dead code detection, dependency analysis, 12-section report
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
