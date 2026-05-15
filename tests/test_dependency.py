"""
Tests for dependency analysis module.
"""
import pytest
from code_analyzer.dependency import analyze_dependencies


class TestAnalyzeDependencies:
    """Tests for analyze_dependencies function."""
    
    def test_stdlib_dependencies(self):
        """Test standard library detection."""
        code = '''
import os
import sys
import json
from pathlib import Path
from typing import List
'''
        result = analyze_dependencies(code)
        
        # Should identify stdlib modules
        assert 'standard_lib' in result
        stdlib = result['standard_lib']
        
        assert 'os' in stdlib
        assert 'sys' in stdlib
        assert 'json' in stdlib
        assert 'pathlib' in stdlib
        assert 'typing' in stdlib
    
    def test_third_party_dependencies(self):
        """Test third-party detection."""
        code = '''
import requests
import numpy as np
import pandas as pd
from flask import Flask
'''
        result = analyze_dependencies(code)
        
        # Should identify third-party modules
        assert 'third_party' in result
        third_party = result['third_party']
        
        assert 'requests' in third_party
        assert 'numpy' in third_party
        assert 'pandas' in third_party
        assert 'flask' in third_party
    
    def test_local_dependencies(self):
        """Test local module detection."""
        code = '''
from .utils import helper
from .models import User
import src.config
'''
        result = analyze_dependencies(code)
        
        # Should identify local modules
        assert 'local' in result
        local = result['local']
        
        # Check for relative imports
        local_modules = [dep['module'] for dep in local]
        assert any('utils' in m for m in local_modules)
        assert any('models' in m for m in local_modules)
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        code = '''
# This would be in file a.py
from b import some_function

def a_function():
    return some_function()
'''
        # Note: This test is limited since we're analyzing single file
        # In real usage, circular dependencies are detected across files
        result = analyze_dependencies(code)
        
        # For single file, just check structure
        assert 'has_circular' in result
    
    def test_dependency_counts(self):
        """Test dependency counting."""
        code = '''
import os
import sys
import requests
from . import utils
'''
        result = analyze_dependencies(code)
        
        # Check counts
        assert 'counts' in result
        counts = result['counts']
        
        assert counts['stdlib'] == 2  # os, sys
        assert counts['third_party'] == 1  # requests
        assert counts['local'] == 1  # utils
    
    def test_empty_code(self):
        """Test with empty code."""
        result = analyze_dependencies('')
        
        assert result['standard_lib'] == []
        assert result['third_party'] == []
        assert result['local'] == []
        assert result['has_circular'] is False
    
    def test_import_from(self):
        """Test from...import statements."""
        code = '''
from os import path
from sys import argv
from collections import defaultdict
'''
        result = analyze_dependencies(code)
        
        # Should handle from...import correctly
        stdlib = result['standard_lib']
        module_names = [dep['module'] for dep in stdlib]
        
        assert 'os' in module_names
        assert 'sys' in module_names
        assert 'collections' in module_names