# PyStreamPDF: Roadmap

**Version:** 2.3.0 (current, per `Cargo.toml` / `python/pystreampdf/__init__.py`)
**Last updated:** 2026-09-06

## Honest status (read this first)

Earlier versions of this roadmap (and of `docs/PRODUCT_VISION.md`)
described PyStreamPDF as part of an "MCP 2.0 Platform" spanning 18-19
projects with a fixed port assignment, listed unmeasured adoption/uptime/
SLA targets, and set hard calendar deadlines (Q3 2026, Q4 2026, 2027) for
speculative features like "ML-based multiplier strategies" and "autonomous
rule optimization." None of that was backed by anything verifiable in this
repo, and the calendar targets didn't track what was actually built. This
rewrite drops the platform framing and unverified metrics, and replaces
the phase/quarter structure with what's actually shipped and what's
realistically next.

## What's real and working (with evidence)

- **Token budget system** — `python/pystreampdf/token_budget.py`
  (`TokenBudgetConfig`, `BudgetRule`): keyword/field-based multiplier rules
  that scale allocation within a fixed 500–1000 token range. Covered by
  `tests/test_token_budget.py`.
- **Semantic chunking** — `python/pystreampdf/extraction.py`
  (`SemanticChunker`): splits text into token-aware chunks by element
  type, not naive word-count splitting. Exercised in
  `tests/test_extraction.py` and the runnable
  `examples/token_budget_and_cache_example.py`.
- **Dual-tier cache** — `python/pystreampdf/cache.py` (`PDFCache`): memory
  (L1) + disk (L2), HMAC-SHA256 signed on disk with owner-only (0600)
  permissions; a tampered cache file is rejected before deserialization.
  Covered by `tests/test_cache.py` and `tests/test_security.py`.
- **Real PDF security handling** — `pystreampdf._core.PyPdfDocument` uses
  PDFium's actual encryption/permission APIs (`is_encrypted()`,
  `permissions()`, `open_with_password()`); this replaced a stub that used
  to silently fall back to unauthenticated parsing (fixed in commit
  `3580f80`).
- **OCR + validation pipelines** — `ocr/manager.py`,
  `ocr/providers/{tesseract,paddle}.py`, and
  `validation/{layout,table,text,scorer}.py` are real implementations with
  dedicated test files, not placeholders.
- **CI actually runs the suite** — `.github/workflows/ci.yml` runs
  `cargo test --release --all-features` and `pytest tests/` across Python
  3.10/3.11/3.12 on every push/PR. CI was red for several weeks from two
  infra bugs (an under-specified `rust-toolchain` action input, and
  `maturin develop` needing an active venv that `actions/setup-python`
  doesn't provide) — both fixed (commits `6ebb03f`, `3e5a651`); the last
  confirmed-green run (linked from README.md) reported `pytest`: 557
  passed / 2 skipped, `cargo test`: 23 passed / 0 failed.
- **MCP tool handlers now call real code.** `_mcp_tools.py` /
  `_mcp_connector.py` were rewired in commit `39f7c8c` (CHANGELOG 2.3.0):
  all 12 tool methods previously ignored their input and returned
  identical hardcoded fixture data (e.g. `validate_pdf` always reported
  `is_valid: True`; `apply_ocr` always reported `confidence: 0.92` without
  running OCR). They now call the real extraction/OCR/validation/citation
  code paths described above.

## What's partial, scaffolding, or unverified

- **No committed token-savings benchmark.** Earlier README/docstring
  claims of "70% reduction" or "10-50x" savings were never backed by a
  checked-in benchmark and have been retracted in README.md. Actual
  savings depend on the caller's documents and query scoping.
- **Narrow wheel coverage.** Only a macOS arm64 wheel is published to
  PyPI. A source distribution ships as of 2.3.0, so other platforms build
  from source, but that still needs a local Rust toolchain and a
  discoverable `libpdfium`.
- **No realistic multi-column / scanned-PDF test fixtures.** The OCR and
  table-validation code is real and unit-tested, but `tests/` only has
  synthetic single-glyph images and mocks — no true multi-column layout or
  realistic scanned-document fixtures exist yet.
- **Cross-project integration claims are unverified from this repo.**
  Earlier docs listed StatGuardian as an inbound dependency and
  PyInferenceManager/PyStreamMCP as downstream consumers. Nothing in this
  repo's code imports from or is imported by those projects — treat this
  as an intended integration, not a demonstrated one.
- **The MCP handler rewire (`39f7c8c`) is new** and currently only
  unit-tested; it hasn't accumulated real invocation history yet.

## Near-term roadmap (concrete, not calendar-committed)

1. **Cross-platform wheels.** Build Linux (manylinux) and, ideally,
   Windows wheels in CI so `pip install pystreampdf` doesn't require a
   local Rust toolchain + PDFium outside macOS arm64.
2. **Real OCR/layout test fixtures.** Replace the synthetic single-glyph
   mocks with actual multi-column and scanned-document samples to give
   the existing OCR/validation code meaningful coverage (already flagged
   as a gap below in "Testing & Quality").
3. **Exercise the rewired MCP handlers beyond unit tests.** Now that
   `_mcp_tools.py` calls real extraction/OCR/validation code, add
   integration-style tests that invoke it through the MCP/DAB connector
   path, not just direct function calls.
4. **If/when a token-savings number is worth publishing, measure it and
   check the benchmark script into the repo** rather than restating a
   percentage in prose. Until then, point users at
   `examples/token_budget_and_cache_example.py` to measure their own
   case.

No committed dates: this project's actual recent pace (`git log`) has
been fixing previously-fabricated claims, security stubs, and CI
infrastructure — not shipping new large features on a quarterly cadence —
so this roadmap intentionally doesn't restate one.

## Testing & Quality (current gaps, not aspirational)

- [x] Token budget tests (`tests/test_token_budget.py`)
- [x] Cache integration tests with budgets (`tests/test_cache.py`)
- [x] Field-matching tests
- [x] Malformed/truncated-file coverage (`tests/test_security.py`)
- [ ] Real multi-column layout and scanned-PDF fixtures (`OcrPipeline` /
      `TableValidator` already handle routing and structure validation,
      but there is no realistic fixture data backing that coverage)
- [ ] Integration tests for the MCP/DAB connector path specifically
- [ ] Any committed performance benchmark (latency, throughput, or token
      savings) — none exist in this repo today

---

This file replaces the previous phase/quarter-based planning, which
didn't reflect actual delivery pace. See README.md's "Known Issues"
section for the fuller, itemized list of verified vs. retracted claims.
