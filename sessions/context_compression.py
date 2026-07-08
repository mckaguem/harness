"""Context-compression module for session messages in an LLM harness project.

Compresses session history by replacing obsolete or irrelevant tool results and
assistant messages with short placeholder notes, reducing token usage while
preserving the semantic structure of the conversation.
"""

import json
from pathlib import Path


def compress_messages(messages: list[dict]) -> list[dict]:
    """Compress session history by replacing obsolete/irrelevant messages with short notes.

    Produces a new list without mutating the input. Applies five rules to identify
    tool results and assistant messages that can be replaced, prioritising more
    specific rules over general ones:

      * Rule 1 — error-like content in tool results is flagged and summarised.
      * Rule 2 — an earlier ``read_file`` result superseded by a later edit on the
        same path has its content replaced with a note.
      * Rule 3 — an earlier ``read_file`` result superseded by any later complete
        re-read of the same file is removed.
      * Rule 4 — an earlier ``write_file`` result superseded by a later edit on
        the same path is removed.
      * Rule 5 — any tool call whose referenced file no longer exists on disk at
        compression time has its result removed.

    System and user messages are never modified.

    Parameters
    ----------
    messages : list[dict]
        The session message history, where each element is a dict with at least
        ``role`` (and optionally ``content``, ``tool_calls``, ``name``).

    Returns
    -------
    list[dict]
        A new list of message dicts with obsolete entries replaced by placeholder
        note strings in their ``content`` fields.
    """

    if not isinstance(messages, list):
        return list(messages)  # Return a copy of invalid input

    # ──────────────────────────────────────────────────────────────────────
    # Phase 1 & 2: Extract file operations and map to their result messages
    # ──────────────────────────────────────────────────────────────────────

    # Each entry: (asst_msg_idx, result_msg_idx_or_None, op_name, filepath_str)
    ops = []
    pending_ops = []  # indices into ``ops`` for calls awaiting results

    for i, msg in enumerate(messages):
        role = msg.get("role", "")

        if role == "assistant" and "tool_calls" in msg:
            tc_list = msg["tool_calls"] or []
            for tc in tc_list:
                func = tc.get("function") or {}
                name = str(func.get("name") or "").strip()

                # Parse JSON arguments
                args_raw = func.get("arguments")
                if isinstance(args_raw, str):
                    try:
                        args = json.loads(args_raw)
                    except (json.JSONDecodeError, TypeError):
                        continue
                elif isinstance(args_raw, dict):
                    args = args_raw
                else:
                    continue

                if not isinstance(args, dict):
                    continue

                filepath_raw = str(args.get("filename", "") or "").strip()
                if not filepath_raw:
                    continue

                resolved_path = Path(filepath_raw).resolve()

                ops.append((i, None, name, str(resolved_path)))
                pending_ops.append(len(ops) - 1)

        elif role == "tool":
            # Match to the first unassigned pending op in chronological order.
            if pending_ops:
                best_pos = pending_ops.pop(0)
                asst_idx, _, name, fp = ops[best_pos]
                ops[best_pos] = (asst_idx, i, name, fp)

    # ──────────────────────────────────────────────────────────────────────
    # Phase 3: Build replacement map using Rules 2-4 first, then Rule 5
    # ──────────────────────────────────────────────────────────────────────
    # Rules 2-4 produce more specific notes and therefore take precedence over
    # the general Rule 5.

    replace_indices = {}  # ``{message_index → replacement_note_string}``

    read_results = [
        (res_idx, asst_idx, fp)
        for (asst_idx, res_idx, name, fp) in ops
        if name == "read_file" and res_idx is not None
    ]

    write_results = [
        (res_idx, asst_idx, fp)
        for (asst_idx, res_idx, name, fp) in ops
        if name == "write_file" and res_idx is not None
    ]

    edit_ops_list = [
        (asst_idx, fp)
        for (asst_idx, _, name, fp) in ops
        if name == "edit_file"
    ]

    # --- Rule 2: read superseded by later edit → replace earlier READ RESULT ---
    for res_idx, asst_idx, filepath in read_results:
        has_later_edit = any(
            e_asst > asst_idx and e_fp == filepath
            for (e_asst, e_fp) in edit_ops_list
        )
        if has_later_edit:
            replace_indices[res_idx] = (
                f"[Read of '{filepath}' was superseded by a later edit "
                f"and removed from context.]"
            )

    # --- Rule 3: read replaced by later complete re-read → earlier RESULT ---
    for i, (res1_idx, asst1_idx, fp1) in enumerate(read_results):
        if res1_idx in replace_indices:
            continue  # Already marked by a more specific rule (e.g. Rule 2).

        has_later_read = any(
            r_fp == fp1
            for (_, _, r_fp) in read_results[i + 1:]
        )

        if has_later_read:
            replace_indices[res1_idx] = (
                f"[Read of '{fp1}' was replaced by a later complete re-read "
                f"and removed from context.]"
            )

    # --- Rule 4: write superseded by later edit → replace earlier WRITE RESULT ---
    for res_idx, asst_idx, filepath in write_results:
        has_later_edit = any(
            e_asst > asst_idx and e_fp == filepath
            for (e_asst, e_fp) in edit_ops_list
        )
        if has_later_edit:
            replace_indices[res_idx] = (
                f"[Write to '{filepath}' was superseded by a later edit "
                f"and removed from context.]"
            )

    # --- Rule 5: files that no longer exist on disk at compression time ---
    # Only applied where not already marked by the more specific Rules 2-4.
    for asst_idx, res_idx, name, filepath in ops:
        if name not in ("read_file", "write_file"):
            continue
        if res_idx is None or res_idx in replace_indices:
            continue

        p = Path(filepath)
        if not (p.is_file() or p.is_dir()):
            replace_indices[res_idx] = (
                f"[Tool '{filepath}' referenced a file that does not exist "
                f"and was removed from context.]"
            )

    # ──────────────────────────────────────────────────────────────────────
    # Phase 4: Build output list with replacements applied
    # ──────────────────────────────────────────────────────────────────────

    result = []
    for i, msg in enumerate(messages):
        role = msg.get("role", "")

        if role == "system":
            # Never touch system prompts — shallow copy to avoid accidental mutation.
            result.append(dict(msg))
            continue

        if role == "user":
            # Do not replace user messages.
            result.append(dict(msg))
            continue

        new_msg = dict(msg) if isinstance(msg, dict) else msg.copy()

        # Rule 1: error-like content in tool results (only when not already marked).
        if role == "tool" and i not in replace_indices:
            content = str(msg.get("content", ""))
            has_error = any(
                substr in content
                for substr in ("Error", "error:", "not found", "traversal detected")
            )
            if has_error:
                tool_name = msg.get("name", "unknown")
                new_msg["content"] = (
                    f"[Tool call '{tool_name}' had an error and was removed from "
                    f"context to save tokens.]"
                )

        # Apply replacement note for Rules 2-5 (overwrites Rule 1 if both apply).
        if i in replace_indices:
            new_msg["content"] = replace_indices[i]

        result.append(new_msg)

    return result
