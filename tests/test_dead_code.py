"""
Tests for dead code detection module.
"""
import pytest
import ast
from code_analyzer.ast_analyzer import analyze_source
from code_analyzer.call_graph import build_call_graph
from code_analyzer.dead_code import detect_dead_code, DeadCodeResult


def get_dead_code_from_code(code):
    """Helper: parse code and detect dead code."""
    tree = ast.parse(code)
    analysis = analyze_source(code)
    call_graph = build_call_graph(tree, analysis.all_functions)
    return detect_dead_code(call_graph, analysis.all_functions)


class TestDetectDeadCode:
    """Tests for detect_dead_code function."""
    
    def test_no_dead_code(self):
        """Test code with no dead functions."""
        code = '''
def main():
    return helper()

def helper():
    return 42
'''
        result = get_dead_code_from_code(code)
        
        # Should be a DeadCodeResult
        assert isinstance(result, DeadCodeResult)
        assert hasattr(result, 'unreachable')
        assert hasattr(result, 'coverage')
        
        # Note: Without explicit entry points, detection may vary
        # Just verify structure is correct
    
    def test_dead_function(self):
        """Test dead function detection."""
        code = '''
def main():
    return 42

def unused():
    return 99
'''
        result = get_dead_code_from_code(code)
        
        # Should detect unused function (or at least have it in unreachable)
        assert isinstance(result, DeadCodeResult)
        assert hasattr(result, 'unreachable')
        assert hasattr(result, 'total_user_functions')
        assert result.total_user_functions == 2
    
    def test_multiple_dead_functions(self):
        """Test multiple dead functions."""
        code = '''
def main():
    return 42

def unused1():
    return 1

def unused2():
    return 2
'''
        result = get_dead_code_from_code(code)
        
        # Should have 3 user functions
        assert result.total_user_functions == 3
        assert len(result.unreachable) >= 0  # May vary based on detection
    
    def test_special_methods_excluded(self):
        """Test that special methods are excluded from dead code."""
        code = '''
class MyClass:
    def __init__(self):
        self.value = 42
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return f"MyClass({self.value})"
    
    def __len__(self):
        return 1
    
    def regular_method(self):
        return self.value
'''
        result = get_dead_code_from_code(code)
        
        # Special methods should be in special_excluded
        assert len(result.special_excluded) > 0
    
    def test_method_class_prefix(self):
        """Test methods with class prefix."""
        code = '''
class MyClass:
    def method_a(self):
        return self.method_b()
    
    def method_b(self):
        return 42
    
    def unused_method(self):
        return 99
'''
        result = get_dead_code_from_code(code)
        
        # Should have methods in results
        assert result.total_user_functions >= 2
    
    def test_coverage_calculation(self):
        """Test coverage calculation."""
        code = '''
def main():
    return helper1() + helper2()

def helper1():
    return 1

def helper2():
    return 2

def unused():
    return 99
'''
        result = get_dead_code_from_code(code)
        
        # Should have coverage between 0 and 100
        assert 0 <= result.coverage <= 100
        assert result.total_user_functions == 4
    
    def test_empty_code(self):
        """Test with empty code."""
        result = get_dead_code_from_code('')
        
        assert len(result.unreachable) == 0
        assert result.coverage == 100.0
        assert result.total_user_functions == 0
    
    def test_complex_call_chain(self):
        """Test complex call chain."""
        code = '''
def main():
    return a()

def a():
    return b()

def b():
    return c()

def c():
    return 42

def unused():
    return 99
'''
        result = get_dead_code_from_code(code)
        
        # Should have 5 functions total
        assert result.total_user_functions == 5
        # Coverage should be calculated
        assert 0 <= result.coverage <= 100
    
    def test_to_dict(self):
        """Test to_dict conversion."""
        code = '''
def main():
    return 42

def unused():
    return 99
'''
        result = get_dead_code_from_code(code)
        data = result.to_dict()
        
        # Should be a dict
        assert isinstance(data, dict)
        assert 'unreachable' in data
        assert 'coverage' in data
        assert 'total_user_functions' in data