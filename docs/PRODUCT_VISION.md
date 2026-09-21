# PyStreamPDF: Product Vision

## Mission

Extract only the relevant parts of a PDF so you send less to an LLM.
PyStreamPDF combines a Rust/PDFium-backed core for real PDF parsing with a
Python layer for semantic chunking, token-budget-aware caching, and OCR/
validation.

## Honest status (read this first)

Earlier versions of this document described PyStreamPDF as a component of
an "MCP 2.0 Platform" (207 tools across 18 projects, port 8780, specific
adoption/uptime targets). None of that is verifiable from this repo — it's
been dropped from this rewrite in favor of what the code and tests here
actually demonstrate. See README.md's "Known Issues" section for the fuller
history of retracted claims (a `Document`/`.extract_relevant()` API that
never existed, unmeasured "70%/10-50x" token-savings numbers, weeks of red
CI from infra bugs).

## What's real and working today (v2.3.0)

- **Token budget system** — `python/pystreampdf/token_budget.py`
  (`TokenBudgetConfig`, `BudgetRule`): keyword/field-based multiplier rules
  scaling allocation within a fixed 500–1000 token range. Tested in
  `tests/test_token_budget.py`.
- **Semantic chunking** — `python/pystreampdf/extraction.py`
  (`SemanticChunker`): splits text into token-aware chunks by element type
  rather than naive word-count splitting. See `tests/test_extraction.py`
  and the runnable `examples/token_budget_and_cache_example.py`.
- **Dual-tier cache** — `python/pystreampdf/cache.py` (`PDFCache`): L1
  memory + L2 disk, HMAC-SHA256-signed on disk with owner-only (0600)
  permissions; a tampered cache file fails verification before any
  deserialization. Covered by `tests/test_cache.py` and
  `tests/test_security.py`.
- **Real PDF security handling** — `pystreampdf._core.PyPdfDocument` is
  backed by PDFium's actual encryption/permission APIs
  (`is_encrypted()`, `permissions()`, `open_with_password()`). A wrong or
  missing password fails closed instead of falling back to an
  unauthenticated parse — this replaced a stub implementation (commit
  `3580f80`).
- **OCR and validation pipelines** — `ocr/manager.py`,
  `ocr/providers/{tesseract,paddle}.py`, and
  `validation/{layout,table,text,scorer}.py` are real implementations with
  dedicated test coverage, not placeholders.
- **CI actually runs the test suite** — `.github/workflows/ci.yml` runs
  `cargo test --release --all-features` and `pytest tests/` across Python
  3.10/3.11/3.12 on every push/PR. The last confirmed-green CI run (linked
  from README.md) reported `pytest`: 557 passed / 2 skipped and
  `cargo test`: 23 passed / 0 failed.
- **MCP tool handlers now call real code** — `_mcp_tools.py` /
  `_mcp_connector.py` were wired to the real extraction/OCR/validation
  implementations in commit `39f7c8c`. This is a recent change; it
  replaced handlers that previously returned hardcoded fixture data.

## What's partial, scaffolding, or unverified

- **No committed token-savings benchmark.** Earlier "70% reduction" /
  "10-50x" claims were never backed by a checked-in benchmark and have
  been retracted in README.md. Actual savings depend on the caller's
  documents and how narrowly queries are scoped.
- **Narrow wheel coverage.** Only a macOS arm64 wheel is published to
  PyPI. A source distribution ships as of 2.3.0, so other platforms build
  from source, but that still needs a local Rust toolchain and a
  discoverable `libpdfium`.
- **No realistic OCR/layout test fixtures yet.** The OCR and
  table-validation code is real and unit-tested, but `tests/` only
  contains synthetic single-glyph images and mocks — no true multi-column
  layout or realistic scanned-document fixtures.
- **Cross-project integration is asserted, not demonstrated.** Nothing in
  this repo imports from or is imported by StatGuardian,
  PyInferenceManager, or PyStreamMCP. If those integrations are a real
  goal, they should be verified against those repos' code before being
  called dependencies here.
- **The MCP handler rewire (`39f7c8c`) is new** and so far only
  unit-tested — it hasn't accumulated real invocation history yet.

## Realistic near-term roadmap

1. Build Linux (manylinux) and, ideally, Windows wheels in CI so
   `pip install pystreampdf` doesn't require a local Rust toolchain +
   PDFium outside macOS arm64.
2. Add real multi-column-layout and scanned-document test fixtures for the
   existing OCR/validation code, replacing the current synthetic
   single-glyph mocks.
3. Exercise the rewired MCP handlers (`39f7c8c`) with integration-style
   tests that go through the MCP/DAB connector path, not just direct
   function calls.
4. If a token-savings number is ever worth publishing, measure it and
   check the benchmark script into the repo rather than restating a
   percentage in prose — until then, point users at
   `examples/token_budget_and_cache_example.py` to measure their own case.

## What this document is not claiming

No specific token-savings percentage, no adoption/uptime/SLA figures, no
enterprise or multi-tenancy roadmap for this single Python package — none
of those are backed by anything in this repo.

---

**Status:** See docs/ROADMAP.md and README.md's "Known Issues" for the
current itemized state of what works, what's partial, and what's broken.
**Last verified:** 2026-09-06 against commit `5c3a6de` (HEAD).
