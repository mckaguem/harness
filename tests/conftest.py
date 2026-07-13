"""Pytest configuration: isolate session-file writes to a temp directory.

Many tests construct a ``Session`` directly, or indirectly via an ``Agent`` or
the ``new`` / ``load_session`` commands. With ``auto_save`` enabled (the
default), every such ``Session`` writes a timestamped ``*.yaml`` file into the
project's ``.sessions/`` directory. Left unguarded this pollutes ``.sessions/``
with hundreds of files across test runs.

This autouse fixture redirects every ``Session`` write to a per-test temporary
directory (automatically removed by pytest) and clears any stale "current run
folder" global that a previous test may have left behind.
"""

import pytest


@pytest.fixture(autouse=True)
def _isolate_session_writes(tmp_path, monkeypatch):
    """Route ``Session`` auto-save files into a temp ``.sessions/`` dir.

    ``Session`` calls ``ensure_sessions_dir`` (imported into the
    ``harness_core.session.session`` namespace) on every save. Patching that
    reference redirects both ``Session.__init__`` and
    ``Session._auto_save_session`` writes to a temp location without touching
    the real ``harness_core.session.session_utils.ensure_sessions_dir`` (which
    has its own dedicated tests in ``test_session_utils.py``).
    """
    # Temp location for any session files written during this test.
    sessions_dir = tmp_path / ".sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "harness_core.session.session.ensure_sessions_dir",
        lambda *args, **kwargs: sessions_dir,
    )

    # Clear any run-folder global leaked between tests so the patched
    # ensure_sessions_dir remains the effective write target.
    from harness_core.session.session_utils import set_current_run_folder
    set_current_run_folder(None)

    yield
