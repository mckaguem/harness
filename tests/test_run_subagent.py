"""Tests for tools/run_subagent.py - sub-agent termination prompt loading."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLoadTerminationPrompt:
    """Test that _load_termination_prompt loads the correct file."""
    
    def test_loads_from_correct_path(self):
        """Verify it reads from agents/prompts/subagent_termination.txt"""
        # Force fresh import to pick up our fix
        if 'tools.run_subagent' in sys.modules:
            del sys.modules['tools.run_subagent']
        
        from tools.run_subagent import _load_termination_prompt
        
        prompt = _load_termination_prompt()
        
        assert len(prompt) > 100, "Prompt should not be empty"
        assert 'submit_results' in prompt.lower(), "Should mention submit_results tool"
    
    def test_returns_empty_string_when_file_missing(self):
        """Verify graceful fallback when file doesn't exist."""
        with patch('pathlib.Path.is_file', return_value=False):
            if 'tools.run_subagent' in sys.modules:
                del sys.modules['tools.run_subagent']
            
            from tools.run_subagent import _load_termination_prompt
            
            prompt = _load_termination_prompt()
            assert prompt == ""


class TestRunSubagent:
    """Test the run_subagent function."""
    
    def test_function_exists(self):
        """Verify run_subagent is callable."""
        if 'tools.run_subagent' in sys.modules:
            del sys.modules['tools.run_subagent']
        
        from tools.run_subagent import run_subagent
        
        assert callable(run_subagent), "run_subagent should be a function"
    
    def test_submit_results_def_available(self):
        """Verify _get_submit_results_def returns the schema."""
        if 'tools.run_subagent' in sys.modules:
            del sys.modules['tools.run_subagent']
        
        from tools.run_subagent import _get_submit_results_def
        
        submit_schema = _get_submit_results_def()
        
        assert isinstance(submit_schema, dict), "Should return a dict"
        assert 'function' in submit_schema, "Missing 'function' key"
        assert submit_schema['function']['name'] == 'submit_results', \
            "Function name should be 'submit_results'"
