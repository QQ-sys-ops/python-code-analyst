"""
dependency.py — Module Dependency Analyzer
Features: Auto-classification of stdlib/third-party/local, circular dependency detection (DFS), fan-in/fan-out
Dependencies: ast_analyzer.py (ImportInfo)
"""

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Python standard library module list (commonly used in Python 3.8+)
STDLIB_MODULES: set[str] = {
    # Built-in modules
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
    # Common submodules
    'os.path', 'os.pathsep', 'os.sep',
    'logging.handlers', 'logging.config',
    'collections.abc', 'collections.defaultdict',
    'pathlib.PurePath', 'pathlib.Path',
    'typing.Dict', 'typing.List', 'typing.Optional', 'typing.Union',
    'typing.TYPE_CHECKING',
    'json.decoder', 'json.encoder',
    'ast.dump', 'ast.parse', 'ast.unparse',
}


@dataclass
class DependencyInfo:
    """Dependency analysis result"""
    standard_lib: list[str]     # standard library dependencies
    third_party: list[str]      # third-party dependencies
    local: list[str]            # local dependencies
    all_modules: list[str]      # all imported modules
    has_circular: bool          # whether circular dependencies exist
    circular_cycles: list[list[str]]  # circular dependency chains
    fan_in: dict[str, int]      # fan-in: how many modules depend on this
    fan_out: dict[str, int]     # fan-out: how many modules this depends on
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
    """Module dependency analyzer"""

    def __init__(self, imports: list, source: str = ""):
        """
        Args:
            imports: StructureAnalysis.imports
            source: source code string (used for local module detection)
        """
        self.imports = imports
        self.source = source

    def analyze(self, source_files: list[str] = None) -> DependencyInfo:
        """
        Execute dependency analysis
        Args:
            source_files: all .py file paths in the project (used for local module detection)
        """
        standard_lib = []
        third_party = []
        local = []
        all_modules = []

        # Collect all imported modules
        for imp in self.imports:
            module = imp.module
            if not module:
                continue

            all_modules.append(module)

            # Classify
            category = self._classify_module(module, source_files)
            if category == 'stdlib':
                standard_lib.append(module)
            elif category == 'third-party':
                third_party.append(module)
            elif category == 'local':
                local.append(module)

        # Deduplicate
        standard_lib = sorted(set(standard_lib))
        third_party = sorted(set(third_party))
        local = sorted(set(local))
        all_modules = sorted(set(all_modules))

        # Circular dependency detection (requires multi-file information)
        has_circular = False
        circular_cycles = []
        if source_files and len(source_files) > 1:
            has_circular, circular_cycles = self._detect_circular(source_files)

        # Fan-in / Fan-out
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

    def _classify_module(self, module: str, source_files: list[str] = None) -> str:
        """Classify module: stdlib / third-party / local"""
        # Get top-level module name
        top_module = module.split('.')[0]

        # Check standard library
        if top_module in STDLIB_MODULES or module in STDLIB_MODULES:
            return 'stdlib'

        # Relative imports are always local
        if module.startswith('.'):
            return 'local'

        # Check local modules (exact match when source_files is available)
        if source_files:
            for sf in source_files:
                sf_path = Path(sf)
                sf_stem = sf_path.stem
                if top_module == sf_stem or top_module == sf_path.name:
                    return 'local'

        # Heuristic: modules starting with src. are usually local project modules
        if top_module == 'src' or top_module.startswith('src_'):
            return 'local'

        # Check if module exists in current directory
        try:
            if Path(f"{top_module}.py").exists() or Path(top_module).is_dir():
                return 'local'
        except (OSError, ValueError):
            pass

        # Remaining are classified as third-party
        return 'third-party'

    def _detect_circular(self, source_files: list[str]) -> tuple[bool, list[list[str]]]:
        """
        Detect circular dependencies (DFS cycle detection)
        Requires scanning import relationships in all source files
        """
        # Build module → dependency mapping
        module_deps: dict[str, set[str]] = {}

        for sf in source_files:
            try:
                for encoding in ('utf-8', 'gbk', 'latin-1'):
                    try:
                        source = Path(sf).read_text(encoding=encoding)
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                else:
                    continue

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

        # DFS to find cycles
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
                    # Cycle found
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
        """Calculate fan-in and fan-out"""
        fan_in: dict[str, int] = {}
        fan_out: dict[str, int] = {}

        for module in all_modules:
            fan_out[module] = fan_out.get(module, 0) + 1
            fan_in[module] = fan_in.get(module, 0) + 1

        return fan_in, fan_out


def analyze_dependencies(imports: list, source_files: list[str] = None) -> DependencyInfo:
    """Convenience function: analyze dependencies"""
    analyzer = DependencyAnalyzer(imports)
    return analyzer.analyze(source_files)
