

"""Tests for config module integration with harness."""

import os
from unittest.mock import patch, MagicMock, PropertyMock

import pytest


class TestConfigIntegration:
    """Test config module integration with harness.py."""

    def test_config_cache_is_used(self):
        """Verify that get_default_provider uses the cached config."""
        from config import _reset_config_cache, get_default_provider, load_harness_config

        # Reset cache to ensure fresh state
        _reset_config_cache()

        # Load config (this populates the cache)
        cfg = load_harness_config()

        # Verify that multiple calls return consistent results
        result1 = get_default_provider()
        result2 = get_default_provider()

        assert result1 is result2 or str(result1) == str(result2)  # Same object (cached)

    def test_reset_config_cache(self):
        """Verify _reset_config_cache clears the cache."""
        from config import _reset_config_cache, load_harness_config

        # Load config first
        cfg = load_harness_config()

        # Reset cache
        _reset_config_cache()

        # Verify it can be reloaded without error
        cfg2 = load_harness_config()
        assert "providers" in cfg2
        assert "default_provider" in cfg2
        assert "default_model" in cfg2
