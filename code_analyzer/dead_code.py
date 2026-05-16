"""
dead_code.py — Dead Code Detector
Features: Traverse call graph from entry points, identify uncalled functions
Dependencies: call_graph.py (CallGraph)
"""

from dataclasses import dataclass
from .call_graph import SPECIAL_FUNCTIONS


@dataclass
class DeadCodeResult:
    """Dead code detection result"""
    unreachable: list[str]      # uncalled functions
    reachable: list[str]        # called functions
    total_user_functions: int   # total number of user-defined functions
    coverage: float             # coverage rate 0-100
    special_excluded: list[str] # excluded special methods

    def to_dict(self) -> dict:
        return {
            "unreachable": self.unreachable,
            "reachable_count": len(self.reachable),
            "unreachable_count": len(self.unreachable),
            "total_user_functions": self.total_user_functions,
            "coverage": round(self.coverage, 1),
            "special_excluded": self.special_excluded,
        }


class DeadCodeDetector:
    """
    Dead code detector
    Logic:
    1. Start from entry points, BFS traversal of call graph
    2. All traversed functions = reachable (live code)
    3. User-defined but unreachable functions = dead code
    4. Python special methods are automatically excluded
    """

    def __init__(self, call_graph, all_functions: list):
        """
        Args:
            call_graph: CallGraph object
            all_functions: StructureAnalysis.all_functions
        """
        self.call_graph = call_graph
        self.all_functions = all_functions

    def detect(self) -> DeadCodeResult:
        """Execute dead code detection"""
        # Build forward adjacency list
        adj: dict[str, set[str]] = {}
        for edge in self.call_graph.edges:
            adj.setdefault(edge.caller, set()).add(edge.callee)

        # BFS from entry points
        reachable = set()
        queue = list(self.call_graph.entry_points)

        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)
            for neighbor in adj.get(current, set()):
                if neighbor not in reachable:
                    queue.append(neighbor)

        # Also mark directly called functions (entry points may be incomplete)
        for edge in self.call_graph.edges:
            reachable.add(edge.callee)

        # Collect all user-defined functions
        user_funcs = set()
        special_excluded = []
        public_api = set()  # public API (module-level functions not starting with underscore)
        for func in self.all_functions:
            qn = func.qualified_name
            name = func.name
            if name in SPECIAL_FUNCTIONS or qn.split('.')[-1] in SPECIAL_FUNCTIONS:
                special_excluded.append(qn)
                continue
            user_funcs.add(qn)
            # Public API: module-level functions not starting with underscore (may be external call entry points)
            if not func.is_method and not name.startswith('_'):
                public_api.add(qn)

        # Dead code = user-defined - reachable - public API
        # Public API is not counted as dead code (may be called by external modules)
        unreachable = sorted(user_funcs - reachable - public_api)
        reachable_list = sorted(user_funcs & reachable)

        # Coverage rate
        total = len(user_funcs)
        coverage = (len(reachable_list) / total * 100) if total > 0 else 100.0

        return DeadCodeResult(
            unreachable=unreachable,
            reachable=reachable_list,
            total_user_functions=total,
            coverage=coverage,
            special_excluded=special_excluded,
        )


def detect_dead_code(call_graph, all_functions: list) -> DeadCodeResult:
    """Convenience function: detect dead code"""
    detector = DeadCodeDetector(call_graph, all_functions)
    return detector.detect()
