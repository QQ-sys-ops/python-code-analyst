"""
report.py — 12节标准报告生成器
功能: 将各分析模块的结果组装为标准化Markdown报告
"""

import json
from datetime import datetime


# 复杂度等级映射
def _complexity_grade(cc: int) -> str:
    if cc <= 5:
        return "A"
    elif cc <= 10:
        return "B"
    elif cc <= 20:
        return "C"
    elif cc <= 50:
        return "D"
    else:
        return "F"


def _grade_color(grade: str) -> str:
    return {"A": "✅", "B": "✅", "C": "⚠️", "D": "🔴", "F": "💀"}.get(grade, "❓")


def generate_report(
    structure,
    call_graph,
    impact_analysis,
    dead_code_result,
    dependency_result,
    ai_analysis: dict = None,
) -> str:
    """
    生成12节标准报告

    Args:
        structure: StructureAnalysis
        call_graph: CallGraph
        impact_analysis: ImpactAnalysis
        dead_code_result: DeadCodeResult
        dependency_result: DependencyInfo
        ai_analysis: Agent层分析结果（可选）
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    filename = structure.file_path

    sections = []

    # ═══ 一、结构概览 ═══
    sections.append(_section_1(structure))

    # ═══ 二、架构分析 ═══
    sections.append(_section_2(structure))

    # ═══ 三、复杂度分析 ═══
    sections.append(_section_3(structure))

    # ═══ 四、调用图分析 ═══
    sections.append(_section_4(call_graph))

    # ═══ 五、影响面分析 ═══
    sections.append(_section_5(impact_analysis))

    # ═══ 六、死代码检测 ═══
    sections.append(_section_6(dead_code_result))

    # ═══ 七、依赖分析 ═══
    sections.append(_section_7(dependency_result))

    # ═══ 八、代码意图（Agent层） ═══
    sections.append(_section_8(ai_analysis))

    # ═══ 九、文档覆盖率 ═══
    sections.append(_section_9(structure))

    # ═══ 十、重构建议 ═══
    sections.append(_section_10(structure, call_graph, dead_code_result, dependency_result))

    # ═══ 十一、综合评估 ═══
    sections.append(_section_11(structure, call_graph, dead_code_result, dependency_result))

    # ═══ 十二、总结 ═══
    sections.append(_section_12(structure, call_graph, dead_code_result))

    # 组装报告
    header = f"""# {filename} 深度分析报告

**分析时间**: {now}
**分析工具**: python-code-analyst v2.0.0
**文件路径**: `{filename}`

---"""

    footer = f"""
---

*分析报告生成时间: {now}*
*分析工具: python-code-analyst v2.0.0*
*⚠️ 本报告由code_analyzer工具自动生成，Agent层分析由LLM完成*"""

    return header + "\n\n".join(sections) + footer


def _section_1(structure) -> str:
    """一、结构概览"""
    # 计算综合评分
    grades = []
    for f in structure.all_functions:
        g = _complexity_grade(f.cyclomatic_complexity)
        grades.append(g)

    grade_counts = {}
    for g in grades:
        grade_counts[g] = grade_counts.get(g, 0) + 1

    grade_str = " ".join(f"{g}:{grade_counts.get(g,0)}" for g in "ABCDF" if g in grade_counts)

    return f"""## 一、结构概览

| 维度 | 数据 | 说明 |
|------|------|------|
| 总行数 | {structure.total_lines}行 | 包含空行 |
| 有效代码行(SLOC) | {structure.sloc}行 | 有效语句 |
| 类数量 | {structure.class_count}个 | |
| 函数数量 | {structure.function_count}个 | 模块级 |
| 方法数量 | {structure.method_count}个 | 含继承方法 |
| 导入数量 | {structure.import_count}个 | |
| 参数总数 | {structure.total_arguments}个 | |

**复杂度分布**: {grade_str}"""


def _section_2(structure) -> str:
    """二、架构分析"""
    lines = ["## 二、架构分析\n"]

    if structure.classes:
        lines.append("### 类结构\n")
        for cls in structure.classes:
            bases = ", ".join(cls.bases) if cls.bases else "无"
            methods = ", ".join(m.name for m in cls.methods[:10])
            if cls.method_count > 10:
                methods += f" ... (共{cls.method_count}个)"
            lines.append(f"**{cls.name}** (继承: {bases})")
            lines.append(f"- 方法: {methods}")
            lines.append("")

    # 设计模式推断
    lines.append("### 设计模式推断\n")
    patterns = []
    for cls in structure.classes:
        method_names = [m.name for m in cls.methods]
        if '__init__' in method_names and len(cls.bases) == 0:
            patterns.append(f"- {cls.name}: 基础类")
        elif any(m.is_classmethod for m in cls.methods):
            patterns.append(f"- {cls.name}: 含类方法（可能的工厂/注册模式）")
        elif any(m.is_staticmethod for m in cls.methods):
            patterns.append(f"- {cls.name}: 含静态方法（工具类）")

    if patterns:
        lines.extend(patterns)
    else:
        lines.append("- 未检测到明显的设计模式")

    return "\n".join(lines)


def _section_3(structure) -> str:
    """三、复杂度分析"""
    lines = ["## 三、复杂度分析\n"]
    lines.append("| 类/方法 | 位置 | 圈复杂度 | 认知复杂度 | 行数 | 评级 |")
    lines.append("|---------|------|:---:|:---:|:---:|:---:|")

    for f in structure.all_functions:
        grade = _complexity_grade(f.cyclomatic_complexity)
        icon = _grade_color(grade)
        loc = f"L{f.lineno}" if f.lineno else "?"
        qn = f.qualified_name
        lines.append(
            f"| {qn} | {loc} | {f.cyclomatic_complexity} | "
            f"{f.cognitive_complexity} | {f.line_count} | {icon}{grade} |"
        )

    # 整体评级
    ccs = [f.cyclomatic_complexity for f in structure.all_functions]
    if ccs:
        avg_cc = sum(ccs) / len(ccs)
        max_cc = max(ccs)
        grade_counts = {}
        for cc in ccs:
            g = _complexity_grade(cc)
            grade_counts[g] = grade_counts.get(g, 0) + 1
        dominant = max(grade_counts, key=grade_counts.get)
        lines.append(f"\n**整体评级**: {dominant}级 "
                      f"({grade_counts.get(dominant,0)}个, "
                      f"{grade_counts.get(dominant,0)/len(ccs)*100:.0f}%) "
                      f"| 平均: {avg_cc:.1f} | 最大: {max_cc}")

    return "\n".join(lines)


def _section_4(call_graph) -> str:
    """四、调用图分析"""
    lines = ["## 四、调用图分析\n"]

    lines.append(f"**调用边**: {len(call_graph.edges)}条  ")
    lines.append(f"**用户定义函数**: {len(call_graph.user_functions)}个  ")
    lines.append(f"**被调用函数**: {len(call_graph.called_functions)}个  ")
    lines.append(f"**最大调用深度**: {call_graph.max_depth}\n")

    # 调用关系表
    if call_graph.edges:
        lines.append("### 调用关系\n")
        lines.append("| 调用者 | 被调用者 | 行号 |")
        lines.append("|--------|----------|------|")
        for e in call_graph.edges[:30]:  # 限制显示数量
            lines.append(f"| {e.caller} | {e.callee} | L{e.lineno} |")
        if len(call_graph.edges) > 30:
            lines.append(f"\n*（仅显示前30条，共{len(call_graph.edges)}条）*")

    # 入口点
    if call_graph.entry_points:
        lines.append("\n### 入口点\n")
        for ep in call_graph.entry_points:
            lines.append(f"- `{ep}`")

    return "\n".join(lines)


def _section_5(impact_analysis) -> str:
    """五、影响面分析"""
    lines = ["## 五、影响面分析\n"]

    if impact_analysis.impacts:
        lines.append("| 修改目标 | 直接影响 | 间接影响 | 总影响 |")
        lines.append("|----------|:--------:|:--------:|:------:|")
        for imp in impact_analysis.impacts[:20]:
            lines.append(
                f"| {imp.function} | {len(imp.direct_impact)} | "
                f"{len(imp.indirect_impact)} | **{imp.total_impact}** |"
            )
    else:
        lines.append("无调用关系，影响面分析不适用。")

    return "\n".join(lines)


def _section_6(dead_code_result) -> str:
    """六、死代码检测"""
    lines = ["## 六、死代码检测\n"]

    lines.append(f"**覆盖率**: {dead_code_result.coverage}% "
                  f"({dead_code_result.total_user_functions - len(dead_code_result.unreachable)}"
                  f"/{dead_code_result.total_user_functions})\n")

    if dead_code_result.unreachable:
        lines.append("### 未覆盖函数\n")
        lines.append("| 函数 | 风险 |")
        lines.append("|------|------|")
        for func in dead_code_result.unreachable:
            lines.append(f"| `{func}` | ⚠️ 无调用路径 |")
    else:
        lines.append("✅ 所有用户定义函数均有调用路径。")

    if dead_code_result.special_excluded:
        lines.append(f"\n*（排除{len(dead_code_result.special_excluded)}个特殊方法）*")

    return "\n".join(lines)


def _section_7(dependency_result) -> str:
    """七、依赖分析"""
    lines = ["## 七、依赖分析\n"]

    lines.append(f"**循环导入**: {'❌ 有' if dependency_result.has_circular else '✅ 无'}\n")

    lines.append("| 依赖类型 | 数量 | 模块列表 |")
    lines.append("|----------|:----:|----------|")
    lines.append(f"| stdlib | {len(dependency_result.standard_lib)} | "
                  f"{', '.join(dependency_result.standard_lib[:10])}{'...' if len(dependency_result.standard_lib) > 10 else ''} |")
    lines.append(f"| third-party | {len(dependency_result.third_party)} | "
                  f"{', '.join(dependency_result.third_party[:10])}{'...' if len(dependency_result.third_party) > 10 else ''} |")
    lines.append(f"| local | {len(dependency_result.local)} | "
                  f"{', '.join(dependency_result.local[:10])}{'...' if len(dependency_result.local) > 10 else ''} |")

    if dependency_result.circular_cycles:
        lines.append("\n### 循环依赖详情\n")
        for cycle in dependency_result.circular_cycles:
            lines.append(f"- {' → '.join(cycle)}")

    return "\n".join(lines)


def _section_8(ai_analysis) -> str:
    """八、代码意图（Agent层）"""
    lines = ["## 八、代码意图\n"]

    if ai_analysis:
        for key, value in ai_analysis.items():
            lines.append(f"### {key}\n")
            lines.append(str(value))
            lines.append("")
    else:
        lines.append("*此部分由Agent层(LLM)分析生成，需AI能力支持。*")
        lines.append("*code_analyzer工具仅提供静态数据，代码意图分析请由Agent完成。*")

    return "\n".join(lines)


def _section_9(structure) -> str:
    """九、文档覆盖率"""
    lines = ["## 九、文档覆盖率\n"]

    total = len(structure.all_functions)
    documented = sum(1 for f in structure.all_functions if f.docstring and f.docstring_length > 10)
    coverage = (documented / total * 100) if total > 0 else 100

    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总函数/方法 | {total} |")
    lines.append(f"| 有docstring | {documented} |")
    lines.append(f"| **覆盖率** | **{coverage:.1f}%** |")

    # 缺失docstring的方法
    missing = [f for f in structure.all_functions if not f.docstring or f.docstring_length <= 10]
    if missing:
        lines.append("\n### 缺失docstring的方法\n")
        lines.append("| 方法 | 位置 | 优先级 |")
        lines.append("|------|------|--------|")
        for f in missing[:15]:
            grade = _complexity_grade(f.cyclomatic_complexity)
            priority = "P0" if grade in ("D", "F") else "P1" if grade == "C" else "P2"
            lines.append(f"| `{f.qualified_name}` | L{f.lineno} | {priority} |")
        if len(missing) > 15:
            lines.append(f"\n*（仅显示前15个，共{len(missing)}个缺失）*")

    return "\n".join(lines)


def _section_10(structure, call_graph, dead_code, dependency) -> str:
    """十、重构建议"""
    lines = ["## 十、重构建议\n"]

    suggestions_p0 = []
    suggestions_p1 = []

    # P0: 高复杂度函数
    for f in structure.all_functions:
        if f.cyclomatic_complexity > 20:
            suggestions_p0.append(
                f"函数 `{f.qualified_name}` 圈复杂度{f.cyclomatic_complexity}(D级)，建议拆分"
            )
        elif f.cyclomatic_complexity > 10:
            suggestions_p1.append(
                f"函数 `{f.qualified_name}` 圈复杂度{f.cyclomatic_complexity}(C级)，可考虑简化"
            )

    # P0: 死代码
    for func in dead_code.unreachable:
        suggestions_p1.append(f"函数 `{func}` 无调用路径，可考虑移除或添加入口")

    # P1: 循环依赖
    if dependency.has_circular:
        for cycle in dependency.circular_cycles:
            suggestions_p0.append(f"循环依赖: {' → '.join(cycle)}，需重构依赖方向")

    # P1: 无docstring的复杂函数
    for f in structure.all_functions:
        if (not f.docstring or f.docstring_length <= 10) and f.cyclomatic_complexity > 5:
            suggestions_p1.append(
                f"函数 `{f.qualified_name}` 复杂度{f.cyclomatic_complexity}但无docstring，建议补充文档"
            )

    if suggestions_p0:
        lines.append("### P0级（建议立即修复）\n")
        lines.append("| # | 建议 |")
        lines.append("|---|------|")
        for i, s in enumerate(suggestions_p0, 1):
            lines.append(f"| {i} | {s} |")

    if suggestions_p1:
        lines.append("\n### P1级（建议后续优化）\n")
        lines.append("| # | 建议 |")
        lines.append("|---|------|")
        for i, s in enumerate(suggestions_p1[:10], 1):
            lines.append(f"| {i} | {s} |")

    if not suggestions_p0 and not suggestions_p1:
        lines.append("✅ 未发现需要重构的问题。")

    return "\n".join(lines)


def _section_11(structure, call_graph, dead_code, dependency) -> str:
    """十一、综合评估"""
    lines = ["## 十一、综合评估\n"]

    # 各维度评分 (0-10)
    # 复杂度: 平均CC越低越好
    avg_cc = structure.avg_complexity
    complexity_score = max(0, min(10, 10 - avg_cc))

    # 文档: 覆盖率越高越好
    doc_score = structure.doc_coverage / 10

    # 结构: 函数数量合理+类结构清晰
    struct_score = 7.0  # 基础分
    if structure.class_count > 0 and structure.method_count > 0:
        struct_score += 1  # 有类结构
    if structure.function_count + structure.method_count < 50:
        struct_score += 1  # 规模合理
    struct_score = min(10, struct_score)

    # 死代码: 覆盖率越高越好
    dead_score = dead_code.coverage / 10

    # 依赖: 无循环+合理分类
    dep_score = 8.0
    if dependency.has_circular:
        dep_score -= 3
    if len(dependency.third_party) > 10:
        dep_score -= 1
    dep_score = max(0, dep_score)

    # 综合分
    weights = {"complexity": 0.25, "doc": 0.25, "structure": 0.2,
               "dead_code": 0.15, "dependency": 0.15}
    total = (
        complexity_score * weights["complexity"]
        + doc_score * weights["doc"]
        + struct_score * weights["structure"]
        + dead_score * weights["dead_code"]
        + dep_score * weights["dependency"]
    )

    grade = "A" if total >= 8.5 else "B" if total >= 7 else "C" if total >= 5.5 else "D" if total >= 4 else "F"

    lines.append("| 维度 | 得分 | 权重 | 说明 |")
    lines.append("|------|:----:|:----:|------|")
    lines.append(f"| 复杂度 | {complexity_score:.1f} | 25% | 平均CC={avg_cc:.1f} |")
    lines.append(f"| 文档 | {doc_score:.1f} | 25% | 覆盖率={structure.doc_coverage:.1f}% |")
    lines.append(f"| 结构 | {struct_score:.1f} | 20% | 类{structure.class_count}个+函数{structure.function_count}个 |")
    lines.append(f"| 死代码 | {dead_score:.1f} | 15% | 覆盖率={dead_code.coverage:.1f}% |")
    lines.append(f"| 依赖 | {dep_score:.1f} | 15% | 循环={dependency.has_circular} |")
    lines.append(f"| **综合** | **{total:.1f}** | **100%** | **{grade}级** |")

    return "\n".join(lines)


def _section_12(structure, call_graph, dead_code) -> str:
    """十二、总结"""
    lines = ["## 十二、总结\n"]

    # 优势
    strengths = []
    if structure.avg_complexity <= 5:
        strengths.append("整体复杂度低，代码可读性好")
    if structure.doc_coverage >= 80:
        strengths.append("文档覆盖率高")
    if not dead_code.unreachable:
        strengths.append("无死代码，所有函数均有调用路径")
    if call_graph.max_depth <= 3:
        strengths.append("调用层次浅，结构清晰")

    # 问题
    issues = []
    high_cc = [f for f in structure.all_functions if f.cyclomatic_complexity > 10]
    if high_cc:
        issues.append(f"{len(high_cc)}个函数复杂度>10，需关注")
    if dead_code.unreachable:
        issues.append(f"{len(dead_code.unreachable)}个函数无调用路径")
    if structure.doc_coverage < 50:
        issues.append("文档覆盖率不足50%")

    lines.append("| 优势 | 问题 |")
    lines.append("|------|------|")

    max_rows = max(len(strengths), len(issues))
    for i in range(max_rows):
        s = f"✅ {strengths[i]}" if i < len(strengths) else ""
        issue = f"⚠️ {issues[i]}" if i < len(issues) else ""
        lines.append(f"| {s} | {issue} |")

    if not strengths and not issues:
        lines.append("| ✅ 无明显问题 | ⚠️ 无明显优势 |")

    # 整体评价
    total_funcs = len(structure.all_functions)
    total_lines = structure.total_lines
    lines.append(f"\n**整体评价**: {total_lines}行代码，{structure.class_count}个类，"
                  f"{total_funcs}个函数/方法，复杂度平均{structure.avg_complexity:.1f}")

    return "\n".join(lines)
