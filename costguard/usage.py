from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths
from .sqlite_store import usage_summary


def summary(period: str, home: Path | None = None) -> dict[str, Any]:
    home = home or paths.costguard_home()
    return usage_summary(period, paths.db_path(home))
