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
- **Prebuilt wheels are macOS arm64 only.** A source distribution has shipped since 2.3.0, so
  other platforms build from source, but that still requires a local Rust toolchain and a
  discoverable `libpdfium` (see `scripts/download_pdfium.sh`).
- **OCR/layout fixtures are generated at test time, not checked in.** `tests/` now
  renders real two-column, mildly rotated/skewed, and Times-Roman (22 pt) pages,
  rasterizes them with PyMuPDF at ~150 dpi, and embeds the images as text-free scanned
  PDFs (`tests/test_scanned_and_span_fixtures.py`). The OCR assertions run against real
  Tesseract output and skip when Tesseract is unavailable; they are not mocked. A
  reportlab table-with-spans fixture covers merged-cell text extraction. This is fixture
  coverage, not an OCR quality benchmark.
- **Cross-project integration is limited but real.** The MCP connector imports the
  canonical `BaseMCPConnector` from `statguardian._mcp_connector` when StatGuardian is
  installed (with a local fallback for older installs), verified by
  `tests/test_mcp_shared_base.py`. No other StatGuardian, PyInferenceManager, or
  PyStreamMCP integration is demonstrated here.
- **The Rust-backed `pystreampdf.open()` / `load_index()` silently becomes `None`** if the
  compiled `_core` extension is unavailable (e.g. a from-source install without
  `maturin develop`), falling back to the pure-Python path rather than erroring.
- **Remote MCP exposure is bearer-token protected and supports TLS/mTLS.** The
  connector binds to `127.0.0.1` with read-only permissions by default.
  `allow_remote=True` requires a non-empty `auth_token`; DAB stays on loopback and a
  stdlib reverse proxy enforces `Authorization: Bearer <token>` plus a per-IP rate limit
  before forwarding. Pass both `tls_cert` and `tls_key` to serve HTTPS directly from the
  proxy (stdlib `ssl.SSLContext`, TLS 1.2+); without them traffic is plaintext HTTP. Set
  `client_ca` (with TLS) to require and verify a client certificate
  (`ssl.CERT_REQUIRED`). Request bodies over `max_body_bytes` (default 10 MiB) get a
  `413`, and the proxy writes a basic access log
  (`pystreampdf._mcp_connector.access`: method/path/status/remote, no auth headers or
  query strings). Rate-limit buckets are in-memory per process and reset on restart;
  there is no persistence or cross-worker sharing. For untrusted networks a hardened
  reverse proxy is still recommended. Request and response bodies are streamed in
  chunks rather than fully buffered; chunked request bodies are rejected with `501`
  (see `SECURITY.md`).

## Project status

**Beta.** Current version **2.4.2** (`Development Status :: 4 - Beta`). The full
`pytest tests/` suite on this change passes locally — 600 passed / 4 skipped
(optional-dependency skips), and the last confirmed-green CI run reported `cargo test` —
23 passed / 0 failed across Python 3.10/3.11/3.12. See
[`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md) for what is real vs. partial.

## Installation

```bash
pip install pystreampdf

# With exact token counting (tiktoken)
pip install "pystreampdf[tiktoken]"

# With PDF table -> .xlsx export (PyStreamXL)
pip install "pystreampdf[excel]"
```

Requires Python 3.9+.

### Optional integrations

Every integration below is optional: the base install and the test suite run
without it, and the relevant tests skip (or assert the actionable error) rather
than fail when it is missing.

- **PyMuPDF** (`pip install pymupdf`) — rasterizes scanned pages for the OCR
  pipeline (`pystreampdf.ocr.pipeline`). Without it, scanned-page OCR raises a
  clear `ImportError` with the install hint.
- **tiktoken** (`pip install "pystreampdf[tiktoken]"`) — real BPE
  (`cl100k_base`) token counts; falls back to the `len(text) / 4` heuristic.
- **PyStreamXL** (`pip install "pystreampdf[excel]"`) — writes extracted tables
  to `.xlsx`. Without it, Excel export raises an `ImportError` naming the extra.
- **pytest-asyncio** — a dev/test extra only (`pip install "pystreampdf[dev]"`),
  required to run the `tests/test_mcp_tools.py` async tests.
- **Tesseract + pytesseract + Pillow** — real OCR for scanned PDFs
  (`brew install tesseract`, `pip install pytesseract pillow`). Or use the OS
  package manager for Tesseract; the OCR tests run against generated rasterized
  fixtures and skip with an explicit reason when the binary/package is missing.

### Optional high-fidelity extraction (Docling)

The native Rust/PDFium path is the default. For complex layouts, tables or
scanned pages, install the MIT-licensed [Docling](https://github.com/docling-project/docling)
backend and use it as an extraction source while keeping PyStreamPDF's chunk
and budget types:

```bash
pip install "pystreampdf[docling]"
```

```python
from pystreampdf import extract_with_docling

result = extract_with_docling("report.pdf", target_tokens=500)
for chunk in result.chunks:
    print(chunk.chunk_type, chunk.page_start, chunk.estimated_tokens)
```

Docling downloads its own layout/OCR models on first use. It is optional and
is **not** part of the base install.

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
- Linux/Windows wheels, Docling/PyMuPDF benchmark.

**Rejected / deferred:**
- A full PDF RAG platform; Docling owns layout understanding.
- Persisting/sharing rate-limit buckets across restarts or workers (the proxy keeps
  them in memory by design; use an external limiter for multi-process deployments).

Full shipped/blocked/rejected detail: [`QUEUE_STATUS.md`](QUEUE_STATUS.md).

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
