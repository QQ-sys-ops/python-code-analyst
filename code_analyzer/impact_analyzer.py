"""
impact_analyzer.py — Modification Impact Analyzer
Features: Transitive closure calculation based on call graph, analyzing who is affected by modifying each function
Dependencies: call_graph.py (CallGraph, CallEdge)
"""

from dataclasses import dataclass, field


@dataclass
class ImpactResult:
    """Impact analysis result for a single function"""
    function: str           # target function
    direct_impact: list[str]   # direct impact (who calls me)
    indirect_impact: list[str] # indirect impact (transitive closure)
    total_impact: int          # total impact scope
    impact_chain: list[list[str]]  # impact chain

    def to_dict(self) -> dict:
        return {
            "function": self.function,
            "direct_impact": self.direct_impact,
            "indirect_impact": self.indirect_impact,
            "total_impact": self.total_impact,
            "impact_chain": self.impact_chain,
        }


@dataclass
class ImpactAnalysis:
    """Complete impact analysis result"""
    impacts: list[ImpactResult]
    most_impacted: list[str]     # functions with largest impact scope
    least_impacted: list[str]    # functions with smallest impact scope

    def to_dict(self) -> dict:
        return {
            "function_count": len(self.impacts),
            "most_impacted": self.most_impacted,
            "least_impacted": self.least_impacted,
            "impacts": [i.to_dict() for i in self.impacts],
        }


class ImpactAnalyzer:
    """
    Impact analysis based on call graph transitive closure
    Core logic: If A calls B, modifying B will affect A
    Transitive closure: If A→B→C, modifying C will affect B and A
    """

    def __init__(self, call_graph):
        """
        Args:
            call_graph: CallGraph object
        """
        self.call_graph = call_graph
        # Build reverse adjacency list: callee → [callers]
        self.reverse_adj: dict[str, list[str]] = {}
        self._build_reverse()

    def _build_reverse(self):
        """Build reverse call graph"""
        for edge in self.call_graph.edges:
            self.reverse_adj.setdefault(edge.callee, []).append(edge.caller)

    def analyze(self) -> ImpactAnalysis:
        """Execute impact analysis for all functions"""
        impacts = []

        for func in self.call_graph.user_functions:
            # Skip Python special methods
            if self._is_special(func):
                continue

            result = self._analyze_function(func)
            if result.total_impact > 0:
                impacts.append(result)

        # Sort by impact scope
        impacts.sort(key=lambda x: x.total_impact, reverse=True)

        most = [i.function for i in impacts[:5]] if impacts else []
        least = [i.function for i in impacts[-5:]] if impacts else []

        return ImpactAnalysis(
            impacts=impacts,
            most_impacted=most,
            least_impacted=least,
        )

    def _analyze_function(self, function: str) -> ImpactResult:
        """Analyze impact of a single function"""
        direct = list(self.reverse_adj.get(function, []))

        # BFS transitive closure
        indirect = []
        chains = []
        visited = set(direct)
        queue = [(d, [function, d]) for d in direct]

        while queue:
            current, chain = queue.pop(0)
            parents = self.reverse_adj.get(current, [])
            for parent in parents:
                if parent not in visited and parent != function:
                    visited.add(parent)
                    indirect.append(parent)
                    new_chain = chain + [parent]
                    chains.append(new_chain)
                    queue.append((parent, new_chain))

        return ImpactResult(
            function=function,
            direct_impact=direct,
            indirect_impact=indirect,
            total_impact=len(direct) + len(indirect),
            impact_chain=chains[:10],  # limit chain count
        )

    def _is_special(self, func: str) -> bool:
        """Check if a function is a Python special method"""
        name = func.split('.')[-1] if '.' in func else func
        from .call_graph import SPECIAL_FUNCTIONS
        return name in SPECIAL_FUNCTIONS


def analyze_impact(call_graph) -> ImpactAnalysis:
    """Convenience function: analyze impact"""
    analyzer = ImpactAnalyzer(call_graph)
    return analyzer.analyze()
