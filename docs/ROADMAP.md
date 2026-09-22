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

## Technical Debt (verified 2026-09-20, file:line specific)

Found during an OSS-standardization pass. Not fixed in that pass
(disclosure-first, not fix-everything) except where noted — these are
candidates for a dedicated follow-up session.

- **Lint debt is real and CI doesn't catch it.** `.pre-commit-config.yaml`
  configures `black` and `ruff`/`ruff-format`, but `.github/workflows/ci.yml`
  never runs them — only `cargo build`/`cargo test` and `pytest`. Actually
  running them against this repo (2026-09-20, ruff 0.x / black 24.7.0-class
  behavior) found:
  - `ruff check python/ tests/` reports **771 errors** (169 auto-fixable).
    Biggest categories: 96 unsorted-import blocks (I001), 92 deprecated
    `typing` imports (UP035, e.g. `List`/`Dict` instead of `list`/`dict`),
    57 unused imports (F401), 25 bare/blind `except Exception` (BLE001),
    12 unused variables (F841). (After the 2026-09-22 exception-narrowing
    fix below, `ruff check` reports 756 errors and
    `--select E722,S110,BLE001` reports 20, down from 25 — the remaining
    771/25 aren't otherwise touched; still real debt, still not fixed.)
  - `black --check python/ tests/` reports **73 of 88 files** would be
    reformatted.
  - This means the pre-commit hooks, if actually installed by a
    contributor, would rewrite most of the codebase on first run — or, if
    not installed (the common case, since CI doesn't enforce it), the
    formatting/lint debt just accumulates silently. Recommend either
    wiring `ruff check` + `black --check` into `ci.yml` as a real
    (non-`|| true`) gate, or dropping the pretense of enforcing them.
- ~~**Swallowed exceptions that hide real failures**~~ **[Fixed 2026-09-22]**
  — `semantic/assembler.py:148`, `cache.py:325`, `ocr/manager.py:127`/`:136`,
  `ocr/providers/paddle.py:45`, `ocr/providers/tesseract.py:49`, and
  `tokenizer.py:63` had bare/broad `except`/`except Exception: pass` with no
  logging. All six narrowed to the specific exception type each call site
  actually expects (`AttributeError`, `(OSError, pickle.PicklingError)`,
  `ImportError` x3, `OSError`, `ValueError` respectively) and now log at
  debug level instead of silently dropping the failure. See CHANGELOG
  `[Unreleased]` for the per-site detail. One new gap surfaced in the
  process, not fixed here: `semantic/assembler.py`'s `self.citations.top_cited(...)`
  call always raised `AttributeError` because `CitationNetwork`
  (`semantic/citations.py`) never implemented a `top_cited` method — the
  citation-assembly branch of `ContextAssembler` has been dead code since
  it was written (no caller in this repo ever constructs a
  `ContextAssembler` with a real `citation_network`, and no test exercises
  it). Implementing `top_cited` is real feature work, out of scope here.
- ~~**Likely-unintended symbol shadowing**~~ **[Fixed 2026-09-22, not a
  behavioral bug]** — `validation/__init__.py:18` and the `.types` import
  block both named `OcrTable`, but diffing them showed `.table.py` never
  defined its own `OcrTable` class — it only did `from .types import
  OcrTable` and re-exported it. So both imports resolved to the identical
  class object (confirmed via `table.OcrTable is types.OcrTable` ->
  `True`); there was no shadowing of distinct behavior, just a confusing
  double import of the same name from two paths. Removed the redundant
  `OcrTable` re-import from `.table` in `validation/__init__.py` and
  `validation/scorer.py` so it's imported from exactly one place
  (`validation/types.py`, the actual definition). Full test suite
  unaffected (557 passed / 2 skipped).
- ~~**`.pre-commit-config.yaml` has at least one broken hook entry.**~~
  **[Fixed 2026-09-22]** — `rustfmt` was configured under
  `repo: https://github.com/oxalica/nil` (a Nix language server, not a Rust
  formatter) and `rust-clippy` was pinned to the floating `rev: master`.
  Fixed to match the convention already used in this org's other Rust
  repos' `.pre-commit-config.yaml` (`PyStreamXL`, `PyRoboFrames`,
  `statguardian`, `pyvectorhound`, `ClusterAudienceKit`):
  `repo: https://github.com/rust-lang/rustfmt` @ `v1.7.0` and
  `repo: https://github.com/rust-lang/rust-clippy` @ `v1.77.0`.
- **`cargo test --release --all-features` fails at the workspace level on
  macOS** (verified in this pass): the `python` crate is a PyO3
  `cdylib`/`extension-module` and cannot be executed as a standalone test
  binary outside a Python process — it aborts with
  `dyld: symbol not found in flat namespace '_PyBaseObject_Type'`. This
  is a macOS linking quirk, not a code bug: `cargo test -p streampdf-core
  --release --all-features` (the crate that actually has `#[test]`s) runs
  clean — 23 passed, 0 failed, matching README's claimed count. CI runs on
  `ubuntu-latest` where this isn't an issue (confirmed green per README's
  linked run). Anyone testing workspace-wide on macOS should scope to
  `-p streampdf-core` rather than assume the workspace-wide command is
  broken.
- **Stale/inconsistent dependabot branches.** `origin/dependabot/github_actions/actions/checkout-7`
  and `origin/dependabot/github_actions/actions/setup-python-7` exist as
  open dependabot branches, but diffing them against `main` shows they
  also rewrite the Python test job to `cd python && pytest tests/`
  (assuming a `python/tests/` layout) and drop the PDFium download +
  `maturin develop` steps entirely — neither matches this repo's actual
  layout (tests live at repo-root `tests/`; the native extension must be
  built before `pytest` can import `pystreampdf._core`). These two
  dependabot PRs would break CI if merged as-is; the underlying version
  bump they're proposing (`actions/setup-python@v7`) has been applied
  manually in this pass without the rest of that diff, but the dependabot
  PRs themselves should be closed without merging (or dependabot needs to
  regenerate them against the current workflow).
- **`libpdfium.dylib` and `dist/*.whl`/`*.tar.gz` present in the working
  tree but correctly gitignored** — not a bug (confirmed not tracked by
  `git ls-files`), just noting they're local build artifacts from a prior
  manual build/release and not part of the repo as published.

---

This file replaces the previous phase/quarter-based planning, which
didn't reflect actual delivery pace. See README.md's "Known Issues"
section for the fuller, itemized list of verified vs. retracted claims.
