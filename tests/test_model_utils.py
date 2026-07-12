"""Tests for harness_core.model.utils — base URL resolution + token counting."""

import json
from unittest.mock import patch, MagicMock

import pytest

from harness_core.model.utils import get_base_url, tokenize_prompt


class TestBaseUrlResolution:
    """get_base_url prefers the client's base_url and falls back safely."""

    def test_uses_client_base_url(self):
        client = MagicMock()
        client.base_url = "http://localhost:11434/"
        assert get_base_url(client) == "http://localhost:11434" or get_base_url(client) is None

    def test_strips_trailing_slash(self):
        client = MagicMock()
        client.base_url = "https://example.com/ollama/"
        assert get_base_url(client) == "https://example.com/ollama"


class TestTokenizePrompt:
    """tokenize_prompt hits the /api/tokenize endpoint and parses the token list."""

    def test_returns_token_count(self):
        fake_response = MagicMock()
        fake_response.read.return_value = json.dumps({"tokens": [1, 2, 3, 4]}).encode()
        fake_response.__enter__ = lambda self: self
        fake_response.__exit__ = lambda self, *a: False

        client = MagicMock()
        client.base_url = "http://localhost:11434"

        import harness_core.model.utils as utils_mod
        import urllib.request as urlrequest
        with patch.object(urlrequest, "urlopen", return_value=fake_response) as mock_urlopen:
            count = tokenize_prompt(client, [{"role": "user", "content": "hi"}], "m")

        assert count == 4
        # The request was sent to <base_url>/api/tokenize with JSON body.
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "http://localhost:11434/api/tokenize"
        body = json.loads(req.data.decode())
        assert body["prompt"] == "hi"

    def test_returns_none_on_error(self):
        import urllib.error

        err = urllib.error.URLError("boom")
        client = MagicMock()
        client.base_url = "http://localhost:11434"
        import harness_core.model.utils as utils_mod
        import urllib.request as urlrequest
        with patch.object(urlrequest, "urlopen", side_effect=err):
            count = tokenize_prompt(client, [{"role": "user", "content": "hi"}], "m")
        assert count is None
