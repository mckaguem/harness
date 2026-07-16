---
tags:
  - index
---
# harness_core Module Index

Configuration resolution — project and global .harness_py paths.

## Files

### config.py
- [harness_core.config](../pages/harness_core_config.md) - Configuration resolution — project and global 
  - [get_project_dir](../pages/harness_core_config_get_project_dir.md) - Function
  - [get_global_dir](../pages/harness_core_config_get_global_dir.md) - Function
  - [get_harness_py_dir](../pages/harness_core_config_get_harness_py_dir.md) - Function
  - [get_discovery_dirs](../pages/harness_core_config_get_discovery_dirs.md) - Function
  - [resolve_config_path](../pages/harness_core_config_resolve_config_path.md) - Function
  - [_load_yaml_file](../pages/harness_core_config__load_yaml_file.md) - Function
  - [_build_providers_dict](../pages/harness_core_config__build_providers_dict.md) - Function
  - [_build_models_dict](../pages/harness_core_config__build_models_dict.md) - Function
  - [_reset_config_cache](../pages/harness_core_config__reset_config_cache.md) - Function
  - [_get_cached_config](../pages/harness_core_config__get_cached_config.md) - Function
  - [load_harness_config](../pages/harness_core_config_load_harness_config.md) - Function
  - [get_provider_config](../pages/harness_core_config_get_provider_config.md) - Function
  - [get_model_config](../pages/harness_core_config_get_model_config.md) - Function
  - [get_default_model](../pages/harness_core_config_get_default_model.md) - Function
  - [VALID_TASK_STATUSES](../pages/harness_core_config_VALID_TASK_STATUSES.md) - Constant
  - [_SKILLS_DIR](../pages/harness_core_config__SKILLS_DIR.md) - Constant
  - [_AGENTS_DIR](../pages/harness_core_config__AGENTS_DIR.md) - Constant
  - [CONFIG_FILENAME](../pages/harness_core_config_CONFIG_FILENAME.md) - Constant

### utils.py
- [harness_core.utils](../pages/harness_core_utils.md) - Utility functions for harnessing project management
  - [project_root](../pages/harness_core_utils_project_root.md) - Function

### eventbus.py
- [harness_core.eventbus](../pages/harness_core_eventbus.md) - Event bus implementation for asynchronous event-driven communication
  - [Event](../pages/harness_core_eventbus_Event.md) - Class
  - [EventBus](../pages/harness_core_eventbus_EventBus.md) - Class
    - [__init__](../pages/harness_core_eventbus_EventBus___init__.md) - Method
    - [register_background_task](../pages/harness_core_eventbus_EventBus_register_background_task.md) - Method
    - [register_agent](../pages/harness_core_eventbus_EventBus_register_agent.md) - Method
    - [deregister_agent](../pages/harness_core_eventbus_EventBus_deregister_agent.md) - Method
    - [subscribe](../pages/harness_core_eventbus_EventBus_subscribe.md) - Method
    - [unsubscribe](../pages/harness_core_eventbus_EventBus_unsubscribe.md) - Method
    - [send_direct](../pages/harness_core_eventbus_EventBus_send_direct.md) - Method
    - [publish_to_topic](../pages/harness_core_eventbus_EventBus_publish_to_topic.md) - Method
    - [publish](../pages/harness_core_eventbus_EventBus_publish.md) - Method
  - [EventListener](../pages/harness_core_eventbus_EventListener.md) - Class
    - [__init__](../pages/harness_core_eventbus_EventListener___init__.md) - Method
    - [_mailbox_listener](../pages/harness_core_eventbus_EventListener__mailbox_listener.md) - Method
    - [_handle_incoming](../pages/harness_core_eventbus_EventListener__handle_incoming.md) - Method
    - [handle](../pages/harness_core_eventbus_EventListener_handle.md) - Method
    - [default_handler](../pages/harness_core_eventbus_EventListener_default_handler.md) - Method
    - [subscribe](../pages/harness_core_eventbus_EventListener_subscribe.md) - Method
    - [unsubscribe](../pages/harness_core_eventbus_EventListener_unsubscribe.md) - Method
    - [send_direct](../pages/harness_core_eventbus_EventListener_send_direct.md) - Method
    - [publish](../pages/harness_core_eventbus_EventListener_publish.md) - Method
  - [set_event_loop](../pages/harness_core_eventbus_set_event_loop.md) - Function
  - [get_event_loop](../pages/harness_core_eventbus_get_event_loop.md) - Function
  - [generate_unique_id](../pages/harness_core_eventbus_generate_unique_id.md) - Function
  - [filter_by_sender](../pages/harness_core_eventbus_filter_by_sender.md) - Function

### __init__.py
- [harness_core.__init__](../pages/harness_core___init__.md) - harness_core — the LLM agent harness application package

### memory.py
- [harness_core.memory](../pages/harness_core_memory.md) - Persistent project memory (MEMORY
  - [get_memory_path](../pages/harness_core_memory_get_memory_path.md) - Function
  - [read_memory](../pages/harness_core_memory_read_memory.md) - Function
  - [memory_section](../pages/harness_core_memory_memory_section.md) - Function
  - [MEMORY_FILENAME](../pages/harness_core_memory_MEMORY_FILENAME.md) - Constant

### event_types.py
- [harness_core.event_types](../pages/harness_core_event_types.md) - Event payload types for the Harness event system
  - [EventPayload](../pages/harness_core_event_types_EventPayload.md) - Class
    - [to_dict](../pages/harness_core_event_types_EventPayload_to_dict.md) - Method
  - [TaskInfo](../pages/harness_core_event_types_TaskInfo.md) - Class
    - [to_dict](../pages/harness_core_event_types_TaskInfo_to_dict.md) - Method
  - [TaskListPayload](../pages/harness_core_event_types_TaskListPayload.md) - Class
    - [from_task_list](../pages/harness_core_event_types_TaskListPayload_from_task_list.md) - Method
    - [to_dict](../pages/harness_core_event_types_TaskListPayload_to_dict.md) - Method
  - [SystemMessagePayload](../pages/harness_core_event_types_SystemMessagePayload.md) - Class
  - [SessionErrorPayload](../pages/harness_core_event_types_SessionErrorPayload.md) - Class
  - [AgentResponsePayload](../pages/harness_core_event_types_AgentResponsePayload.md) - Class
  - [TurnStatsPayload](../pages/harness_core_event_types_TurnStatsPayload.md) - Class
  - [ToolCallPayload](../pages/harness_core_event_types_ToolCallPayload.md) - Class
  - [ToolResultPayload](../pages/harness_core_event_types_ToolResultPayload.md) - Class
  - [ToolErrorPayload](../pages/harness_core_event_types_ToolErrorPayload.md) - Class

### __main__.py
- [harness_core.__main__](../pages/harness_core___main__.md) - Entry point — wires up configuration and starts the agent loop
  - [parse_args](../pages/harness_core___main___parse_args.md) - Function
  - [build_agent](../pages/harness_core___main___build_agent.md) - Function
  - [run_non_interactive](../pages/harness_core___main___run_non_interactive.md) - Function
  - [main](../pages/harness_core___main___main.md) - Function
  - [USAGE](../pages/harness_core___main___USAGE.md) - Constant

### tool_result.py
- [harness_core.tools.tool_result](../pages/harness_core_tools_tool_result.md) - ToolResult — structured return value for tools with display metadata
  - [ToolResult](../pages/harness_core_tools_tool_result_ToolResult.md) - Class

### utils.py
- [harness_core.tools.utils](../pages/harness_core_tools_utils.md) - Shared utilities for tools — path safety checks, ANSI stripping, and error formatting
  - [is_safe_path](../pages/harness_core_tools_utils_is_safe_path.md) - Function
  - [_strip_ansi](../pages/harness_core_tools_utils__strip_ansi.md) - Function
  - [make_error_result](../pages/harness_core_tools_utils_make_error_result.md) - Function

### subagent_manager.py
- [harness_core.tools.subagent_manager](../pages/harness_core_tools_subagent_manager.md) - SubagentManager — registry/orchestrator for background sub-agent jobs
  - [SubagentManager](../pages/harness_core_tools_subagent_manager_SubagentManager.md) - Class
    - [__init__](../pages/harness_core_tools_subagent_manager_SubagentManager___init__.md) - Method
    - [launch](../pages/harness_core_tools_subagent_manager_SubagentManager_launch.md) - Method
    - [await_one](../pages/harness_core_tools_subagent_manager_SubagentManager_await_one.md) - Method
    - [active_count](../pages/harness_core_tools_subagent_manager_SubagentManager_active_count.md) - Method
    - [is_running](../pages/harness_core_tools_subagent_manager_SubagentManager_is_running.md) - Method
  - [DEFAULT_MAX_CONCURRENT](../pages/harness_core_tools_subagent_manager_DEFAULT_MAX_CONCURRENT.md) - Constant

### list_dir.py
- [harness_core.tools.list_dir](../pages/harness_core_tools_list_dir.md) - list_dir — explore directory contents as an LLM-friendly tree view
  - [_format_size](../pages/harness_core_tools_list_dir__format_size.md) - Function
  - [_build_tree](../pages/harness_core_tools_list_dir__build_tree.md) - Function
  - [list_dir](../pages/harness_core_tools_list_dir_list_dir.md) - Function
  - [summary](../pages/harness_core_tools_list_dir_summary.md) - Function
  - [IGNORE_DIRS](../pages/harness_core_tools_list_dir_IGNORE_DIRS.md) - Constant

### update_task_status.py
- [harness_core.tools.update_task_status](../pages/harness_core_tools_update_task_status.md) - update_task_status — Tool for updating task execution state machine
  - [update_task_status](../pages/harness_core_tools_update_task_status_update_task_status.md) - Function
  - [summary](../pages/harness_core_tools_update_task_status_summary.md) - Function

### initialize_task_list.py
- [harness_core.tools.initialize_task_list](../pages/harness_core_tools_initialize_task_list.md) - initialize_task_list — Tool for initializing the task execution state machine
  - [initialize_task_list](../pages/harness_core_tools_initialize_task_list_initialize_task_list.md) - Function
  - [summary](../pages/harness_core_tools_initialize_task_list_summary.md) - Function

### web_search.py
- [harness_core.tools.web_search](../pages/harness_core_tools_web_search.md) - web_search — search the web using DuckDuckGo via the ddgs package
  - [web_search](../pages/harness_core_tools_web_search_web_search.md) - Function
  - [summary](../pages/harness_core_tools_web_search_summary.md) - Function

### __init__.py
- [harness_core.tools.__init__](../pages/harness_core_tools___init__.md) - Tools subpackage — self-discovering skills
  - [_discover_skills](../pages/harness_core_tools___init____discover_skills.md) - Function
  - [_build](../pages/harness_core_tools___init____build.md) - Function
  - [AGENT_TOOLS](../pages/harness_core_tools___init___AGENT_TOOLS.md) - Constant
  - [DISPATCH_REGISTRY](../pages/harness_core_tools___init___DISPATCH_REGISTRY.md) - Constant
  - [SUMMARY_REGISTRY](../pages/harness_core_tools___init___SUMMARY_REGISTRY.md) - Constant

### web_fetch.py
- [harness_core.tools.web_fetch](../pages/harness_core_tools_web_fetch.md) - web_fetch — fetch and read the contents of web pages
  - [web_fetch](../pages/harness_core_tools_web_fetch_web_fetch.md) - Function
  - [summary](../pages/harness_core_tools_web_fetch_summary.md) - Function

### submit_results.py
- [harness_core.tools.submit_results](../pages/harness_core_tools_submit_results.md) - submit_results — sub-agent termination signal
  - [submit_results](../pages/harness_core_tools_submit_results_submit_results.md) - Function
  - [summary](../pages/harness_core_tools_submit_results_summary.md) - Function

### execute_bash.py
- [harness_core.tools.execute_bash](../pages/harness_core_tools_execute_bash.md) - execute_bash — run a shell command in the terminal
  - [execute_bash](../pages/harness_core_tools_execute_bash_execute_bash.md) - Function
  - [summary](../pages/harness_core_tools_execute_bash_summary.md) - Function

### read_file.py
- [harness_core.tools.read_file](../pages/harness_core_tools_read_file.md) - read_file — read the contents of a file in the current working directory
  - [_detect_format](../pages/harness_core_tools_read_file__detect_format.md) - Function
  - [read_file](../pages/harness_core_tools_read_file_read_file.md) - Function
  - [summary](../pages/harness_core_tools_read_file_summary.md) - Function
  - [_EXT_FORMATS](../pages/harness_core_tools_read_file__EXT_FORMATS.md) - Constant

### run_subagent.py
- [harness_core.tools.run_subagent](../pages/harness_core_tools_run_subagent.md) - run_subagent — spawn a sub-agent, run a task, return the result
  - [_get_agents_dir_paths](../pages/harness_core_tools_run_subagent__get_agents_dir_paths.md) - Function
  - [_build_function_def](../pages/harness_core_tools_run_subagent__build_function_def.md) - Function
  - [_run_one](../pages/harness_core_tools_run_subagent__run_one.md) - Function
  - [run_subagent](../pages/harness_core_tools_run_subagent_run_subagent.md) - Function
  - [run_subagent_async](../pages/harness_core_tools_run_subagent_run_subagent_async.md) - Function
  - [run_subagents_parallel](../pages/harness_core_tools_run_subagent_run_subagents_parallel.md) - Function
  - [summary](../pages/harness_core_tools_run_subagent_summary.md) - Function
  - [_get_submit_results_def](../pages/harness_core_tools_run_subagent__get_submit_results_def.md) - Function
  - [TERMINATION_PROMPT](../pages/harness_core_tools_run_subagent_TERMINATION_PROMPT.md) - Constant

### activate_skill.py
- [harness_core.tools.activate_skill](../pages/harness_core_tools_activate_skill.md) - activate_skill — tool to activate a discovered skill during agent execution
  - [activate_skill](../pages/harness_core_tools_activate_skill_activate_skill.md) - Function
  - [summary](../pages/harness_core_tools_activate_skill_summary.md) - Function

### edit_file.py
- [harness_core.tools.edit_file](../pages/harness_core_tools_edit_file.md) - edit_file — apply a single search-and-replace edit to a file
  - [edit_file](../pages/harness_core_tools_edit_file_edit_file.md) - Function
  - [summary](../pages/harness_core_tools_edit_file_summary.md) - Function

### dispatcher.py
- [harness_core.tools.dispatcher](../pages/harness_core_tools_dispatcher.md) - Dispatcher — routes a tool name to its callable at runtime
  - [_accepts_ctx](../pages/harness_core_tools_dispatcher__accepts_ctx.md) - Function
  - [dispatch](../pages/harness_core_tools_dispatcher_dispatch.md) - Function
  - [summarize](../pages/harness_core_tools_dispatcher_summarize.md) - Function

### await_subagent.py
- [harness_core.tools.await_subagent](../pages/harness_core_tools_await_subagent.md) - await_subagent — block until a background sub-agent job completes
  - [await_subagent](../pages/harness_core_tools_await_subagent_await_subagent.md) - Function

### write_file.py
- [harness_core.tools.write_file](../pages/harness_core_tools_write_file.md) - write_file — write or overwrite a file in the current working directory
  - [write_file](../pages/harness_core_tools_write_file_write_file.md) - Function
  - [summary](../pages/harness_core_tools_write_file_summary.md) - Function

### grep.py
- [harness_core.tools.grep](../pages/harness_core_tools_grep.md) - grep — search for patterns across files in the current working directory
  - [grep](../pages/harness_core_tools_grep_grep.md) - Function
  - [_is_binary](../pages/harness_core_tools_grep__is_binary.md) - Function
  - [_matches_file_filter](../pages/harness_core_tools_grep__matches_file_filter.md) - Function
  - [summary](../pages/harness_core_tools_grep_summary.md) - Function

### update_memory.py
- [harness_core.tools.update_memory](../pages/harness_core_tools_update_memory.md) - update_memory — append to or rewrite the project's MEMORY
  - [update_memory](../pages/harness_core_tools_update_memory_update_memory.md) - Function
  - [summary](../pages/harness_core_tools_update_memory_summary.md) - Function

### base.py
- [harness_core.skills.base](../pages/harness_core_skills_base.md) - Base skill class and interfaces
  - [Skill](../pages/harness_core_skills_base_Skill.md) - Class
    - [__init__](../pages/harness_core_skills_base_Skill___init__.md) - Method
    - [activate](../pages/harness_core_skills_base_Skill_activate.md) - Method
    - [get_instructions](../pages/harness_core_skills_base_Skill_get_instructions.md) - Method
  - [YamlSkill](../pages/harness_core_skills_base_YamlSkill.md) - Class
    - [__init__](../pages/harness_core_skills_base_YamlSkill___init__.md) - Method
    - [activate](../pages/harness_core_skills_base_YamlSkill_activate.md) - Method

### interceptor.py
- [harness_core.skills.interceptor](../pages/harness_core_skills_interceptor.md) - Chat-interceptor middleware for slash-command skill activation
  - [InterceptorKind](../pages/harness_core_skills_interceptor_InterceptorKind.md) - Class
  - [InterceptorOutcome](../pages/harness_core_skills_interceptor_InterceptorOutcome.md) - Class
  - [intercept_message](../pages/harness_core_skills_interceptor_intercept_message.md) - Function
  - [matches_slash_pattern](../pages/harness_core_skills_interceptor_matches_slash_pattern.md) - Function
  - [extract_command_name](../pages/harness_core_skills_interceptor_extract_command_name.md) - Function
  - [SLASH_COMMAND_RE](../pages/harness_core_skills_interceptor_SLASH_COMMAND_RE.md) - Constant

### __init__.py
- [harness_core.skills.__init__](../pages/harness_core_skills___init__.md) - Skills module — skill discovery, activation, and management

### discovery.py
- [harness_core.skills.discovery](../pages/harness_core_skills_discovery.md) - Skills discovery module — scans for and validates agent skills
  - [parse_skill_metadata](../pages/harness_core_skills_discovery_parse_skill_metadata.md) - Function
  - [_merge_skill_discoveries](../pages/harness_core_skills_discovery__merge_skill_discoveries.md) - Function
  - [discover_skills](../pages/harness_core_skills_discovery_discover_skills.md) - Function
  - [format_skill_catalog](../pages/harness_core_skills_discovery_format_skill_catalog.md) - Function
  - [get_skill_by_name](../pages/harness_core_skills_discovery_get_skill_by_name.md) - Function
  - [get_skill_body](../pages/harness_core_skills_discovery_get_skill_body.md) - Function
  - [check_command_skill_collision](../pages/harness_core_skills_discovery_check_command_skill_collision.md) - Function
  - [_SKILL_DISCOVERY_CACHE](../pages/harness_core_skills_discovery__SKILL_DISCOVERY_CACHE.md) - Constant

### new.py
- [harness_core.commands.new](../pages/harness_core_commands_new.md) - Handler for the /new command
  - [cmd_new](../pages/harness_core_commands_new_cmd_new.md) - Function

### exit_quit.py
- [harness_core.commands.exit_quit](../pages/harness_core_commands_exit_quit.md) - Handler for the /exit and /quit commands
  - [cmd_exit](../pages/harness_core_commands_exit_quit_cmd_exit.md) - Function

### save_session.py
- [harness_core.commands.save_session](../pages/harness_core_commands_save_session.md) - Handler for the /save command
  - [cmd_save_session](../pages/harness_core_commands_save_session_cmd_save_session.md) - Function

### sub.py
- [harness_core.commands.sub](../pages/harness_core_commands_sub.md) - Handler for the /sub command — spawn an interactive sub-agent conversation
  - [cmd_sub](../pages/harness_core_commands_sub_cmd_sub.md) - Function

### __init__.py
- [harness_core.commands.__init__](../pages/harness_core_commands___init__.md) - Slash-command handlers (/exit, /quit, /sub, etc
  - [cmd_sub](../pages/harness_core_commands___init___cmd_sub.md) - Function
  - [cmd_tasks](../pages/harness_core_commands___init___cmd_tasks.md) - Function
  - [COMMANDS](../pages/harness_core_commands___init___COMMANDS.md) - Constant

### tasks.py
- [harness_core.commands.tasks](../pages/harness_core_commands_tasks.md) - Handler for the /tasks command — print the current task list
  - [cmd_tasks](../pages/harness_core_commands_tasks_cmd_tasks.md) - Function

### load_session.py
- [harness_core.commands.load_session](../pages/harness_core_commands_load_session.md) - Handler for the /load command
  - [cmd_load_session](../pages/harness_core_commands_load_session_cmd_load_session.md) - Function

### compress.py
- [harness_core.commands.compress](../pages/harness_core_commands_compress.md) - Handler for the /compress command
  - [compress_handler](../pages/harness_core_commands_compress_compress_handler.md) - Function

### __init__.py
- [harness_core.session.__init__](../pages/harness_core_session___init__.md) - Top-level session package exposing Session management and compression utilities

### session_utils.py
- [harness_core.session.session_utils](../pages/harness_core_session_session_utils.md) - Module
  - [format_session_yaml](../pages/harness_core_session_session_utils_format_session_yaml.md) - Function
  - [parse_session_yaml](../pages/harness_core_session_session_utils_parse_session_yaml.md) - Function
  - [create_session_filename](../pages/harness_core_session_session_utils_create_session_filename.md) - Function
  - [ensure_sessions_dir](../pages/harness_core_session_session_utils_ensure_sessions_dir.md) - Function
  - [create_run_folder](../pages/harness_core_session_session_utils_create_run_folder.md) - Function
  - [get_current_run_folder](../pages/harness_core_session_session_utils_get_current_run_folder.md) - Function
  - [set_current_run_folder](../pages/harness_core_session_session_utils_set_current_run_folder.md) - Function
  - [_CURRENT_RUN_FOLDER](../pages/harness_core_session_session_utils__CURRENT_RUN_FOLDER.md) - Constant

### session.py
- [harness_core.session.session](../pages/harness_core_session_session.md) - Module
  - [Session](../pages/harness_core_session_session_Session.md) - Class
    - [__init__](../pages/harness_core_session_session_Session___init__.md) - Method
    - [add_user_message](../pages/harness_core_session_session_Session_add_user_message.md) - Method
    - [add_assistant_message](../pages/harness_core_session_session_Session_add_assistant_message.md) - Method
    - [add_tool_result](../pages/harness_core_session_session_Session_add_tool_result.md) - Method
    - [_auto_save_session](../pages/harness_core_session_session_Session__auto_save_session.md) - Method
    - [save](../pages/harness_core_session_session_Session_save.md) - Method
    - [_save_impl](../pages/harness_core_session_session_Session__save_impl.md) - Method
    - [get_messages](../pages/harness_core_session_session_Session_get_messages.md) - Method
    - [inject_text](../pages/harness_core_session_session_Session_inject_text.md) - Method
    - [consume_injected_text](../pages/harness_core_session_session_Session_consume_injected_text.md) - Method
    - [summarize](../pages/harness_core_session_session_Session_summarize.md) - Method
    - [prepare_message_for_injection](../pages/harness_core_session_session_Session_prepare_message_for_injection.md) - Method
    - [export_session](../pages/harness_core_session_session_Session_export_session.md) - Method
    - [from_file](../pages/harness_core_session_session_Session_from_file.md) - Method

### context_compression.py
- [harness_core.session.context_compression](../pages/harness_core_session_context_compression.md) - Context Compression Module
==========================
Implements context compression for the Agent Harness
  - [_already_truncated](../pages/harness_core_session_context_compression__already_truncated.md) - Function
  - [compress_list_dir](../pages/harness_core_session_context_compression_compress_list_dir.md) - Function
  - [_extract_read_file_path](../pages/harness_core_session_context_compression__extract_read_file_path.md) - Function
  - [_parse_tool_arguments](../pages/harness_core_session_context_compression__parse_tool_arguments.md) - Function
  - [_update_filename_mapping](../pages/harness_core_session_context_compression__update_filename_mapping.md) - Function
  - [compress_file_operation](../pages/harness_core_session_context_compression_compress_file_operation.md) - Function
  - [_must_preserve](../pages/harness_core_session_context_compression__must_preserve.md) - Function
  - [compress_messages](../pages/harness_core_session_context_compression_compress_messages.md) - Function
  - [should_auto_compress](../pages/harness_core_session_context_compression_should_auto_compress.md) - Function
  - [build_compressed_filepath](../pages/harness_core_session_context_compression_build_compressed_filepath.md) - Function
  - [compress_session](../pages/harness_core_session_context_compression_compress_session.md) - Function
  - [TRUNCATED_PREFIX](../pages/harness_core_session_context_compression_TRUNCATED_PREFIX.md) - Constant
  - [LIST_DIR_TOOL_NAMES](../pages/harness_core_session_context_compression_LIST_DIR_TOOL_NAMES.md) - Constant
  - [FILE_OPERATING_TOOLS](../pages/harness_core_session_context_compression_FILE_OPERATING_TOOLS.md) - Constant

### core.py
- [harness_core.agent.core](../pages/harness_core_agent_core.md) - Agent class — owns the conversation and processes one user prompt to completion
  - [Agent](../pages/harness_core_agent_core_Agent.md) - Class
    - [__init__](../pages/harness_core_agent_core_Agent___init__.md) - Method
    - [id](../pages/harness_core_agent_core_Agent_id.md) - Method
    - [task_list](../pages/harness_core_agent_core_Agent_task_list.md) - Method
    - [provider](../pages/harness_core_agent_core_Agent_provider.md) - Method
    - [context_length](../pages/harness_core_agent_core_Agent_context_length.md) - Method
    - [session](../pages/harness_core_agent_core_Agent_session.md) - Method
    - [messages](../pages/harness_core_agent_core_Agent_messages.md) - Method
    - [inject_text](../pages/harness_core_agent_core_Agent_inject_text.md) - Method
    - [_chat](../pages/harness_core_agent_core_Agent__chat.md) - Method
    - [handle_prompt](../pages/harness_core_agent_core_Agent_handle_prompt.md) - Method
    - [spawn_subagent](../pages/harness_core_agent_core_Agent_spawn_subagent.md) - Method
    - [from_file](../pages/harness_core_agent_core_Agent_from_file.md) - Method

### utils.py
- [harness_core.agent.utils](../pages/harness_core_agent_utils.md) - Shared utilities for the agent package
  - [filter_tool_schemas](../pages/harness_core_agent_utils_filter_tool_schemas.md) - Function

### tool_context.py
- [harness_core.agent.tool_context](../pages/harness_core_agent_tool_context.md) - ToolContext — the execution context handed to every tool call
  - [ToolContext](../pages/harness_core_agent_tool_context_ToolContext.md) - Class
    - [__init__](../pages/harness_core_agent_tool_context_ToolContext___init__.md) - Method
    - [__repr__](../pages/harness_core_agent_tool_context_ToolContext___repr__.md) - Method
  - [current_tool_context](../pages/harness_core_agent_tool_context_current_tool_context.md) - Function

### __init__.py
- [harness_core.agent.__init__](../pages/harness_core_agent___init__.md) - Agent package — types, core agent class, utilities, and interactive loop

### context.py
- [harness_core.agent.context](../pages/harness_core_agent_context.md) - Context variable management for tracking the current agent
  - [get_current_agent](../pages/harness_core_agent_context_get_current_agent.md) - Function
  - [CURRENT_AGENT](../pages/harness_core_agent_context_CURRENT_AGENT.md) - Constant

### executor.py
- [harness_core.agent.executor](../pages/harness_core_agent_executor.md) - Tool executor — handles dispatch, result formatting, and error wrapping
  - [ToolExecutor](../pages/harness_core_agent_executor_ToolExecutor.md) - Class
    - [__init__](../pages/harness_core_agent_executor_ToolExecutor___init__.md) - Method
    - [execute](../pages/harness_core_agent_executor_ToolExecutor_execute.md) - Method
    - [make_error_result](../pages/harness_core_agent_executor_ToolExecutor_make_error_result.md) - Method
    - [make_submit_results_block](../pages/harness_core_agent_executor_ToolExecutor_make_submit_results_block.md) - Method

### constants.py
- [harness_core.agent.constants](../pages/harness_core_agent_constants.md) - Module-level constants used throughout the agent package
  - [RESPONSE](../pages/harness_core_agent_constants_RESPONSE.md) - Constant
  - [TOOL_CALL](../pages/harness_core_agent_constants_TOOL_CALL.md) - Constant
  - [TOOL_RESULT](../pages/harness_core_agent_constants_TOOL_RESULT.md) - Constant
  - [ERROR](../pages/harness_core_agent_constants_ERROR.md) - Constant

### types.py
- [harness_core.agent.types](../pages/harness_core_agent_types.md) - Agent type definition — model, tools, and system prompt configuration
  - [AgentType](../pages/harness_core_agent_types_AgentType.md) - Class
    - [_substitute_variables](../pages/harness_core_agent_types_AgentType__substitute_variables.md) - Method
    - [_build_system_prompt](../pages/harness_core_agent_types_AgentType__build_system_prompt.md) - Method
    - [from_file](../pages/harness_core_agent_types_AgentType_from_file.md) - Method
    - [inject_extra_system_prompt](../pages/harness_core_agent_types_AgentType_inject_extra_system_prompt.md) - Method
  - [_SYSTEM_VARIABLES](../pages/harness_core_agent_types__SYSTEM_VARIABLES.md) - Constant

### loop.py
- [harness_core.agent.loop](../pages/harness_core_agent_loop.md) - Interactive user loop for the agent harness
  - [_count_approx_tokens](../pages/harness_core_agent_loop__count_approx_tokens.md) - Function
  - [_check_and_compress_if_needed](../pages/harness_core_agent_loop__check_and_compress_if_needed.md) - Function
  - [_emit_system_event](../pages/harness_core_agent_loop__emit_system_event.md) - Function
  - [_emit_control_event](../pages/harness_core_agent_loop__emit_control_event.md) - Function
  - [_emit_tool_error_event](../pages/harness_core_agent_loop__emit_tool_error_event.md) - Function
  - [_emit_session_error_event](../pages/harness_core_agent_loop__emit_session_error_event.md) - Function
  - [_emit_agent_response_event](../pages/harness_core_agent_loop__emit_agent_response_event.md) - Function
  - [_emit_turn_stats_event](../pages/harness_core_agent_loop__emit_turn_stats_event.md) - Function
  - [_emit_tool_call_event](../pages/harness_core_agent_loop__emit_tool_call_event.md) - Function
  - [_emit_tool_result_event](../pages/harness_core_agent_loop__emit_tool_result_event.md) - Function
  - [user_loop](../pages/harness_core_agent_loop_user_loop.md) - Function

### task_list.py
- [harness_core.agent.task_list](../pages/harness_core_agent_task_list.md) - TaskList — cache-friendly state machine for tracking agent execution
  - [Task](../pages/harness_core_agent_task_list_Task.md) - Class
    - [__post_init__](../pages/harness_core_agent_task_list_Task___post_init__.md) - Method
    - [to_json](../pages/harness_core_agent_task_list_Task_to_json.md) - Method
  - [NextTaskInfo](../pages/harness_core_agent_task_list_NextTaskInfo.md) - Class
  - [TaskList](../pages/harness_core_agent_task_list_TaskList.md) - Class
    - [__init__](../pages/harness_core_agent_task_list_TaskList___init__.md) - Method
    - [_emit](../pages/harness_core_agent_task_list_TaskList__emit.md) - Method
    - [initialize_tasks](../pages/harness_core_agent_task_list_TaskList_initialize_tasks.md) - Method
    - [reset](../pages/harness_core_agent_task_list_TaskList_reset.md) - Method
    - [update_status](../pages/harness_core_agent_task_list_TaskList_update_status.md) - Method
    - [_build_next_task_info](../pages/harness_core_agent_task_list_TaskList__build_next_task_info.md) - Method
    - [has_incomplete_tasks](../pages/harness_core_agent_task_list_TaskList_has_incomplete_tasks.md) - Method
    - [all_complete](../pages/harness_core_agent_task_list_TaskList_all_complete.md) - Method
    - [next_uncompleted_task](../pages/harness_core_agent_task_list_TaskList_next_uncompleted_task.md) - Method
    - [to_json_list](../pages/harness_core_agent_task_list_TaskList_to_json_list.md) - Method
    - [to_markdown](../pages/harness_core_agent_task_list_TaskList_to_markdown.md) - Method
  - [VALID_STATUSES](../pages/harness_core_agent_task_list_VALID_STATUSES.md) - Constant

### discovery.py
- [harness_core.agent.discovery](../pages/harness_core_agent_discovery.md) - Agents discovery — scans both config paths for available agent YAML files
  - [_merge_agent_discoveries](../pages/harness_core_agent_discovery__merge_agent_discoveries.md) - Function
  - [discover_agents](../pages/harness_core_agent_discovery_discover_agents.md) - Function
  - [get_agent_yaml](../pages/harness_core_agent_discovery_get_agent_yaml.md) - Function
  - [get_agent_yaml_paths](../pages/harness_core_agent_discovery_get_agent_yaml_paths.md) - Function
  - [_AGENT_DISCOVERY_CACHE](../pages/harness_core_agent_discovery__AGENT_DISCOVERY_CACHE.md) - Constant

### event_listener.py
- [harness_core.terminal_io.event_listener](../pages/harness_core_terminal_io_event_listener.md) - Event-driven wiring between the terminal_io EventBus and the TUI
  - [_make_refresh_handler](../pages/harness_core_terminal_io_event_listener__make_refresh_handler.md) - Function
  - [_make_system_message_handler](../pages/harness_core_terminal_io_event_listener__make_system_message_handler.md) - Function
  - [make_event_listener](../pages/harness_core_terminal_io_event_listener_make_event_listener.md) - Function
  - [subscribe_event_listener](../pages/harness_core_terminal_io_event_listener_subscribe_event_listener.md) - Function
  - [make_task_list_listener](../pages/harness_core_terminal_io_event_listener_make_task_list_listener.md) - Function
  - [subscribe_task_list_listener](../pages/harness_core_terminal_io_event_listener_subscribe_task_list_listener.md) - Function

### prompt.py
- [harness_core.terminal_io.prompt](../pages/harness_core_terminal_io_prompt.md) - User input prompt with readline support (arrow keys, history)
  - [prompt_user](../pages/harness_core_terminal_io_prompt_prompt_user.md) - Function

### display.py
- [harness_core.terminal_io.display](../pages/harness_core_terminal_io_display.md) - High-level display helpers using Rich for rendering
  - [_tui_write](../pages/harness_core_terminal_io_display__tui_write.md) - Function
  - [print_system](../pages/harness_core_terminal_io_display_print_system.md) - Function
  - [display_tool_call](../pages/harness_core_terminal_io_display_display_tool_call.md) - Function
  - [_theme_border](../pages/harness_core_terminal_io_display__theme_border.md) - Function
  - [display_message_panel](../pages/harness_core_terminal_io_display_display_message_panel.md) - Function
  - [display_tool_result](../pages/harness_core_terminal_io_display_display_tool_result.md) - Function
  - [reset_pending_tool_panel](../pages/harness_core_terminal_io_display_reset_pending_tool_panel.md) - Function
  - [display_error](../pages/harness_core_terminal_io_display_display_error.md) - Function
  - [display_user_message](../pages/harness_core_terminal_io_display_display_user_message.md) - Function
  - [_combine_reasoning](../pages/harness_core_terminal_io_display__combine_reasoning.md) - Function
  - [display_agent_response](../pages/harness_core_terminal_io_display_display_agent_response.md) - Function
  - [display_turn_stats](../pages/harness_core_terminal_io_display_display_turn_stats.md) - Function
  - [_LAST_TOOL_PANEL](../pages/harness_core_terminal_io_display__LAST_TOOL_PANEL.md) - Constant

### __init__.py
- [harness_core.terminal_io.__init__](../pages/harness_core_terminal_io___init__.md) - Terminal I/O layer — Rich-based rendering with an optional textual TUI

### task_display.py
- [harness_core.terminal_io.task_display](../pages/harness_core_terminal_io_task_display.md) - Task display utilities for rendering TaskList as formatted Markdown
  - [render_task_list_markdown](../pages/harness_core_terminal_io_task_display_render_task_list_markdown.md) - Function
  - [render_task_list_markdown_from_payload](../pages/harness_core_terminal_io_task_display_render_task_list_markdown_from_payload.md) - Function

### tui.py
- [harness_core.terminal_io.tui](../pages/harness_core_terminal_io_tui.md) - Textual-based terminal UI for the harness
  - [StatusSpinner](../pages/harness_core_terminal_io_tui_StatusSpinner.md) - Class
    - [__init__](../pages/harness_core_terminal_io_tui_StatusSpinner___init__.md) - Method
    - [render](../pages/harness_core_terminal_io_tui_StatusSpinner_render.md) - Method
  - [TaskListSidebar](../pages/harness_core_terminal_io_tui_TaskListSidebar.md) - Class
    - [__init__](../pages/harness_core_terminal_io_tui_TaskListSidebar___init__.md) - Method
    - [set_agent](../pages/harness_core_terminal_io_tui_TaskListSidebar_set_agent.md) - Method
    - [set_usage](../pages/harness_core_terminal_io_tui_TaskListSidebar_set_usage.md) - Method
    - [refresh_tasks](../pages/harness_core_terminal_io_tui_TaskListSidebar_refresh_tasks.md) - Method
    - [refresh_tasks_from_payload](../pages/harness_core_terminal_io_tui_TaskListSidebar_refresh_tasks_from_payload.md) - Method
  - [HarnessTUI](../pages/harness_core_terminal_io_tui_HarnessTUI.md) - Class
    - [__init__](../pages/harness_core_terminal_io_tui_HarnessTUI___init__.md) - Method
    - [bind](../pages/harness_core_terminal_io_tui_HarnessTUI_bind.md) - Method
    - [is_active](../pages/harness_core_terminal_io_tui_HarnessTUI_is_active.md) - Method
    - [write](../pages/harness_core_terminal_io_tui_HarnessTUI_write.md) - Method
    - [begin_tool_panel](../pages/harness_core_terminal_io_tui_HarnessTUI_begin_tool_panel.md) - Method
    - [complete_tool_panel](../pages/harness_core_terminal_io_tui_HarnessTUI_complete_tool_panel.md) - Method
    - [write_count](../pages/harness_core_terminal_io_tui_HarnessTUI_write_count.md) - Method
    - [update_sidebar_usage](../pages/harness_core_terminal_io_tui_HarnessTUI_update_sidebar_usage.md) - Method
    - [update_sidebar_tasks_from_payload](../pages/harness_core_terminal_io_tui_HarnessTUI_update_sidebar_tasks_from_payload.md) - Method
    - [show_spinner](../pages/harness_core_terminal_io_tui_HarnessTUI_show_spinner.md) - Method
    - [hide_spinner](../pages/harness_core_terminal_io_tui_HarnessTUI_hide_spinner.md) - Method
    - [prompt](../pages/harness_core_terminal_io_tui_HarnessTUI_prompt.md) - Method
    - [_arm_input](../pages/harness_core_terminal_io_tui_HarnessTUI__arm_input.md) - Method
    - [submit](../pages/harness_core_terminal_io_tui_HarnessTUI_submit.md) - Method
    - [reset](../pages/harness_core_terminal_io_tui_HarnessTUI_reset.md) - Method
  - [TextualHarnessApp](../pages/harness_core_terminal_io_tui_TextualHarnessApp.md) - Class
    - [__init__](../pages/harness_core_terminal_io_tui_TextualHarnessApp___init__.md) - Method
    - [compose](../pages/harness_core_terminal_io_tui_TextualHarnessApp_compose.md) - Method
    - [update_sidebar_usage](../pages/harness_core_terminal_io_tui_TextualHarnessApp_update_sidebar_usage.md) - Method
    - [update_sidebar_tasks_from_payload](../pages/harness_core_terminal_io_tui_TextualHarnessApp_update_sidebar_tasks_from_payload.md) - Method
    - [on_mount](../pages/harness_core_terminal_io_tui_TextualHarnessApp_on_mount.md) - Method
    - [_start_loop](../pages/harness_core_terminal_io_tui_TextualHarnessApp__start_loop.md) - Method
    - [_show_loop_error](../pages/harness_core_terminal_io_tui_TextualHarnessApp__show_loop_error.md) - Method
    - [action_submit_input](../pages/harness_core_terminal_io_tui_TextualHarnessApp_action_submit_input.md) - Method
  - [get_tui](../pages/harness_core_terminal_io_tui_get_tui.md) - Function
  - [launch](../pages/harness_core_terminal_io_tui_launch.md) - Function
  - [TOOL_SEPARATOR](../pages/harness_core_terminal_io_tui_TOOL_SEPARATOR.md) - Constant

### speed.py
- [harness_core.terminal_io.speed](../pages/harness_core_terminal_io_speed.md) - Token-speed formatting for chat responses
  - [_resolve_usage](../pages/harness_core_terminal_io_speed__resolve_usage.md) - Function
  - [_resolve_duration_ms](../pages/harness_core_terminal_io_speed__resolve_duration_ms.md) - Function
  - [format_speed](../pages/harness_core_terminal_io_speed_format_speed.md) - Function
  - [format_tool_elapsed](../pages/harness_core_terminal_io_speed_format_tool_elapsed.md) - Function

### provider.py
- [harness_core.model.provider](../pages/harness_core_model_provider.md) - Provider abstraction for AI model backends with singleton registry
  - [Provider](../pages/harness_core_model_provider_Provider.md) - Class
    - [get_or_create](../pages/harness_core_model_provider_Provider_get_or_create.md) - Method
    - [get](../pages/harness_core_model_provider_Provider_get.md) - Method
    - [chat_completion](../pages/harness_core_model_provider_Provider_chat_completion.md) - Method
    - [chat_completion_async](../pages/harness_core_model_provider_Provider_chat_completion_async.md) - Method
    - [tokenize](../pages/harness_core_model_provider_Provider_tokenize.md) - Method
    - [get_base_url](../pages/harness_core_model_provider_Provider_get_base_url.md) - Method
    - [from_config](../pages/harness_core_model_provider_Provider_from_config.md) - Method
  - [OpenAIProvider](../pages/harness_core_model_provider_OpenAIProvider.md) - Class
    - [__init__](../pages/harness_core_model_provider_OpenAIProvider___init__.md) - Method
    - [chat_completion](../pages/harness_core_model_provider_OpenAIProvider_chat_completion.md) - Method
    - [chat_completion_async](../pages/harness_core_model_provider_OpenAIProvider_chat_completion_async.md) - Method
    - [tokenize](../pages/harness_core_model_provider_OpenAIProvider_tokenize.md) - Method
    - [get_base_url](../pages/harness_core_model_provider_OpenAIProvider_get_base_url.md) - Method
  - [_to_responses_input](../pages/harness_core_model_provider__to_responses_input.md) - Function
  - [_to_responses_tools](../pages/harness_core_model_provider__to_responses_tools.md) - Function
  - [_normalize_response](../pages/harness_core_model_provider__normalize_response.md) - Function
  - [create_provider](../pages/harness_core_model_provider_create_provider.md) - Function

### utils.py
- [harness_core.model.utils](../pages/harness_core_model_utils.md) - Model utilities — base URL resolution and tokenization
  - [get_base_url](../pages/harness_core_model_utils_get_base_url.md) - Function
  - [tokenize_prompt](../pages/harness_core_model_utils_tokenize_prompt.md) - Function

### __init__.py
- [harness_core.model.__init__](../pages/harness_core_model___init__.md) - Model module — provider abstractions and utilities for AI models

### types.py
- [harness_core.model.types](../pages/harness_core_model_types.md) - Model-related type definitions
  - [ModelConfig](../pages/harness_core_model_types_ModelConfig.md) - Class
  - [ProviderConfig](../pages/harness_core_model_types_ProviderConfig.md) - Class
  - [TokenUsage](../pages/harness_core_model_types_TokenUsage.md) - Class
  - [CompletionResponse](../pages/harness_core_model_types_CompletionResponse.md) - Class