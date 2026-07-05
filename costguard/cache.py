from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config, paths
from .utils import directory_size, safe_rmtree, write_yaml


VALID_MODES = {"disabled", "basic", "semantic"}


def status(home: Path | None = None) -> dict[str, Any]:
    home = home or paths.costguard_home()
    settings = config.load_settings(home)
    mode = settings.get("cache", {}).get("mode", "disabled")
    cache_path = paths.vector_cache_dir(home) if mode == "semantic" else paths.cache_dir(home)
    entries = 0
    if cache_path.exists():
        entries = sum(1 for child in cache_path.rglob("*") if child.is_file())
    return {
        "mode": mode,
        "path": cache_path,
        "entries": entries,
        "size_bytes": directory_size(cache_path),
    }


def enable(mode: str, home: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    if mode not in {"basic", "semantic"}:
        raise ValueError("Cache mode must be basic or semantic.")
    home = home or paths.costguard_home()
    settings = config.load_settings(home)
    settings.setdefault("cache", {})["mode"] = mode
    config.save_settings(settings, home, dry_run=dry_run)
    path = paths.vector_cache_dir(home) if mode == "semantic" else paths.cache_dir(home)
    if not dry_run:
        path.mkdir(parents=True, exist_ok=True)
        index = path / "index.json"
        if not index.exists():
            index.write_text(json.dumps({"entries": []}, indent=2) + "\n", encoding="utf-8")
    return status(home)


def disable(home: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    home = home or paths.costguard_home()
    settings = config.load_settings(home)
    settings.setdefault("cache", {})["mode"] = "disabled"
    config.save_settings(settings, home, dry_run=dry_run)
    return status(home)


def clear(home: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    home = home or paths.costguard_home()
    safe_rmtree(paths.cache_dir(home), dry_run=dry_run)
    safe_rmtree(paths.vector_cache_dir(home), dry_run=dry_run)
    if not dry_run:
        paths.cache_dir(home).mkdir(parents=True, exist_ok=True)
        paths.vector_cache_dir(home).mkdir(parents=True, exist_ok=True)
    return status(home)
