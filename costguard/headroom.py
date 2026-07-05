from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from . import config, paths


def available() -> bool:
    return importlib.util.find_spec("headroom") is not None


def status(home: Path | None = None) -> dict[str, Any]:
    home = home or paths.costguard_home()
    return {
        "available": available(),
        "enabled": config.headroom_enabled(home),
        "install_hint": 'pip install "ai-costguard[headroom]"',
    }


def enable(home: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    if not available():
        raise RuntimeError('Headroom is not installed. Run: pip install "ai-costguard[headroom]"')
    home = home or paths.costguard_home()
    settings = config.load_settings(home)
    settings.setdefault("headroom", {})["enabled"] = True
    config.save_settings(settings, home, dry_run=dry_run)
    return status(home)


def disable(home: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    home = home or paths.costguard_home()
    settings = config.load_settings(home)
    settings.setdefault("headroom", {})["enabled"] = False
    config.save_settings(settings, home, dry_run=dry_run)
    return status(home)
