"""
call_graph.py — Function Call Graph Analyzer
Features: Two-pass scan to extract call edges, special function filtering, call depth calculation
Dependencies: ast_analyzer.py (FunctionInfo, StructureAnalysis)
"""

import ast
from dataclasses import dataclass, field


# Python special methods (excluded during dead code detection)
SPECIAL_FUNCTIONS = frozenset({
    '__init__', '__new__', '__del__',
    '__str__', '__repr__', '__bytes__',
    '__format__', '__hash__', '__bool__',
    '__call__', '__len__', '__length_hint__',
    '__getitem__', '__setitem__', '__delitem__',
    '__iter__', '__next__', '__reversed__',
    '__contains__', '__add__', '__sub__',
    '__mul__', '__truediv__', '__floordiv__',
    '__mod__', '__pow__', '__lshift__', '__rshift__',
    '__and__', '__or__', '__xor__',
    '__enter__', '__exit__', '__aenter__', '__aexit__',
    '__get__', '__set__', '__delete__',
    '__init_subclass__', '__class_getitem__',
    '__missing__', '__set_name__',
    # Framework hooks
    'setup', 'teardown', 'setUp', 'tearDown',
    'setUpClass', 'tearDownClass',
})


@dataclass
class CallEdge:
    """A call edge: caller → callee"""
    caller: str       # caller qualified_name
    callee: str       # callee qualified_name
    lineno: int       # line number of call location
    callee_raw: str   # raw call name (unresolved)


@dataclass
class CallGraph:
    """Call graph analysis result"""
    edges: list[CallEdge]
    user_functions: set[str]    # set of all user-defined function names
    called_functions: set[str]  # set of called function names
    entry_points: list[str]     # entry point functions
    max_depth: int              # maximum call depth

    def to_dict(self) -> dict:
        return {
            "edge_count": len(self.edges),
            "user_function_count": len(self.user_functions),
            "called_function_count": len(self.called_functions),
            "entry_point_count": len(self.entry_points),
            "max_depth": self.max_depth,
            "edges": [
                {
                    "caller": e.caller,
                    "callee": e.callee,
                    "lineno": e.lineno,
                }
                for e in self.edges
            ],
            "entry_points": self.entry_points,
        }


class CallGraphBuilder:
    """
    Two-pass scan to build call graph:
    Pass 1: Collect all user-defined function names
    Pass 2: Extract all call relationships
    """

    def __init__(self, tree: ast.AST, all_functions: list):
        """
        Args:
            tree: result of ast.parse()
            all_functions: StructureAnalysis.all_functions
        """
        self.tree = tree
        self.all_functions = all_functions

        # Pass 1: Build function name set
        self.user_functions: set[str] = set()
        self.func_line_map: dict[str, int] = {}  # qualified_name → lineno
        self._collect_functions()

    def _collect_functions(self):
        """Pass 1: Collect all user-defined function names"""
        for func in self.all_functions:
            self.user_functions.add(func.qualified_name)
            self.func_line_map[func.qualified_name] = func.lineno
            # Also register short name (without class prefix)
            self.user_functions.add(func.name)

    def build(self) -> CallGraph:
        """Pass 2: Extract call relationships, build call graph"""
        edges = []
        called = set()

        for node in ast.walk(self.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Determine the caller
            caller = self._get_qualified_name(node)
            if caller is None:
                continue

            # Traverse all Call nodes in function body
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    callee_name = self._extract_callee_name(child)
                    if callee_name and callee_name in self.user_functions:
                        # Resolve callee's qualified_name
                        resolved = self._resolve_callee(callee_name)
                        if resolved:
                            edges.append(CallEdge(
                                caller=caller,
                                callee=resolved,
                                lineno=getattr(child, 'lineno', 0),
                                callee_raw=callee_name,
                            ))
                            called.add(resolved)

        # Find entry points: among called functions, those not called by other functions
        all_called = {e.callee for e in edges}
        all_callers = {e.caller for e in edges}
        entry_points = []
        for func in self.all_functions:
            qn = func.qualified_name
            if qn in all_called and qn not in all_callers:
                entry_points.append(qn)

        # If no entry points found, use common entry patterns
        if not entry_points:
            for func in self.all_functions:
                if func.name in ('main', 'run', 'execute', 'process',
                                 'train', 'predict', 'evaluate',
                                 'cli', 'app'):
                    entry_points.append(func.qualified_name)

        # Calculate maximum call depth
        max_depth = self._calc_max_depth(edges)

        return CallGraph(
            edges=edges,
            user_functions=self.user_functions,
            called_functions=called,
            entry_points=entry_points,
            max_depth=max_depth,
        )

    def _get_qualified_name(self, node) -> str | None:
        """Get qualified_name for a function node"""
        # Need to find matching entry in all_functions
        for func in self.all_functions:
            if func.lineno == node.lineno and func.name == node.name:
                return func.qualified_name
        return node.name

    def _extract_callee_name(self, call_node: ast.Call) -> str | None:
        """Extract called function name from Call node"""
        func = call_node.func

        if isinstance(func, ast.Name):
            # Direct call: train_one_epoch() → may be user function
            return func.id
        elif isinstance(func, ast.Attribute):
            # Method call: model.train() / optimizer.step()
            # Not resolved to user function (to avoid model.train() falsely matching train() function)
            return None
        elif isinstance(func, ast.Call):
            # Decorator factory: @decorator()
            return None
        return None

    def _resolve_callee(self, name: str) -> str | None:
        """Resolve short name to qualified_name"""
        # Exact match
        if name in self.func_line_map:
            # If there are multiple functions with the same name, return the first one
            for qn in self.user_functions:
                if qn == name or qn.endswith(f".{name}"):
                    return qn
        # Fuzzy match: with class prefix
        for qn in self.user_functions:
            if qn.endswith(f".{name}"):
                return qn
        return name  # Return original name when cannot resolve

    def _calc_max_depth(self, edges: list[CallEdge]) -> int:
        """Calculate maximum call depth"""
        if not edges:
            return 0

        # Build adjacency list
        adj: dict[str, list[str]] = {}
        for e in edges:
            adj.setdefault(e.caller, []).append(e.callee)

        # DFS to find longest path (may have cycles, need visited)
        visited = set()
        max_d = 0

        def dfs(node: str, depth: int):
            nonlocal max_d
            if node in visited:
                return
            visited.add(node)
            max_d = max(max_d, depth)
            for neighbor in adj.get(node, []):
                dfs(neighbor, depth + 1)
            visited.remove(node)

        for caller in adj:
            dfs(caller, 0)

        return max_d


def build_call_graph(tree: ast.AST, all_functions: list) -> CallGraph:
    """Convenience function: build call graph"""
    builder = CallGraphBuilder(tree, all_functions)
    return builder.build()
