from __future__ import annotations

import os
import signal
from pathlib import Path
from typing import Any

from . import claude_code, paths
from .utils import safe_rmtree


def stop_proxy(home: Path | None = None, dry_run: bool = False) -> str:
    pid_file = paths.pid_path(home)
    if not pid_file.exists():
        return "no pid file found"
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except ValueError:
        if not dry_run:
            pid_file.unlink(missing_ok=True)
        return "invalid pid file removed"
    if dry_run:
        return f"would stop pid {pid}"
    try:
        os.kill(pid, signal.SIGTERM)
        pid_file.unlink(missing_ok=True)
        return f"stopped pid {pid}"
    except OSError as exc:
        pid_file.unlink(missing_ok=True)
        return f"could not stop pid {pid}: {exc}"


def uninstall_costguard(purge: bool = False, yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    home = paths.costguard_home()
    claude_home = paths.claude_home()
    stop_message = stop_proxy(home, dry_run=dry_run)
    claude_message = claude_code.restore_or_clean_settings(claude_home, dry_run=dry_run)

    purged = False
    if purge:
        if not yes:
            raise RuntimeError("Purge requires confirmation. Re-run with --yes.")
        if home == Path.home().resolve():
            raise RuntimeError("Refusing to purge HOME.")
        safe_rmtree(home, dry_run=dry_run)
        purged = True

    return {
        "home": home,
        "claude_home": claude_home,
        "stop": stop_message,
        "claude": claude_message,
        "purged": purged,
        "dry_run": dry_run,
    }
