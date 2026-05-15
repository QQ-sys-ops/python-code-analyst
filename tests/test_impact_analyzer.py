"""
Tests for impact analyzer module.
"""
import pytest
from code_analyzer.impact_analyzer import analyze_impact


class TestAnalyzeImpact:
    """Tests for analyze_impact function."""
    
    def test_direct_impact(self):
        """Test direct impact analysis."""
        code = '''
def a():
    return b()

def b():
    return c()

def c():
    return 42
'''
        result = analyze_impact(code, 'b')
        
        # b is called by a
        assert 'direct_impact' in result
        assert 'a' in result['direct_impact']
    
    def test_indirect_impact(self):
        """Test indirect impact analysis."""
        code = '''
def a():
    return b()

def b():
    return c()

def c():
    return 42
'''
        result = analyze_impact(code, 'c')
        
        # c is called by b, which is called by a
        assert 'indirect_impact' in result
        assert 'b' in result['indirect_impact']
        
        # a should be in total impact (direct or indirect)
        total_impact = result.get('total_impact', [])
        assert 'a' in total_impact
    
    def test_no_impact(self):
        """Test function with no impact."""
        code = '''
def a():
    return 42

def b():
    return 43
'''
        result = analyze_impact(code, 'a')
        
        # a is not called by anyone
        assert result['direct_impact'] == []
        assert result['indirect_impact'] == []
    
    def test_class_method_impact(self):
        """Test class method impact."""
        code = '''
class MyClass:
    def method_a(self):
        return self.method_b()
    
    def method_b(self):
        return self.method_c()
    
    def method_c(self):
        return 42
'''
        result = analyze_impact(code, 'MyClass.method_c')
        
        # method_c is called by method_b
        assert 'MyClass.method_b' in result['direct_impact']
    
    def test_recursive_impact(self):
        """Test recursive function impact."""
        code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def wrapper():
    return factorial(5)
'''
        result = analyze_impact(code, 'factorial')
        
        # factorial is called by wrapper
        assert 'wrapper' in result['direct_impact']
    
    def test_multiple_callers(self):
        """Test function with multiple callers."""
        code = '''
def a():
    return common()

def b():
    return common()

def c():
    return common()

def common():
    return 42
'''
        result = analyze_impact(code, 'common')
        
        # common is called by a, b, and c
        direct = set(result['direct_impact'])
        assert 'a' in direct
        assert 'b' in direct
        assert 'c' in direct
    
    def test_impact_chain(self):
        """Test impact chain calculation."""
        code = '''
def a():
    return b()

def b():
    return c()

def c():
    return d()

def d():
    return 42
'''
        result = analyze_impact(code, 'd')
        
        # d -> c -> b -> a
        assert 'c' in result['direct_impact']
        assert 'b' in result['indirect_impact']
        
        # Total impact should include all affected functions
        total = result.get('total_impact', [])
        assert 'c' in total
        assert 'b' in total
        assert 'a' in total