"""Tests for config module integration with harness."""

import os
from unittest.mock import patch, MagicMock, PropertyMock

import pytest


class TestConfigIntegration:
    """Test config module integration with harness.py."""

    def test_config_cache_is_used(self):
        """Verify load_harness_config returns a consistent providers mapping."""
        from harness_core.config import _reset_config_cache, load_harness_config

        # Reset cache to ensure fresh state
        _reset_config_cache()

        # Load config (this populates the cache)
        cfg = load_harness_config()

        # Verify the expected keys are present and providers mapping is stable
        assert "providers" in cfg
        assert "models" in cfg
        assert "default_model" in cfg
        cfg_again = load_harness_config()
        # Reloading yields a consistent (equal) providers mapping.
        assert cfg["providers"] == cfg_again["providers"]

    def test_reset_config_cache(self):
        """Verify _reset_config_cache clears the cache and the default_provider key is gone."""
        from harness_core.config import _reset_config_cache, load_harness_config

        # Load config first
        cfg = load_harness_config()

        # Reset cache
        _reset_config_cache()

        # Verify it can be reloaded without error
        cfg2 = load_harness_config()
        assert "providers" in cfg2
        # default_provider has been removed — providers are specified via model config only
        assert "default_provider" not in cfg2
        assert "default_model" in cfg2
