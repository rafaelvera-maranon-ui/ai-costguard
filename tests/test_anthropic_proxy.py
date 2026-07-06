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


def _anthropic_request(
    home,
    payload: dict[str, Any],
    monkeypatch,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any], dict[str, Any]]:
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
        headers = {
            "x-api-key": "sk-costguard-local",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        connection.request(
            "POST",
            "/v1/messages",
            body=json.dumps(payload),
            headers=headers,
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


def test_anthropic_proxy_forwards_claude_code_headers_and_configurable_auth(isolated_env, monkeypatch):
    home = isolated_env["home"]
    setup_costguard(
        tool="claude-code",
        non_interactive=True,
        anthropic_upstream_base_url="http://anthropic-upstream.example/v1",
        anthropic_model_standard="real-sonnet",
    )
    monkeypatch.setenv("ANTHROPIC_UPSTREAM_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("ANTHROPIC_UPSTREAM_AUTH_HEADER", "Authorization")
    monkeypatch.setenv("ANTHROPIC_UPSTREAM_AUTH_SCHEME", "Bearer")

    status, _body, captured = _anthropic_request(
        home,
        {
            "model": "cg-standard",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "Say OK"}],
        },
        monkeypatch,
        extra_headers={
            "anthropic-beta": "test-beta",
            "x-claude-code-session-id": "session-1",
        },
    )

    assert status == 200
    assert captured["headers"]["Authorization"] == "Bearer test-anthropic-key"
    assert captured["headers"]["anthropic-beta"] == "test-beta"
    assert captured["headers"]["x-claude-code-session-id"] == "session-1"


def test_anthropic_proxy_streams_sse_and_records_usage(isolated_env, monkeypatch):
    home = isolated_env["home"]
    setup_costguard(
        tool="claude-code",
        non_interactive=True,
        anthropic_upstream_base_url="http://anthropic-upstream.example/v1",
        anthropic_model_standard="real-sonnet",
    )
    monkeypatch.setenv("ANTHROPIC_UPSTREAM_API_KEY", "test-anthropic-key")
    captured: dict[str, Any] = {}

    class FakeStreamResponse:
        status_code = 200
        headers = httpx.Headers({"content-type": "text/event-stream"})

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def iter_bytes(self):
            yield b"event: message_start\n"
            yield b"data: {\"type\":\"message_start\"}\n\n"

    def fake_stream(method: str, url: str, json: dict[str, Any], headers: dict[str, str], timeout: int):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeStreamResponse()

    monkeypatch.setattr(proxy.httpx, "stream", fake_stream)
    server = ThreadingHTTPServer(("127.0.0.1", 0), proxy.CostGuardHandler)
    server.costguard_home = home  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request(
            "POST",
            "/v1/messages",
            body=json.dumps(
                {
                    "model": "cg-standard",
                    "stream": True,
                    "max_tokens": 64,
                    "messages": [{"role": "user", "content": "Say OK"}],
                }
            ),
            headers={
                "authorization": "Bearer sk-costguard-local",
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

    assert response.status == 200
    assert response.getheader("content-type") == "text/event-stream"
    assert b"message_start" in response_body
    assert captured["method"] == "POST"
    assert captured["url"] == "http://anthropic-upstream.example/v1/messages"
    assert captured["json"]["model"] == "real-sonnet"
    summary = usage_summary("today", paths.db_path(home))
    assert summary["requests"] == 1
    assert summary["top_model"] == "cg-standard"


def test_proxy_exposes_local_model_alias_catalog(isolated_env):
    setup_costguard(tool="claude-code", non_interactive=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), proxy.CostGuardHandler)
    server.costguard_home = isolated_env["home"]  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/v1/models", headers={"authorization": "Bearer sk-costguard-local"})
        response = connection.getresponse()
        response_body = response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    payload = json.loads(response_body)
    assert [item["id"] for item in payload["data"]] == ["cg-active", "cg-cheap", "cg-standard", "cg-strong"]
