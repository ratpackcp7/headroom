"""Headroom CLI - Command-line interface for memory and proxy management.

The subcommand submodules are imported eagerly below so they are bound as
attributes of `headroom.cli`. Click registration happens via side effects in
`main.py::_register_commands`, but that only binds them to the *main.py*
module. Tests that do `patch("headroom.cli.<sub>.<attr>")` resolve the target
by walking attributes on the package object, and that lookup fails when a
prior test has popped `headroom.cli` from `sys.modules` and re-imported it
through a path other than `main.py` (e.g. a test that replaces
`sys.modules["headroom.cli.main"]` with a fake to isolate one subcommand).
Doing `from . import ...` here means the submodule attribute binding
survives that kind of sys.modules mutation.
"""
import sys


def _fast_init_hook_ensure() -> bool:
    """Fast-path health check for `init hook ensure` to avoid heavy CLI imports."""
    import os
    if os.environ.get("HEADROOM_FAST_PATH_DISABLE") == "1":
        return False
    if len(sys.argv) >= 4 and sys.argv[1:4] == ["init", "hook", "ensure"]:
        profile = "init-user"
        for i, arg in enumerate(sys.argv):
            if arg == "--profile" and i + 1 < len(sys.argv):
                profile = sys.argv[i + 1]

        import json
        import urllib.request
        from pathlib import Path

        manifest_path = Path.home() / ".headroom" / "deploy" / profile / "manifest.json"
        if not manifest_path.is_file():
            return False

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            health_url = manifest.get("health_url")
            if not health_url:
                host = manifest.get("host", "127.0.0.1")
                port = manifest.get("port", 8787)
                health_url = f"http://{host}:{port}/readyz"

            req = urllib.request.Request(health_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") == "healthy" and data.get("ready") is True:
                        return True
        except Exception:
            return False
    return False


if _fast_init_hook_ensure():
    sys.exit(0)

from . import (  # noqa: F401
    audit,
    capture,
    copilot_auth,
    evals,
    init,
    inspect,
    install,
    learn,
    mcp,
    perf,
    proxy,
    recover,
    rollout,
    tools,
    update,
    wrap,
)
from .main import main

try:
    from . import memory  # noqa: F401
except ImportError:
    pass

__all__ = ["main"]
