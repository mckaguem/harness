"""Tests for agent.py — AgentType, filter_tool_schemas, and Agent class."""

import os
from unittest.mock import MagicMock, patch, call
from pathlib import Path

import pytest


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
            os.chdir("/workspaces/harness")

    def test_uses_inline_system_prompt(self, tmp_path):
        """Should use inline system_prompt from YAML."""
        from agent import AgentType
        
        yaml_content = """
model_name: "mistral"
system_prompt: "You are Mistral."
agent_tools: ["*"]
"""
        (tmp_path / "config.yaml").write_text(yaml_content)
        
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
            os.chdir("/workspaces/harness")

    def test_raises_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing YAML."""
        from agent import AgentType
        
        with pytest.raises(FileNotFoundError):
            AgentType.from_file(str(tmp_path / "nonexistent.yaml"))

    def test_raises_value_error_missing_model_name(self, tmp_path):
        """Should raise ValueError if model_name is missing."""
        from agent import AgentType
        
        yaml_content = """
system_prompt: "Test"
agent_tools: []
"""
        (tmp_path / "bad_config.yaml").write_text(yaml_content)
        
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="model_name"):
                AgentType.from_file(str(tmp_path / "bad_config.yaml"))
        finally:
            os.chdir("/workspaces/harness")

    def test_raises_value_error_invalid_tools(self, tmp_path):
        """Should raise ValueError if agent_tools is not a list."""
        from agent import AgentType
        
        yaml_content = """
model_name: "test"
agent_tools: "not_a_list"
"""
        (tmp_path / "bad_config.yaml").write_text(yaml_content)
        
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="agent_tools"):
                AgentType.from_file(str(tmp_path / "bad_config.yaml"))
        finally:
            os.chdir("/workspaces/harness")

    def test_defaults_agent_tools_to_empty(self, tmp_path):
        """Should default agent_tools to empty list if not specified."""
        from agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Test prompt"
"""
        (tmp_path / "config.yaml").write_text(yaml_content)
        
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "config.yaml"))
            assert agent_type.agent_tools == []
        finally:
            os.chdir("/workspaces/harness")

    def test_raises_value_error_missing_system_prompt(self, tmp_path):
        """Should raise ValueError if system_prompt is missing from YAML."""
        from agent import AgentType
        
        yaml_content = """
model_name: "test"
agent_tools: []
"""
        (tmp_path / "no_prompt.yaml").write_text(yaml_content)
        
        os.chdir(tmp_path)
        try:
            with pytest.raises(ValueError, match="missing required 'system_prompt'"):
                AgentType.from_file(str(tmp_path / "no_prompt.yaml"))
        finally:
            os.chdir("/workspaces/harness")

    def test_system_prompt_only_includes_cwd_name(self, tmp_path):
        """Should only inject cwd name — not full listing or AGENTS.md."""
        from agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Hello world."
agent_tools: []
"""
        (tmp_path / "config.yaml").write_text(yaml_content)
        
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
            os.chdir("/workspaces/harness")

    def test_name_defaults_to_stem(self, tmp_path):
        """Should fall back to YAML filename stem if 'name' is not specified."""
        from agent import AgentType
        
        yaml_content = """
model_name: "test"
system_prompt: "Test"
agent_tools: []
"""
        (tmp_path / "my_agent.yaml").write_text(yaml_content)
        
        os.chdir(tmp_path)
        try:
            agent_type = AgentType.from_file(str(tmp_path / "my_agent.yaml"))
            assert agent_type.name == "my_agent"
        finally:
            os.chdir("/workspaces/harness")


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
        agent = Agent(agent_type, mock_client, 4096)
        
        assert len(agent.messages) == 1
        assert agent.messages[0]["role"] == "system"
        assert agent.messages[0]["content"] == "You are helpful."

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
        
        agent = Agent(agent_type, mock_client, 4096, tool_schemas=all_schemas)
        
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
        agent = Agent(agent_type, mock_client, 4096)
        
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
        agent = Agent(agent_type, mock_client, 8192)
        
        assert agent._context_length == 8192


class TestAgentHandlePrompt:
    """Tests for Agent.handle_prompt() method."""

    def test_yields_response_on_simple_chat(self):
        """Should yield RESPONSE tuple when no tool calls are needed."""
        from agent import Agent, AgentType, RESPONSE
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        mock_client = MagicMock()
        mock_response = {
            "message": {"role": "assistant", "content": "Hello!", "tool_calls": None},
            "eval_count": 10,
        }
        mock_client.chat.return_value = mock_response
        
        agent = Agent(agent_type, mock_client, 4096)
        
        outputs = list(agent.handle_prompt("Hi"))
        
        assert len(outputs) == 1
        kind, content, response = outputs[0]
        assert kind == RESPONSE
        assert content == "Hello!"
        assert response is mock_response

    def test_yields_tool_call_and_result(self):
        """Should yield TOOL_CALL and TOOL_RESULT for function calls."""
        from agent import Agent, AgentType, TOOL_CALL, TOOL_RESULT
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()
        mock_response1 = {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "function": {
                        "name": "execute_bash",
                        "arguments": {"command": "ls"}
                    }
                }]
            },
        }
        mock_response2 = {
            "message": {"role": "assistant", "content": "Done!", "tool_calls": None},
        }
        mock_client.chat.side_effect = [mock_response1, mock_response2]
        
        agent = Agent(agent_type, mock_client, 4096)
        
        outputs = list(agent.handle_prompt("List files"))
        
        assert len(outputs) == 3
        
        # First: TOOL_CALL
        kind, func_name, args_str = outputs[0]
        assert kind == TOOL_CALL
        assert func_name == "execute_bash"
        assert "ls" in args_str
        
        # Second: TOOL_RESULT (from dispatch)
        kind, func_name, result_type, result = outputs[1]
        assert kind == TOOL_RESULT
        assert func_name == "execute_bash"
        
        # Third: RESPONSE
        kind, content, response = outputs[2]
        assert kind == "response"
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
        mock_response1 = {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "function": {
                        "name": "unknown_tool",
                        "arguments": {}
                    }
                }]
            },
        }
        mock_response2 = {
            "message": {"role": "assistant", "content": "Sorry", "tool_calls": None},
        }
        mock_client.chat.side_effect = [mock_response1, mock_response2]
        
        agent = Agent(agent_type, mock_client, 4096)
        
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
        mock_response = {
            "message": {"role": "assistant", "content": "Hi", "tool_calls": None},
        }
        mock_client.chat.return_value = mock_response
        
        agent = Agent(agent_type, mock_client, 4096)
        
        list(agent.handle_prompt("Hello"))
        
        # system + user + assistant
        assert len(agent.messages) == 3
        assert agent.messages[1]["role"] == "user"
        assert agent.messages[1]["content"] == "Hello"

    def test_appends_assistant_message_to_history(self):
        """Should append assistant message to conversation history."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        mock_client = MagicMock()
        mock_response = {
            "message": {"role": "assistant", "content": "Response", "tool_calls": None},
        }
        mock_client.chat.return_value = mock_response
        
        agent = Agent(agent_type, mock_client, 4096)
        
        list(agent.handle_prompt("Hi"))
        
        # system + user + assistant
        assert len(agent.messages) == 3
        assert agent.messages[2]["role"] == "assistant"
        assert agent.messages[2]["content"] == "Response"

    def test_appends_tool_result_to_history(self):
        """Should append tool result to conversation history."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()
        mock_response1 = {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "function": {
                        "name": "execute_bash",
                        "arguments": {"command": "echo test"}
                    }
                }]
            },
        }
        mock_response2 = {
            "message": {"role": "assistant", "content": "Done", "tool_calls": None},
        }
        mock_client.chat.side_effect = [mock_response1, mock_response2]
        
        agent = Agent(agent_type, mock_client, 4096)
        
        list(agent.handle_prompt("Run command"))
        
        # system + user + assistant(tool_calls) + tool(result) + assistant(final)
        assert len(agent.messages) == 5
        assert agent.messages[3]["role"] == "tool"
        assert agent.messages[3]["name"] == "execute_bash"

    def test_handles_multiple_tool_calls(self):
        """Should handle multiple tool calls in one response."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()
        mock_response1 = {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "function": {
                            "name": "execute_bash",
                            "arguments": {"command": "ls"}
                        }
                    },
                    {
                        "function": {
                            "name": "execute_bash",
                            "arguments": {"command": "pwd"}
                        }
                    }
                ]
            },
        }
        mock_response2 = {
            "message": {"role": "assistant", "content": "Done!", "tool_calls": None},
        }
        mock_client.chat.side_effect = [mock_response1, mock_response2]
        
        agent = Agent(agent_type, mock_client, 4096)
        
        outputs = list(agent.handle_prompt("Run commands"))
        
        # Should have: TOOL_CALL, TOOL_RESULT, TOOL_CALL, TOOL_RESULT, RESPONSE
        assert len(outputs) == 5
        
        # First two: first tool call and result
        assert outputs[0][0] == "tool_call"
        assert outputs[1][0] == "tool_result"
        
        # Next two: second tool call and result
        assert outputs[2][0] == "tool_call"
        assert outputs[3][0] == "tool_result"
        
        # Final response
        assert outputs[4][0] == "response"

    def test_calls_chat_with_correct_params(self):
        """Should call ollama chat with correct model, messages, tools."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="llama3",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()
        mock_response = {
            "message": {"role": "assistant", "content": "Hi", "tool_calls": None},
        }
        mock_client.chat.return_value = mock_response
        
        all_schemas = [{"function": {"name": "execute_bash"}}]
        agent = Agent(agent_type, mock_client, 4096, tool_schemas=all_schemas)
        
        list(agent.handle_prompt("Test"))
        
        # Verify chat was called with correct parameters
        call_args = mock_client.chat.call_args
        assert call_args.kwargs["model"] == "llama3"
        assert call_args.kwargs["messages"] is not None
        assert len(call_args.kwargs["messages"]) > 0
        
        # Should pass tools since they exist
        assert call_args.kwargs["tools"] is not None
        assert len(call_args.kwargs["tools"]) == 1

    def test_passes_context_length_in_options(self):
        """Should pass context length in chat options."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[]
        )
        
        mock_client = MagicMock()
        mock_response = {
            "message": {"role": "assistant", "content": "Hi", "tool_calls": None},
        }
        mock_client.chat.return_value = mock_response
        
        agent = Agent(agent_type, mock_client, 8192)
        
        list(agent.handle_prompt("Test"))
        
        # Verify chat was called with context length in options
        call_args = mock_client.chat.call_args
        assert call_args.kwargs["options"]["num_ctx"] == 8192

    def test_handles_tool_call_with_unexpected_args(self):
        """Should yield ERROR when dispatch fails with unexpected args."""
        from agent import Agent, AgentType
        
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"]
        )
        
        mock_client = MagicMock()
        # Simulate tool call with wrong argument keys (execute_bash expects 'command')
        mock_response1 = {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "function": {
                        "name": "execute_bash",
                        "arguments": {"wrong_key": "value"}
                    }
                }]
            },
        }
        mock_response2 = {
            "message": {"role": "assistant", "content": "Done", "tool_calls": None},
        }
        mock_client.chat.side_effect = [mock_response1, mock_response2]
        
        agent = Agent(agent_type, mock_client, 4096)
        
        # Should yield TOOL_CALL, ERROR, TOOL_RESULT, RESPONSE without raising
        outputs = list(agent.handle_prompt("Test"))
        assert len(outputs) == 4
        kind_error = outputs[1][0]
        assert kind_error == "error"
