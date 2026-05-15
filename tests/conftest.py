"""
Pytest configuration and shared fixtures for python-code-analyst tests.
"""
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
def simple_function():
    """A simple function."""
    return 42

def complex_function(x, y):
    """A complex function with multiple branches."""
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x < 0:
        if y > 0:
            return -x + y
        else:
            return -x - y
    else:
        return 0

class SampleClass:
    """A sample class."""
    
    def __init__(self, value):
        self.value = value
    
    def method_a(self):
        """Method A calls method B."""
        return self.method_b() + 1
    
    def method_b(self):
        """Method B is called by method A."""
        return self.value * 2
    
    def unused_method(self):
        """This method is never called."""
        return "unused"
'''


@pytest.fixture
def sample_file(tmp_path, sample_python_code):
    """Create a temporary Python file for testing."""
    file_path = tmp_path / "sample.py"
    file_path.write_text(sample_python_code)
    return file_path


@pytest.fixture
def sample_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    # Create main module
    main_py = src_dir / "main.py"
    main_py.write_text('''
from utils import helper_function

def main():
    result = helper_function(10)
    print(result)

if __name__ == "__main__":
    main()
''')
    
    # Create utils module
    utils_py = src_dir / "utils.py"
    utils_py.write_text('''
def helper_function(x):
    """Helper function."""
    return x * 2

def unused_function():
    """This function is never imported."""
    return "unused"
''')
    
    return tmp_path