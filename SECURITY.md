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
  `allow_remote=True` opt-in. **The connector has no authentication of its
  own** — if you opt into `allow_remote=True`, you are responsible for
  putting authentication/network controls in front of it; nothing in this
  package provides that.
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
