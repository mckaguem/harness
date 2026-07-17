"""Tests for agent.py — AgentType, filter_tool_schemas, and Agent class."""

import json
import os
from unittest.mock import MagicMock, patch, call
from pathlib import Path

import pytest
from harness_core.model.provider import OpenAIProvider

from harness_core.agent import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.model.types import ProviderConfig
from harness_core.utils import project_root


@pytest.fixture(autouse=True)
def _resolve_placeholder_model_config(monkeypatch):
    """Resolve placeholder model/provider names used by these tests.

    After the refactor ``AgentType.from_file`` requires that the agent's
    ``model_name`` resolves to a model defined in config.yaml. These tests
    historically used placeholder names ("test", "llama3", "mistral") that are
    not present in the real config. This fixture resolves them to a valid
    model/provider config (while still deferring to the real config for names
    that genuinely exist) without reverting the refactor.
    """
    from harness_core.config import (
        get_model_config as _real_get_model_config,
        get_provider_config as _real_get_provider_config,
    )
    from harness_core.model.types import ProviderConfig

    def _fake_get_model_config(name):
        real = _real_get_model_config(name)
        if real is not None:
            return real
        return {
            "name": name,
            "provider_model_name": name,
            "provider": "openai",
            "context_length": 262144,
        }

    def _fake_get_provider_config(name):
        real = _real_get_provider_config(name)
        if real is not None:
            return real
        return ProviderConfig(
            name=name,
            provider_type="openai",
            base_url="http://test.invalid/v1",
            api_key="test",
        )

    monkeypatch.setattr(
        "harness_core.config.get_model_config", _fake_get_model_config
    )
    monkeypatch.setattr(
        "harness_core.config.get_provider_config", _fake_get_provider_config
    )


class TestAgentTypeFromFile:
    """Tests for AgentType.from_file() YAML loading."""

    def test_loads_valid_yaml(self, tmp_path):
        """Should load a valid YAML file correctly with inline system_prompt."""
        from harness_core.agent import AgentType
        
        yaml_content = """
model_name: "llama3"
system_prompt: "You are a helpful assistant."
agent_tools: [execute_bash, write_file]
"""
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            assert agent_type.model_name == "llama3"
            # System prompt should start with base text and include cwd name injection.
            assert agent_type.system_prompt.startswith("You are a helpful assistant.")
            assert "Current working directory name:" in agent_type.system_prompt
            assert tmp_path.name in agent_type.system_prompt  # cwd dir name injected
            assert agent_type.agent_tools == ["execute_bash", "write_file"]
        finally:
            os.chdir(old_cwd)

    def test_uses_inline_system_prompt(self, tmp_path):
        """Should use inline system_prompt from YAML."""
        from harness_core.agent import AgentType
        
        yaml_content = """
model_name: "mistral"
system_prompt: "You are Mistral."
agent_tools: ["*"]
"""
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            assert agent_type.model_name == "mistral"
            # Should be augmented with cwd name.
            assert agent_type.system_prompt.startswith("You are Mistral.")
            assert "Current working directory name:" in agent_type.system_prompt
            assert tmp_path.name in agent_type.system_prompt
            assert agent_type.agent_tools == ["*"]
        finally:
            os.chdir(old_cwd)

    def test_raises_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing YAML."""
        from harness_core.agent import AgentType
        
        with pytest.raises(FileNotFoundError):
            AgentType.from_file(str(tmp_path / "nonexistent.yaml"))

    @patch("harness_core.config.get_default_model", return_value=None)
    def test_raises_value_error_missing_model_name(self, mock_default_model, tmp_path):
        """Should raise ValueError if model_name is missing."""
        from harness_core.agent import AgentType
        
        yaml_content = """
system_prompt: "Test"
agent_tools: []
"""
        (tmp_path / "bad_config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="model_name"):
                AgentType.from_file(str(tmp_path / "bad_config.yaml"))
        finally:
            os.chdir(old_cwd)

    @patch("harness_core.config.get_default_model", return_value="tencent/hy3:free")
    def test_uses_default_model_when_missing(self, mock_default_model, tmp_path):
        """Should fall back to configured default model when YAML has no model_name."""
        from harness_core.agent import AgentType

        yaml_content = """
system_prompt: "Test"
agent_tools: []
"""
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            assert agent_type.model_name == "tencent/hy3:free"
            assert agent_type.provider_model_name == "tencent/hy3:free"
        finally:
            os.chdir(old_cwd)

    def test_raises_value_error_invalid_tools(self, tmp_path):
        """Should raise ValueError if agent_tools is not a list."""
        from harness_core.agent import AgentType
        
        yaml_content = """
model_name: "test"
agent_tools: "not_a_list"
"""
        (tmp_path / "bad_config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="agent_tools"):
                AgentType.from_file(str(tmp_path / "bad_config.yaml"))
        finally:
            os.chdir(old_cwd)

    def test_defaults_agent_tools_to_empty(self, tmp_path):
        """Should default agent_tools to empty list if not specified."""
        from harness_core.agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Test prompt"
"""
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            assert agent_type.agent_tools == []
        finally:
            os.chdir(old_cwd)

    def test_raises_value_error_missing_system_prompt(self, tmp_path):
        """Should raise ValueError if system_prompt is missing from YAML."""
        from harness_core.agent import AgentType
        
        yaml_content = """
model_name: "test"
agent_tools: []
"""
        (tmp_path / "no_prompt.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="missing required 'system_prompt'"):
                AgentType.from_file(str(tmp_path / "no_prompt.yaml"))
        finally:
            os.chdir(old_cwd)

    def test_system_prompt_only_includes_cwd_name(self, tmp_path):
        """Should only inject cwd name — not full listing or AGENTS.md."""
        from harness_core.agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Hello world."
agent_tools: []
"""
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            # Should NOT contain full cwd listing.
            assert "Current working directory contents:" not in agent_type.system_prompt
            # Should NOT contain AGENTS.md.
            assert "--- AGENTS.md ---" not in agent_type.system_prompt
            # Should contain the simple cwd name injection.
            assert "Current working directory name:" in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_name_defaults_to_stem(self, tmp_path):
        """Should fall back to YAML filename stem if 'name' is not specified."""
        from harness_core.agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Test"
agent_tools: []
"""
        (tmp_path / "my_agent.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "my_agent.yaml"))
            assert agent_type.name == "my_agent"
        finally:
            os.chdir(old_cwd)

    def test_builds_system_prompt_with_cwd_variable(self, tmp_path):
        """Should substitute $CWD with the absolute cwd path."""
        from harness_core.agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "You are in $CWD. Be helpful."\n'
            'agent_tools: []\n'
        )
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            # $CWD is replaced with the absolute path.
            assert str(tmp_path.resolve()) in agent_type.system_prompt
            # No legacy cwd-name footer because template variables were used.
            assert "Current working directory name:" not in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_builds_system_prompt_with_skills_variable(self, tmp_path):
        """Should substitute $SKILLS with one-line-per-skill catalog."""
        from harness_core.agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Available skills:\n${SKILLS}"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            # With no skills discovered, $SKILLS is replaced with an empty string.
            assert "Available skills:" in agent_type.system_prompt
            assert "Current working directory name:" not in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_builds_system_prompt_with_agents_variable(self, tmp_path):
        """Should substitute $AGENTS with one-line-per-agent catalog."""
        from harness_core.agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Sub-agents:\n${AGENTS}"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            # $AGENTS is replaced; if no agents discovered, the section is empty.
            assert "Sub-agents:" in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_builds_system_prompt_with_tools_variable(self, tmp_path):
        """Should substitute $TOOLS with one-line-per-tool catalog."""
        from harness_core.agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Tools:\n${TOOLS}"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            # $TOOLS is replaced with the list of available tools.
            assert "Tools:" in agent_type.system_prompt
            # At least one tool description should appear (e.g., execute_bash).
            assert "execute_bash" in agent_type.system_prompt or "Tool " in agent_type.system_prompt.lower()
        finally:
            os.chdir(old_cwd)

    def test_unknown_variable_left_intact(self, tmp_path):
        """Should leave unknown $UNLIKELY_NAME placeholders untouched."""
        from harness_core.agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Hello $UNKNOWN_PLACEHOLDER_42 world"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            # Unknown placeholders are preserved literally so typos surface visibly.
            assert "$UNKNOWN_PLACEHOLDER_42" in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_no_legacy_footer_when_template_used(self, tmp_path):
        """When template variables are present, the legacy cwd-name footer is not appended."""
        from harness_core.agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Working in $CWD with $TOOLS"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "harness_core.config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "harness_core.config.yaml"))
            assert "Current working directory name:" not in agent_type.system_prompt
            # But $CWD must have been substituted with the resolved path.
            assert str(tmp_path.resolve()) in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)


class TestFilterToolSchemas:
    """Tests for filter_tool_schemas() function."""

    def test_wildcard_returns_all(self):
        """Should return all schemas when agent_tools contains '*']."""
        from harness_core.agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["*"]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        schemas = [
            {"function": {"name": "tool1"}},
            {"function": {"name": "tool2"}},
        ]
        
        result = filter_tool_schemas(agent_type, schemas)
        assert len(result) == 2

    def test_filters_by_name_list(self):
        """Should filter schemas to only include requested names."""
        from harness_core.agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        schemas = [
            {"function": {"name": "execute_bash"}},
            {"function": {"name": "write_file"}},
            {"function": {"name": "grep"}},
        ]
        
        result = filter_tool_schemas(agent_type, schemas)
        assert len(result) == 1
        assert result[0]["function"]["name"] == "execute_bash"

    def test_raises_value_error_for_missing_tools(self):
        """Should raise ValueError if requested tools don't exist."""
        from harness_core.agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["nonexistent_tool"]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        schemas = [
            {"function": {"name": "execute_bash"}},
        ]
        
        with pytest.raises(ValueError, match="nonexistent_tool"):
            filter_tool_schemas(agent_type, schemas)

    def test_empty_agent_tools_returns_empty(self):
        """Should return empty list when agent_tools is empty."""
        from harness_core.agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        schemas = [
            {"function": {"name": "tool1"}},
        ]
        
        result = filter_tool_schemas(agent_type, schemas)
        assert len(result) == 0

    def test_preserves_order_of_requested_names(self):
        """Should preserve the order of names as requested."""
        from harness_core.agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["tool_b", "tool_a"]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        schemas = [
            {"function": {"name": "tool_a"}},
            {"function": {"name": "tool_b"}},
        ]
        
        result = filter_tool_schemas(agent_type, schemas)
        assert result[0]["function"]["name"] == "tool_b"
        assert result[1]["function"]["name"] == "tool_a"


class TestAgentInit:
    """Tests for Agent.__init__() method."""

    def test_initializes_with_system_message(self):
        """Should initialize messages list with system message."""
        from harness_core.agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="You are helpful.",
            agent_tools=[]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        mock_client = MagicMock()
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=mock_client):
            agent = Agent(agent_type, id="test-agent")
        
        assert len(agent._session.messages) == 1
        assert agent._session.messages[0]["role"] == "system"
        assert agent._session.messages[0]["content"] == "You are helpful."

    def test_filters_tool_schemas(self):
        """Should filter tool schemas based on AgentType."""
        from harness_core.agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        mock_client = MagicMock()
        all_schemas = [
            {"function": {"name": "execute_bash"}},
            {"function": {"name": "write_file"}},
        ]
        
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=mock_client):
            agent = Agent(agent_type, id="test-agent", tool_schemas=all_schemas)
        
        assert len(agent._tools) == 1
        assert agent._tools[0]["function"]["name"] == "execute_bash"

    def test_empty_tools_when_none_provided(self):
        """Should set empty tools list when tool_schemas is None."""
        from harness_core.agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["*"]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        mock_client = MagicMock()
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=mock_client):
            agent = Agent(agent_type, id="test-agent")
        
        assert agent._tools == []

    def test_stores_context_length(self):
        """Should store context length for use in handle_prompt."""
        from harness_core.agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        
        mock_client = MagicMock()
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=mock_client):
            agent = Agent(agent_type, id="test-agent")
        
        # Context length is now derived from the agent type, not stored on the
        # agent instance. Verify the agent resolves it through the public API.
        assert agent.context_length == agent_type.context_length

class TestAgentHandlePrompt:
    """Tests for Agent.handle_prompt() method.

    Production calls ``provider.chat_completion(...)`` (normalized dict), NOT a
    raw OpenAI client. These tests mock the ``Provider`` interface via
    ``MagicMock(spec=OpenAIProvider)`` and return normalized completion dicts
    shaped like ``OpenAIProvider._normalize_response``.
    """

    def _make_provider(self, responses):
        """Build a provider mock that passes isinstance(provider, Provider) and
        returns/cycles *responses* (normalized chat-completion dicts)."""
        provider = MagicMock(spec=OpenAIProvider)
        provider.get_base_url.return_value = "http://test"
        if len(responses) == 1:
            provider.chat_completion.return_value = responses[0]
        else:
            provider.chat_completion.side_effect = responses
        return provider

    @staticmethod
    def _response(content, tool_calls=None):
        """Build a normalized chat-completion dict for the agent's provider API."""
        message = {"role": "assistant", "content": content}
        if tool_calls is not None:
            message["tool_calls"] = tool_calls
        return {
            "choices": [{"message": message}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    @staticmethod
    def _tool_call(name, arguments, call_id="call_1"):
        """Build a single normalized tool_call dict."""
        return {
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)},
        }

    def test_yields_response_on_simple_chat(self):
        """Should yield RESPONSE tuple when no tool calls are needed."""
        from harness_core.agent import Agent, AgentType, RESPONSE

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=[])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([self._response("Hello!")])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        outputs = list(agent.handle_prompt("Hi"))

        assert len(outputs) == 1
        kind, content, response, _resp_data = outputs[0]
        assert kind == RESPONSE
        assert content == "Hello!"

    def test_yields_tool_call_and_result(self):
        """Should yield TOOL_CALL and TOOL_RESULT for function calls."""
        from harness_core.agent import Agent, AgentType, TOOL_CALL, TOOL_RESULT

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=["execute_bash"])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([
            self._response(None, tool_calls=[self._tool_call("execute_bash", {"command": "ls"})]),
            self._response("Done!"),
        ])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        outputs = list(agent.handle_prompt("List files"))

        assert len(outputs) == 3
        kind, func_name, args_str, _response_data = outputs[0]
        assert kind == TOOL_CALL
        assert func_name == "execute_bash"
        assert "ls" in args_str
        kind, func_name, result, _response_data = outputs[1]
        assert kind == TOOL_RESULT
        assert func_name == "execute_bash"
        from harness_core.tools.tool_result import ToolResult
        assert isinstance(result, ToolResult)
        kind, content, response, _resp_data = outputs[2]
        assert content == "Done!"

    def test_yields_error_on_unknown_tool(self):
        """Should yield ERROR when dispatch raises KeyError (unknown tool)."""
        from harness_core.agent import Agent, AgentType, ERROR, TOOL_CALL

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=[])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([
            self._response(None, tool_calls=[self._tool_call("unknown_tool", {})]),
            self._response("Sorry"),
        ])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        outputs = list(agent.handle_prompt("Do something"))

        assert len(outputs) >= 2
        assert outputs[0][0] == TOOL_CALL
        error_item = next(o for o in outputs if o[0] == ERROR)
        description = error_item[1]
        assert "unknown_tool" in str(description).lower()

    def test_appends_user_message_to_history(self):
        """Should append user message to conversation history."""
        from harness_core.agent import Agent, AgentType

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=[])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([self._response("Hi")])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        list(agent.handle_prompt("Hello"))

        assert len(agent._session.messages) == 3
        assert agent._session.messages[1]["role"] == "user"
        assert "Hello" in agent._session.messages[1]["content"]

    def test_appends_assistant_message_to_history(self):
        """Should append assistant message to conversation history."""
        from harness_core.agent import Agent, AgentType

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=[])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([self._response("Response")])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        list(agent.handle_prompt("Hi"))

        assert len(agent._session.messages) == 3
        assert agent._session.messages[2]["role"] == "assistant"
        assert agent._session.messages[2]["content"] == "Response"

    def test_appends_tool_result_to_history(self):
        """Should append tool result to conversation history."""
        from harness_core.agent import Agent, AgentType

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=["execute_bash"])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([
            self._response(None, tool_calls=[self._tool_call("execute_bash", {"command": "echo test"})]),
            self._response("Done"),
        ])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        list(agent.handle_prompt("Run command"))

        assert len(agent._session.messages) == 5
        assert agent._session.messages[3]["role"] == "tool"
        assert agent._session.messages[3]["name"] == "execute_bash"

    def test_handles_multiple_tool_calls(self):
        """Should handle multiple tool calls in one response."""
        from harness_core.agent import Agent, AgentType, TOOL_CALL, TOOL_RESULT

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=["execute_bash"])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([
            self._response(None, tool_calls=[
                self._tool_call("execute_bash", {"command": "ls"}),
                self._tool_call("execute_bash", {"command": "pwd"}),
            ]),
            self._response("Done!"),
        ])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        outputs = list(agent.handle_prompt("Run commands"))

        assert len(outputs) == 5
        assert outputs[0][0] == TOOL_CALL
        assert outputs[1][0] == TOOL_RESULT
        assert outputs[2][0] == TOOL_CALL
        assert outputs[3][0] == TOOL_RESULT
        assert outputs[4][0] == RESPONSE

    def test_handles_tool_call_with_unexpected_args(self):
        """Should yield ERROR when dispatch fails with unexpected args."""
        from harness_core.agent import Agent, AgentType, ERROR

        agent_type = AgentType(model_name="test", system_prompt="Test", agent_tools=["execute_bash"])
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        provider = self._make_provider([
            self._response(None, tool_calls=[self._tool_call("execute_bash", {"wrong_key": "value"})]),
            self._response("Done"),
        ])
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="test-agent")

        outputs = list(agent.handle_prompt("Test"))
        assert any(o[0] == ERROR for o in outputs)

