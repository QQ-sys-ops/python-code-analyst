# Architecture

## Overview

python-code-analyst is a Python code analysis toolkit designed for AI agents. It provides static analysis capabilities through a layered architecture.

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│              Agent Layer (Probabilistic)             │
│  • Code intent explanation (LLM required)           │
│  • Design flaw identification                       │
│  • Natural language summaries                        │
├─────────────────────────────────────────────────────┤
│              Library Layer (Deterministic)           │
│  • AST structure extraction                          │
│  • Cyclomatic/cognitive complexity                   │
│  • Call graph construction                           │
│  • Impact analysis (transitive closure)              │
│  • Dead code detection                               │
│  • Dependency classification                         │
│  • 12-section report generation                      │
├─────────────────────────────────────────────────────┤
│              Accessor Layer (AST Traversal)          │
│  • FunctionVisitor                                   │
│  • ClassVisitor                                      │
│  • ImportVisitor                                     │
│  • Single parse, multiple module reuse               │
└─────────────────────────────────────────────────────┘
```

## Module Structure

```
code_analyzer/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── ast_analyzer.py      # AST structure extraction + complexity
├── call_graph.py        # Two-pass call graph construction
├── dependency.py        # Module dependency classification
├── impact_analyzer.py   # Transitive closure impact analysis
├── dead_code.py         # Entry-point traversal dead code detection
└── report.py            # 12-section Markdown report generation
```

## Core Algorithms

### 1. Two-Pass Call Graph Construction

**Problem**: Function A calls Function B, but B is defined after A. Single-pass scanning misses this edge.

**Solution**: Two-pass approach:
1. **Pass 1 (FunctionCollector)**: Collect all user-defined function names
2. **Pass 2 (CallGraphVisitor)**: Extract call relationships using complete function list

### 2. Transitive Closure Impact Analysis

**Logic**: If A calls B, modifying B affects A. Transitive closure: if A→B→C, modifying C affects both B and A.

**Implementation**: BFS from target function through reverse adjacency list.

### 3. Entry-Point Dead Code Detection

**Algorithm**:
1. Start from entry points (functions with no callers, or explicitly specified)
2. BFS through call graph to mark reachable functions
3. Dead code = User-defined functions - Reachable functions - Special methods

### 4. Dependency Classification

**Rules**:
- **stdlib**: Module name in STANDARD_LIB_MODULES set
- **third-party**: Not in stdlib, not a local module
- **local**: Starts with `.` (relative import) or matches project structure

## Data Flow

```
Input Code (string/file)
    ↓
AST Parsing (ast.parse)
    ↓
┌─────────────────────────────────────────┐
│ Structure Analysis (ast_analyzer.py)    │
│ • Extract imports, classes, functions   │
│ • Calculate complexity                  │
│ • Build function metadata               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Call Graph (call_graph.py)              │
│ • Two-pass scanning                     │
│ • Build edge list                       │
│ • Calculate depth                       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Parallel Analysis                       │
│ • Impact Analysis (impact_analyzer.py)  │
│ • Dead Code Detection (dead_code.py)    │
│ • Dependency Analysis (dependency.py)   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Report Generation (report.py)           │
│ • 12-section Markdown report            │
│ • JSON export                           │
└─────────────────────────────────────────┘
```

## Design Decisions

### 1. Why Two-Pass Scanning?

- **Single-pass**: Misses forward references (function A calls B defined later)
- **Two-pass**: Complete function list before edge extraction
- **Trade-off**: Slightly more memory, but 100% accuracy

### 2. Why Transitive Closure for Impact?

- **Direct only**: Misses cascading effects
- **Transitive**: Complete impact picture
- **Use case**: "If I modify function C, what else breaks?"

### 3. Why Entry-Point Based Dead Code?

- **Export-based**: Misses internal dead code
- **Entry-point**: More accurate for library code
- **Public API**: Auto-exclude non-underscore module functions

## Performance Characteristics

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| AST Parsing | O(n) | O(n) |
| Call Graph | O(V + E) | O(V + E) |
| Impact Analysis | O(V × (V + E)) | O(V) |
| Dead Code | O(V + E) | O(V) |
| Report Generation | O(n) | O(n) |

Where: n = source lines, V = functions, E = call edges

## Extension Points

### 1. Adding New Analysis

```python
# 1. Create analyzer module
code_analyzer/my_analyzer.py

# 2. Define result dataclass
@dataclass
class MyResult:
    ...

# 3. Implement analysis function
def analyze_my_feature(structure, call_graph) -> MyResult:
    ...

# 4. Add to report generation
# In report.py, add _section_N() function

# 5. Export in __init__.py
```

### 2. Custom Report Sections

```python
# In report.py
def _section_custom(structure, my_result) -> str:
    return f"""
## N. Custom Section

| Metric | Value |
|--------|-------|
| ... | ... |
"""
```

## Known Limitations

1. **Dynamic Code**: Cannot analyze `eval()`, `exec()`, dynamic imports
2. **Method Calls**: `self.method()` calls may not be fully detected
3. **Relative Imports**: Single-file analysis may miss `from .utils import ...`
4. **Cross-File**: Dead code detection is per-file, not project-wide

## Future Extensions

- [ ] Cross-project dependency analysis
- [ ] Plugin system for custom analyzers
- [ ] Incremental analysis for large codebases
- [ ] Integration with language servers (LSP)