# PyStreamPDF

**Extract only what matters from PDFs, so you send less to LLMs.**

Stop sending entire documents to LLMs. PyStreamPDF parses PDF structure and
splits content into semantic, token-budget-aware chunks so you can send
only the relevant parts of a document to a model. See "Token Savings"
below for how much that saves in practice — it depends on your documents.

[![PyPI](https://img.shields.io/pypi/v/pystreampdf)](https://pypi.org/project/pystreampdf)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![Tests: 557 Passing](https://img.shields.io/badge/tests-557%20passing-success)](./tests)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

---

## 30-Second Start

```python
from pystreampdf import SemanticChunker, ElementType

with open("financial_report.pdf", "rb") as f:
    text = f.read().decode("latin-1", errors="ignore")  # or use a real PDF text extractor first

chunker = SemanticChunker(target_tokens=500)
chunks = chunker.chunk_content(
    text, element_type=ElementType.TEXT, page_start=1, page_end=1
)
print(f"Split into {len(chunks)} semantic chunks")
```

There is no `Document`/`.extract_relevant()` class in this package —
`SemanticChunker` (shown above) and `PDFCache` (see "Quick Start: Document
Extraction" below) are the real, exported API. If you built against a
`Document` class from an earlier version of these docs, it never actually
existed in source; see Known Issues.

---

## Why PyStreamPDF?

**The Problem:**
- You send entire PDFs to LLMs (wasteful, expensive)
- RAG systems retrieve too much content
- Token costs skyrocket on large documents
- No way to know which parts actually matter

**The Solution:**
- Semantic chunking with context awareness (real, in `SemanticChunker`)
- Token-budget-aware caching (real, in `PDFCache` / `TokenBudgetConfig`)
- Reduces the volume of text you send per query — see "Token Savings"
  below for what's measured vs. illustrative

---

## Key Features

- **Real encryption/permission detection:** Backed by PDFium's actual document security APIs — not a stub. Encrypted, password-protected, and permission-restricted PDFs are detected and reported accurately; opening with a wrong/missing password fails closed rather than silently succeeding.
- **Honest failure signaling:** If a PDF can't be parsed (corrupt, truncated, unsupported), you get a real error — never fabricated placeholder content.
- **Intelligent Extraction:** Find relevant sections automatically
- **Semantic Chunking:** Context-aware splitting, not just word count
- **Multi-Format:** Text, tables, images, charts, OCR
- **Token Budgeting:** Allocate tokens by document type
- **Smart Caching:** L1 memory + L2 disk (HMAC-signed on disk — no unverified deserialization)
- **Metadata Preservation:** Keep tables, images, structure
- **Tested:** 557 passing tests (2 skipped when optional OCR system deps aren't installed) — run with `pytest tests/`, see "Documentation" below for CI results

---

## Real-World Use Cases

See [examples/basic_parse.py](examples/basic_parse.py) for the Rust-backed
`pystreampdf.open()` path (document/page/structure inspection — requires
the compiled `_core` extension, see Known Issues) and
[examples/token_budget_and_cache_example.py](examples/token_budget_and_cache_example.py)
for the pure-Python `SemanticChunker` + `PDFCache` + `TokenBudgetConfig`
path shown above. Both are real, runnable scripts — copying them is more
reliable than a README snippet for an evolving API.

---

## Token Savings

**A note on how token counts are computed:** by default, token counts use a
`len(text) / 4` heuristic (a common rule of thumb, but approximate — it can
be off by a meaningful margin, especially for code or non-English text).
Install the optional `tiktoken` extra for exact BPE token counts:

```bash
pip install "pystreampdf[tiktoken]"
```

When `tiktoken` is installed, `pystreampdf.tokenizer.is_exact()` returns
`True` and counts use the real `cl100k_base` encoding; otherwise it falls
back to the heuristic. Check `pystreampdf.tokenizer.TOKENIZER_MODE` to see
which mode produced a given number.

Actual token savings depend entirely on your documents and how narrowly
you scope `extract_relevant`-style queries — there's no committed
benchmark result in this repo backing a specific percentage (the earlier
"70%"/"10-50x" style claims in this README and in `__init__.py`'s
docstring weren't measured against anything checked in). Run
[examples/token_budget_and_cache_example.py](examples/token_budget_and_cache_example.py)
against your own documents to get a real number for your use case.

---

## Security Notes

- **Encryption & permissions**: `pystreampdf._core.PyPdfDocument.is_encrypted()`,
  `.permissions()`, and `.open_with_password()` are backed by PDFium's real
  document security APIs. A wrong or missing password on an encrypted PDF
  raises an error — it never falls back to an unauthenticated parse.
- **Cache integrity**: the on-disk (L2) cache is HMAC-SHA256 signed using a
  key generated on first use and stored with owner-only (0600) permissions.
  A tampered or foreign cache file fails signature verification and is
  discarded before any deserialization occurs.
- **MCP/DAB connector**: binds to `127.0.0.1` with no cross-origin access
  and read-only permissions by default. Wider exposure requires an explicit
  `allow_remote=True` opt-in — review the security implications first, since
  the connector has no authentication of its own.

---

## Installation

```bash
pip install pystreampdf

# With exact token counting (tiktoken)
pip install "pystreampdf[tiktoken]"
```

---

## Documentation

- [Token Budget Multipliers](docs/TOKEN_BUDGET_MULTIPLIERS.md) — Comprehensive token budget guide with examples
- [Product Vision](docs/PRODUCT_VISION.md) — What's real and working vs. partial/unverified, verified against source
- [Roadmap](docs/ROADMAP.md) — Same honest-status treatment plus near-term plans and known testing gaps
- [Examples](examples/) — Real, runnable scripts: [basic_parse.py](examples/basic_parse.py) (Rust-backed document API), [token_budget_and_cache_example.py](examples/token_budget_and_cache_example.py) (SemanticChunker/PDFCache), [mcp_pystreampdf.py](examples/mcp_pystreampdf.py) (MCP connector)

There is no separate Quick Start / Extraction Strategies / Token Budgeting guide beyond what's above — earlier revisions of this README linked to `docs/QUICKSTART.md`, `docs/EXTRACTION.md`, and `docs/TOKEN_BUDGETS.md`, none of which exist in this repo. Those dead links have been removed; the "30-Second Start" section above and the `examples/` scripts are the actual quick-start material.

## Quick Start: Document Extraction

```python
from pystreampdf import SemanticChunker, PDFCache, TokenBudgetConfig, BudgetRule

# Setup budget config
budget_config = TokenBudgetConfig(
    base_budget=800,
    rules=[BudgetRule("complex", 1.1, match_fields=["filename"])]
)

# Initialize cache with budget management
cache = PDFCache(
    memory_limit_mb=500,
    disk_cache_dir="./pdf_cache",
    token_budget_config=budget_config
)

# Process PDF with intelligent chunking
def extract_pdf(pdf_path):
    chunks, preview, title, pages = cache.get_or_process(
        pdf_path,
        process_fn=extract_chunks
    )
    return chunks

# Use semantic chunker directly
chunker = SemanticChunker(target_tokens=500)
chunks = chunker.chunk_content(text, element_type=ElementType.TEXT, page_start=1, page_end=1)
```

## Budget Configuration

### Default Settings
- **Minimum budget**: 500 tokens (fixed)
- **Maximum budget**: 1000 tokens (fixed)
- **Default base**: 1000 tokens
- **Multiplier range**: 0.5 - 1.5 (common)

### Dynamic Adjustment via Multipliers
Use keyword-based rules to scale within the 500-1000 range without changing hard limits. See examples for [financial](docs/TOKEN_BUDGET_MULTIPLIERS.md#high-complexity-documents), [legal](docs/TOKEN_BUDGET_MULTIPLIERS.md#high-complexity-documents), and [summary](docs/TOKEN_BUDGET_MULTIPLIERS.md#low-complexity-documents) documents.

## MCP Integration (optional, local by default)

PyStreamPDF ships an optional MCP/DAB connector (`pystreampdf._mcp_connector`)
exposing document-processing tools (extract text/tables/images, OCR,
structure detection, metadata, chunking, citations, validation). It's
opt-in, binds to `127.0.0.1` only, and requires `allow_remote=True` to be
exposed beyond localhost. See [examples/mcp_pystreampdf.py](examples/mcp_pystreampdf.py).

## Known Issues

- Earlier versions of this README documented a `Document` class with
  `.extract_relevant()` and a `.token_savings` attribute — verified
  against source: this class has never existed in this package. Fixed
  in this pass to describe the real, exported API (`SemanticChunker`,
  `PDFCache`, `TokenBudgetConfig`, and the Rust-backed `pystreampdf.open()`).
- The published PyPI wheel is macOS arm64 only — no Linux/Windows wheel.
  Starting with 2.3.0, a source distribution is also published, so
  `pip install` on another platform will build from source rather than
  fail outright, but it still needs a local Rust toolchain and a
  discoverable `libpdfium` (see `scripts/download_pdfium.sh`) to succeed.
- ~~The published version (2.2.1) is ahead of what's tagged in this repo's
  Cargo.toml/__init__.py (2.2.0)~~ Resolved: 2.3.0 (this release) is
  unambiguously ahead of both 2.2.0 and 2.2.1.
- The Rust-backed `pystreampdf.open()` / `pystreampdf.load_index()` API
  (used in `examples/basic_parse.py`) silently becomes `None` if the
  compiled `_core` extension isn't available (e.g. a from-source install
  without `maturin develop`) — falling back to `SemanticChunker`/`PDFCache`
  in that case, per the code above, not a hard error.
- The "Tests & Build" GitHub Actions workflow was red for several weeks
  due to two CI infrastructure bugs (not the test suite itself), both
  now fixed and confirmed green in CI:
  [run 32611116541](https://github.com/Mullassery/PyStreamPDF/actions/runs/32611116541).
  First, `dtolnay/rust-toolchain@v1` required an explicit `toolchain`
  input the workflow didn't provide, failing both jobs before any tests
  ran — fixed by pinning to `dtolnay/rust-toolchain@stable`. Second, once
  that was fixed, `maturin develop` failed in the Python-test job because
  `actions/setup-python` doesn't provide an active virtualenv, which
  maturin requires — fixed by creating and activating a `.venv` before
  the build step. Actual CI output as of 2.2.0: `pytest` — 536 passed, 2
  skipped (Python 3.10, 3.11, and 3.12, each identical); `cargo test` — 23
  passed, 0 failed. (The Rust suite has 23 tests, not 536 — an earlier
  version of this section conflated the pytest count with the Rust one.)
  As of 2.3.0: `pytest` — 557 passed, 2 skipped (21 new tests added for
  `tests/test_mcp_tools.py`).

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

**PyStreamPDF v2.3.0** | Intelligent PDF processing for AI | Python 3.9+ | 557 passing tests
