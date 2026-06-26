"""Import-time configuration for everclaw-tracing.

Deliberately dependency-free and side-effect-light: we must NOT import everclaw
internals here. This module is first imported during EverClaw plugin discovery,
before the agent config is loaded, so everything is driven by environment
variables with sane defaults — the plugin works the moment it is pip-installed.
"""

from __future__ import annotations

import os
from pathlib import Path

_OFF = {"0", "false", "off", "no"}


def enabled() -> bool:
    """Tracing is on unless ``EVERCLAW_TRACING`` is a falsy string."""
    return os.environ.get("EVERCLAW_TRACING", "1").strip().lower() not in _OFF


def state_dir() -> Path:
    """Trace state dir. Matches the viewer's everclaw convention (``~/.everclaw/traces``).

    Overridable with ``EVERCLAW_TRACING_DIR`` (absolute) or ``EVERCLAW_HOME``.
    Spans land at ``<state_dir>/logs/audit-spans.log``.
    """
    override = os.environ.get("EVERCLAW_TRACING_DIR")
    if override:
        return Path(override).expanduser()
    home = os.environ.get("EVERCLAW_HOME")
    base = Path(home).expanduser() if home else Path.home() / ".everclaw"
    return base / "traces"


def preview_len() -> int:
    """Max chars kept inline on a span; full payloads go to artifacts."""
    try:
        return max(0, int(os.environ.get("EVERCLAW_TRACING_PREVIEW", "500")))
    except ValueError:
        return 500
