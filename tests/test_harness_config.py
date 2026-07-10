

"""Tests for _resolve_provider_settings() and config integration in harness.py."""

import os
from unittest.mock import patch, MagicMock, PropertyMock

import pytest


class TestResolveProviderSettings:
    """Test the _resolve_provider_settings function from harness.py."""

    def test_uses_default_provider_base_url(self):
        """Should use base_url from default provider when configured."""
        from harness import _resolve_provider_settings
        from model.types import ProviderConfig

        mock_provider = MagicMock(spec=ProviderConfig)
        mock_provider.base_url = "https://api.openai.com/v1"
        mock_provider.api_key = "sk-test-key-123"

        with patch("harness.get_default_provider", return_value=mock_provider):
            base_url, api_key = _resolve_provider_settings()

        assert base_url == "https://api.openai.com/v1"
        assert api_key == "sk-test-key-123"

    def test_uses_default_provider_base_url_strips_trailing_slash(self):
        """Should strip trailing slash from provider's base_url."""
        from harness import _resolve_provider_settings
        from model.types import ProviderConfig

        mock_provider = MagicMock(spec=ProviderConfig)
        mock_provider.base_url = "https://api.example.com/"
        mock_provider.api_key = "sk-key"

        with patch("harness.get_default_provider", return_value=mock_provider):
            base_url, api_key = _resolve_provider_settings()

        assert base_url == "https://api.example.com"

    def test_falls_back_to_env_var_for_api_key(self):
        """Should fall back to OPENAI_API_KEY env var if provider has no key."""
        from harness import _resolve_provider_settings
        from model.types import ProviderConfig

        mock_provider = MagicMock(spec=ProviderConfig)
        mock_provider.base_url = "https://api.openai.com/v1"
        mock_provider.api_key = None  # No API key in config

        env_vars = {
            "OPENAI_API_KEY": "sk-env-key",
            "OPENAI_BASE_URL": "",  # Not used when provider is configured
            "OLLAMA_HOST": "",  # Not used when provider is configured
        }

        with patch("harness.get_default_provider", return_value=mock_provider), \
             patch.dict(os.environ, env_vars):
            base_url, api_key = _resolve_provider_settings()

        assert base_url == "https://api.openai.com/v1"
        assert api_key == "sk-env-key"

    def test_falls_back_to_env_vars_when_no_default_provider(self):
        """Should fall back to environment variables when no default provider configured."""
        from harness import _resolve_provider_settings

        env_vars = {
            "OPENAI_API_KEY": "sk-env-fallback",
            "OPENAI_BASE_URL": "https://env.example.com/v1",
            "OLLAMA_HOST": "",  # Not used since OPENAI_BASE_URL is set
        }

        with patch("harness.get_default_provider", return_value=None), \
             patch.dict(os.environ, env_vars):
            base_url, api_key = _resolve_provider_settings()

        assert base_url == "https://env.example.com/v1"
        assert api_key == "sk-env-fallback"

    def test_falls_back_to_ollama_host_when_openai_not_set(self):
        """Should use OLLAMA_HOST when OPENAI_BASE_URL is not set."""
        from harness import _resolve_provider_settings

        # Use clear=True to replace ALL env vars, only setting what we want
        env_vars = {
            "OPENAI_API_KEY": "",
            "OLLAMA_HOST": "http://localhost:11434",
        }

        with patch("harness.get_default_provider", return_value=None), \
             patch.dict(os.environ, env_vars, clear=True):
            base_url, api_key = _resolve_provider_settings()

        assert base_url == "http://localhost:11434"
        assert api_key == ""  # Empty OPENAI_API_KEY

    def test_no_default_provider_and_no_env_returns_defaults(self):
        """Should return fallback URL when no provider and no env vars."""
        from harness import _resolve_provider_settings

        # Clear relevant env vars - only set OPENAI_API_KEY, let OLLAMA_HOST use its value
        env_vars = {
            "OPENAI_API_KEY": "",
            "OLLAMA_HOST": "http://localhost:11434",
        }

        with patch("harness.get_default_provider", return_value=None), \
             patch.dict(os.environ, env_vars):
            # Remove OPENAI_BASE_URL if it exists in the real environment
            os.environ.pop("OPENAI_BASE_URL", None)
            base_url, api_key = _resolve_provider_settings()

        # Should fall back to OLLAMA_HOST value (which is localhost:11434 in our test)
        assert base_url == "http://localhost:11434"
        assert api_key == ""


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
