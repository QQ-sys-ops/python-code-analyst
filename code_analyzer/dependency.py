"""
dependency.py — 模块依赖分析器
功能: stdlib/third-party/local自动分类、循环依赖检测(DFS)、扇入扇出
依赖: ast_analyzer.py (ImportInfo)
"""

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Python标准库模块列表（Python 3.8+常用）
STDLIB_MODULES: set[str] = {
    # 内置模块
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
    'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
    'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
    'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
    'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
    'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
    'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
    'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
    'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
    'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
    'getpass', 'gettext', 'glob', 'grp', 'gzip', 'hashlib', 'heapq',
    'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr', 'imp',
    'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json',
    'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma',
    'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap',
    'modulefinder', 'multiprocessing', 'netrc', 'nis', 'nntplib',
    'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib',
    'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
    'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile',
    'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc',
    'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
    'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
    'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site',
    'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
    'sqlite3', 'sre_compile', 'sre_constants', 'sre_parse', 'ssl',
    'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
    'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
    'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
    'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize',
    'tomllib', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
    'turtledemo', 'types', 'typing', 'unicodedata', 'unittest',
    'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave',
    'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
    'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport',
    'zlib',
    # 常用子模块
    'os.path', 'os.pathsep', 'os.sep',
    'logging.handlers', 'logging.config',
    'collections.abc', 'collections.defaultdict',
    'pathlib.PurePath', 'pathlib.Path',
    'typing.Dict', 'typing.List', 'typing.Optional', 'typing.Union',
    'typing.TYPE_CHECKING',
    'json.decoder', 'json.encoder',
    'ast.dump', 'ast.parse', 'ast.unparse',
    # Python 3.11+ 新增模块
    'tomllib', 'exceptiongroup', 'taskgroup',
    # Python 3.12+ 新增模块
    'dbm.sqlite3',
}


@dataclass
class DependencyInfo:
    """依赖分析结果"""
    standard_lib: list[str]     # 标准库依赖
    third_party: list[str]      # 第三方依赖
    local: list[str]            # 本地依赖
    all_modules: list[str]      # 所有导入的模块
    has_circular: bool          # 是否存在循环依赖
    circular_cycles: list[list[str]]  # 循环链
    fan_in: dict[str, int]      # 扇入: 被多少模块依赖
    fan_out: dict[str, int]     # 扇出: 依赖多少模块
    import_count: int

    def to_dict(self) -> dict:
        return {
            "standard_lib": self.standard_lib,
            "third_party": self.third_party,
            "local": self.local,
            "standard_lib_count": len(self.standard_lib),
            "third_party_count": len(self.third_party),
            "local_count": len(self.local),
            "import_count": self.import_count,
            "has_circular": self.has_circular,
            "circular_cycles": self.circular_cycles,
            "fan_in": self.fan_in,
            "fan_out": self.fan_out,
        }


class DependencyAnalyzer:
    """模块依赖分析器"""

    def __init__(self, imports: list, source: str = "", root_dir: str | None = None):
        """
        Args:
            imports: StructureAnalysis.imports
            source: 源码字符串（用于本地模块检测）
            root_dir: 项目根目录（用于本地模块检测，解决CWD问题）
        """
        self.imports = imports
        self.source = source
        self.root_dir = root_dir

    def analyze(self, source_files: list[str] | None = None) -> DependencyInfo:
        """
        执行依赖分析
        Args:
            source_files: 项目中所有.py文件路径（用于本地模块检测）
        """
        standard_lib = []
        third_party = []
        local = []
        all_modules = []

        # 收集所有导入的模块
        for imp in self.imports:
            module = imp.module
            if not module:
                continue

            all_modules.append(module)

            # 分类
            category = self._classify_module(module, source_files)
            if category == 'stdlib':
                standard_lib.append(module)
            elif category == 'third-party':
                third_party.append(module)
            elif category == 'local':
                local.append(module)

        # 去重
        standard_lib = sorted(set(standard_lib))
        third_party = sorted(set(third_party))
        local = sorted(set(local))
        all_modules = sorted(set(all_modules))

        # 循环依赖检测（需要多文件信息）
        has_circular = False
        circular_cycles = []
        if source_files and len(source_files) > 1:
            has_circular, circular_cycles = self._detect_circular(source_files)

        # 扇入扇出
        fan_in, fan_out = self._calc_fan(all_modules)

        return DependencyInfo(
            standard_lib=standard_lib,
            third_party=third_party,
            local=local,
            all_modules=all_modules,
            has_circular=has_circular,
            circular_cycles=circular_cycles,
            fan_in=fan_in,
            fan_out=fan_out,
            import_count=len(self.imports),
        )

    def _classify_module(self, module: str, source_files: list[str] | None = None) -> str:
        """分类模块: stdlib / third-party / local"""
        # 取顶层模块名
        top_module = module.split('.')[0]

        # 检查标准库
        if top_module in STDLIB_MODULES or module in STDLIB_MODULES:
            return 'stdlib'

        # 相对导入一定是本地
        if module.startswith('.'):
            return 'local'

        # 检查本地模块（有source_files时精确匹配）
        if source_files:
            for sf in source_files:
                sf_path = Path(sf)
                sf_stem = sf_path.stem
                if top_module == sf_stem or top_module == sf_path.name:
                    return 'local'

        # 启发式判断：src.开头的通常是本地项目模块
        if top_module == 'src' or top_module.startswith('src_'):
            return 'local'

        # 检查是否是项目目录下存在的模块（解决CWD问题）
        try:
            if self.root_dir:
                # 使用项目根目录判断
                if Path(self.root_dir, f"{top_module}.py").exists() or Path(self.root_dir, top_module).is_dir():
                    return 'local'
            else:
                # 降级到当前目录（向后兼容）
                if Path(f"{top_module}.py").exists() or Path(top_module).is_dir():
                    return 'local'
        except (OSError, ValueError):
            pass

        # 其余归为第三方
        return 'third-party'

    def _detect_circular(self, source_files: list[str]) -> tuple[bool, list[list[str]]]:
        """
        检测循环依赖（DFS环检测）
        需要扫描所有源文件的import关系
        """
        # 构建模块→依赖映射
        module_deps: dict[str, set[str]] = {}

        for sf in source_files:
            try:
                from .utils import read_file_with_encoding
                source = read_file_with_encoding(sf)

                tree = ast.parse(source)
                deps = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            deps.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            deps.add(node.module.split('.')[0])

                module_name = Path(sf).stem
                module_deps[module_name] = deps
            except (SyntaxError, ValueError):
                continue

        # DFS找环
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in module_deps.get(node, set()):
                if neighbor not in module_deps:
                    continue
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # 找到环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for module in module_deps:
            if module not in visited:
                dfs(module)

        return len(cycles) > 0, cycles

    def _calc_fan(self, all_modules: list[str]) -> tuple[dict[str, int], dict[str, int]]:
        """
        计算扇入扇出（修复逻辑错误）
        fan_in: 被多少模块导入（依赖这个模块的模块数）
        fan_out: 导入了多少模块（这个模块依赖的模块数）
        """
        fan_in: dict[str, int] = {}
        fan_out: dict[str, int] = {}

        # fan_out: 每个模块导入了哪些模块
        for imp in self.imports:
            module = imp.module.split('.')[0] if imp.module else ''
            if module:
                fan_out[module] = fan_out.get(module, 0) + 1

        # fan_in: 哪些模块导入了这个模块
        for imp in self.imports:
            for name in imp.names:
                # 取顶层模块名
                top_name = name.split('.')[0] if name else ''
                if top_name:
                    fan_in[top_name] = fan_in.get(top_name, 0) + 1

        return fan_in, fan_out


def analyze_dependencies(imports: list, source_files: list[str] | None = None, 
                         root_dir: str | None = None) -> DependencyInfo:
    """便捷函数: 分析依赖
    
    Args:
        imports: 导入列表
        source_files: 源文件列表（用于循环依赖检测）
        root_dir: 项目根目录（用于本地模块检测，解决CWD问题）
    """
    analyzer = DependencyAnalyzer(imports, root_dir=root_dir)
    return analyzer.analyze(source_files)
