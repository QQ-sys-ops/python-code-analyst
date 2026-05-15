"""
Tests for AST analyzer module.
"""
import pytest
from code_analyzer.ast_analyzer import analyze_structure, calculate_cyclomatic_complexity


class TestAnalyzeStructure:
    """Tests for analyze_structure function."""
    
    def test_basic_structure(self, sample_python_code):
        """Test basic structure extraction."""
        result = analyze_structure(sample_python_code)
        
        # Check basic fields exist
        assert 'imports' in result
        assert 'classes' in result
        assert 'functions' in result
        assert 'line_count' in result
        assert 'complexity' in result
    
    def test_function_extraction(self, sample_python_code):
        """Test function extraction."""
        result = analyze_structure(sample_python_code)
        
        # Should find 2 functions
        assert len(result['functions']) == 2
        
        # Check function names
        function_names = [f['name'] for f in result['functions']]
        assert 'simple_function' in function_names
        assert 'complex_function' in function_names
    
    def test_class_extraction(self, sample_python_code):
        """Test class extraction."""
        result = analyze_structure(sample_python_code)
        
        # Should find 1 class
        assert len(result['classes']) == 1
        assert result['classes'][0]['name'] == 'SampleClass'
        
        # Should find 4 methods
        assert len(result['classes'][0]['methods']) == 4
    
    def test_import_extraction(self):
        """Test import extraction."""
        code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict
'''
        result = analyze_structure(code)
        
        # Should find 4 imports
        assert len(result['imports']) == 4
    
    def test_empty_code(self):
        """Test with empty code."""
        result = analyze_structure('')
        
        assert result['imports'] == []
        assert result['classes'] == []
        assert result['functions'] == []
        assert result['line_count'] == 0


class TestCyclomaticComplexity:
    """Tests for cyclomatic complexity calculation."""
    
    def test_simple_function(self):
        """Test simple function complexity."""
        code = '''
def simple():
    return 42
'''
        result = analyze_structure(code)
        func = result['functions'][0]
        
        # Simple function should have complexity 1
        assert func['complexity'] == 1
    
    def test_if_statement(self):
        """Test if statement complexity."""
        code = '''
def with_if(x):
    if x > 0:
        return 1
    return 0
'''
        result = analyze_structure(code)
        func = result['functions'][0]
        
        # Should have complexity 2 (base 1 + if)
        assert func['complexity'] == 2
    
    def test_multiple_branches(self, sample_python_code):
        """Test multiple branches complexity."""
        result = analyze_structure(sample_python_code)
        func = next(f for f in result['functions'] if f['name'] == 'complex_function')
        
        # complex_function has multiple if/elif/else branches
        assert func['complexity'] > 3
    
    def test_for_loop(self):
        """Test for loop complexity."""
        code = '''
def with_loop(items):
    result = 0
    for item in items:
        result += item
    return result
'''
        result = analyze_structure(code)
        func = result['functions'][0]
        
        # Should have complexity 2 (base 1 + for)
        assert func['complexity'] == 2
    
    def test_while_loop(self):
        """Test while loop complexity."""
        code = '''
def with_while(n):
    result = 0
    while n > 0:
        result += n
        n -= 1
    return result
'''
        result = analyze_structure(code)
        func = result['functions'][0]
        
        # Should have complexity 2 (base 1 + while)
        assert func['complexity'] == 2
    
    def test_try_except(self):
        """Test try/except complexity."""
        code = '''
def with_try():
    try:
        return 1
    except ValueError:
        return 2
    except TypeError:
        return 3
'''
        result = analyze_structure(code)
        func = result['functions'][0]
        
        # Should have complexity 3 (base 1 + 2 except)
        assert func['complexity'] == 3