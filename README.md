# PyStreamPDF v2.1.0

**Intelligent PDF Processing with Smart Token Budget Management**

## Overview

PyStreamPDF is a production-ready PDF processing library for AI applications. It combines semantic chunking, intelligent caching, and dynamic token budgeting to optimize LLM context usage. Part of the unified **MCP 2.0 Mega-Platform** (207 tools across 18 projects).

## Key Features

- **Smart Token Budgeting**: Automatically scale context allocation (500-1000 tokens) based on document type and complexity
- **Semantic Chunking**: Context-aware document splitting with configurable token targets
- **Intelligent Caching**: L1 memory + L2 disk caching with cache invalidation
- **Multi-Format Extraction**: Text, tables, images, OCR (Tesseract, PaddleOCR)
- **MCP 2.0 Integration**: 12 discoverable tools via MCP protocol
- **Production-Ready**: 523 tests, comprehensive error handling, type-safe API
- **Zero Configuration**: Works out-of-the-box with sensible defaults

## Installation

```bash
pip install PyStreamPDF
```

Wheels-only distribution (recommended for production):

```bash
pip install --only-binary=:all: PyStreamPDF
```

## Quick Start: Token Budget Configuration

Configure intelligent token allocation for different document types:

```python
from pystreampdf import TokenBudgetConfig, BudgetRule

# Define keyword-based multiplier rules
rules = [
    BudgetRule("financial", 1.2, match_fields=["filename", "title"]),
    BudgetRule("legal", 1.3, match_fields=["filename", "title"]),
    BudgetRule("summary", 0.8, match_fields=["filename"]),
]

# Create config: base 1000 tokens, scales 500-1000 based on rules
config = TokenBudgetConfig(base_budget=1000, rules=rules)

# Evaluate for a document
budget = config.evaluate("financial_quarterly_report.pdf")
# Result: 1000 * 1.2 = 1000 (clamped to max)
```

See [TOKEN_BUDGET_MULTIPLIERS.md](docs/TOKEN_BUDGET_MULTIPLIERS.md) for comprehensive guide.

## Quick Start: Document Extraction

```python
from pystreampdf import SemanticChunker, PDFCache, TokenBudgetConfig

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
        processor_fn=extract_chunks
    )
    return chunks

# Use semantic chunker directly
chunker = SemanticChunker(target_tokens=500)
chunks = chunker.chunk_content(text, element_type=ElementType.TEXT)
```

## Budget Configuration

### Default Settings
- **Minimum budget**: 500 tokens (fixed)
- **Maximum budget**: 1000 tokens (fixed)  
- **Default base**: 1000 tokens
- **Multiplier range**: 0.5 - 1.5 (common)

### Dynamic Adjustment via Multipliers
Use keyword-based rules to scale within the 500-1000 range without changing hard limits. See examples for [financial](docs/TOKEN_BUDGET_MULTIPLIERS.md#high-complexity-documents), [legal](docs/TOKEN_BUDGET_MULTIPLIERS.md#high-complexity-documents), and [summary](docs/TOKEN_BUDGET_MULTIPLIERS.md#low-complexity-documents) documents.

## MCP 2.0 Integration

Enable MCP tools on port **8780** (see MCP_QUICKSTART.md for details).

AI systems discover all 207 tools across 18 projects:
- 12 PyStreamPDF tools for document processing
- 195 tools from 17 integrated projects
- Multi-project workflows with intelligent orchestration
- 60-75% reduction in context usage through query optimization

## Documentation

- **[TOKEN_BUDGET_MULTIPLIERS.md](docs/TOKEN_BUDGET_MULTIPLIERS.md)** - Comprehensive token budget guide with examples
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and components
- **[PRODUCT_VISION.md](docs/PRODUCT_VISION.md)** - Long-term strategy and roadmap
- **[ROADMAP.md](docs/ROADMAP.md)** - Planned features and enhancements

## Part of Unified Platform

18 projects, 207 tools, 18 simultaneous MCP endpoints (8765-8782).

**All tools discoverable via MCP protocol in a single connection.**

## Version History

### v2.0.0 (Current)
- ✅ MCP 2.0 Support
- ✅ Integrated with 17 other projects
- ✅ 207 unified MCP tools
- ✅ Intelligent orchestration
- ✅ Production-ready (wheels only)

## License

MIT

---

**MCP 2.0 Mega-Platform | v2.0.0 | Wheels-Only Distribution**
