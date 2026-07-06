from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from typing import Any

import httpx

from costguard import config, paths, proxy
from costguard.install import setup_costguard
from costguard.sqlite_store import usage_summary


def _anthropic_request(home, payload: dict[str, Any], monkeypatch) -> tuple[int, dict[str, Any], dict[str, Any]]:
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any], headers: dict[str, str], timeout: int) -> httpx.Response:
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            json={
                "id": "msg_mock",
                "type": "message",
                "role": "assistant",
                "model": json["model"],
                "content": [{"type": "text", "text": "OK"}],
            },
        )

    monkeypatch.setattr(proxy.httpx, "post", fake_post)
    server = ThreadingHTTPServer(("127.0.0.1", 0), proxy.CostGuardHandler)
    server.costguard_home = home  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request(
            "POST",
            "/v1/messages",
            body=json.dumps(payload),
            headers={
                "x-api-key": "sk-costguard-local",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        response = connection.getresponse()
        response_body = response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    return response.status, json.loads(response_body), captured


def test_anthropic_compatible_messages_proxy_routes_and_records_usage(isolated_env, monkeypatch):
    home = isolated_env["home"]
    setup_costguard(
        tool="claude-code",
        non_interactive=True,
        anthropic_upstream_base_url="http://anthropic-upstream.example/v1",
        anthropic_model_cheap="real-haiku",
        anthropic_model_standard="real-sonnet",
        anthropic_model_strong="real-opus",
    )
    monkeypatch.setenv("ANTHROPIC_UPSTREAM_API_KEY", "test-anthropic-key")
    config.set_active_model("cheap", home)

    status, body, captured = _anthropic_request(
        home,
        {
            "model": "cg-active",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "Say OK"}],
        },
        monkeypatch,
    )

    assert status == 200
    assert body["model"] == "real-haiku"
    assert captured["url"] == "http://anthropic-upstream.example/v1/messages"
    assert captured["json"]["model"] == "real-haiku"
    assert captured["headers"]["x-api-key"] == "test-anthropic-key"
    assert captured["headers"]["anthropic-version"] == "2023-06-01"
    summary = usage_summary("today", paths.db_path(home))
    assert summary["requests"] == 1
    assert summary["top_model"] == "cg-cheap"
