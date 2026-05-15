"""
Tests for call graph module.
"""
import pytest
from code_analyzer.call_graph import analyze_call_graph


class TestAnalyzeCallGraph:
    """Tests for analyze_call_graph function."""
    
    def test_simple_calls(self):
        """Test simple function calls."""
        code = '''
def a():
    return b()

def b():
    return 42
'''
        result = analyze_call_graph(code)
        
        # Should find call from a to b
        assert 'call_edges' in result
        edges = result['call_edges']
        
        # Check that a calls b
        a_calls = [e['callee'] for e in edges if e['caller'] == 'a']
        assert 'b' in a_calls
    
    def test_no_cycles(self):
        """Test that simple code has no cycles."""
        code = '''
def a():
    return b()

def b():
    return c()

def c():
    return 42
'''
        result = analyze_call_graph(code)
        
        # Should not detect cycles in linear calls
        assert result.get('has_cycles', False) is False
    
    def test_self_call(self):
        """Test self-recursive function."""
        code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
        result = analyze_call_graph(code)
        
        # Should detect self-call
        edges = result['call_edges']
        self_calls = [e for e in edges if e['caller'] == 'factorial' and e['callee'] == 'factorial']
        assert len(self_calls) == 1
    
    def test_method_calls(self):
        """Test method calls within a class."""
        code = '''
class MyClass:
    def method_a(self):
        return self.method_b()
    
    def method_b(self):
        return 42
'''
        result = analyze_call_graph(code)
        
        # Should find method calls
        edges = result['call_edges']
        # Check for method_a -> method_b call
        a_calls = [e['callee'] for e in edges if e['caller'] == 'MyClass.method_a']
        assert 'MyClass.method_b' in a_calls
    
    def test_special_functions_filtered(self):
        """Test that special functions are filtered."""
        code = '''
class MyClass:
    def __init__(self):
        self.value = 42
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return f"MyClass({self.value})"
'''
        result = analyze_call_graph(code)
        
        # Special methods should not appear in call graph
        edges = result['call_edges']
        special_calls = [e for e in edges if '__' in e['caller'] or '__' in e['callee']]
        assert len(special_calls) == 0
    
    def test_two_pass_scanning(self):
        """Test that two-pass scanning handles forward references."""
        code = '''
def a():
    # b is defined after a
    return b()

def b():
    return 42
'''
        result = analyze_call_graph(code)
        
        # Should still detect a -> b call
        edges = result['call_edges']
        a_calls = [e['callee'] for e in edges if e['caller'] == 'a']
        assert 'b' in a_calls