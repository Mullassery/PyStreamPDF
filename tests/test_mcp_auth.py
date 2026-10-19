"""Tests for the remote MCP auth proxy (C1).

These tests exercise the stdlib bearer-token/rate-limit proxy against a tiny
local fake upstream, so they do not require DAB or any network access.
"""

from __future__ import annotations

import http.client
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
        body = b"upstream-ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
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


def _request(port, authorization=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {} if authorization is None else {"Authorization": authorization}
    try:
        connection.request("GET", "/mcp", headers=headers)
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
