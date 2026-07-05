# AI Cost Guard

AI Cost Guard is a local-first AI gateway/middleware for developers using coding agents in VS Code, mainly Cline and Claude Code. It sits between the local agent and your configured upstream model provider, applying budget checks, rule-based command guardrails, output limits, model aliases, and SQLite usage accounting.

It is not a full agent, model provider, cloud service, or VS Code extension. The shipped package is a small CLI plus a localhost proxy, editable rules, Claude Code hooks, Cline configuration text, and local storage under `COSTGUARD_HOME`.

```text
VS Code
  Cline       -> http://127.0.0.1:4040/v1 -> Cost Guard -> OpenAI-compatible upstream
  Claude Code -> http://127.0.0.1:4040    -> Cost Guard -> Anthropic-compatible upstream
```

## Solution Components

- CLI: `costguard setup`, `doctor`, `status`, `rules`, `budget`, `usage`, `cache`, `headroom`, and `uninstall`.
- Local proxy: localhost HTTP gateway for OpenAI-compatible Cline traffic and Anthropic-compatible Claude Code traffic.
- Rules: editable YAML files for blocked paths, blocked commands, command rewrites, log handling, and output limits.
- Hooks: Claude Code `PreToolUse` and `PostToolUse` commands that block risky access and reduce noisy tool output.
- Safe commands: small helper scripts such as `short-diff`, `safe-grep`, `summarize-log`, and `test-failures-only`.
- SQLite store: local `costguard.db` for usage metadata, budget state, and audit events.
- Config files: `.env` and `config/settings.yaml` under `COSTGUARD_HOME`.
- Docs: runbook, architecture notes, security notes, and troubleshooting guide.

## What It Does

- Runs a localhost proxy on `127.0.0.1:4040`.
- Supports Cline via OpenAI-compatible `/v1/chat/completions`.
- Supports Claude Code via Anthropic-compatible `/v1/messages`.
- Maps model aliases: `cg-cheap`, `cg-standard`, `cg-strong`, `cg-sonnet`.
- Enforces daily/monthly budgets with `warn`, `block-premium`, or `block-all`.
- Blocks secret-like paths and commands such as `cat .env`.
- Rewrites noisy commands such as full `git diff` and `find .`.
- Logs usage metadata to local SQLite without prompts or responses by default.
- Installs reversible Claude Code hooks and safe commands.

## What It Does Not Do

- It does not replace Cline, Claude Code, or your corporate GenAI backends.
- It does not require Docker, Kubernetes, Postgres, or a cloud dashboard.
- It does not expose the proxy outside localhost unless you explicitly choose another host.
- It does not modify project repos unless you run `costguard attach`.
- It does not store real API keys in Git.

## Install

From a GitHub repo:

```bash
pipx install git+https://github.com/<user-or-org>/ai-costguard.git
```

For local development:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Quickstart

```bash
costguard setup --tool both --daily-budget 5 --monthly-budget 100 --budget-mode warn --non-interactive
costguard doctor
costguard start
costguard cline-config
```

Then configure upstream endpoints and model names in:

```text
~/.costguard/.env
```

Set `COSTGUARD_HOME` and `COSTGUARD_CLAUDE_HOME` before setup if you want all files somewhere else. This is recommended for tests, demos, and shared internal validation.

## Cline Configuration

Run:

```bash
costguard cline-config
```

Paste the printed values into Cline:

```text
Provider: OpenAI Compatible
Base URL: http://127.0.0.1:4040/v1
API Key: sk-costguard-local
Model ID: cg-standard
```

## Useful Commands

```bash
costguard status
costguard doctor
costguard use cheap|standard|strong|sonnet
costguard budget status
costguard budget set --daily 5 --monthly 100
costguard budget mode warn|block-premium|block-all
costguard rules test "cat .env"
costguard rules test "git diff"
costguard usage today
costguard cache status
costguard headroom status
costguard uninstall
```

## Safe Local Development

Use isolated paths so setup and uninstall never touch your real home configuration:

```powershell
$env:COSTGUARD_HOME = "$(Get-Location)\.tmp\costguard"
$env:COSTGUARD_CLAUDE_HOME = "$(Get-Location)\.tmp\claude"
costguard setup --tool both --daily-budget 5 --monthly-budget 100 --budget-mode warn --non-interactive
costguard doctor
costguard rules test "cat .env"
costguard uninstall --yes
```

## Documentation

- `docs/RUNBOOK.md`: step-by-step operating guide.
- `docs/ARCHITECTURE.md`: local proxy architecture and data flow.
- `docs/SECURITY.md`: security model and local data handling.
- `docs/TROUBLESHOOTING.md`: common failures and fixes.

## License

MIT. See `LICENSE`.
