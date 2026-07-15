# StreamPDF

**The Intelligence Engine for PDFs**

StreamPDF is a high-performance PDF intelligence platform that enables AI agents to retrieve, understand, and process PDF documents without requiring full document conversion.

Instead of converting entire PDFs to markdown, StreamPDF intelligently identifies relevant sections and converts only what's needed — dramatically reducing compute, storage, and token costs.

---

## The Problem

Modern PDF processing pipelines are wasteful:

```
Traditional RAG:
1. Convert entire PDF to markdown
2. Generate embeddings for all content
3. Store complete document
4. Retrieve small portions on demand

Result: 
- Process 100% of document
- Use only 1% of retrieved content
```

StreamPDF solves this:

```
StreamPDF:
1. Analyze PDF structure
2. Retrieve relevant pages (not full document)
3. Convert only selected pages to markdown
4. Optimize context for AI consumption

Result:
- Process only 5-10% of document
- Same or better accuracy
- 10-50x lower token consumption
```

---

## Core Vision

**Build the retrieval engine for PDFs.**

Not PDF parsing. Not PDF-to-Markdown conversion. But intelligent PDF access that makes RAG systems dramatically faster, cheaper, and more efficient.

### 10 Strategic Pillars

1. **PDF-Native Retrieval** — Understand structure before converting
2. **Page-Level Intelligence** — Find relevant pages instantly
3. **Dynamic Markdown** — Generate only what's needed
4. **Token Efficiency** — Minimize token consumption
5. **Large Documents** — Optimized for books and manuals
6. **Security-Aware** — Handle encrypted and protected PDFs
7. **Agent-Native** — APIs designed for AI systems
8. **Multi-Method Retrieval** — Combine semantic, structural, and keyword search
9. **Knowledge Index** — Lightweight persistent understanding
10. **RAG Infrastructure** — Foundation layer for PDF-based AI systems

---

## Installation

### PyPI (pip)

```bash
pip install streampdf
```

### uv

```bash
uv pip install streampdf
```

### From Source

```bash
git clone https://github.com/Mullassery/StreamPDF
cd StreamPDF
pip install -e .
```

---

## Quick Start

### Open and Parse a PDF

```python
import streampdf

# Open a PDF
doc = streampdf.open("example.pdf")
print(f"Pages: {doc.page_count}")

# Get a single page
page = doc.page(1)
print(f"Page 1 text: {page.text[:200]}")

# Get document structure
structure = doc.structure
for heading in structure.headings[:5]:
    print(f"{'  ' * heading.level}{heading.text}")
```

### Build an Index and Search

```python
# Build index for fast searching
index = doc.build_index("doc_index.db")

# Search for content
results = index.search("machine learning", top_k=5)
for result in results:
    print(f"Page {result.page_number}: {result.snippet}")

# Persist and reload
index2 = streampdf.load_index("doc_index.db")
```

### Navigate with Agent Context

```python
# Create a navigator for hierarchical browsing
nav = doc.navigator_with_index(index)

# Get top-level chapters
chapters = nav.chapters()
for chapter in chapters:
    print(f"Chapter: {chapter.heading.text} (pages {chapter.start_page}-{chapter.end_page})")

# Retrieve context for a query with token budget
context = nav.retrieve("attention mechanisms", max_tokens=2000)
print(f"Query: {context.query}")
print(f"Total tokens: {context.total_tokens}")
for section in context.sections:
    print(f"  {section.heading_path}: {len(section.content)} chars")
```

### Enterprise Features

```python
# Check if PDF is encrypted
is_encrypted = streampdf.PdfDocument.is_encrypted("document.pdf")

# Open encrypted PDF with password
doc = streampdf.PdfDocument.open_with_password("document.pdf", "password")

# Get document permissions
perms = streampdf.PdfDocument.permissions("document.pdf")
print(f"Can copy: {perms.can_copy}, Can print: {perms.can_print}")

# Fingerprint for integrity checking
fingerprint = doc.fingerprint()
print(f"SHA-256: {fingerprint}")

# Audit logging
audit = streampdf.PyAuditLog.new("audit.jsonl")
audit.record_open(doc.path)
audit.record_search(doc.path, "query", results_count=5)
events = audit.events()
```

---

## Current Status: v1.5.0 (Enterprise Features)

### What's Complete

✅ **Phase 1a: Foundation** (v0.1)
- Project scaffolding with Cargo workspace
- Core data types (document, page, structure)
- Python bindings via PyO3

✅ **Phase 1b: Intelligent Indexing** (v0.5)
- Real PDF parsing with pdfium-render
- SQLite knowledge index with FTS5
- Keyword search, page retrieval, index persistence

✅ **Phase 2: Agent Integration** (v1.0)
- Hierarchical heading extraction with page ranges
- Dynamic markdown generation with token budgets
- Token-efficient context assembly
- PdfNavigator for structured browsing

✅ **Phase 3: Enterprise Features** (v1.5) — **CURRENT**
- Full-text FTS5 indexing (not just preview)
- Thread-safe index sharing with Arc<Mutex>
- Real heading level detection (H1-H4)
- Breadcrumb paths in context sections
- Security module (encryption detection, password handling, permissions)
- Audit logging with JSON-lines format
- Form field detection framework
- Scanned PDF detection
- SHA-256 fingerprinting
- 48/48 tests passing

### Roadmap

- **v2.0** (Phase 4) — Semantic understanding, citation networks, topic hierarchies
- **v2.5** (Phase 5+) — Advanced cost optimization, multi-format support

---

## Strategic Documents

- **[STREAMPDF_VISION.md](STREAMPDF_VISION.md)** — Complete strategic vision and positioning
- **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** — 4-phase roadmap (36 weeks to v2.0)

---

## Roadmap

- **v0.1** (4 weeks) — PDF parsing & structure analysis
- **v0.5** (4 weeks) — Intelligent indexing & page-level retrieval  
- **v1.0** (8 weeks) — Agent integration & token optimization
- **v1.5** (8 weeks) — Enterprise features & security
- **v2.0** (12 weeks) — Advanced intelligence & cost analytics

---

## Why StreamPDF

### Performance First
- Parse PDFs 10x faster than traditional approaches
- Retrieve relevant pages in <50ms
- Convert selected pages to markdown in <1s

### Cost Reduction
- 10-50x reduction in token consumption
- Eliminate unnecessary processing
- Orders of magnitude savings for large document collections

### AI-Native Design
- APIs built for how agents actually work
- Agent-native navigation
- Token-aware context generation

### Enterprise Ready
- Security-aware (encrypted PDFs, permissions)
- Large document optimization (1000+ pages)
- Production observability

### Open Source
- MIT License
- No vendor lock-in
- Community-driven

---

## The Insight

Most questions require less than 1% of a PDF.

Most AI systems currently process 100% anyway.

StreamPDF changes that fundamental inefficiency.

---

## License

MIT License — See [LICENSE](LICENSE) for details

---

## Vision

Transform how the world works with PDF data in AI systems.

From:
> "A faster PDF-to-Markdown converter"

To:
> "The retrieval engine for PDFs"

**Only convert what's needed. Retrieve what matters. Optimize everything else.**
