"""Tests for the remote MCP auth proxy (C1).

These tests exercise the stdlib bearer-token/rate-limit proxy against a tiny
local fake upstream, so they do not require DAB or any network access.
"""

from __future__ import annotations

import http.client
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pystreampdf._mcp_connector import (
    PDFProcessor,
    _AuthReverseProxy,
    _MCPPDFConnector,
    _TokenBucket,
)

TOKEN = "test-bearer-token-0123456789"


class _FakeUpstreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/large":
            body = b"x" * (1024 * 1024)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/no-length":
            body = b"close-delimited-body"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True
            return

        body = b"upstream-ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@pytest.fixture
def upstream_port():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeUpstreamHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def proxy(upstream_port):
    instance = _AuthReverseProxy(
        auth_token=TOKEN,
        upstream_port=upstream_port,
        listen_host="127.0.0.1",
        listen_port=0,
        rate_limit_per_minute=60,
    )
    instance.start()
    try:
        yield instance
    finally:
        instance.stop()


def _request(port, authorization=None, *, path="/mcp", method="GET", body=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {} if authorization is None else {"Authorization": authorization}
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, response.read(), dict(response.getheaders())
    finally:
        connection.close()


def test_missing_authorization_returns_401(proxy):
    status, body, _ = _request(proxy.port)
    assert status == 401
    assert b"unauthorized" in body


@pytest.mark.parametrize(
    "authorization",
    [
        "Bearer wrong-token",
        f"Basic {TOKEN}",
        TOKEN,
        "Bearer ",
    ],
)
def test_invalid_authorization_returns_401(proxy, authorization):
    status, _, _ = _request(proxy.port, authorization)
    assert status == 401


def test_valid_bearer_token_proxies_to_upstream(proxy):
    status, body, headers = _request(proxy.port, f"Bearer {TOKEN}")
    assert status == 200
    assert body == b"upstream-ok"
    assert headers["Content-Type"] == "text/plain"


def test_large_request_body_is_streamed_through_proxy(proxy):
    payload = b"a" * (1024 * 1024)
    status, body, _ = _request(
        proxy.port,
        f"Bearer {TOKEN}",
        path="/echo",
        method="POST",
        body=payload,
    )
    assert status == 200
    assert body == payload


def test_large_response_body_is_relayed(proxy):
    status, body, headers = _request(proxy.port, f"Bearer {TOKEN}", path="/large")
    assert status == 200
    assert body == b"x" * (1024 * 1024)
    assert headers["Content-Length"] == str(len(body))


def test_response_without_content_length_is_close_delimited(proxy):
    status, body, headers = _request(proxy.port, f"Bearer {TOKEN}", path="/no-length")
    assert status == 200
    assert body == b"close-delimited-body"
    assert "Content-Length" not in headers
    assert headers["Connection"] == "close"


def test_request_body_over_configured_limit_is_rejected(upstream_port):
    limited = _AuthReverseProxy(
        auth_token=TOKEN,
        upstream_port=upstream_port,
        listen_host="127.0.0.1",
        listen_port=0,
        max_body_bytes=16,
    )
    limited.start()
    try:
        status, body, _ = _request(
            limited.port,
            f"Bearer {TOKEN}",
            path="/echo",
            method="POST",
            body=b"a" * 32,
        )
        assert status == 413
        assert b"request body too large" in body

        status, body, _ = _request(
            limited.port,
            f"Bearer {TOKEN}",
            path="/echo",
            method="POST",
            body=b"a" * 8,
        )
        assert status == 200
        assert body == b"a" * 8
    finally:
        limited.stop()


def test_invalid_max_body_bytes_is_rejected(upstream_port):
    for invalid in (0, -1, True, 1.5, "1024"):
        with pytest.raises(ValueError, match="max_body_bytes"):
            _AuthReverseProxy(
                auth_token=TOKEN,
                upstream_port=upstream_port,
                max_body_bytes=invalid,
            )


def test_access_log_has_method_path_status_remote_without_secrets(proxy, caplog):
    with caplog.at_level(logging.INFO, logger="pystreampdf._mcp_connector.access"):
        _request(proxy.port, f"Bearer {TOKEN}", path=f"/mcp?token={TOKEN}")
        _request(proxy.port)

    access_records = [
        record for record in caplog.records if record.name == "pystreampdf._mcp_connector.access"
    ]
    messages = [record.getMessage() for record in access_records]
    assert any("GET /mcp 200 127.0.0.1" in message for message in messages)
    assert any("GET /mcp 401 127.0.0.1" in message for message in messages)
    assert all(TOKEN not in message for message in messages)
    assert all("Authorization" not in message for message in messages)


def test_rate_limit_returns_429_per_ip_bucket(upstream_port):
    limited = _AuthReverseProxy(
        auth_token=TOKEN,
        upstream_port=upstream_port,
        listen_host="127.0.0.1",
        listen_port=0,
        rate_limit_per_minute=2,
    )
    limited.start()
    try:
        assert _request(limited.port, f"Bearer {TOKEN}")[0] == 200
        assert _request(limited.port, f"Bearer {TOKEN}")[0] == 200
        status, body, headers = _request(limited.port, f"Bearer {TOKEN}")
        assert status == 429
        assert b"rate limit exceeded" in body
        assert int(headers["Retry-After"]) >= 1
    finally:
        limited.stop()


def test_token_buckets_are_isolated_per_key():
    limiter = _TokenBucket(1)
    assert limiter.consume("10.0.0.1")[0] is True
    assert limiter.consume("10.0.0.1")[0] is False
    assert limiter.consume("10.0.0.2")[0] is True


def test_remote_bind_requires_non_empty_token():
    with pytest.raises(ValueError, match="auth_token"):
        _MCPPDFConnector(PDFProcessor(), port=9124, host="0.0.0.0", allow_remote=True)
    with pytest.raises(ValueError, match="auth_token"):
        _MCPPDFConnector(
            PDFProcessor(), port=9124, host="0.0.0.0", allow_remote=True, auth_token="  "
        )
    with pytest.raises(ValueError, match="auth_token"):
        PDFProcessor().start_mcp_connector(host="0.0.0.0", allow_remote=True)


def test_local_connector_needs_no_token_and_starts_no_proxy():
    connector = _MCPPDFConnector(PDFProcessor(), port=9124)
    assert connector.auth_token is None
    assert connector._auth_proxy is None
    assert connector._generate_dab_config({"tool": {}})["runtime"] == {
        "host": "127.0.0.1",
        "port": 9124,
        "cors": {"origins": []},
    }


def test_remote_connector_keeps_dab_on_loopback_and_uses_public_proxy_port():
    connector = _MCPPDFConnector(
        PDFProcessor(),
        port=9124,
        host="0.0.0.0",
        allow_remote=True,
        auth_token=TOKEN,
        rate_limit_per_minute=10,
    )
    config = connector._generate_dab_config({"tool": {}})
    assert config["runtime"]["host"] == "127.0.0.1"
    assert config["runtime"]["port"] != 9124
    assert connector.public_host == "0.0.0.0"
    assert connector.public_port == 9124
    assert connector.rate_limit_per_minute == 10
