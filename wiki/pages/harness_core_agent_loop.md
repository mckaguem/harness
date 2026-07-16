---
name: "harness_core.agent.loop"
description: "Interactive user loop for the agent harness."
source: "harness_core/agent/loop.py"
---

Interactive user loop for the agent harness.

## References
- [_count_approx_tokens](harness_core_agent_loop__count_approx_tokens) - Approximate token count from a message list using character estimation
- [_check_and_compress_if_needed](harness_core_agent_loop__check_and_compress_if_needed) - Check context utilization and trigger compression if above threshold
- [_emit_system_event](harness_core_agent_loop__emit_system_event) - Emit a system-notification event, or render it directly when no TUI is active
- [_emit_control_event](harness_core_agent_loop__emit_control_event) - Emit a control event (e
- [_emit_tool_error_event](harness_core_agent_loop__emit_tool_error_event) - Emit an 'agent
- [_emit_session_error_event](harness_core_agent_loop__emit_session_error_event) - Emit an 'agent
- [_emit_agent_response_event](harness_core_agent_loop__emit_agent_response_event) - Emit an 'agent
- [_emit_turn_stats_event](harness_core_agent_loop__emit_turn_stats_event) - Emit an 'agent
- [_emit_tool_call_event](harness_core_agent_loop__emit_tool_call_event) - Emit an 'agent
- [_emit_tool_result_event](harness_core_agent_loop__emit_tool_result_event) - Emit an 'agent
- [user_loop](harness_core_agent_loop_user_loop) - Run the interactive chat loop
- [Module Index](../index/harness_core_agent.md) - Parent module index
