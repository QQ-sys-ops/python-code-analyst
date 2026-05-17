"""
dead_code.py — 死代码检测器
功能: 从入口点遍历调用图，识别未被调用的函数
依赖: call_graph.py (CallGraph)
"""

from collections import deque
from dataclasses import dataclass
from .call_graph import SPECIAL_FUNCTIONS


@dataclass
class DeadCodeResult:
    """死代码检测结果"""
    unreachable: list[str]      # 未被调用的函数
    reachable: list[str]        # 被调用的函数
    total_user_functions: int   # 用户定义的函数总数
    coverage: float             # 覆盖率 0-100
    special_excluded: list[str] # 被排除的特殊方法

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
    死代码检测器
    逻辑:
    1. 从入口点出发，BFS遍历调用图
    2. 所有被遍历到的函数 = 可达（活代码）
    3. 用户定义但不可达的函数 = 死代码
    4. Python特殊方法自动排除
    """

    def __init__(self, call_graph, all_functions: list):
        """
        Args:
            call_graph: CallGraph对象
            all_functions: StructureAnalysis.all_functions
        """
        self.call_graph = call_graph
        self.all_functions = all_functions

    def detect(self) -> DeadCodeResult:
        """执行死代码检测"""
        # 构建正向邻接表
        adj: dict[str, set[str]] = {}
        for edge in self.call_graph.edges:
            adj.setdefault(edge.caller, set()).add(edge.callee)

        # 从入口点BFS（使用deque优化性能）
        reachable = set()
        queue = deque(self.call_graph.entry_points)

        while queue:
            current = queue.popleft()  # O(1) instead of O(n)
            if current in reachable:
                continue
            reachable.add(current)
            for neighbor in adj.get(current, set()):
                if neighbor not in reachable:
                    queue.append(neighbor)

        # 收集所有用户定义的函数
        user_funcs = set()
        special_excluded = []
        public_api = set()  # 公共API（非下划线开头的模块级函数）
        for func in self.all_functions:
            qn = func.qualified_name
            name = func.name
            if name in SPECIAL_FUNCTIONS or qn.split('.')[-1] in SPECIAL_FUNCTIONS:
                special_excluded.append(qn)
                continue
            user_funcs.add(qn)
            # 公共API: 非下划线开头的模块级函数（可能是外部调用入口）
            if not func.is_method and not name.startswith('_'):
                public_api.add(qn)

        # 死代码 = 用户定义 - 可达 - 公共API
        # 公共API不计入死代码（可能被外部模块调用）
        unreachable = sorted(user_funcs - reachable - public_api)
        reachable_list = sorted(user_funcs & reachable)

        # 覆盖率
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
    """便捷函数: 检测死代码"""
    detector = DeadCodeDetector(call_graph, all_functions)
    return detector.detect()
