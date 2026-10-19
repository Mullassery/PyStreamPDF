# Security Policy

## Reporting a Vulnerability

Please report security issues privately by emailing
**mullassery@gmail.com** rather than opening a public GitHub issue.

Include, if possible:
- A description of the vulnerability and its impact
- Steps to reproduce (a minimal PDF/script that triggers it, if applicable)
- The version/commit you tested against

This is a single-maintainer project with no dedicated security team and
no SLA — there is no guaranteed response time. Reports will be
acknowledged and triaged on a best-effort basis.

## Supported Versions

Only the latest release on PyPI / the `main` branch is supported. There is
no backport policy for older versions.

## Known Security-Relevant Behavior (read this before relying on it)

This section documents what has actually been verified in this codebase,
not aspirational security posture.

- **Encryption/permission detection** (`pystreampdf._core.PyPdfDocument`):
  backed by PDFium's real document security APIs
  (`is_encrypted()`, `permissions()`, `open_with_password()`). A wrong or
  missing password on an encrypted PDF raises an error rather than
  falling back to an unauthenticated parse. Covered by
  `tests/test_security.py` and `core/src/security.rs` unit tests.
- **On-disk cache integrity** (`python/pystreampdf/cache.py`): the L2 disk
  cache is HMAC-SHA256 signed using a key generated on first use and
  stored with owner-only (`0600`) file permissions. A tampered or foreign
  cache file fails signature verification and is discarded before any
  deserialization occurs. Covered by `tests/test_cache.py` and
  `tests/test_security.py`.
- **MCP/DAB connector** (`python/pystreampdf/_mcp_connector.py`): binds to
  `127.0.0.1` by default with no cross-origin access and read-only tool
  behavior. Exposing it beyond localhost requires an explicit
  `allow_remote=True` opt-in **and a non-empty `auth_token`**. In remote
  mode DAB still binds only to `127.0.0.1`; a small stdlib reverse proxy
  binds the requested public `host`/`port`, requires
  `Authorization: Bearer <auth_token>` (constant-time comparison via
  `secrets.compare_digest`), and applies a per-IP token bucket
  (`rate_limit_per_minute`, default 60). Covered by
  `tests/test_mcp_auth.py` against a fake upstream (401/200/429).
  Supplying both `tls_cert` and `tls_key` makes the proxy serve HTTPS
  directly via a stdlib `ssl.SSLContext` (TLS 1.2 minimum, no custom cipher
  list); `tests/test_mcp_tls.py` verifies a self-signed certificate with a
  verifying client and confirms that plaintext HTTP is rejected. Without
  those parameters the default remains plaintext HTTP.
  Setting `client_ca` (which requires `tls_cert`/`tls_key`) enables mutual
  TLS: the proxy loads that CA bundle and sets `ssl.CERT_REQUIRED`, so a
  client without a certificate chaining to one of those CAs fails the TLS
  handshake before any HTTP request is parsed. `tests/test_mcp_tls.py`
  generates a CA plus server and client certificates with `cryptography` and
  asserts that an unauthenticated client is rejected while a client signed by
  the CA succeeds.
  Request bodies larger than `max_body_bytes` (default 10 MiB) are rejected
  with `413` before forwarding. The limit is enforced from
  `Content-Length`; chunked request bodies are rejected with `501`, so the
  proxy does not buffer an unbounded body. Request and response bodies are
  streamed in chunks instead of being fully buffered.
  The proxy emits a basic access log through the
  `pystreampdf._mcp_connector.access` logger containing only method, path
  (query string stripped), status, and remote address. It never logs
  `Authorization` headers, tokens, or request bodies. Applications must
  configure logging levels/destinations themselves; by default the access
  logger follows normal Python logging rules and may be silent.
  **The built-in token/TLS boundary is not a hardened reverse proxy.** Rate
  limit buckets are in-memory, per proxy process, and reset on restart; they
  are not shared across workers or hosts, so a restart briefly restores full
  capacity and horizontal replicas each get their own bucket. TLS certificate
  rotation, structured/centralized access logs, and denial-of-service
  hardening are left to the caller. For exposure to untrusted networks, keep
  a real reverse proxy (with TLS, request-size limits, and logging) in front
  of the connector. Loopback-only mode is unchanged and does not require a
  token.
- **Untrusted PDF input**: this library parses arbitrary PDF files via
  PDFium (a large, C++, memory-unsafe parser embedded via FFI). PDFium has
  had real historical CVEs. This project does not sandbox PDF parsing
  (e.g. no seccomp/process isolation) — if you process PDFs from untrusted
  sources, treat the parsing step as running attacker-influenced native
  code, and isolate it accordingly (separate process/container) rather
  than assuming PyStreamPDF does this for you.
- **Dependency scanning**: `.github/workflows/audit.yml` runs `cargo
  audit` and `pip-audit` on push/PR to `main` and weekly. As of this
  writing that workflow has not been exercised in CI (added in this same
  change) — treat it as unverified until you see it pass on a real GitHub
  Actions run.

## Not Covered / Explicitly Out of Scope

- Denial-of-service via pathological PDFs (e.g. zip-bomb-style nested
  objects, extremely deep structure trees) has not been fuzz-tested here.
- No sandboxing of the native PDFium/Rust extension is provided or
  planned as part of this package.
