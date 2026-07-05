from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import yaml


def parse_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def ensure_dir(path: Path, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text_if_changed(path: Path, content: str, dry_run: bool = False) -> bool:
    if dry_run:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def read_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if data is None else data


def write_yaml(path: Path, payload: Any, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def copy_file(src: Path, dst: Path, dry_run: bool = False, overwrite: bool = False) -> bool:
    if dst.exists() and not overwrite:
        return False
    if dry_run:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True


def append_jsonl(path: Path, payload: dict[str, Any], dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def make_executable(path: Path) -> None:
    if os.name == "nt" or not path.exists():
        return
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def safe_rmtree(path: Path, dry_run: bool = False) -> None:
    if dry_run or not path.exists():
        return
    shutil.rmtree(path)
