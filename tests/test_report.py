"""
Tests for report generation module.
"""
import pytest
import ast
from code_analyzer.ast_analyzer import analyze_source
from code_analyzer.call_graph import build_call_graph
from code_analyzer.impact_analyzer import analyze_impact
from code_analyzer.dead_code import detect_dead_code
from code_analyzer.dependency import analyze_dependencies
from code_analyzer.report import generate_report


def generate_report_for_code(code, filename="<test>"):
    """Helper: generate report for code."""
    # Parse and analyze
    tree = ast.parse(code)
    structure = analyze_source(code, filename)
    call_graph = build_call_graph(tree, structure.all_functions)
    impact_analysis = analyze_impact(call_graph)
    dead_code_result = detect_dead_code(call_graph, structure.all_functions)
    dependency_result = analyze_dependencies(structure.imports)
    
    # Generate report
    return generate_report(
        structure,
        call_graph,
        impact_analysis,
        dead_code_result,
        dependency_result
    )


class TestGenerateReport:
    """Tests for generate_report function."""
    
    def test_basic_report_generation(self, sample_python_code):
        """Test basic report generation."""
        report = generate_report_for_code(sample_python_code)
        
        # Report should be a string
        assert isinstance(report, str)
        
        # Report should contain basic sections (English output by default)
        assert 'Deep Analysis Report' in report or 'Report' in report
        assert 'Structure Overview' in report
    
    def test_report_contains_functions(self, sample_python_code):
        """Test that report contains function information."""
        report = generate_report_for_code(sample_python_code)
        
        # Should mention functions (English label)
        assert 'Functions' in report
        assert 'simple_function' in report
        assert 'complex_function' in report
    
    def test_report_contains_classes(self, sample_python_code):
        """Test that report contains class information."""
        report = generate_report_for_code(sample_python_code)
        
        # Should mention classes (English label)
        assert 'Classes' in report
        assert 'SampleClass' in report
    
    def test_report_contains_complexity(self, sample_python_code):
        """Test that report contains complexity information."""
        report = generate_report_for_code(sample_python_code)
        
        # Should mention complexity (English label)
        assert 'Complexity' in report
    
    def test_report_format_markdown(self, sample_python_code):
        """Test that report is in Markdown format."""
        report = generate_report_for_code(sample_python_code)
        
        # Should contain Markdown elements
        assert '#' in report  # Headers
        assert '|' in report  # Tables
    
    def test_empty_code_report(self):
        """Test report for empty code."""
        report = generate_report_for_code('')
        
        # Should still generate a valid report
        assert isinstance(report, str)
        # English report title by default
        assert 'Deep Analysis Report' in report or 'Report' in report
    
    def test_report_with_imports(self):
        """Test report with imports."""
        code = '''
import os
import sys
from pathlib import Path

def main():
    pass
'''
        report = generate_report_for_code(code)
        
        # Should mention imports (English label)
        assert 'Imports' in report
    
    def test_report_quality(self, sample_python_code):
        """Test report quality and completeness."""
        report = generate_report_for_code(sample_python_code)
        
        # Report should have reasonable length
        assert len(report) > 500  # At least 500 characters
        
        # Should have multiple sections
        sections = report.split('##')
        assert len(sections) >= 3  # At least 3 sections
    
    def test_report_12_sections(self, sample_python_code):
        """Test that report has 12 sections."""
        report = generate_report_for_code(sample_python_code)
        
        # Count sections
        sections = report.split('## ')
        # Should have 12 sections (plus header)
        assert len(sections) >= 12
    
    def test_report_with_filename(self):
        """Test report includes filename."""
        code = '''
def test():
    pass
'''
        report = generate_report_for_code(code, filename="test.py")
        
        # Should mention filename
        assert 'test.py' in report
