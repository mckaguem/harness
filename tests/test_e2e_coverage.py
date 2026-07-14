"""End-to-end non-interactive coverage tests for harness_core.

This module exercises the harness's main functionalities by driving the agent in
NON-INTERACTIVE mode (through ``run_non_interactive`` / ``Agent.handle_prompt``)
with an in-memory fake provider so no network or live LLM is contacted.

It covers:
  A) Every tool exposed by the harness (driven through the real dispatch path).
  B) The skill mechanisms (discovery, interceptor routing, activate_skill).
  C) Subagents (run_subagent spawning + discovery).

All providers are fakes; any network call (web_search / web_fetch / sub-agent
provider resolution) is patched so the suite stays fully offline and fast.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from harness_core.agent import Agent, AgentType
from harness_core.model.provider import Provider
from harness_core.__main__ import run_non_interactive


# ─────────────────────────────────────────────────────────────────────────────
# Fake provider + response builders
# ─────────────────────────────────────────────────────────────────────────────


class FakeProvider(Provider):
    """In-memory Provider: consumes a list of chat-completion dicts in order."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.base_url = "http://localhost.test"

    def chat_completion(self, messages, model, **kwargs):
        if self._responses:
            return self._responses.pop(0)
        # Default: empty assistant text turn (no tool calls).
        return {
            "choices": [{"message": {"role": "assistant", "content": ""}}],
            "model": model,
            "usage": {},
        }

    def tokenize(self, text, model):
        return None

    def get_base_url(self):
        return self.base_url


def text_response(content):
    """Build a plain assistant text turn (no tool calls)."""
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "model": "test",
        "usage": {},
    }


def tool_response(name, args_dict, call_id="call_1"):
    """Build an assistant turn requesting a single tool call.

    *args_dict* is serialized to the JSON string the dispatcher will parse.
    """
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps(args_dict),
                    },
                }],
            }
        }],
        "model": "test",
        "usage": {},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Offline fakes for network-backed tools.
# ─────────────────────────────────────────────────────────────────────────────


class _FakeDDGS:
    """Stand-in for ``ddgs.DDGS`` used to exercise web_search offline."""

    def __init__(self, *args, **kwargs):
        pass

    def text(self, **kwargs):
        return [
            {"title": "Result One", "href": "https://example.com/1", "body": "snippet"},
        ]


class _FakeResponse:
    """Stand-in for ``urllib.request.urlopen`` context manager."""

    status = 200
    url = "https://example.com"

    def __init__(self):
        self._headers = {"Content-Type": "text/html; charset=utf-8"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def headers(self):  # pragma: no cover - unused alternate accessor
        return self._headers

    def read(self):
        return b"<html>HARNESS_FETCH_OK</html>"

    def get(self, key, default=None):
        return self._headers.get(key, default)


def _fake_urlopen(req, timeout=30):
    return _FakeResponse()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers for running the agent with terminal display patched out.
# ─────────────────────────────────────────────────────────────────────────────


def run_captured(agent, message):
    """Drive the agent non-interactively, capturing display events.

    Returns a dict with:
      * rc           — return code from run_non_interactive
      * response     — final assistant text captured from display_agent_response
      * tool_calls   — list of function names from display_tool_call
      * tool_results — list of (func_name, ToolResult) from display_tool_result
      * errors       — list of error strings from display_error
    """
    captured = {"response": None, "tool_calls": [], "tool_results": [], "errors": []}
    with patch("harness_core.terminal_io.display_agent_response",
               side_effect=lambda c, r, cl, **k: captured.__setitem__("response", c)), \
         patch("harness_core.terminal_io.display_user_message"), \
         patch("harness_core.terminal_io.display_tool_call",
               side_effect=lambda fn, a, **k: captured["tool_calls"].append(fn)), \
         patch("harness_core.terminal_io.display_tool_result",
               side_effect=lambda fn, r: captured["tool_results"].append((fn, r))), \
         patch("harness_core.terminal_io.display_error",
               side_effect=lambda d: captured["errors"].append(d)):
        rc = run_non_interactive(agent, message)
    return {"rc": rc, **captured}


def make_agent(responses, agent_tools=None):
    """Build a single-tool (or all-tools) agent wired to a FakeProvider."""
    tools = agent_tools if agent_tools is not None else ["*"]
    agent_type = AgentType(
        model_name="test",
        system_prompt="You are a helpful test agent.",
        agent_tools=tools,
    )
    return Agent(agent_type, 4096, provider=FakeProvider(responses))


# ─────────────────────────────────────────────────────────────────────────────
# A) All tools, end-to-end
# ─────────────────────────────────────────────────────────────────────────────


class TestAllToolsE2E:
    # -- execute_bash --------------------------------------------------------
    def test_execute_bash_e2e(self):
        agent = make_agent([
            tool_response("execute_bash", {"command": "echo HARNESS_E2E_BASH"}),
            text_response("done"),
        ])
        out = run_captured(agent, "run it")
        assert out["rc"] == 0
        assert "execute_bash" in [n for n, _ in out["tool_results"]]
        _name, result = next((n, r) for n, r in out["tool_results"]
                             if n == "execute_bash")
        assert "HARNESS_E2E_BASH" in result.llm_text

    # -- write_file / read_file roundtrip -----------------------------------
    def test_write_file_then_read_file_e2e(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        # write_file/read_file resolve paths relative to the project root, so
        # plant a project marker so tmp_path is recognised as the root.
        (tmp_path / ".harness_py").mkdir()
        fname = "e2e_out.txt"
        agent = make_agent([
            tool_response("write_file", {"filename": fname, "content": "e2e-content-123"}),
            tool_response("read_file", {"filename": fname, "offset": 0, "limit": 50}),
            text_response("done"),
        ])
        out = run_captured(agent, "do it")
        assert out["rc"] == 0
        results = dict(out["tool_results"])
        assert "write_file" in results and "read_file" in results
        assert "e2e-content-123" in results["read_file"].llm_text

    # -- edit_file -----------------------------------------------------------
    def test_edit_file_e2e(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".harness_py").mkdir()
        fname = "edit_me.txt"
        (tmp_path / fname).write_text("hello world\n", encoding="utf-8")
        agent = make_agent([
            tool_response("edit_file", {
                "filename": fname,
                "old_text": "hello",
                "new_text": "goodbye",
            }),
            text_response("done"),
        ])
        out = run_captured(agent, "edit it")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"]
                             if n == "edit_file")
        assert "replaced" in result.llm_text.lower()
        assert (tmp_path / fname).read_text() == "goodbye world\n"

    # -- grep ----------------------------------------------------------------
    def test_grep_e2e(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".harness_py").mkdir()
        (tmp_path / "notes.txt").write_text("alpha\nbeta HARNESS_GREP_MARKER\ngamma\n",
                                            encoding="utf-8")
        agent = make_agent([
            tool_response("grep", {"pattern": "HARNESS_GREP_MARKER", "path": "."}),
            text_response("done"),
        ])
        out = run_captured(agent, "search")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"] if n == "grep")
        assert "HARNESS_GREP_MARKER" in result.llm_text

    # -- list_dir ------------------------------------------------------------
    def test_list_dir_e2e(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".harness_py").mkdir()
        (tmp_path / "a_file.txt").write_text("x", encoding="utf-8")
        (tmp_path / "subdir").mkdir()
        agent = make_agent([
            tool_response("list_dir", {"path": "."}),
            text_response("done"),
        ])
        out = run_captured(agent, "list")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"] if n == "list_dir")
        assert "a_file.txt" in result.llm_text

    # -- web_search (network patched) ---------------------------------------
    def test_web_search_e2e(self, monkeypatch):
        # web_search imports ``DDGS`` lazily from ``ddgs`` inside the function
        # body, so we patch the ``ddgs`` module's ``DDGS`` attribute to resolve
        # to our offline fake class.
        import ddgs as _ddgs_mod
        monkeypatch.setattr("ddgs.DDGS", _FakeDDGS, raising=False)
        agent = make_agent([
            tool_response("web_search", {"query": "harness testing"}),
            text_response("done"),
        ])
        out = run_captured(agent, "search the web")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"] if n == "web_search")
        assert "Result One" in result.llm_text

    # -- web_fetch (network patched) -----------------------------------------
    def test_web_fetch_e2e(self, monkeypatch):
        # web_fetch imports ``urlopen`` from ``urllib.request``; patch that name
        # in the module namespace so our fake is used instead of a real request.
        import harness_core.tools.web_fetch as _web_fetch_mod
        monkeypatch.setattr("harness_core.tools.web_fetch.urlopen", _fake_urlopen)
        agent = make_agent([
            tool_response("web_fetch", {"url": "https://example.com"}),
            text_response("done"),
        ])
        out = run_captured(agent, "fetch it")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"] if n == "web_fetch")
        assert "example.com" in result.llm_text

    # -- submit_results ------------------------------------------------------
    def test_submit_results_e2e(self):
        payload = {
            "summary_of_actions": "did a thing",
            "actionable_data": {"file_paths": []},
            "unresolved_issues": None,
        }
        agent = make_agent([
            tool_response("submit_results", {"json_payload": json.dumps(payload)}),
            text_response("done"),
        ])
        out = run_captured(agent, "finish up")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"]
                             if n == "submit_results")
        assert "did a thing" in result.llm_text

    # -- initialize_task_list + update_task_status (combined, due to the
    #    task-completion blocker in handle_prompt) --------------------------
    def test_task_list_e2e(self):
        agent = make_agent([
            tool_response("initialize_task_list", {"tasks": ["first", "second"]}),
            tool_response("update_task_status", {"task_id": 1, "status": "completed"}),
            tool_response("update_task_status", {"task_id": 2, "status": "completed"}),
            text_response("all done"),
        ])
        out = run_captured(agent, "manage tasks")
        assert out["rc"] == 0
        names = [n for n, _ in out["tool_results"]]
        assert "initialize_task_list" in names
        assert "update_task_status" in names
        _n, init_result = next((n, r) for n, r in out["tool_results"]
                               if n == "initialize_task_list")
        assert "2 tasks" in init_result.llm_text or "Initialized" in init_result.llm_text

    # -- activate_skill (real skill from .harness_py/skills) -----------------
    def test_activate_skill_e2e(self):
        agent = make_agent([
            tool_response("activate_skill", {"skill_name": "code-review"}),
            text_response("done"),
        ])
        out = run_captured(agent, "activate a skill")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"]
                             if n == "activate_skill")
        assert "code-review" in result.llm_text

    # -- run_subagent (sub-agent provider patched to a fake) -----------------
    def test_run_subagent_e2e(self):
        sub_payload = {
            "summary_of_actions": "sub-agent finished",
            "actionable_data": {"file_paths": []},
            "unresolved_issues": None,
        }
        sub_provider = FakeProvider([
            tool_response("submit_results", {"json_payload": json.dumps(sub_payload)}),
        ])
        sub_agent = Agent(
            AgentType(model_name="test", system_prompt="sub", agent_tools=[]),
            4096,
            provider=sub_provider,
        )

        parent = make_agent([
            tool_response("run_subagent", {"sub_agent": "analyst", "task": "go"}),
            text_response("parent done"),
        ])

        # Patch the spawn seam so the sub-agent runs fully offline on the fake.
        with patch("harness_core.agent.core.Agent.spawn_subagent",
                   return_value=sub_agent):
            out = run_captured(parent, "spawn a subagent")

        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"]
                             if n == "run_subagent")
        assert "sub-agent finished" in result.llm_text


# ─────────────────────────────────────────────────────────────────────────────
# B) Skill mechanisms
# ─────────────────────────────────────────────────────────────────────────────


class TestSkillMechanisms:
    def test_skills_discovered(self):
        from harness_core.skills.discovery import discover_skills

        skills = discover_skills()
        assert skills  # non-empty
        names = {name for name, _ in skills}
        # At least the skills shipped in .harness_py/skills must be present.
        for expected in ("code-review", "python-coding", "sample-skill"):
            assert expected in names

    def test_interceptor_routes_slash_or_skill(self):
        from harness_core.skills.interceptor import intercept_message, InterceptorKind

        outcome = intercept_message("/code-review")
        # /code-review maps to a real, user-invocable skill → ACTIVATED.
        assert outcome.kind == InterceptorKind.ACTIVATED
        assert outcome.payload
        assert outcome.stripped_message == ""

    def test_interceptor_unknown_slash_is_unknown(self):
        from harness_core.skills.interceptor import intercept_message, InterceptorKind

        outcome = intercept_message("/no-such-skill-xyz")
        assert outcome.kind in (InterceptorKind.UNKNOWN, InterceptorKind.SKIP)

    def test_activate_skill_tool_e2e(self):
        agent = make_agent([
            tool_response("activate_skill", {"skill_name": "python-coding"}),
            text_response("done"),
        ])
        out = run_captured(agent, "use python-coding skill")
        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"]
                             if n == "activate_skill")
        assert "python-coding" in result.llm_text


# ─────────────────────────────────────────────────────────────────────────────
# C) Subagents
# ─────────────────────────────────────────────────────────────────────────────


class TestSubagents:
    def test_subagent_discovery(self):
        from harness_core.agent.discovery import discover_agents, get_agent_yaml

        agents = discover_agents()
        names = {name for name, _ in agents}
        for expected in ("analyst", "coder"):
            assert expected in names

        path, error = get_agent_yaml("analyst")
        assert error == ""
        assert path is not None and Path(path).is_file()

    def test_run_subagent_e2e_via_patched_provider(self):
        sub_payload = {
            "summary_of_actions": "research complete",
            "actionable_data": {"file_paths": ["/tmp/x"]},
            "unresolved_issues": None,
        }
        sub_provider = FakeProvider([
            tool_response("submit_results", {"json_payload": json.dumps(sub_payload)}),
        ])
        sub_agent = Agent(
            AgentType(model_name="test", system_prompt="sub", agent_tools=[]),
            4096,
            provider=sub_provider,
        )
        parent = make_agent([
            tool_response("run_subagent", {"sub_agent": "researcher", "task": "research"}),
            text_response("parent finished"),
        ])
        with patch("harness_core.agent.core.Agent.spawn_subagent",
                   return_value=sub_agent):
            out = run_captured(parent, "delegate research")

        assert out["rc"] == 0
        _name, result = next((n, r) for n, r in out["tool_results"]
                             if n == "run_subagent")
        assert "research complete" in result.llm_text
