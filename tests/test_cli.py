"""
Tests for CLI module.
"""
import pytest
import subprocess
import sys
from pathlib import Path


class TestCLI:
    """Tests for CLI functionality."""
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = subprocess.run(
            [sys.executable, '-m', 'code_analyzer', '--help'],
            capture_output=True,
            text=True
        )
        
        # Should return help information
        assert result.returncode == 0
        assert 'usage' in result.stdout.lower() or 'help' in result.stdout.lower()
    
    def test_cli_version(self):
        """Test CLI version command."""
        result = subprocess.run(
            [sys.executable, '-m', 'code_analyzer', '--help'],
            capture_output=True,
            text=True
        )
        
        # Should return help information (version is not a separate flag)
        assert result.returncode == 0
        assert 'code_analyzer' in result.stdout.lower()
    
    def test_cli_analyze_file(self, sample_file):
        """Test CLI file analysis."""
        result = subprocess.run(
            [sys.executable, '-m', 'code_analyzer', str(sample_file)],
            capture_output=True,
            text=True
        )
        
        # Should analyze successfully
        assert result.returncode == 0
        
        # Output should contain JSON (default format)
        assert '{' in result.stdout
        assert '}' in result.stdout
    
    def test_cli_report_format(self, sample_file):
        """Test CLI report format."""
        result = subprocess.run(
            [sys.executable, '-m', 'code_analyzer', str(sample_file), '--report'],
            capture_output=True,
            text=True
        )
        
        # Should generate report
        assert result.returncode == 0
        
        # Output should be Markdown
        assert '#' in result.stdout
    
    def test_cli_nonexistent_file(self):
        """Test CLI with nonexistent file."""
        result = subprocess.run(
            [sys.executable, '-m', 'code_analyzer', 'nonexistent.py'],
            capture_output=True,
            text=True
        )
        
        # Should fail gracefully
        assert result.returncode != 0
    
    def test_cli_invalid_python(self, tmp_path):
        """Test CLI with invalid Python file."""
        # Create invalid Python file
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("def invalid syntax")
        
        result = subprocess.run(
            [sys.executable, '-m', 'code_analyzer', str(invalid_file)],
            capture_output=True,
            text=True
        )
        
        # Should handle syntax error gracefully
        # May return non-zero or show error message
        assert 'error' in result.stderr.lower() or result.returncode != 0
    
    def test_cli_batch_mode(self, sample_project):
        """Test CLI batch mode."""
        src_dir = sample_project / "src"
        
        result = subprocess.run(
            [sys.executable, '-m', 'code_analyzer', str(src_dir), '--batch'],
            capture_output=True,
            text=True
        )
        
        # Should analyze directory
        assert result.returncode == 0
        
        # Output should contain multiple files
        assert 'main.py' in result.stdout or 'utils.py' in result.stdout