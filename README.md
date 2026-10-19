# PyStreamPDF

[![PyPI](https://img.shields.io/pypi/v/pystreampdf)](https://pypi.org/project/pystreampdf/)
[![CI](https://github.com/Mullassery/PyStreamPDF/actions/workflows/ci.yml/badge.svg)](https://github.com/Mullassery/PyStreamPDF/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)

Token-efficient PDF extraction for RAG: parse PDF structure and split content into token-budget-aware chunks.

## What it is

PyStreamPDF combines a Rust/PDFium-backed core for real PDF parsing with a Python layer
for semantic chunking, token-budget-aware caching, and OCR/validation. Instead of sending
an entire document to a model, it parses PDF structure and splits content into semantic,
token-budget-aware chunks so you can send only the relevant parts. It ships as
`pystreampdf` on PyPI and imports as `pystreampdf`.

## Features / Highlights

- **Semantic chunking** — `SemanticChunker` splits text into token-aware chunks by
  element type rather than naive word-count splitting.
- **Token-budget system** — `TokenBudgetConfig` / `BudgetRule` scale allocation within a
  fixed 500–1000 token range using keyword/field-based multipliers.
- **Dual-tier cache** — `PDFCache`: L1 memory + L2 disk, HMAC-SHA256-signed on disk with
  owner-only (0600) permissions; a tampered cache file fails verification before any
  deserialization.
- **Real PDF security handling** — `pystreampdf._core.PyPdfDocument` is backed by
  PDFium's actual encryption/permission APIs (`is_encrypted()`, `permissions()`,
  `open_with_password()`); a wrong or missing password fails closed.
- **Honest failure signaling** — unparseable PDFs raise a real error; no fabricated
  placeholder content.
- **OCR and validation pipelines** — `ocr/` and `validation/` are real implementations
  with dedicated test coverage.
- **Exact or heuristic token counts** — uses `len(text) / 4` by default (clearly labeled
  approximate); install the optional `tiktoken` extra for real BPE (`cl100k_base`) counts.
- **Optional MCP/DAB connector** — exposes document-processing tools over MCP, binds to
  `127.0.0.1` only, read-only by default.

## Who it's for / Use cases

- **RAG pipeline authors** who want to reduce the volume of text sent per query without
  losing the parts that matter.
- **Token-cost-conscious teams** that need to budget tokens per document type.
- **Document-processing services** that need real encryption/permission detection and a
  cache that fails closed on tampering.
- **Agent/tool builders** who want PDF extraction surfaced over MCP locally.

## What it is not

- **There is no `Document` class and no `.extract_relevant()` / `.token_savings` API.**
  That class never existed in the source. The real exported API is `SemanticChunker`,
  `PDFCache`, `TokenBudgetConfig`, and the Rust-backed `pystreampdf.open()`.
- **No committed token-savings benchmark.** Earlier "70% reduction" / "10-50x" claims
  were never backed by a checked-in benchmark and have been retracted. Actual savings
  depend on your documents and how narrowly you scope queries.
- **Prebuilt wheels are macOS arm64 only.** A source distribution ships as of 2.3.0, so
  other platforms build from source, but that still requires a local Rust toolchain and a
  discoverable `libpdfium` (see `scripts/download_pdfium.sh`).
- **No realistic OCR/layout test fixtures yet.** The OCR and table-validation code is real
  and unit-tested, but tests use synthetic images and mocks — no true multi-column layout
  or realistic scanned-document fixtures.
- **Cross-project integration is asserted, not demonstrated.** Nothing in this repo
  imports from or is imported by StatGuardian, PyInferenceManager, or PyStreamMCP.
- **The Rust-backed `pystreampdf.open()` / `load_index()` silently becomes `None`** if the
  compiled `_core` extension is unavailable (e.g. a from-source install without
  `maturin develop`), falling back to the pure-Python path rather than erroring.
- **The MCP connector has no authentication of its own.** It binds to `127.0.0.1` with
  read-only permissions by default; exposing it further requires `allow_remote=True`.

## Project status

**Beta.** Current version **2.3.0** (`Development Status :: 4 - Beta`). The last
confirmed-green CI run reported `pytest` — 557 passed / 2 skipped and `cargo test` — 23
passed / 0 failed across Python 3.10/3.11/3.12. See
[`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md) for what is real vs. partial.

## Installation

```bash
pip install pystreampdf

# With exact token counting (tiktoken)
pip install "pystreampdf[tiktoken]"
```

Requires Python 3.9+.

## Quick start

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

## Usage

**Budget-aware caching and chunking:**

```python
from pystreampdf import SemanticChunker, PDFCache, TokenBudgetConfig, BudgetRule, ElementType

budget_config = TokenBudgetConfig(
    base_budget=800,
    rules=[BudgetRule("complex", 1.1, match_fields=["filename"])]
)

cache = PDFCache(
    memory_limit_mb=500,
    disk_cache_dir="./pdf_cache",
    token_budget_config=budget_config,
)

def extract_pdf(pdf_path):
    chunks, preview, title, pages = cache.get_or_process(pdf_path, process_fn=extract_chunks)
    return chunks

chunker = SemanticChunker(target_tokens=500)
chunks = chunker.chunk_content(text, element_type=ElementType.TEXT, page_start=1, page_end=1)
```

**Exact vs. heuristic token counts.** By default counts use `len(text) / 4`. With the
`tiktoken` extra installed, `pystreampdf.tokenizer.is_exact()` returns `True` and
`cl100k_base` is used; check `pystreampdf.tokenizer.TOKENIZER_MODE` to see which mode
produced a given number.

**Rust-backed document API** (`examples/basic_parse.py`) — document/page/structure
inspection, requires the compiled `_core` extension:

```python
import pystreampdf
doc = pystreampdf.open("report.pdf")  # None if _core isn't available
```

**MCP connector** — optional, local by default, read-only:

```python
# see examples/mcp_pystreampdf.py
```

## Documentation

- [Product Vision](docs/PRODUCT_VISION.md) — what's real and working vs. partial/unverified, verified against source
- [Token Budget Multipliers](docs/TOKEN_BUDGET_MULTIPLIERS.md) — token budget guide with examples
- [Architecture](docs/ARCHITECTURE.md) — component overview
- [Roadmap](docs/ROADMAP.md) — honest status plus near-term plans and known testing gaps
- [Examples](examples/) — runnable scripts: [basic_parse.py](examples/basic_parse.py) (Rust-backed document API), [token_budget_and_cache_example.py](examples/token_budget_and_cache_example.py) (`SemanticChunker`/`PDFCache`), [mcp_pystreampdf.py](examples/mcp_pystreampdf.py) (MCP connector)

Run the tests with:

```bash
make test          # cargo test && pytest tests/
```

## Known issues and deferred work

**Blocked / failed:**
- Linux/Windows wheels, Docling/PyMuPDF benchmark, realistic OCR fixtures.

**Rejected / deferred:**
- A full PDF RAG platform; Docling owns layout understanding.

Full shipped/blocked/rejected detail: [`QUEUE_STATUS.md`](QUEUE_STATUS.md).

## Queue status

Shipped, blocked/failed, and rejected work for this repository is documented in
[`QUEUE_STATUS.md`](QUEUE_STATUS.md).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security issues: see
[SECURITY.md](SECURITY.md) for the reporting process and the cache/MCP security model.

## Related projects

- [PyStreamXL](https://github.com/Mullassery/PyStreamXL) — stream large Excel workbooks with constant memory
- [PyStreamPDF](https://github.com/Mullassery/PyStreamPDF) — token-efficient PDF extraction for RAG
- [PyStreamMCP](https://github.com/Mullassery/PyStreamMCP) — context and token optimization for AI agents
- [PyStreamAI](https://github.com/Mullassery/PyStreamAI) — ML deployment toolkit (canary/A-B, cost tracking, ONNX)
- [PyTokenCalc](https://github.com/Mullassery/PyTokenCalc) — LLM token counting and cost estimation
- [Browse all projects](https://github.com/Mullassery?tab=repositories)

## License

This project is licensed under the [Apache License 2.0](LICENSE).
