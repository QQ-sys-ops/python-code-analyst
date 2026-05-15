"""
Tests for AST analyzer module.
"""
import pytest
from code_analyzer.ast_analyzer import analyze_source, analyze_file


class TestAnalyzeSource:
    """Tests for analyze_source function."""
    
    def test_basic_structure(self, sample_python_code):
        """Test basic structure extraction."""
        result = analyze_source(sample_python_code)
        
        # Check basic fields exist (StructureAnalysis dataclass)
        assert hasattr(result, 'imports')
        assert hasattr(result, 'classes')
        assert hasattr(result, 'functions')
        assert hasattr(result, 'total_lines')
        assert hasattr(result, 'avg_complexity')
    
    def test_function_extraction(self, sample_python_code):
        """Test function extraction."""
        result = analyze_source(sample_python_code)
        
        # Should find 2 module-level functions
        assert len(result.functions) == 2
        
        # Check function names
        function_names = [f.name for f in result.functions]
        assert 'simple_function' in function_names
        assert 'complex_function' in function_names
    
    def test_class_extraction(self, sample_python_code):
        """Test class extraction."""
        result = analyze_source(sample_python_code)
        
        # Should find 1 class
        assert len(result.classes) == 1
        assert result.classes[0].name == 'SampleClass'
        
        # Should find 4 methods
        assert result.classes[0].method_count == 4
    
    def test_import_extraction(self):
        """Test import extraction."""
        code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict
'''
        result = analyze_source(code)
        
        # Should find 4 imports
        assert len(result.imports) == 4
    
    def test_empty_code(self):
        """Test with empty code."""
        result = analyze_source('')
        
        assert len(result.imports) == 0
        assert len(result.classes) == 0
        assert len(result.functions) == 0
        assert result.total_lines == 0
    
    def test_to_dict(self, sample_python_code):
        """Test to_dict conversion."""
        result = analyze_source(sample_python_code)
        data = result.to_dict()
        
        # Should be a dict
        assert isinstance(data, dict)
        assert 'functions' in data
        assert 'classes' in data
        assert 'imports' in data


class TestCyclomaticComplexity:
    """Tests for cyclomatic complexity calculation."""
    
    def test_simple_function(self):
        """Test simple function complexity."""
        code = '''
def simple():
    return 42
'''
        result = analyze_source(code)
        func = result.functions[0]
        
        # Simple function should have complexity 1
        assert func.cyclomatic_complexity == 1
    
    def test_if_statement(self):
        """Test if statement complexity."""
        code = '''
def with_if(x):
    if x > 0:
        return 1
    return 0
'''
        result = analyze_source(code)
        func = result.functions[0]
        
        # Should have complexity 2 (base 1 + if)
        assert func.cyclomatic_complexity == 2
    
    def test_multiple_branches(self, sample_python_code):
        """Test multiple branches complexity."""
        result = analyze_source(sample_python_code)
        func = next(f for f in result.functions if f.name == 'complex_function')
        
        # complex_function has multiple if/elif/else branches
        assert func.cyclomatic_complexity > 3
    
    def test_for_loop(self):
        """Test for loop complexity."""
        code = '''
def with_loop(items):
    result = 0
    for item in items:
        result += item
    return result
'''
        result = analyze_source(code)
        func = result.functions[0]
        
        # Should have complexity 2 (base 1 + for)
        assert func.cyclomatic_complexity == 2
    
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
        result = analyze_source(code)
        func = result.functions[0]
        
        # Should have complexity 2 (base 1 + while)
        assert func.cyclomatic_complexity == 2
    
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
        result = analyze_source(code)
        func = result.functions[0]
        
        # Should have complexity 3 (base 1 + 2 except)
        assert func.cyclomatic_complexity == 3


class TestAnalyzeFile:
    """Tests for analyze_file function."""
    
    def test_analyze_file(self, sample_file):
        """Test file analysis."""
        result = analyze_file(str(sample_file))
        
        assert hasattr(result, 'functions')
        assert hasattr(result, 'classes')
        assert len(result.functions) == 2