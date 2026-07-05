from __future__ import annotations

import pytest

from costguard import budget, paths, pricing
from costguard.install import setup_costguard
from costguard.utils import write_yaml


def test_parse_catalog_supports_generic_model_prices():
    payload = [
        {
            "provider": "bedrock",
            "name": "anthropic.claude-sonnet-4-6",
            "systemName": "eu.anthropic.claude-sonnet-4-6",
            "inputPrice": 3.3,
            "outputPrice": 16.5,
            "cachedTokenReadPrice": 0.33,
            "cachedTokenCreationPrice": 4.125,
        }
    ]

    parsed = pricing.parse_catalog(payload)

    assert parsed["eu.anthropic.claude-sonnet-4-6"]["input_per_million"] == 3.3
    assert parsed["eu.anthropic.claude-sonnet-4-6"]["output_per_million"] == 16.5
    assert parsed["eu.anthropic.claude-sonnet-4-6"]["cached_read_per_million"] == 0.33
    assert parsed["anthropic.claude-sonnet-4-6"]["input_per_million"] == 3.3


def test_budget_uses_pricing_catalog_for_configured_upstream_model(isolated_env):
    setup_costguard(tool="cline", non_interactive=True)
    home = isolated_env["home"]
    env_file = paths.env_path(home)
    env_file.write_text(
        env_file.read_text(encoding="utf-8") + "OPENAI_MODEL_STANDARD=eu.anthropic.claude-sonnet-4-6\n",
        encoding="utf-8",
    )
    write_yaml(
        paths.pricing_path(home),
        {
            "models": {
                "eu.anthropic.claude-sonnet-4-6": {
                    "input_per_million": 3.3,
                    "output_per_million": 16.5,
                }
            }
        },
    )

    assert budget.estimate_cost("cg-standard", 1000, home, output_tokens=2000) == pytest.approx(0.0363)


def test_budget_falls_back_to_local_estimate_without_pricing_catalog(isolated_env):
    setup_costguard(tool="cline", non_interactive=True)

    assert budget.estimate_cost("cg-standard", 1000, isolated_env["home"]) == 0.001
