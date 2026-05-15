"""
Tests for dead code detection module.
"""
import pytest
from code_analyzer.dead_code import analyze_dead_code


class TestAnalyzeDeadCode:
    """Tests for analyze_dead_code function."""
    
    def test_no_dead_code(self):
        """Test code with no dead functions."""
        code = '''
def main():
    return helper()

def helper():
    return 42

if __name__ == "__main__":
    main()
'''
        result = analyze_dead_code(code, ['main'])
        
        # All functions are reachable
        assert result['unreachable'] == []
        assert result['coverage'] == 100.0
    
    def test_dead_function(self):
        """Test dead function detection."""
        code = '''
def main():
    return 42

def unused():
    return 99

if __name__ == "__main__":
    main()
'''
        result = analyze_dead_code(code, ['main'])
        
        # unused function is dead
        assert 'unused' in result['unreachable']
        assert result['coverage'] < 100.0
    
    def test_multiple_dead_functions(self):
        """Test multiple dead functions."""
        code = '''
def main():
    return 42

def unused1():
    return 1

def unused2():
    return 2

if __name__ == "__main__":
    main()
'''
        result = analyze_dead_code(code, ['main'])
        
        # Both unused functions are dead
        assert 'unused1' in result['unreachable']
        assert 'unused2' in result['unreachable']
        assert len(result['unreachable']) == 2
    
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
        result = analyze_dead_code(code, [])
        
        # Special methods should not be in unreachable
        unreachable = result['unreachable']
        special_methods = [f for f in unreachable if '__' in f]
        assert len(special_methods) == 0
    
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
        result = analyze_dead_code(code, [])
        
        # Check that methods are detected
        # Note: Without entry points, all non-special methods may be unreachable
        unreachable = result['unreachable']
        
        # Unused method should be unreachable
        assert any('unused_method' in f for f in unreachable)
    
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

if __name__ == "__main__":
    main()
'''
        result = analyze_dead_code(code, ['main'])
        
        # 4 functions total, 1 unreachable
        # Coverage should be 75%
        assert result['coverage'] == 75.0
    
    def test_empty_code(self):
        """Test with empty code."""
        result = analyze_dead_code('', [])
        
        assert result['unreachable'] == []
        assert result['coverage'] == 100.0
    
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

if __name__ == "__main__":
    main()
'''
        result = analyze_dead_code(code, ['main'])
        
        # Only unused is dead
        assert 'unused' in result['unreachable']
        assert len(result['unreachable']) == 1
        
        # Coverage: 5 functions, 1 unreachable = 80%
        assert result['coverage'] == 80.0