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


def _write_private_key(path, key):
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def _issue_certificate(
    subject_cn,
    public_key,
    issuer_name,
    signing_key,
    *,
    ca=False,
    server=False,
    client=False,
):
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_cn)]))
        .issuer_name(issuer_name)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
    )
    if ca:
        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
    if server:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        ).add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
    if client:
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
    return builder.sign(signing_key, hashes.SHA256())


@pytest.fixture
def mutual_tls_certs(tmp_path):
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PyStreamPDF Test CA")])
    ca_cert = _issue_certificate(
        "PyStreamPDF Test CA", ca_key.public_key(), ca_name, ca_key, ca=True
    )

    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_cert = _issue_certificate(
        "127.0.0.1", server_key.public_key(), ca_name, ca_key, server=True
    )

    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_cert = _issue_certificate(
        "test-client", client_key.public_key(), ca_name, ca_key, client=True
    )

    paths = {
        "ca": tmp_path / "ca.pem",
        "server_cert": tmp_path / "server-cert.pem",
        "server_key": tmp_path / "server-key.pem",
        "client_cert": tmp_path / "client-cert.pem",
        "client_key": tmp_path / "client-key.pem",
    }
    paths["ca"].write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    paths["server_cert"].write_bytes(server_cert.public_bytes(serialization.Encoding.PEM))
    _write_private_key(paths["server_key"], server_key)
    paths["client_cert"].write_bytes(client_cert.public_bytes(serialization.Encoding.PEM))
    _write_private_key(paths["client_key"], client_key)
    return paths


@pytest.fixture
def mtls_proxy(upstream_port, mutual_tls_certs):
    instance = _AuthReverseProxy(
        auth_token=TOKEN,
        upstream_port=upstream_port,
        listen_host="127.0.0.1",
        listen_port=0,
        tls_cert=str(mutual_tls_certs["server_cert"]),
        tls_key=str(mutual_tls_certs["server_key"]),
        client_ca=str(mutual_tls_certs["ca"]),
    )
    instance.start()
    try:
        yield instance
    finally:
        instance.stop()


def _mtls_client_context(mutual_tls_certs):
    context = ssl.create_default_context(cafile=str(mutual_tls_certs["ca"]))
    return context


def test_mtls_rejects_client_without_certificate(mtls_proxy, mutual_tls_certs):
    context = _mtls_client_context(mutual_tls_certs)
    connection = http.client.HTTPSConnection(
        "127.0.0.1", mtls_proxy.port, timeout=5, context=context
    )
    try:
        with pytest.raises((ssl.SSLError, OSError, http.client.HTTPException)):
            connection.request("GET", "/mcp", headers={"Authorization": f"Bearer {TOKEN}"})
            connection.getresponse()
    finally:
        connection.close()


def test_mtls_accepts_client_with_certificate(mtls_proxy, mutual_tls_certs):
    context = _mtls_client_context(mutual_tls_certs)
    context.load_cert_chain(
        certfile=str(mutual_tls_certs["client_cert"]),
        keyfile=str(mutual_tls_certs["client_key"]),
    )
    connection = http.client.HTTPSConnection(
        "127.0.0.1", mtls_proxy.port, timeout=5, context=context
    )
    try:
        connection.request("GET", "/mcp", headers={"Authorization": f"Bearer {TOKEN}"})
        response = connection.getresponse()
        assert response.status == 200
        assert response.read() == b"upstream-ok"
    finally:
        connection.close()


def test_client_ca_requires_tls_cert_and_key(upstream_port, mutual_tls_certs):
    with pytest.raises(ValueError, match="client_ca requires tls_cert and tls_key"):
        _AuthReverseProxy(
            auth_token=TOKEN,
            upstream_port=upstream_port,
            client_ca=str(mutual_tls_certs["ca"]),
        )
