"""Tests for harness_core.model.provider (OpenAI Responses API refactor)."""

from unittest.mock import MagicMock, Mock

import harness_core.model as model_module
from harness_core.model.provider import OpenAIProvider, create_provider


def _make_message_item(text="Hello!"):
    item = Mock()
    item.type = "message"
    item.content = [Mock(text=text)]
    return item


def _make_function_call_item(call_id="call_1", name="execute_bash", arguments='{"cmd":"ls"}'):
    item = Mock()
    item.type = "function_call"
    item.call_id = call_id
    item.name = name
    item.arguments = arguments
    return item


def _make_reasoning_item(summary=None, content=None, item_id="r1"):
    item = Mock()
    item.type = "reasoning"
    item.id = item_id
    item.summary = [Mock(text=t) for t in (summary or [])]
    item.content = [Mock(text=t) for t in (content or [])]
    return item


def _make_usage(input_tokens=10, output_tokens=5, total_tokens=15):
    usage = Mock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    usage.total_tokens = total_tokens
    return usage


class TestProviderNormalization:
    """Tests for OpenAIProvider.chat_completion output normalization."""

    def test_simple_text_response_normalization(self):
        client = MagicMock()
        provider = OpenAIProvider(client)

        response = Mock()
        response.output = [_make_message_item("Hello!")]
        response.usage = _make_usage(10, 5, 15)
        client.responses.create.return_value = response

        result = provider.chat_completion(messages=[{"role": "user", "content": "Hi"}], model="gpt-x")

        assert result["choices"][0]["message"]["role"] == "assistant"
        assert result["choices"][0]["message"]["content"] == "Hello!"
        assert "tool_calls" not in result["choices"][0]["message"]
        assert result["usage"] == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    def test_function_call_output_normalization(self):
        client = MagicMock()
        provider = OpenAIProvider(client)

        response = Mock()
        response.output = [
            _make_message_item("Sure"),
            _make_function_call_item("call_1", "execute_bash", '{"cmd":"ls"}'),
        ]
        response.usage = _make_usage(20, 8, 28)
        client.responses.create.return_value = response

        result = provider.chat_completion(messages=[{"role": "user", "content": "Run ls"}], model="gpt-x")

        message = result["choices"][0]["message"]
        assert message["content"] == "Sure"
        assert message["tool_calls"] == [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "execute_bash", "arguments": '{"cmd":"ls"}'},
            }
        ]
        assert result["usage"] == {"prompt_tokens": 20, "completion_tokens": 8, "total_tokens": 28}

    def test_error_wrapping(self):
        client = MagicMock()
        provider = OpenAIProvider(client)
        client.responses.create.side_effect = RuntimeError("boom")

        raised = None
        try:
            provider.chat_completion(messages=[{"role": "user", "content": "Hi"}], model="gpt-x")
        except RuntimeError as exc:
            raised = exc

        assert raised is not None
        assert str(raised).startswith("Provider chat request failed:")

    def test_reasoning_item_extracted_into_message(self):
        client = MagicMock()
        provider = OpenAIProvider(client)

        response = Mock()
        response.output = [
            _make_reasoning_item(summary=["Let me think. ", "The answer is 42."]),
            _make_message_item("The answer is 42."),
        ]
        response.usage = _make_usage(10, 5, 15)
        client.responses.create.return_value = response

        result = provider.chat_completion(messages=[{"role": "user", "content": "Hi"}], model="gpt-x")

        message = result["choices"][0]["message"]
        assert message["content"] == "The answer is 42."
        assert message["reasoning"] == "Let me think. The answer is 42."
        assert result["usage"] == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    def test_reasoning_item_falls_back_to_content(self):
        client = MagicMock()
        provider = OpenAIProvider(client)

        response = Mock()
        response.output = [
            _make_reasoning_item(summary=[], content=["inner thought"]),
            _make_message_item("done"),
        ]
        response.usage = _make_usage(1, 1, 2)
        client.responses.create.return_value = response

        result = provider.chat_completion(messages=[{"role": "user", "content": "Hi"}], model="gpt-x")
        message = result["choices"][0]["message"]
        assert message["reasoning"] == "inner thought"
        assert message["content"] == "done"

    def test_no_reasoning_yields_none(self):
        client = MagicMock()
        provider = OpenAIProvider(client)

        response = Mock()
        response.output = [_make_message_item("plain")]
        response.usage = _make_usage(1, 1, 2)
        client.responses.create.return_value = response

        result = provider.chat_completion(messages=[{"role": "user", "content": "Hi"}], model="gpt-x")
        message = result["choices"][0]["message"]
        assert message.get("reasoning") is None
        assert message["content"] == "plain"


class TestProviderFactory:
    """Tests for the provider factory helpers."""

    def test_factory_returns_openai_provider(self):
        assert isinstance(create_provider(MagicMock()), OpenAIProvider)
        assert isinstance(create_provider(MagicMock()), OpenAIProvider)

    def test_ollama_provider_not_importable(self):
        import_error = None
        try:
            from harness_core.model import OllamaProvider  # noqa: F401
        except (ImportError, AttributeError) as exc:
            import_error = exc
        assert import_error is not None
        assert hasattr(model_module, "OllamaProvider") is False
