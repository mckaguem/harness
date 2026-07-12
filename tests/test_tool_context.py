"""Tests for harness_core.agent.tool_context — ToolContext + current_tool_context."""

from harness_core.agent.context import CURRENT_AGENT
from harness_core.agent.tool_context import ToolContext, current_tool_context


class _FakeAgent:
    name = "test-agent"


class TestToolContext:
    """ToolContext carries the calling agent; current_tool_context reads CURRENT_AGENT."""

    def test_tool_context_stores_agent(self):
        agent = _FakeAgent()
        ctx = ToolContext(agent=agent)
        assert ctx.agent is agent
        assert "test-agent" in repr(ctx)

    def test_tool_context_none_agent(self):
        ctx = ToolContext(agent=None)
        assert ctx.agent is None
        assert "None" in repr(ctx)

    def test_current_tool_context_reads_agent(self, monkeypatch):
        agent = _FakeAgent()
        monkeypatch.setattr(
            "harness_core.agent.tool_context.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: agent)})(),
        )
        ctx = current_tool_context()
        assert ctx.agent is agent

    def test_current_tool_context_none_when_unset(self, monkeypatch):
        monkeypatch.setattr(
            "harness_core.agent.tool_context.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: None)})(),
        )
        CURRENT_AGENT.set(None)
        ctx = current_tool_context()
        assert ctx.agent is None
