"""
call_graph.py — 函数调用图分析器
功能: 两遍扫描提取调用边、特殊函数过滤、调用深度计算
依赖: ast_analyzer.py (FunctionInfo, StructureAnalysis)
"""

import ast
from dataclasses import dataclass, field


# Python特殊方法（死代码检测时排除）
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
    # 框架钩子
    'setup', 'teardown', 'setUp', 'tearDown',
    'setUpClass', 'tearDownClass',
})


@dataclass
class CallEdge:
    """一条调用边: caller → callee"""
    caller: str       # 调用者 qualified_name
    callee: str       # 被调用者 qualified_name
    lineno: int       # 调用位置行号
    callee_raw: str   # 原始调用名（未解析）


@dataclass
class CallGraph:
    """调用图分析结果"""
    edges: list[CallEdge]
    user_functions: set[str]    # 所有用户定义的函数名集合
    called_functions: set[str]  # 被调用过的函数名集合
    entry_points: list[str]     # 入口点函数
    max_depth: int              # 最大调用深度

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
    两遍扫描构建调用图:
    第1遍: 收集所有用户定义的函数名
    第2遍: 提取所有调用关系
    """

    def __init__(self, tree: ast.AST, all_functions: list):
        """
        Args:
            tree: ast.parse() 的结果
            all_functions: StructureAnalysis.all_functions
        """
        self.tree = tree
        self.all_functions = all_functions

        # 第1遍: 构建函数名集合
        self.user_functions: set[str] = set()
        self.func_line_map: dict[str, int] = {}  # qualified_name → lineno
        self._collect_functions()

    def _collect_functions(self):
        """第1遍: 收集所有用户定义的函数名"""
        for func in self.all_functions:
            self.user_functions.add(func.qualified_name)
            self.func_line_map[func.qualified_name] = func.lineno
            # 也注册短名（不带类前缀）
            self.user_functions.add(func.name)

    def build(self) -> CallGraph:
        """第2遍: 提取调用关系，构建调用图"""
        edges = []
        called = set()

        for node in ast.walk(self.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # 确定调用者
            caller = self._get_qualified_name(node)
            if caller is None:
                continue

            # 遍历函数体中的所有Call节点
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    callee_name = self._extract_callee_name(child)
                    if callee_name and callee_name in self.user_functions:
                        # 解析callee的qualified_name
                        resolved = self._resolve_callee(callee_name)
                        if resolved:
                            edges.append(CallEdge(
                                caller=caller,
                                callee=resolved,
                                lineno=getattr(child, 'lineno', 0),
                                callee_raw=callee_name,
                            ))
                            called.add(resolved)

        # 找入口点: 被调用过的函数中，没有被其他函数调用的
        all_called = {e.callee for e in edges}
        all_callers = {e.caller for e in edges}
        entry_points = []
        for func in self.all_functions:
            qn = func.qualified_name
            if qn in all_called and qn not in all_callers:
                entry_points.append(qn)

        # 如果没找到入口点，用常见的入口模式
        if not entry_points:
            for func in self.all_functions:
                if func.name in ('main', 'run', 'execute', 'process',
                                 'train', 'predict', 'evaluate',
                                 'cli', 'app'):
                    entry_points.append(func.qualified_name)

        # 计算最大调用深度
        max_depth = self._calc_max_depth(edges)

        return CallGraph(
            edges=edges,
            user_functions=self.user_functions,
            called_functions=called,
            entry_points=entry_points,
            max_depth=max_depth,
        )

    def _get_qualified_name(self, node) -> str | None:
        """获取函数节点的qualified_name"""
        # 需要从all_functions中查找匹配的
        for func in self.all_functions:
            if func.lineno == node.lineno and func.name == node.name:
                return func.qualified_name
        return node.name

    def _extract_callee_name(self, call_node: ast.Call) -> str | None:
        """从Call节点提取被调用函数名"""
        func = call_node.func

        if isinstance(func, ast.Name):
            # 直接调用: train_one_epoch() → 可能是用户函数
            return func.id
        elif isinstance(func, ast.Attribute):
            # 方法调用: model.train() / optimizer.step()
            # 不解析为用户函数（避免model.train()误匹配train()函数）
            return None
        elif isinstance(func, ast.Call):
            # 装饰器工厂: @decorator()
            return None
        return None

    def _resolve_callee(self, name: str) -> str | None:
        """将短名解析为qualified_name"""
        # 精确匹配
        if name in self.func_line_map:
            # 如果有多个同名函数，返回第一个
            for qn in self.user_functions:
                if qn == name or qn.endswith(f".{name}"):
                    return qn
        # 模糊匹配: 带类前缀的
        for qn in self.user_functions:
            if qn.endswith(f".{name}"):
                return qn
        return name  # 无法解析时返回原名

    def _calc_max_depth(self, edges: list[CallEdge]) -> int:
        """计算最大调用深度"""
        if not edges:
            return 0

        # 构建邻接表
        adj: dict[str, list[str]] = {}
        for e in edges:
            adj.setdefault(e.caller, []).append(e.callee)

        # DFS求最长路径（可能有环，需要visited）
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
    """便捷函数: 构建调用图"""
    builder = CallGraphBuilder(tree, all_functions)
    return builder.build()
