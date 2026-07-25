# PyStreamPDF

> **Intelligence engine for PDFs.** Selective retrieval, structure analysis, token-efficient RAG. 10-50x cost reduction through technical intelligence and smart context selection.

![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Tests](https://img.shields.io/badge/Tests-523%20Passing-brightgreen.svg)
![Distribution](https://img.shields.io/badge/Distribution-Wheels--Only-blue.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

---

## Product Overview

**PyStreamPDF** is a proprietary, production-grade PDF intelligence engine. Extract structure, identify technical content, optimize tokens. Achieve 10-50x cost reduction in RAG systems.

### Why Enterprise Teams Choose This

**The Problem**:
- PDF RAG wastes 80% of tokens on irrelevant content
- Naive chunking misses document structure
- Technical PDFs need specialized analysis
- RAG costs spiral with large document collections

**The Solution**:
- Technical intelligence layer (YAML, JSON, code, SQL analysis)
- Structure recovery (TOC, headers, figures, tables)
- Smart context selection (only send relevant content)
- Confidence scoring for each extraction

**Result**: 10-50x cost reduction, higher RAG quality, faster inference.

---

## Installation

```bash
pip install pystreampdf
# or with uv
uv pip install pystreampdf
```

### Requirements
- Python 3.10+
- Precompiled wheels for macOS, Linux, Windows

### Distribution Model

**Proprietary-first distribution**:
- ✅ Wheels-only via PyPI (no source code)
- ✅ Production-optimized PDF processing
- ✅ 523 comprehensive tests
- ✅ Used in enterprise RAG systems

---

## Quick Start

```python
from pystreampdf import PDFIntelligence

# Initialize intelligence engine
pdf_engine = PDFIntelligence()

# Process PDF with structure extraction
analysis = pdf_engine.analyze('technical_manual.pdf')

# Extract technical content
yaml_blocks = analysis.extract_yaml()
code_blocks = analysis.extract_code()
sql_queries = analysis.extract_sql()

# Generate context for RAG (minimal, highest-value)
context = analysis.select_optimal_context(
    query="How do I configure the API endpoint?",
    max_tokens=500,  # Strict token budget
)

# Cost-efficient RAG
response = llm.query(
    query="How do I configure the API endpoint?",
    context=context,  # Only essential content
)

print(f"Cost: ${response.cost:.4f} (vs ${response.cost_naive:.2f} with naive RAG)")
```

---

## Features

- **Technical Intelligence**: YAML, JSON, code, SQL, log analysis
- **Structure Recovery**: TOC extraction, headers, figures, tables
- **Smart Context Selection**: Only send relevant chunks to LLM
- **Confidence Scoring**: Know how confident each extraction is
- **Format Exporters**: Markdown, JSON-LD, RAG-optimized JSON
- **Production Ready**: 523 tests, observability included

---

## Performance

- **Processing speed**: 100+ pages/sec
- **Token reduction**: 10-50x vs naive chunking
- **Cost reduction**: Proportional to token reduction
- **Quality improvement**: Higher relevance to queries

---

## Quality & Testing

- **523 tests** passing
- **Production-grade** — enterprise RAG systems
- **Observability** — cost tracking, performance metrics

---

## Support

For production deployments: **mullassery@gmail.com**

---

**Version**: 2.2.1  
**License**: Proprietary  
**Distribution**: Wheels-only via PyPI  
**Python**: 3.10+  

Built for cost-efficient RAG.
