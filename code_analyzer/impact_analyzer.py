"""
impact_analyzer.py — 修改影响面分析器
功能: 基于调用图的传递闭包计算，分析修改每个函数会影响谁
依赖: call_graph.py (CallGraph, CallEdge)
"""

from dataclasses import dataclass, field


@dataclass
class ImpactResult:
    """单个函数的影响面分析结果"""
    function: str           # 目标函数
    direct_impact: list[str]   # 直接影响（谁调用了我）
    indirect_impact: list[str] # 间接影响（传递闭包）
    total_impact: int          # 总影响范围
    impact_chain: list[list[str]]  # 影响链路

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
    """完整的影响面分析结果"""
    impacts: list[ImpactResult]
    most_impacted: list[str]     # 影响范围最大的函数
    least_impacted: list[str]    # 影响范围最小的函数

    def to_dict(self) -> dict:
        return {
            "function_count": len(self.impacts),
            "most_impacted": self.most_impacted,
            "least_impacted": self.least_impacted,
            "impacts": [i.to_dict() for i in self.impacts],
        }


class ImpactAnalyzer:
    """
    基于调用图的传递闭包影响面分析
    核心逻辑: 如果A调用B，修改B会影响A
    传递闭包: 如果A→B→C，修改C会影响B和A
    """

    def __init__(self, call_graph):
        """
        Args:
            call_graph: CallGraph对象
        """
        self.call_graph = call_graph
        # 构建反向邻接表: callee → [callers]
        self.reverse_adj: dict[str, list[str]] = {}
        self._build_reverse()

    def _build_reverse(self):
        """构建反向调用图"""
        for edge in self.call_graph.edges:
            self.reverse_adj.setdefault(edge.callee, []).append(edge.caller)

    def analyze(self) -> ImpactAnalysis:
        """对所有函数执行影响面分析"""
        impacts = []

        for func in self.call_graph.user_functions:
            # 跳过Python特殊方法
            if self._is_special(func):
                continue

            result = self._analyze_function(func)
            if result.total_impact > 0:
                impacts.append(result)

        # 按影响范围排序
        impacts.sort(key=lambda x: x.total_impact, reverse=True)

        most = [i.function for i in impacts[:5]] if impacts else []
        least = [i.function for i in impacts[-5:]] if impacts else []

        return ImpactAnalysis(
            impacts=impacts,
            most_impacted=most,
            least_impacted=least,
        )

    def _analyze_function(self, function: str) -> ImpactResult:
        """分析单个函数的影响面"""
        direct = list(self.reverse_adj.get(function, []))

        # BFS传递闭包
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
            impact_chain=chains[:10],  # 限制链路数量
        )

    def _is_special(self, func: str) -> bool:
        """检查是否为Python特殊方法"""
        name = func.split('.')[-1] if '.' in func else func
        from .call_graph import SPECIAL_FUNCTIONS
        return name in SPECIAL_FUNCTIONS


def analyze_impact(call_graph) -> ImpactAnalysis:
    """便捷函数: 分析影响面"""
    analyzer = ImpactAnalyzer(call_graph)
    return analyzer.analyze()
