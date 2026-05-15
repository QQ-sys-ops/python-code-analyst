"""
Tests for report generation module.
"""
import pytest
from code_analyzer.report import generate_report


class TestGenerateReport:
    """Tests for generate_report function."""
    
    def test_basic_report_generation(self, sample_python_code):
        """Test basic report generation."""
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure(sample_python_code)
        report = generate_report(structure)
        
        # Report should be a string
        assert isinstance(report, str)
        
        # Report should contain basic sections
        assert '代码分析报告' in report
        assert '基本信息' in report
        assert '结构概览' in report
    
    def test_report_contains_functions(self, sample_python_code):
        """Test that report contains function information."""
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure(sample_python_code)
        report = generate_report(structure)
        
        # Should mention functions
        assert '函数' in report
        assert 'simple_function' in report
        assert 'complex_function' in report
    
    def test_report_contains_classes(self, sample_python_code):
        """Test that report contains class information."""
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure(sample_python_code)
        report = generate_report(structure)
        
        # Should mention classes
        assert '类' in report
        assert 'SampleClass' in report
    
    def test_report_contains_complexity(self, sample_python_code):
        """Test that report contains complexity information."""
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure(sample_python_code)
        report = generate_report(structure)
        
        # Should mention complexity
        assert '复杂度' in report
    
    def test_report_format_markdown(self, sample_python_code):
        """Test that report is in Markdown format."""
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure(sample_python_code)
        report = generate_report(structure)
        
        # Should contain Markdown elements
        assert '#' in report  # Headers
        assert '|' in report  # Tables
    
    def test_empty_code_report(self):
        """Test report for empty code."""
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure('')
        report = generate_report(structure)
        
        # Should still generate a valid report
        assert isinstance(report, str)
        assert '代码分析报告' in report
    
    def test_report_with_imports(self):
        """Test report with imports."""
        code = '''
import os
import sys
from pathlib import Path

def main():
    pass
'''
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure(code)
        report = generate_report(structure)
        
        # Should mention imports
        assert '导入' in report
    
    def test_report_quality(self, sample_python_code):
        """Test report quality and completeness."""
        from code_analyzer.ast_analyzer import analyze_structure
        
        structure = analyze_structure(sample_python_code)
        report = generate_report(structure)
        
        # Report should have reasonable length
        assert len(report) > 500  # At least 500 characters
        
        # Should have multiple sections
        sections = report.split('##')
        assert len(sections) >= 3  # At least 3 sections