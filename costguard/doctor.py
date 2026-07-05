from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import httpx

from . import config, paths


@dataclass(frozen=True)
class Check:
    level: str
    name: str
    detail: str


def _exists(path: Path, name: str, required: bool = True) -> Check:
    if path.exists():
        return Check("OK", name, str(path))
    return Check("ERROR" if required else "WARN", name, f"missing: {path}")


def run_checks(home: Path | None = None, claude_home: Path | None = None) -> list[Check]:
    home = home or paths.costguard_home()
    claude_home = claude_home or paths.claude_home()
    env = config.load_env(home)
    settings = config.load_settings(home)
    checks: list[Check] = [
        _exists(home, "Cost Guard home"),
        _exists(paths.env_path(home), ".env"),
        _exists(paths.settings_path(home), "settings.yaml"),
        _exists(paths.db_path(home), "SQLite database"),
        _exists(paths.rules_dir(home) / "default.yaml", "default rules"),
        _exists(paths.rules_dir(home) / "user.yaml", "user rules"),
        _exists(paths.hooks_dir(home) / "pre_tool_use.py", "pre hook"),
        _exists(paths.hooks_dir(home) / "post_tool_use.py", "post hook"),
    ]

    for command in ("safe-grep", "short-diff", "summarize-log", "test-failures-only"):
        command_path = paths.bin_dir(home) / command
        if command_path.exists() and (os.name == "nt" or os.access(command_path, os.X_OK)):
            checks.append(Check("OK", f"safe command {command}", str(command_path)))
        elif command_path.exists():
            checks.append(Check("WARN", f"safe command {command}", "not executable"))
        else:
            checks.append(Check("ERROR", f"safe command {command}", f"missing: {command_path}"))

    tools = settings.get("tools", {})
    if tools.get("claude_code"):
        checks.append(_exists(paths.claude_settings_path(claude_home), "Claude Code settings", required=False))
    if tools.get("cline"):
        checks.append(Check("OK", "Cline config", "run costguard cline-config and paste it in Cline"))

    if env.get("OPENAI_UPSTREAM_BASE_URL") or not tools.get("cline"):
        checks.append(Check("OK", "OpenAI upstream", env.get("OPENAI_UPSTREAM_BASE_URL", "not required")))
    else:
        checks.append(Check("WARN", "OpenAI upstream", "OPENAI_UPSTREAM_BASE_URL is empty"))

    if env.get("ANTHROPIC_UPSTREAM_BASE_URL") or not tools.get("claude_code"):
        checks.append(Check("OK", "Anthropic upstream", env.get("ANTHROPIC_UPSTREAM_BASE_URL", "not required")))
    else:
        checks.append(Check("WARN", "Anthropic upstream", "ANTHROPIC_UPSTREAM_BASE_URL is empty"))

    if env.get("COSTGUARD_PRICING_URL"):
        if paths.pricing_path(home).exists():
            checks.append(Check("OK", "Pricing catalog", str(paths.pricing_path(home))))
        else:
            checks.append(Check("WARN", "Pricing catalog", "run costguard pricing refresh"))

    budget = settings.get("budget", {})
    if budget.get("daily") and budget.get("monthly"):
        checks.append(Check("OK", "Budget", f"daily={budget.get('daily')} monthly={budget.get('monthly')} mode={budget.get('mode')}"))
    else:
        checks.append(Check("WARN", "Budget", "daily or monthly budget is missing"))

    host = env.get("COSTGUARD_HOST", "127.0.0.1")
    port = env.get("COSTGUARD_PORT", "4040")
    try:
        response = httpx.get(f"http://{host}:{port}/health", timeout=0.4)
        if response.status_code == 200:
            checks.append(Check("OK", "Proxy health", "responding"))
        else:
            checks.append(Check("WARN", "Proxy health", f"status {response.status_code}"))
    except httpx.HTTPError:
        checks.append(Check("WARN", "Proxy health", "not running"))

    return checks


def has_errors(checks: Iterable[Check]) -> bool:
    return any(check.level == "ERROR" for check in checks)
