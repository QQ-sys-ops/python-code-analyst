"""
Basic import test to ensure package structure is correct.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_import_code_analyzer():
    """Test that code_analyzer can be imported."""
    try:
        import code_analyzer
        assert True
    except ImportError as e:
        assert False, f"Failed to import code_analyzer: {e}"


def test_import_ast_analyzer():
    """Test that ast_analyzer can be imported."""
    try:
        from code_analyzer import ast_analyzer
        assert True
    except ImportError as e:
        assert False, f"Failed to import ast_analyzer: {e}"


def test_import_call_graph():
    """Test that call_graph can be imported."""
    try:
        from code_analyzer import call_graph
        assert True
    except ImportError as e:
        assert False, f"Failed to import call_graph: {e}"


def test_import_dependency():
    """Test that dependency can be imported."""
    try:
        from code_analyzer import dependency
        assert True
    except ImportError as e:
        assert False, f"Failed to import dependency: {e}"


def test_import_impact_analyzer():
    """Test that impact_analyzer can be imported."""
    try:
        from code_analyzer import impact_analyzer
        assert True
    except ImportError as e:
        assert False, f"Failed to import impact_analyzer: {e}"


def test_import_dead_code():
    """Test that dead_code can be imported."""
    try:
        from code_analyzer import dead_code
        assert True
    except ImportError as e:
        assert False, f"Failed to import dead_code: {e}"


def test_import_report():
    """Test that report can be imported."""
    try:
        from code_analyzer import report
        assert True
    except ImportError as e:
        assert False, f"Failed to import report: {e}"


if __name__ == "__main__":
    # Run tests manually
    tests = [
        test_import_code_analyzer,
        test_import_ast_analyzer,
        test_import_call_graph,
        test_import_dependency,
        test_import_impact_analyzer,
        test_import_dead_code,
        test_import_report,
    ]
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")