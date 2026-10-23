"""MCP Connector for PyStreamPDF - PDF Document Processing"""

import http.client
import http.server
import ipaddress
import json
import logging
import os
import secrets
import socket
import ssl
import subprocess
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)
access_logger = logging.getLogger(f"{__name__}.access")

_STREAM_CHUNK_SIZE = 64 * 1024
_DEFAULT_MAX_BODY_BYTES = 10 * 1024 * 1024

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def _validate_tls_pair(tls_cert: Optional[str], tls_key: Optional[str]) -> None:
    if (tls_cert is None) != (tls_key is None):
        raise ValueError("tls_cert and tls_key must be provided together")


def _validate_client_ca(
    tls_cert: Optional[str], tls_key: Optional[str], client_ca: Optional[str]
) -> None:
    if client_ca is not None and tls_cert is None:
        raise ValueError("client_ca requires tls_cert and tls_key")


def _create_server_ssl_context(
    tls_cert: str, tls_key: str, client_ca: Optional[str] = None
) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=os.fspath(tls_cert), keyfile=os.fspath(tls_key))
    if client_ca is not None:
        # Mutual TLS: the client must present a certificate chaining to a CA
        # in the supplied bundle. The handshake fails otherwise, before any
        # HTTP request is parsed.
        context.load_verify_locations(cafile=os.fspath(client_ca))
        context.verify_mode = ssl.CERT_REQUIRED
    return context


class _LimitedReader:
    """Stream at most ``remaining`` bytes from an underlying request body."""

    def __init__(self, stream, remaining: int):
        self._stream = stream
        self._remaining = remaining

    def read(self, size: int = -1) -> bytes:
        if self._remaining <= 0:
            return b""
        size = self._remaining if size is None or size < 0 else min(size, self._remaining)
        data = self._stream.read(size)
        self._remaining -= len(data)
        return data


class _TokenBucket:
    """Thread-safe per-key token bucket used for per-IP rate limiting."""

    def __init__(self, rate_per_minute: float):
        if isinstance(rate_per_minute, bool) or not isinstance(rate_per_minute, (int, float)):
            raise ValueError("rate_limit_per_minute must be a positive number")
        if rate_per_minute <= 0:
            raise ValueError("rate_limit_per_minute must be greater than zero")
        self.rate_per_minute = float(rate_per_minute)
        self.capacity = float(rate_per_minute)
        self._tokens: dict[str, float] = {}
        self._updated: dict[str, float] = {}
        self._lock = threading.Lock()

    def consume(self, key: str) -> tuple[bool, float]:
        """Consume one token for ``key``.

        Returns ``(allowed, retry_after_seconds)``. ``retry_after_seconds`` is
        zero when the request is allowed.
        """
        now = time.monotonic()
        refill_per_second = self.rate_per_minute / 60.0
        with self._lock:
            tokens = self._tokens.get(key, self.capacity)
            last = self._updated.get(key, now)
            tokens = min(self.capacity, tokens + (now - last) * refill_per_second)
            self._updated[key] = now
            if tokens >= 1.0:
                self._tokens[key] = tokens - 1.0
                return True, 0.0
            self._tokens[key] = tokens
            return False, (1.0 - tokens) / refill_per_second


class _AuthProxyHandler(http.server.BaseHTTPRequestHandler):
    """Bearer-token + rate-limited reverse proxy to the loopback DAB server."""

    protocol_version = "HTTP/1.1"
    server_version = "PyStreamPDFAuthProxy/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("%s - %s", self.address_string(), format % args)

    def _log_access(self) -> None:
        # Basic access log: method/path/status/remote only. Authorization and
        # query strings are deliberately excluded so tokens are never logged.
        status = getattr(self, "_response_status", None)
        path = self.path.split("?", 1)[0]
        access_logger.info(
            "%s %s %s %s",
            self.command,
            path,
            "-" if status is None else status,
            self.client_address[0],
        )

    def _send_json(
        self, status: int, payload: dict[str, Any], extra_headers: Optional[dict] = None
    ):
        body = json.dumps(payload).encode("utf-8")
        self._response_status = status
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.close_connection = True

    def _is_authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        scheme, separator, token = header.partition(" ")
        if not separator or scheme.lower() != "bearer":
            return False
        return secrets.compare_digest(
            token.strip().encode("utf-8"),
            self.server.auth_token.encode("utf-8"),
        )

    def _handle(self) -> None:
        self._response_status = None
        try:
            # Authenticate before rate limiting so unauthenticated callers cannot
            # exhaust another client's bucket or learn whether a token is valid.
            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            allowed, retry_after = self.server.limiter.consume(self.client_address[0])
            if not allowed:
                self._send_json(
                    429,
                    {"error": "rate limit exceeded"},
                    {"Retry-After": str(max(1, int(retry_after + 0.999)))},
                )
                return

            self._forward()
        finally:
            self._log_access()

    def _forward(self) -> None:
        if self.headers.get("Transfer-Encoding"):
            self._send_json(
                501,
                {"error": "chunked request bodies are not supported"},
            )
            return

        length_header = self.headers.get("Content-Length")
        try:
            content_length = int(length_header) if length_header else 0
        except ValueError:
            self._send_json(400, {"error": "invalid Content-Length"})
            return
        if content_length < 0:
            self._send_json(400, {"error": "invalid Content-Length"})
            return
        if content_length > self.server.max_body_bytes:
            self._send_json(413, {"error": "request body too large"})
            return

        # Stream request bodies instead of buffering them in memory. HTTPConnection
        # reads file-like bodies in chunks; _LimitedReader stops at Content-Length
        # so it never consumes a pipelined request or blocks waiting for EOF.
        body = _LimitedReader(self.rfile, content_length) if content_length > 0 else None
        forwarded_headers = {
            name: value
            for name, value in self.headers.items()
            if name.lower() not in _HOP_BY_HOP_HEADERS
            and name.lower() not in {"authorization", "host"}
        }
        forwarded_headers["Host"] = f"{self.server.upstream_host}:{self.server.upstream_port}"
        forwarded_headers["Connection"] = "close"

        connection = http.client.HTTPConnection(
            self.server.upstream_host, self.server.upstream_port, timeout=30
        )
        try:
            try:
                connection.request(self.command, self.path, body=body, headers=forwarded_headers)
                response = connection.getresponse()
            except (OSError, http.client.HTTPException) as exc:
                logger.warning("MCP auth proxy upstream request failed: %s", exc)
                self._send_json(502, {"error": "upstream unavailable"})
                return

            upstream_length = response.getheader("Content-Length")
            self._response_status = response.status
            self.send_response(response.status, response.reason)
            for name, value in response.getheaders():
                if name.lower() not in _HOP_BY_HOP_HEADERS and name.lower() != "content-length":
                    self.send_header(name, value)
            if upstream_length is not None:
                self.send_header("Content-Length", upstream_length)
            self.send_header("Connection", "close")
            self.end_headers()

            if self.command != "HEAD":
                try:
                    while True:
                        # read1 returns whatever is available, so large responses
                        # are relayed incrementally instead of being fully buffered.
                        chunk = response.read1(_STREAM_CHUNK_SIZE)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                except (OSError, http.client.HTTPException) as exc:
                    logger.warning("MCP auth proxy response stream failed: %s", exc)
        finally:
            connection.close()
            self.close_connection = True

    do_GET = _handle
    do_HEAD = _handle
    do_POST = _handle
    do_PUT = _handle
    do_PATCH = _handle
    do_DELETE = _handle
    do_OPTIONS = _handle


class _AuthProxyServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        handler_class,
        *,
        auth_token,
        upstream_host,
        upstream_port,
        limiter,
        max_body_bytes,
        ssl_context=None,
    ):
        self.auth_token = auth_token
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.limiter = limiter
        self.max_body_bytes = max_body_bytes
        self.ssl_context = ssl_context
        super().__init__(server_address, handler_class)

    def server_bind(self):
        super().server_bind()
        if self.ssl_context is not None:
            # Wrap the bound/listening socket; accepted connections then perform
            # the TLS handshake before any HTTP parsing occurs.
            self.socket = self.ssl_context.wrap_socket(self.socket, server_side=True)


class _AuthReverseProxy:
    """Small stdlib reverse proxy that fronts DAB with bearer auth + rate limits."""

    def __init__(
        self,
        auth_token: str,
        upstream_port: int,
        listen_host: str = "127.0.0.1",
        listen_port: int = 0,
        upstream_host: str = "127.0.0.1",
        rate_limit_per_minute: float = 60,
        tls_cert: Optional[str] = None,
        tls_key: Optional[str] = None,
        client_ca: Optional[str] = None,
        max_body_bytes: int = _DEFAULT_MAX_BODY_BYTES,
    ):
        if not isinstance(auth_token, str) or not auth_token.strip():
            raise ValueError("auth_token must be a non-empty string")
        _validate_tls_pair(tls_cert, tls_key)
        _validate_client_ca(tls_cert, tls_key, client_ca)
        if (
            isinstance(max_body_bytes, bool)
            or not isinstance(max_body_bytes, int)
            or max_body_bytes <= 0
        ):
            raise ValueError("max_body_bytes must be a positive integer")
        self.auth_token = auth_token
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.client_ca = client_ca
        self.max_body_bytes = max_body_bytes
        self.limiter = _TokenBucket(rate_limit_per_minute)
        self._server: Optional[_AuthProxyServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def port(self) -> int:
        if self._server is None:
            return self.listen_port
        return self._server.server_address[1]

    @property
    def url(self) -> str:
        host = self.listen_host
        if host in {"0.0.0.0", "::"}:
            host = "127.0.0.1"
        if ":" in host:
            host = f"[{host}]"
        scheme = "https" if self.tls_cert is not None else "http"
        return f"{scheme}://{host}:{self.port}/mcp"

    def start(self) -> str:
        if self._server is not None:
            return self.url
        ssl_context = None
        if self.tls_cert is not None:
            ssl_context = _create_server_ssl_context(self.tls_cert, self.tls_key, self.client_ca)
        server = _AuthProxyServer(
            (self.listen_host, self.listen_port),
            _AuthProxyHandler,
            auth_token=self.auth_token,
            upstream_host=self.upstream_host,
            upstream_port=self.upstream_port,
            limiter=self.limiter,
            max_body_bytes=self.max_body_bytes,
            ssl_context=ssl_context,
        )
        self._server = server
        self._thread = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.05},
            name="pystreampdf-mcp-auth-proxy",
            daemon=True,
        )
        try:
            self._thread.start()
        except Exception:
            server.server_close()
            self._server = None
            self._thread = None
            raise
        logger.info("MCP auth proxy listening on %s", self.url)
        return self.url

    def stop(self) -> None:
        server = self._server
        if server is None:
            return
        server.shutdown()
        server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None


try:
    from statguardian import BaseMCPConnector
except ImportError:

    class BaseMCPConnector(ABC):
        def __init__(
            self,
            project_name: str,
            port: int = 8765,
            host: str = "127.0.0.1",
            allow_remote: bool = False,
            cors_origins: Optional[list] = None,
        ):
            self.project_name = project_name
            self.port = port
            # Secure-by-default: bind to loopback only. Any non-loopback host
            # (e.g. "0.0.0.0") requires an explicit opt-in via
            # `allow_remote=True`. PyStreamPDF's connector additionally
            # requires an auth_token and fronts DAB with a bearer-auth proxy.
            if not allow_remote:
                try:
                    is_loopback = ipaddress.ip_address(host).is_loopback
                except ValueError:
                    is_loopback = host == "localhost"
                if not is_loopback:
                    raise ValueError(
                        "Binding the MCP/DAB connector to a non-loopback host "
                        f"(host={host!r}) requires allow_remote=True. By default the "
                        "connector only binds to 127.0.0.1."
                    )
            self.host = host
            self.allow_remote = allow_remote
            # CORS defaults to no cross-origin access; wildcard origins must be
            # requested explicitly and only take effect when allow_remote=True.
            if cors_origins is None:
                cors_origins = [] if not allow_remote else ["*"]
            self.cors_origins = cors_origins
            self.dab_process: Optional[subprocess.Popen] = None
            self._ready = False

        @abstractmethod
        def get_mcp_tools(self) -> dict[str, Any]:
            pass

        @abstractmethod
        def get_tool_handlers(self) -> Any:
            pass

        def start_mcp_connector(self) -> str:
            logger.info(f"Starting {self.project_name} MCP...")
            try:
                tools = self.get_mcp_tools()
                self.handler = self.get_tool_handlers()
                config = self._generate_dab_config(tools)
                config_path = self._write_temp_config(config)
                self._start_dab_subprocess(config_path)
                self._ready = True
                return f"http://localhost:{self.port}/mcp"
            except Exception as e:
                logger.error(f"Failed: {e}")
                raise

        def stop_mcp_connector(self):
            if self.dab_process:
                try:
                    self.dab_process.terminate()
                    self.dab_process.wait(timeout=5)
                except (subprocess.TimeoutExpired, OSError):
                    pass
                self._ready = False

        def _generate_dab_config(self, tools: dict[str, Any]) -> dict:
            # Secure defaults: loopback-only host, no cross-origin access, and
            # permissions scoped to a "local" role rather than wildcard "*"/"*".
            # Callers that genuinely need remote access or wildcard permissions
            # must opt in explicitly via allow_remote=True / cors_origins=[...].
            permissions_role = "*" if self.allow_remote else "local"
            permissions_actions = ["*"] if self.allow_remote else ["read"]
            return {
                "runtime": {
                    "host": self.host,
                    "port": self.port,
                    "cors": {"origins": self.cors_origins},
                },
                "entities": {
                    k: {
                        "source": k,
                        "permissions": [
                            {"actions": permissions_actions, "roles": [permissions_role]}
                        ],
                    }
                    for k in tools
                },
                "rest": {"enabled": True, "path": "/api"},
                "graphql": {"enabled": True, "path": "/graphql"},
                "mcp": {"enabled": True, "path": "/mcp"},
            }

        def _write_temp_config(self, config: dict) -> str:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config, f)
                return f.name

        def _start_dab_subprocess(self, config_path: str):
            self.dab_process = subprocess.Popen(
                ["dab", "start", "--config", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        def is_ready(self) -> bool:
            return self._ready


class PDFProcessor:
    """PDF document processing with extraction and OCR"""

    def __init__(self):
        self.mcp_connector: Optional[Any] = None

    def start_mcp_connector(
        self,
        port: int = 8780,
        host: str = "127.0.0.1",
        allow_remote: bool = False,
        cors_origins: Optional[list] = None,
        allowed_root: Optional[str] = None,
        auth_token: Optional[str] = None,
        rate_limit_per_minute: Optional[float] = None,
        tls_cert: Optional[str] = None,
        tls_key: Optional[str] = None,
        client_ca: Optional[str] = None,
        max_body_bytes: Optional[int] = None,
    ) -> str:
        """Start the local MCP/DAB connector.

        Binds to 127.0.0.1 with no cross-origin access by default. Pass
        ``allow_remote=True`` (and optionally an explicit ``host`` /
        ``cors_origins``) to expose the connector beyond localhost.

        Remote exposure requires a non-empty ``auth_token``. DAB itself still
        binds to ``127.0.0.1`` on an internal port; a small stdlib reverse
        proxy binds the requested ``host``/``port``, requires
        ``Authorization: Bearer <auth_token>`` on every request, and applies a
        per-IP token bucket (``rate_limit_per_minute``, default 60). With
        ``tls_cert`` and ``tls_key`` the proxy serves HTTPS directly using a
        stdlib ``ssl.SSLContext``; without them traffic is plaintext HTTP and a
        TLS-terminating reverse proxy is still required for untrusted networks.

        ``client_ca`` enables mutual TLS: when set, the proxy requires and
        verifies a client certificate chaining to that CA bundle
        (``ssl.CERT_REQUIRED``). It therefore requires ``tls_cert`` and
        ``tls_key`` too. ``max_body_bytes`` caps accepted request bodies
        (default 10 MiB); larger requests are rejected with ``413``. The proxy
        emits a basic access log (method/path/status/remote) through the
        ``pystreampdf._mcp_connector.access`` logger.

        Loopback-only mode is unchanged: no token is required and no proxy is
        started.

        ``allowed_root`` restricts every MCP tool's ``pdf_path`` to that
        directory (resolved, symlink-aware). Without it, paths are not
        sandboxed; set it whenever the connector is reachable by anything
        other than a trusted local caller.
        """
        self.mcp_connector = _MCPPDFConnector(
            pdf=self,
            port=port,
            host=host,
            allow_remote=allow_remote,
            cors_origins=cors_origins,
            allowed_root=allowed_root,
            auth_token=auth_token,
            rate_limit_per_minute=rate_limit_per_minute,
            tls_cert=tls_cert,
            tls_key=tls_key,
            client_ca=client_ca,
            max_body_bytes=max_body_bytes,
        )
        return self.mcp_connector.start_mcp_connector()

    def stop_mcp_connector(self):
        if self.mcp_connector:
            self.mcp_connector.stop_mcp_connector()


class _MCPPDFConnector(BaseMCPConnector):
    def __init__(
        self,
        pdf: PDFProcessor,
        port: int = 8780,
        host: str = "127.0.0.1",
        allow_remote: bool = False,
        cors_origins: Optional[list] = None,
        allowed_root: Optional[str] = None,
        auth_token: Optional[str] = None,
        rate_limit_per_minute: Optional[float] = None,
        tls_cert: Optional[str] = None,
        tls_key: Optional[str] = None,
        client_ca: Optional[str] = None,
        max_body_bytes: Optional[int] = None,
    ):
        _validate_tls_pair(tls_cert, tls_key)
        _validate_client_ca(tls_cert, tls_key, client_ca)
        if allow_remote and (not isinstance(auth_token, str) or not auth_token.strip()):
            raise ValueError(
                "allow_remote=True requires a non-empty auth_token; the remote "
                "MCP connector is fronted by a bearer-token reverse proxy."
            )
        if rate_limit_per_minute is not None and (
            isinstance(rate_limit_per_minute, bool)
            or not isinstance(rate_limit_per_minute, (int, float))
            or rate_limit_per_minute <= 0
        ):
            raise ValueError("rate_limit_per_minute must be a positive number")
        if max_body_bytes is not None and (
            isinstance(max_body_bytes, bool)
            or not isinstance(max_body_bytes, int)
            or max_body_bytes <= 0
        ):
            raise ValueError("max_body_bytes must be a positive integer")

        super().__init__(
            "PyStreamPDF",
            port=port,
            host=host,
            allow_remote=allow_remote,
            cors_origins=cors_origins,
        )
        self.pdf = pdf
        self.allowed_root = allowed_root
        self.auth_token = auth_token
        self.rate_limit_per_minute = 60 if rate_limit_per_minute is None else rate_limit_per_minute
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.client_ca = client_ca
        self.max_body_bytes = _DEFAULT_MAX_BODY_BYTES if max_body_bytes is None else max_body_bytes
        self.public_host = host
        self.public_port = port
        self._auth_proxy: Optional[_AuthReverseProxy] = None
        if allow_remote:
            # DAB stays on loopback; only the authenticated proxy is public.
            self._dab_host = "127.0.0.1"
            self._dab_port = _find_free_port()
        else:
            self._dab_host = host
            self._dab_port = port

    def get_mcp_tools(self) -> dict[str, Any]:
        from pystreampdf._mcp_tools import PyStreamPDFMCPTools

        return PyStreamPDFMCPTools.get_tools()

    def get_tool_handlers(self) -> Any:
        from pystreampdf._mcp_tools import PyStreamPDFMCPHandler

        return PyStreamPDFMCPHandler(self.pdf, allowed_root=self.allowed_root)

    def _generate_dab_config(self, tools: dict[str, Any]) -> dict:
        config = super()._generate_dab_config(tools)
        if self.allow_remote:
            config["runtime"]["host"] = self._dab_host
            config["runtime"]["port"] = self._dab_port
        return config

    def start_mcp_connector(self) -> str:
        url = super().start_mcp_connector()
        if not self.allow_remote:
            return url

        proxy = _AuthReverseProxy(
            auth_token=self.auth_token,
            upstream_host=self._dab_host,
            upstream_port=self._dab_port,
            listen_host=self.public_host,
            listen_port=self.public_port,
            rate_limit_per_minute=self.rate_limit_per_minute,
            tls_cert=self.tls_cert,
            tls_key=self.tls_key,
            client_ca=self.client_ca,
            max_body_bytes=self.max_body_bytes,
        )
        try:
            proxy.start()
        except Exception:
            super().stop_mcp_connector()
            raise
        self._auth_proxy = proxy
        return proxy.url

    def stop_mcp_connector(self):
        if self._auth_proxy is not None:
            self._auth_proxy.stop()
            self._auth_proxy = None
        super().stop_mcp_connector()
