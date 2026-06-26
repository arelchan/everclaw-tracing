"""everclaw-tracing — pluggable, non-invasive tracing for EverClaw.

EverClaw's plugin discovery imports this package (to read the bundled
``everclaw-plugin.toml`` via importlib.resources). We use that import as the
hook to install auto-instrumentation — the same pattern OpenTelemetry uses.
This runs before any ``AgentLoop`` is constructed, and we patch *class* methods,
so every later instance is observed.

Turn off with ``EVERCLAW_TRACING=0``. Spans land at
``~/.everclaw/traces/logs/audit-spans.log`` (override ``EVERCLAW_TRACING_DIR``).
"""

from __future__ import annotations

import logging

from . import config

__version__ = "0.1.0"

if config.enabled():
    try:
        from . import instrument

        instrument.install()
    except Exception:  # noqa: BLE001 — instrumentation must never break the host
        logging.getLogger("everclaw.plugin.everclaw-tracing").warning(
            "everclaw-tracing: install failed; agent unaffected", exc_info=True
        )
