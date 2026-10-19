"""Optional TLS coverage for the remote MCP auth proxy (C22).

A throwaway self-signed certificate is generated with ``cryptography``. HTTPS
requests must verify against that certificate, while plaintext HTTP to the TLS
listener must fail its handshake.
"""

from __future__ import annotations

import datetime
import http.client
import ipaddress
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

x509 = pytest.importorskip("cryptography.x509")
from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID  # noqa: E402

from pystreampdf._mcp_connector import (  # noqa: E402
    PDFProcessor,
    _AuthReverseProxy,
    _MCPPDFConnector,
)

TOKEN = "test-bearer-token-tls-0123456789"


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
def tls_cert_pair(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    cert_path = tmp_path / "server-cert.pem"
    key_path = tmp_path / "server-key.pem"
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return cert_path, key_path


@pytest.fixture
def tls_proxy(upstream_port, tls_cert_pair):
    cert_path, key_path = tls_cert_pair
    instance = _AuthReverseProxy(
        auth_token=TOKEN,
        upstream_port=upstream_port,
        listen_host="127.0.0.1",
        listen_port=0,
        rate_limit_per_minute=60,
        tls_cert=str(cert_path),
        tls_key=str(key_path),
    )
    instance.start()
    try:
        yield instance
    finally:
        instance.stop()


def test_https_request_succeeds_with_verifying_client(tls_proxy, tls_cert_pair):
    cert_path, _ = tls_cert_pair
    context = ssl.create_default_context(cafile=str(cert_path))
    connection = http.client.HTTPSConnection(
        "127.0.0.1", tls_proxy.port, timeout=5, context=context
    )
    try:
        connection.request("GET", "/mcp", headers={"Authorization": f"Bearer {TOKEN}"})
        response = connection.getresponse()
        assert response.status == 200
        assert response.read() == b"upstream-ok"
    finally:
        connection.close()


def test_plain_http_to_tls_listener_fails(tls_proxy):
    connection = http.client.HTTPConnection("127.0.0.1", tls_proxy.port, timeout=5)
    try:
        with pytest.raises((OSError, http.client.HTTPException)):
            connection.request("GET", "/mcp", headers={"Authorization": f"Bearer {TOKEN}"})
            connection.getresponse()
    finally:
        connection.close()


def test_tls_url_uses_https_scheme(tls_proxy):
    assert tls_proxy.url.startswith("https://")


def test_tls_requires_cert_and_key_together(upstream_port, tls_cert_pair):
    cert_path, _ = tls_cert_pair
    with pytest.raises(ValueError, match="tls_cert and tls_key"):
        _AuthReverseProxy(
            auth_token=TOKEN,
            upstream_port=upstream_port,
            tls_cert=str(cert_path),
        )
    with pytest.raises(ValueError, match="tls_cert and tls_key"):
        _MCPPDFConnector(
            PDFProcessor(),
            allow_remote=True,
            auth_token=TOKEN,
            host="0.0.0.0",
            tls_key="server-key.pem",
        )
