from __future__ import annotations


CLINE_CONFIG_TEXT = """Provider: OpenAI Compatible
Base URL: http://127.0.0.1:4040/v1
API Key: sk-costguard-local
Model ID: cg-active
Fixed Model IDs: cg-cheap, cg-standard, cg-strong
"""

CLINE_STEPS = [
    "Open Cline settings.",
    "Select OpenAI Compatible.",
    "Paste Base URL.",
    "Paste API Key.",
    "Set Model ID to cg-active for dynamic routing, or to a fixed cg-* alias.",
    "Save.",
    "Test a short request.",
]


def config_text(include_steps: bool = True) -> str:
    if not include_steps:
        return CLINE_CONFIG_TEXT
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(CLINE_STEPS, start=1))
    return f"{CLINE_CONFIG_TEXT}\n{steps}\n"
