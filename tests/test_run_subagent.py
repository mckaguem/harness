"""Tests for tools/run_subagent.py - sub-agent termination prompt loading."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLoadTerminationPrompt:
    """Test that TERMINATION_PROMPT is properly defined."""
    
    def test_termination_prompt_exists_and_is_non_empty(self):
        """Verify TERMINATION_PROMPT constant exists and has content."""
        # Force fresh import to pick up our fix
        if 'harness_core.tools.run_subagent' in sys.modules:
            del sys.modules['harness_core.tools.run_subagent']
        
        from harness_core.tools.run_subagent import TERMINATION_PROMPT
        
        assert len(TERMINATION_PROMPT) > 100, "Prompt should not be empty"
        assert 'submit_results' in TERMINATION_PROMPT.lower(), "Should mention submit_results tool"
    
    def test_termination_prompt_mentions_protocol(self):
        """Verify the termination prompt includes protocol instructions."""
        if 'harness_core.tools.run_subagent' in sys.modules:
            del sys.modules['harness_core.tools.run_subagent']
        
        from harness_core.tools.run_subagent import TERMINATION_PROMPT
        
        assert 'TERMINATION PROTOCOL' in TERMINATION_PROMPT or 'Termination Protocol' in TERMINATION_PROMPT


class TestRunSubagent:
    """Test the run_subagent function."""
    
    def test_function_exists(self):
        """Verify run_subagent is callable."""
        if 'harness_core.tools.run_subagent' in sys.modules:
            del sys.modules['harness_core.tools.run_subagent']
        
        from harness_core.tools.run_subagent import run_subagent
        
        assert callable(run_subagent), "run_subagent should be a function"
    
    def test_submit_results_def_available(self):
        """Verify _get_submit_results_def returns the schema."""
        if 'harness_core.tools.run_subagent' in sys.modules:
            del sys.modules['harness_core.tools.run_subagent']
        
        from harness_core.tools.run_subagent import _get_submit_results_def
        
        submit_schema = _get_submit_results_def()
        
        assert isinstance(submit_schema, dict), "Should return a dict"
        assert 'function' in submit_schema, "Missing 'function' key"
        assert submit_schema['function']['name'] == 'submit_results', \
            "Function name should be 'submit_results'"
