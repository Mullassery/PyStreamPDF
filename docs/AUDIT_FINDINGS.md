# Audit findings — 2026-10-26

This file records the current portfolio-audit findings for PyStreamPDF. It is
documentation only; no code or release artifacts were changed. The fuller
evidence report is kept in the portfolio workspace at
`.audit/reports/PyStreamPDF/audit.md`.

## What it is

A PDF intelligence engine for token-efficient retrieval and RAG: PDFium-backed
extraction, semantic chunking, token budgets, validation, OCR, a signed two-tier
cache, and an MCP/DAB tool connector.

## Verified strengths

- Real PDFium encryption/permission handling and PyO3 core.
- Semantic chunking, table/image extraction, citations, validation, and
  structure recovery.
- L1 memory + L2 disk cache: SHA256 content addressing, HMAC-SHA256 signature
  verified before `pickle.loads()`, cache directory `0700`, key `0600`.
- MCP tools now call real extraction/validation code instead of fixtures.
- MCP reverse proxy includes token-bucket limiting, optional TLS, client CA,
  bearer auth, and body limits.
- Security workflow runs `cargo-audit` and `pip-audit`.
- 42 test files and 601 static Python test definitions.

## Verified gaps and user-facing risks

- **Version drift:** source is `2.4.3`; README and roadmap say `2.4.2`.
- **Test-count drift:** README says 600 passed / 4 skipped; roadmap says 557/2;
  architecture says 523.
- **Lint/format debt is not gated:** roadmap documents ~756 ruff findings and 73
  black files; CI does not run either.
- **Pickle cache:** HMAC protects against tampering when the key is separate,
  but the key and cache share a directory and same-user access defeats it.
  A safer serialization would reduce blast radius.
- **MCP reverse proxy is a material security surface** and was recently
  rewired; it has limited real invocation history.
- **OCR quality is unproven:** tests use generated/synthetic fixtures and skip
  when Tesseract is absent.
- **No fuzzing** at the PDFium parsing boundary.
- **Python 3.9 is declared but CI covers only 3.10–3.12.**
- **Benchmark is synthetic** and should not be generalized to all PDFs.
- Documentation still carries stale platform/"MCP 2.0" framing in places.

## Direct positioning

Against Docling, PyMuPDF, Unstructured, Marker, and LlamaParse. The niche is
token-budget-aware chunking plus a real PDFium core and MCP tool surface.

## Ranked next actions

1. P0: unify version and test counts from one verified release command.
2. P0: threat-model the MCP reverse proxy; require secure binds/auth defaults.
3. P1: replace pickle with a schema-based format, or separate the signing key
   and document the residual same-user risk.
4. P1: gate `ruff` and `black` in CI, then burn down or baseline debt.
5. P1: add a realistic scanned/multi-column OCR corpus and thresholds.
6. P1: add fuzz targets for PDF parsing and cache decode.
7. P2: add Python 3.9 to CI or raise `requires-python`.
8. P2: add large-PDF/concurrency benchmarks and structured metrics.

## Do not build

- A full PDF RAG platform or layout-understanding competitor. Docling and
  PyMuPDF already own broad layout/rendering space.

## Evidence gaps / validation needed

- No real scanned-document benchmark.
- No end-to-end RAG quality/savings measurement.
- No fuzzing or malicious-PDF corpus.
- No live MCP proxy traffic test.

## Recommended disposition

Invest narrowly. Fix release truth and cache/proxy security first; the core
extraction and token-budget niche is credible.
