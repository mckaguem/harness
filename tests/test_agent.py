"""Tests for agent.py — AgentType, filter_tool_schemas, and Agent class."""

import json
import os
from unittest.mock import MagicMock, patch, call
from pathlib import Path

import pytest

from agent import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from utils import project_root


class TestAgentTypeFromFile:
    """Tests for AgentType.from_file() YAML loading."""

    def test_loads_valid_yaml(self, tmp_path):
        """Should load a valid YAML file correctly with inline system_prompt."""
        from agent import AgentType
        
        yaml_content = """
model_name: "llama3"
system_prompt: "You are a helpful assistant."
agent_tools: [execute_bash, write_file]
"""
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
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
        from agent import AgentType
        
        yaml_content = """
model_name: "mistral"
system_prompt: "You are Mistral."
agent_tools: ["*"]
"""
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
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
        from agent import AgentType
        
        with pytest.raises(FileNotFoundError):
            AgentType.from_file(str(tmp_path / "nonexistent.yaml"))

    @patch("config.get_default_model", return_value=None)
    def test_raises_value_error_missing_model_name(self, mock_default_model, tmp_path):
        """Should raise ValueError if model_name is missing."""
        from agent import AgentType
        
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

    @patch("config.get_default_model", return_value="fallback-model")
    def test_uses_default_model_when_missing(self, mock_default_model, tmp_path):
        """Should fall back to configured default model when YAML has no model_name."""
        from agent import AgentType

        yaml_content = """
system_prompt: "Test"
agent_tools: []
"""
        (tmp_path / "config.yaml").write_text(yaml_content)

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            assert agent_type.model_name == "fallback-model"
        finally:
            os.chdir(old_cwd)

    def test_raises_value_error_invalid_tools(self, tmp_path):
        """Should raise ValueError if agent_tools is not a list."""
        from agent import AgentType
        
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
        from agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Test prompt"
"""
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            assert agent_type.agent_tools == []
        finally:
            os.chdir(old_cwd)

    def test_raises_value_error_missing_system_prompt(self, tmp_path):
        """Should raise ValueError if system_prompt is missing from YAML."""
        from agent import AgentType
        
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
        from agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Hello world."
agent_tools: []
"""
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
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
        from agent import AgentType
        
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
        from agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "You are in $CWD. Be helpful."\n'
            'agent_tools: []\n'
        )
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            # $CWD is replaced with the absolute path.
            assert str(tmp_path.resolve()) in agent_type.system_prompt
            # No legacy cwd-name footer because template variables were used.
            assert "Current working directory name:" not in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_builds_system_prompt_with_skills_variable(self, tmp_path):
        """Should substitute $SKILLS with one-line-per-skill catalog."""
        from agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Available skills:\n${SKILLS}"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            # With no skills discovered, $SKILLS is replaced with an empty string.
            assert "Available skills:" in agent_type.system_prompt
            assert "Current working directory name:" not in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_builds_system_prompt_with_agents_variable(self, tmp_path):
        """Should substitute $AGENTS with one-line-per-agent catalog."""
        from agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Sub-agents:\n${AGENTS}"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            # $AGENTS is replaced; if no agents discovered, the section is empty.
            assert "Sub-agents:" in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_builds_system_prompt_with_tools_variable(self, tmp_path):
        """Should substitute $TOOLS with one-line-per-tool catalog."""
        from agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Tools:\n${TOOLS}"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            # $TOOLS is replaced with the list of available tools.
            assert "Tools:" in agent_type.system_prompt
            # At least one tool description should appear (e.g., execute_bash).
            assert "execute_bash" in agent_type.system_prompt or "Tool " in agent_type.system_prompt.lower()
        finally:
            os.chdir(old_cwd)

    def test_unknown_variable_left_intact(self, tmp_path):
        """Should leave unknown $UNLIKELY_NAME placeholders untouched."""
        from agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Hello $UNKNOWN_PLACEHOLDER_42 world"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            # Unknown placeholders are preserved literally so typos surface visibly.
            assert "$UNKNOWN_PLACEHOLDER_42" in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)

    def test_no_legacy_footer_when_template_used(self, tmp_path):
        """When template variables are present, the legacy cwd-name footer is not appended."""
        from agent import AgentType
        
        yaml_content = (
            'model_name: "test"\n'
            'system_prompt: "Working in $CWD with $TOOLS"\n'
            'agent_tools: []\n'
        )
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            assert "Current working directory name:" not in agent_type.system_prompt
            # But $CWD must have been substituted with the resolved path.
            assert str(tmp_path.resolve()) in agent_type.system_prompt
        finally:
            os.chdir(old_cwd)


class TestFilterToolSchemas:
    """Tests for filter_tool_schemas() function."""

    def test_wildcard_returns_all(self):
        """Should return all schemas when agent_tools contains '*']."""
        from agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["*"]
        )
        
        schemas = [
            {"function": {"name": "tool1"}},
            {"function": {"name": "tool2"}},
        ]
        
        result = filter_tool_schemas(agent_type, schemas)
        assert len(result) == 2

    def test_filters_by_name_list(self):
        """Should filter schemas to only include requested names."""
        from agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
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
        from agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["nonexistent_tool"]
        )
        
        schemas = [
            {"function": {"name": "execute_bash"}},
        ]
        
        with pytest.raises(ValueError, match="nonexistent_tool"):
            filter_tool_schemas(agent_type, schemas)

    def test_empty_agent_tools_returns_empty(self):
        """Should return empty list when agent_tools is empty."""
        from agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        schemas = [
            {"function": {"name": "tool1"}},
        ]
        
        result = filter_tool_schemas(agent_type, schemas)
        assert len(result) == 0

    def test_preserves_order_of_requested_names(self):
        """Should preserve the order of names as requested."""
        from agent import AgentType, filter_tool_schemas
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["tool_b", "tool_a"]
        )
        
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
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="You are helpful.",
            agent_tools=[]
        )
        
        mock_client = MagicMock()
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        assert len(agent._session.messages) == 1
        assert agent._session.messages[0]["role"] == "system"
        assert agent._session.messages[0]["content"] == "You are helpful."

    def test_filters_tool_schemas(self):
        """Should filter tool schemas based on AgentType."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()
        all_schemas = [
            {"function": {"name": "execute_bash"}},
            {"function": {"name": "write_file"}},
        ]
        
        agent = Agent(agent_type, 4096, provider=mock_client, tool_schemas=all_schemas)
        
        assert len(agent._tools) == 1
        assert agent._tools[0]["function"]["name"] == "execute_bash"

    def test_empty_tools_when_none_provided(self):
        """Should set empty tools list when tool_schemas is None."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["*"]
        )
        
        mock_client = MagicMock()
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        assert agent._tools == []

    def test_stores_context_length(self):
        """Should store context length for use in handle_prompt."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        mock_client = MagicMock()
        agent = Agent(agent_type, 8192, provider=mock_client)
        
        assert agent._context_length == 8192


class TestAgentHandlePrompt:
    """Tests for Agent.handle_prompt() method."""

    def _create_mock_client(self):
        """Create a mock client that passes isinstance check for OpenAI."""
        from openai import OpenAI
        return MagicMock(spec=OpenAI)

    def test_yields_response_on_simple_chat(self):
        """Should yield RESPONSE tuple when no tool calls are needed."""
        from agent import Agent, AgentType, RESPONSE
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        # Create mock that has chat.completions.create (duck typing)
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock(content="Hello!", role="assistant")
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_completion.model = "test"
        mock_client.chat.completions.create.return_value = mock_completion
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        outputs = list(agent.handle_prompt("Hi"))
        
        assert len(outputs) == 1
        kind, content, response = outputs[0]
        assert kind == RESPONSE
        assert content == "Hello!"

    def test_yields_tool_call_and_result(self):
        """Should yield TOOL_CALL and TOOL_RESULT for function calls."""
        from agent import Agent, AgentType, TOOL_CALL, TOOL_RESULT
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()

        def make_tool_call(name="execute_bash", arguments=None):
            tc = MagicMock()
            tc.id = "call_1"
            tc.type = "function"
            tc.function.name = name
            tc.function.arguments = json.dumps(arguments or {})
            return tc

        def make_mock_completion(content, tool_calls_list=None, model="test"):
            c = MagicMock()
            ch = MagicMock()
            m = MagicMock(content=content, role="assistant", tool_calls=tool_calls_list)
            ch.message = m
            c.choices = [ch]
            c.model = model
            return c
        
        mock_client.chat.completions.create.side_effect = [
            make_mock_completion(None, tool_calls_list=[
                make_tool_call("execute_bash", {"command": "ls"})
            ]),
            make_mock_completion("Done!"),
        ]
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        outputs = list(agent.handle_prompt("List files"))
        
        assert len(outputs) == 3
        
        # First: TOOL_CALL (now 4-tuple with response_data)
        kind, func_name, args_str, _response_data = outputs[0]
        assert kind == TOOL_CALL
        assert func_name == "execute_bash"
        assert "ls" in args_str
        
        # Second: TOOL_RESULT (now 4-tuple with response_data)
        kind, func_name, result, _response_data = outputs[1]
        assert kind == TOOL_RESULT
        assert func_name == "execute_bash"
        from tools.tool_result import ToolResult
        assert isinstance(result, ToolResult)
        
        # Third: RESPONSE
        kind, content, response = outputs[2]
        assert kind == RESPONSE
        assert content == "Done!"

    def test_yields_error_on_unknown_tool(self):
        """Should yield ERROR when dispatch raises KeyError."""
        from agent import Agent, AgentType, ERROR
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]  # No tools available
        )
        
        mock_client = MagicMock()

        def make_tool_call(name="unknown_tool", arguments=None):
            tc = MagicMock()
            tc.id = "call_1"
            tc.type = "function"
            tc.function.name = name
            tc.function.arguments = json.dumps(arguments or {})
            return tc

        def make_mock_completion(content, tool_calls_list=None, model="test"):
            c = MagicMock()
            ch = MagicMock()
            m = MagicMock(content=content, role="assistant", tool_calls=tool_calls_list)
            ch.message = m
            c.choices = [ch]
            c.model = model
            return c
        
        mock_client.chat.completions.create.side_effect = [
            make_mock_completion(None, tool_calls_list=[
                make_tool_call("unknown_tool", {})
            ]),
            make_mock_completion("Sorry"),
        ]
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        outputs = list(agent.handle_prompt("Do something"))
        
        # Should have TOOL_CALL, ERROR, TOOL_RESULT, then RESPONSE
        assert len(outputs) == 4
        kind, description = outputs[1][0], outputs[1][1]
        assert kind == ERROR
        assert "unknown_tool" in str(description).lower()

    def test_appends_user_message_to_history(self):
        """Should append user message to conversation history."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock(content="Hi", role="assistant", tool_calls=None)
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_completion.model = "test"
        mock_client.chat.completions.create.return_value = mock_completion
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        list(agent.handle_prompt("Hello"))
        
        # system + user + assistant
        assert len(agent._session.messages) == 3
        assert agent._session.messages[1]["role"] == "user"
        # User content may be wrapped with system state; just verify it's present.
        assert "Hello" in agent._session.messages[1]["content"]

    def test_appends_assistant_message_to_history(self):
        """Should append assistant message to conversation history."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock(content="Response", role="assistant", tool_calls=None)
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_completion.model = "test"
        mock_client.chat.completions.create.return_value = mock_completion
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        list(agent.handle_prompt("Hi"))
        
        # system + user + assistant
        assert len(agent._session.messages) == 3
        assert agent._session.messages[2]["role"] == "assistant"
        assert agent._session.messages[2]["content"] == "Response"

    def test_appends_tool_result_to_history(self):
        """Should append tool result to conversation history."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()

        def make_tool_call(name="execute_bash", arguments=None):
            tc = MagicMock()
            tc.id = "call_1"
            tc.type = "function"
            tc.function.name = name
            tc.function.arguments = json.dumps(arguments or {})
            return tc

        def make_mock_completion(content, tool_calls_list=None, model="test"):
            c = MagicMock()
            ch = MagicMock()
            m = MagicMock(content=content, role="assistant", tool_calls=tool_calls_list)
            ch.message = m
            c.choices = [ch]
            c.model = model
            return c
        
        mock_client.chat.completions.create.side_effect = [
            make_mock_completion(None, tool_calls_list=[
                make_tool_call("execute_bash", {"command": "echo test"})
            ]),
            make_mock_completion("Done"),
        ]
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        list(agent.handle_prompt("Run command"))
        
        # system + user + assistant(tool_calls) + tool(result) + assistant(final)
        assert len(agent._session.messages) == 5
        assert agent._session.messages[3]["role"] == "tool"
        assert agent._session.messages[3]["name"] == "execute_bash"

    def test_handles_multiple_tool_calls(self):
        """Should handle multiple tool calls in one response."""
        from agent import Agent, AgentType, TOOL_CALL, TOOL_RESULT
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()

        def make_tool_call(name="execute_bash", arguments=None):
            tc = MagicMock()
            tc.id = "call_1"
            tc.type = "function"
            tc.function.name = name
            tc.function.arguments = json.dumps(arguments or {})
            return tc

        def make_mock_completion(content, tool_calls_list=None, model="test"):
            c = MagicMock()
            ch = MagicMock()
            m = MagicMock(content=content, role="assistant", tool_calls=tool_calls_list)
            ch.message = m
            c.choices = [ch]
            c.model = model
            return c
        
        mock_client.chat.completions.create.side_effect = [
            make_mock_completion(None, tool_calls_list=[
                make_tool_call("execute_bash", {"command": "ls"}),
                make_tool_call("execute_bash", {"command": "pwd"}),
            ]),
            make_mock_completion("Done!"),
        ]
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        outputs = list(agent.handle_prompt("Run commands"))
        
        # Should have: TOOL_CALL, TOOL_RESULT, TOOL_CALL, TOOL_RESULT, RESPONSE
        assert len(outputs) == 5
        
        # First two: first tool call and result
        assert outputs[0][0] == TOOL_CALL
        assert outputs[1][0] == TOOL_RESULT
        
        # Next two: second tool call and result
        assert outputs[2][0] == TOOL_CALL
        assert outputs[3][0] == TOOL_RESULT
        
        # Final response
        assert outputs[4][0] == RESPONSE

    def test_calls_chat_with_correct_params(self):
        """Should call ollama chat with correct model, messages, tools."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="llama3",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock(content="Hi", role="assistant", tool_calls=None)
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_completion.model = "test"
        mock_client.chat.completions.create.return_value = mock_completion
        
        all_schemas = [{"function": {"name": "execute_bash"}}]
        agent = Agent(agent_type, 4096, provider=mock_client, tool_schemas=all_schemas)
        
        list(agent.handle_prompt("Test"))
        
        # Verify chat.completions.create was called with correct parameters
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "llama3"
        assert call_args.kwargs["messages"] is not None
        assert len(call_args.kwargs["messages"]) > 0
        
        # Should pass tools since they exist
        assert call_args.kwargs["tools"] is not None
        assert len(call_args.kwargs["tools"]) == 1

    def test_handles_tool_call_with_unexpected_args(self):
        """Should yield ERROR when dispatch fails with unexpected args."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()

        def make_tool_call(name="execute_bash", arguments=None):
            tc = MagicMock()
            tc.id = "call_1"
            tc.type = "function"
            tc.function.name = name
            tc.function.arguments = json.dumps(arguments or {})
            return tc

        def make_mock_completion(content, tool_calls_list=None, model="test"):
            c = MagicMock()
            ch = MagicMock()
            m = MagicMock(content=content, role="assistant", tool_calls=tool_calls_list)
            ch.message = m
            c.choices = [ch]
            c.model = model
            return c
        
        mock_client.chat.completions.create.side_effect = [
            make_mock_completion(None, tool_calls_list=[
                make_tool_call("execute_bash", {"wrong_key": "value"})
            ]),
            make_mock_completion("Done"),
        ]
        
        agent = Agent(agent_type, 4096, provider=mock_client)
        
        # Should yield TOOL_CALL, ERROR, TOOL_RESULT, RESPONSE without raising
        outputs = list(agent.handle_prompt("Test"))
        assert len(outputs) == 4
        kind_error = outputs[1][0]
        assert kind_error == ERROR
