"""
ast_analyzer.py — Python代码AST结构分析器
功能: 结构提取、圈复杂度、认知复杂度、文档覆盖率
依赖: Python标准库(ast, pathlib, dataclasses)
"""

import ast
import sys
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


# ─── 数据结构 ───────────────────────────────────────────────

@dataclass
class FunctionInfo:
    name: str
    qualified_name: str  # ClassName.method 或 module.function
    lineno: int
    end_lineno: Optional[int]
    args: list[str]
    decorators: list[str]
    docstring: Optional[str]
    docstring_length: int
    line_count: int  # 函数体行数
    cyclomatic_complexity: int
    cognitive_complexity: int
    is_method: bool
    is_classmethod: bool
    is_staticmethod: bool
    is_property: bool
    is_async: bool
    parent_class: Optional[str] = None


@dataclass
class ClassInfo:
    name: str
    lineno: int
    end_lineno: Optional[int]
    bases: list[str]
    decorators: list[str]
    docstring: Optional[str]
    methods: list[FunctionInfo] = field(default_factory=list)
    method_count: int = 0


@dataclass
class ImportInfo:
    module: str
    names: list[str]
    lineno: int
    is_from: bool  # from X import Y vs import X


@dataclass
class StructureAnalysis:
    """完整的结构分析结果"""
    file_path: str
    total_lines: int
    sloc: int  # 有效代码行数（不含空行和纯注释）
    classes: list[ClassInfo]
    functions: list[FunctionInfo]  # 模块级函数（不含类方法）
    imports: list[ImportInfo]
    all_functions: list[FunctionInfo]  # 所有函数（含类方法）
    # 汇总统计
    class_count: int
    function_count: int  # 模块级函数数
    method_count: int  # 类方法数
    import_count: int
    avg_complexity: float
    max_complexity: int
    doc_coverage: float  # 0-100
    total_arguments: int

    def to_dict(self) -> dict:
        """转为JSON可序列化的dict"""
        return {
            "file_path": self.file_path,
            "total_lines": self.total_lines,
            "sloc": self.sloc,
            "class_count": self.class_count,
            "function_count": self.function_count,
            "method_count": self.method_count,
            "import_count": self.import_count,
            "avg_complexity": round(self.avg_complexity, 2),
            "max_complexity": self.max_complexity,
            "doc_coverage": round(self.doc_coverage, 1),
            "total_arguments": self.total_arguments,
            "classes": [
                {
                    "name": c.name,
                    "lineno": c.lineno,
                    "bases": c.bases,
                    "method_count": c.method_count,
                    "docstring": c.docstring[:80] if c.docstring else None,
                }
                for c in self.classes
            ],
            "functions": [self._func_to_dict(f) for f in self.functions],
            "all_functions": [self._func_to_dict(f) for f in self.all_functions],
            "imports": [
                {
                    "module": i.module,
                    "names": i.names,
                    "lineno": i.lineno,
                    "is_from": i.is_from,
                }
                for i in self.imports
            ],
        }

    @staticmethod
    def _func_to_dict(f: FunctionInfo) -> dict:
        return {
            "name": f.name,
            "qualified_name": f.qualified_name,
            "lineno": f.lineno,
            "end_lineno": f.end_lineno,
            "args": f.args,
            "cyclomatic_complexity": f.cyclomatic_complexity,
            "cognitive_complexity": f.cognitive_complexity,
            "docstring_length": f.docstring_length,
            "line_count": f.line_count,
            "is_method": f.is_method,
            "parent_class": f.parent_class,
            # radon 兼容字段
            "complexity": f.cyclomatic_complexity,
            "rank": _cc_rank(f.cyclomatic_complexity),
            "type": "M" if f.is_method else "F",
        }


# ─── radon 兼容：圈复杂度等级 ───────────────────────────────

def _cc_rank(cc: int) -> str:
    """与 radon 完全一致的评级映射: A(1-5) B(6-10) C(11-15) D(16-20) E(21-25) F(>25)"""
    if cc <= 5:
        return "A"
    if cc <= 10:
        return "B"
    if cc <= 15:
        return "C"
    if cc <= 20:
        return "D"
    if cc <= 25:
        return "E"
    return "F"


# ─── 复杂度计算 ─────────────────────────────────────────────

def _cyclomatic_complexity(node: ast.AST) -> int:
    """
    圈复杂度: 基础分1，每个决策点+1
    决策点: if/elif/for/while/except/with/and/or/ifexp/try
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While,
                              ast.ExceptHandler, ast.With)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.IfExp):
            complexity += 1
        elif isinstance(child, (ast.Try, getattr(ast, 'TryStar', ast.AST))):
            # Python 3.11+ 有 TryStar, 3.8-3.10 只有 Try
            if isinstance(child, ast.Try) or (
                hasattr(ast, 'TryStar') and isinstance(child, ast.TryStar)
            ):
                # Try本身不算，但ExceptHandler已经在上面算了
                pass
    return complexity


def _cognitive_complexity(node: ast.AST) -> int:
    """
    认知复杂度: 嵌套加权 + 结构打断
    - 每层嵌套(if/for/while/with/try) +1
    - else/elif/except +1
    - 嵌套内的决策点 + 嵌套深度
    """
    complexity = 0

    def _walk_depth(node, depth):
        nonlocal complexity
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                depth += 1
                complexity += depth  # 嵌套深度加权
                _walk_depth(child, depth)
                depth -= 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += depth + 1  # except打断+嵌套
                _walk_depth(child, depth + 1)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.IfExp):
                complexity += depth + 1
            else:
                _walk_depth(child, depth)

    _walk_depth(node, 0)
    return complexity


# ─── AST分析器 ───────────────────────────────────────────────

class ASTAnalyzer:
    """Python代码AST结构分析器"""

    def __init__(self, source: str, filename: str = "<unknown>"):
        self.source = source
        self.filename = filename
        self.lines = source.splitlines()
        self.tree = ast.parse(source, filename=filename)

    def analyze(self) -> StructureAnalysis:
        """执行完整结构分析"""
        classes = self._extract_classes()
        functions = self._extract_module_functions()
        imports = self._extract_imports()

        # 合并所有函数（模块级 + 类方法）
        all_functions = list(functions)
        for cls in classes:
            all_functions.extend(cls.methods)

        # 统计
        total_lines = len(self.lines)
        sloc = sum(1 for line in self.lines if line.strip() and not line.strip().startswith('#'))

        # 复杂度统计
        complexities = [f.cyclomatic_complexity for f in all_functions]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0

        # 文档覆盖率
        total_funcs = len(all_functions)
        documented = sum(1 for f in all_functions if f.docstring and f.docstring_length > 10)
        doc_coverage = (documented / total_funcs * 100) if total_funcs > 0 else 100.0

        # 参数总数
        total_args = sum(len(f.args) for f in all_functions)

        return StructureAnalysis(
            file_path=self.filename,
            total_lines=total_lines,
            sloc=sloc,
            classes=classes,
            functions=functions,
            imports=imports,
            all_functions=all_functions,
            class_count=len(classes),
            function_count=len(functions),
            method_count=sum(c.method_count for c in classes),
            import_count=len(imports),
            avg_complexity=avg_complexity,
            max_complexity=max_complexity,
            doc_coverage=doc_coverage,
            total_arguments=total_args,
        )

    def _extract_classes(self) -> list[ClassInfo]:
        """提取所有类定义"""
        classes = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.ClassDef):
                continue

            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(ast.unparse(base))

            decorators = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Attribute):
                    decorators.append(ast.unparse(dec))

            docstring = ast.get_docstring(node)
            methods = self._extract_methods(node, node.name)

            classes.append(ClassInfo(
                name=node.name,
                lineno=node.lineno,
                end_lineno=getattr(node, 'end_lineno', None),
                bases=bases,
                decorators=decorators,
                docstring=docstring,
                methods=methods,
                method_count=len(methods),
            ))

        return classes

    def _extract_methods(self, class_node: ast.ClassDef, class_name: str) -> list[FunctionInfo]:
        """提取类的所有方法"""
        methods = []
        for node in class_node.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            func = self._make_function_info(
                node, class_name=class_name, is_method=True
            )
            methods.append(func)

        return methods

    def _extract_module_functions(self) -> list[FunctionInfo]:
        """提取模块级函数（不在类内部的）"""
        functions = []
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = self._make_function_info(node, is_method=False)
                functions.append(func)
        return functions

    def _make_function_info(self, node, class_name: str = None, is_method: bool = False) -> FunctionInfo:
        """从AST节点创建FunctionInfo"""
        # 函数名
        name = node.name
        if class_name:
            qualified_name = f"{class_name}.{name}"
        else:
            qualified_name = name

        # 参数列表
        args = []
        for arg in node.args.args:
            if arg.arg != 'self' and arg.arg != 'cls':
                args.append(arg.arg)

        # 装饰器
        decorators = []
        is_classmethod = False
        is_staticmethod = False
        is_property = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
                if dec.id == 'classmethod':
                    is_classmethod = True
                elif dec.id == 'staticmethod':
                    is_staticmethod = True
                elif dec.id == 'property':
                    is_property = True
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.unparse(dec))

        # Docstring
        docstring = ast.get_docstring(node)
        docstring_length = len(docstring) if docstring else 0

        # 行数
        end_lineno = getattr(node, 'end_lineno', None)
        line_count = (end_lineno - node.lineno + 1) if end_lineno else 0

        # 复杂度
        cc = _cyclomatic_complexity(node)
        cog = _cognitive_complexity(node)

        return FunctionInfo(
            name=name,
            qualified_name=qualified_name,
            lineno=node.lineno,
            end_lineno=end_lineno,
            args=args,
            decorators=decorators,
            docstring=docstring[:200] if docstring else None,
            docstring_length=docstring_length,
            line_count=line_count,
            cyclomatic_complexity=cc,
            cognitive_complexity=cog,
            is_method=is_method,
            is_classmethod=is_classmethod,
            is_staticmethod=is_staticmethod,
            is_property=is_property,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            parent_class=class_name,
        )

    def _extract_imports(self) -> list[ImportInfo]:
        """提取所有导入语句"""
        imports = []
        for node in self.tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[alias.asname or alias.name],
                        lineno=node.lineno,
                        is_from=False,
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = [alias.name for alias in node.names]
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    lineno=node.lineno,
                    is_from=True,
                ))
        return imports


# ─── 便捷函数 ───────────────────────────────────────────────

def analyze_source(source: str, filename: str = "<unknown>") -> StructureAnalysis:
    """分析Python源码字符串"""
    analyzer = ASTAnalyzer(source, filename)
    return analyzer.analyze()


def analyze_file(file_path: str) -> StructureAnalysis:
    """分析Python文件"""
    path = Path(file_path)
    # 尝试多种编码
    for encoding in ('utf-8', 'gbk', 'latin-1'):
        try:
            source = path.read_text(encoding=encoding)
            return analyze_source(source, str(path))
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"无法读取文件 {file_path}: 编码不支持")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python -m code_analyzer.ast_analyzer <file.py>")
        sys.exit(1)

    result = analyze_file(sys.argv[1])
    import json
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
