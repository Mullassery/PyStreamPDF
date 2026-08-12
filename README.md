# PyStreamPDF

**Reduce RAG costs 50-70%. Extract only what matters from PDFs.**

Stop sending entire documents to LLMs. PyStreamPDF analyzes structure, identifies relevant sections, and extracts only critical content. Cut token costs 50-70% while improving retrieval accuracy.

[![PyPI](https://img.shields.io/pypi/v/pystreampdf)](https://pypi.org/project/pystreampdf)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![Tests: 536 Passing](https://img.shields.io/badge/tests-536%20passing-success)](./tests)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)

---

## 30-Second Start

```python
from pystreampdf import Document

# Extract only relevant content from PDF
doc = Document("financial_report.pdf")

# Smart content extraction
relevant = doc.extract_relevant("revenue for Q3 2024")
print(f"Extracted {len(relevant)} chunks")
print(f"Token savings: {relevant.token_savings:.0%}")  # 60% savings

# Send only relevant parts to LLM
for chunk in relevant:
    response = llm.query(chunk, "What was Q3 revenue?")
```

---

## Why PyStreamPDF?

**The Problem:**
- You send entire PDFs to LLMs (wasteful, expensive)
- RAG systems retrieve too much content
- Token costs skyrocket on large documents
- No way to know which parts actually matter

**The Solution:**
- Intelligent document analysis finds relevant sections
- Semantic chunking with context awareness
- 50-70% reduction in token usage
- Better retrieval accuracy (less noise)

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
- **Production-Ready:** 536 passing tests (2 skipped when optional OCR system deps aren't installed)

---

## Real-World Use Cases

**Financial Documents:**
```python
# Extract relevant sections from annual report
doc = Document("10-K_2024.pdf")
revenue_sections = doc.extract_relevant("revenue")
earnings_sections = doc.extract_relevant("earnings")

# 70% fewer tokens than sending whole PDF
for section in revenue_sections:
    summary = llm.query(section, "What was total revenue?")
```

**Legal Contracts:**
```python
# Find clauses without reading everything
doc = Document("contract.pdf")
liability = doc.extract_relevant("liability", "indemnification")
print(f"Found in {len(liability)} sections")
```

**Research Papers:**
```python
# Extract methodology and results
doc = Document("paper.pdf")
methods = doc.extract_relevant("methods", "experiment")
results = doc.extract_relevant("results", "findings")
```

---

## Token Savings

| Document | Size | Full PDF Tokens | PyStreamPDF | Savings |
|----------|------|-----------------|-------------|---------|
| Annual Report | 200 pages | 50K | 15K | 70% |
| Contract | 50 pages | 12K | 4K | 67% |
| Research Paper | 30 pages | 8K | 2K | 75% |

**Results:** Lower costs + better retrieval accuracy + faster responses

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
which mode produced a given number. The savings figures in the table above
were measured using the heuristic mode; your exact numbers with `tiktoken`
enabled may differ slightly.

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

- [Quick Start](docs/QUICKSTART.md) — Process your first PDF
- [Extraction Strategies](docs/EXTRACTION.md) — Different approaches for different documents
- [Token Budgeting](docs/TOKEN_BUDGETS.md) — Control context allocation
- [Token Budget Multipliers](docs/TOKEN_BUDGET_MULTIPLIERS.md) — Comprehensive token budget guide with examples
- [Examples](examples/) — Real-world RAG optimization

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

## License

Proprietary License — Free to use with explicit attribution. See [LICENSE](LICENSE).

---

**PyStreamPDF v2.2.0** | Intelligent PDF processing for AI | Python 3.9+ | 536 passing tests
