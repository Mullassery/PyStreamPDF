# StreamPDF: Technical Architecture

## Tech Stack

### Core Engine
- **Language:** Rust
- **Why Rust:**
  - Performance (critical for parsing 1000-page PDFs in <500ms)
  - Memory safety (no segfaults, predictable memory usage)
  - Concurrency (parallel page processing)
  - SIMD optimizations (vectorized operations)
  - Proven for data processing (DuckDB, Polars use Rust)

### Python Bindings
- **Framework:** PyO3 (Rust ↔ Python FFI)
- **Build:** Maturin (Rust + Python packaging)
- **Why PyO3:**
  - Zero-copy data transfer between Rust and Python
  - Minimal overhead (<5% performance penalty)
  - Excellent Python integration
  - Mature and well-tested

### PDF Processing
- **Parser:** pdfium-render (Rust FFI to PDFium)
- **Why:** Battle-tested (Chrome uses it), fast, handles complex PDFs
- **Alternative:** PDF-rs (pure Rust) for v1.5+ if needed

### Indexing & Storage
- **Metadata Storage:** SQLite (embedded database)
- **Why:** Zero-configuration, ACID compliant, excellent Rust bindings
- **Search:** Full-text search (SQLite FTS5)
- **Embedding Storage:** Local SQLite (option for remote storage in v1.5+)

### Embeddings
- **Model:** BGE-small-en-v1.5 (40M parameters)
- **Framework:** ONNX Runtime (optimized inference)
- **Why:** Fast (10ms per embedding), accurate, CPU-friendly
- **Alternative:** Ollama integration for local LLMs

### Dependencies (Minimal)
- `pdfium-render` — PDF parsing
- `rusqlite` — SQLite bindings
- `serde` / `serde_json` — Serialization
- `tokio` — Async runtime
- `ort` — ONNX Runtime for embeddings
- `rayon` — Parallel processing

---

## Architecture Diagram

```
Python Client (PyO3 bindings)
    ↓
Core Engine (Rust)
    ├─ PDF Parser (pdfium-render)
    ├─ Indexer (Metadata extraction)
    ├─ Search Engine (SQLite FTS5)
    ├─ Embedding Generator (ONNX)
    ├─ Markdown Generator
    └─ Context Optimizer
    ↓
Storage Layer
    ├─ SQLite (Metadata + Embeddings)
    └─ File system (PDF cache)
```

---

## Module Breakdown

### Phase 1 (v0.1-v0.5)

**pdf_parser.rs** (Rust)
- PDF structure analysis
- Page-level metadata extraction
- Text region detection
- Heading hierarchy parsing
- Efficient memory-mapped access

**indexer.rs** (Rust)
- Build knowledge index
- Generate page summaries
- Extract keywords
- Store in SQLite
- Manage incremental updates

**search.rs** (Rust)
- Full-text search (SQLite)
- Semantic search (embeddings)
- Ranking and relevance scoring
- Query optimization

**markdown.rs** (Rust)
- Convert PDF pages to markdown
- Preserve structure and formatting
- Token-efficient output

**bindings.py** (PyO3)
- Python API surface
- Type conversions
- Error handling
- Async support

---

### Phase 2-3 (v1.0-v2.0)

**security.rs** (Rust)
- Encryption detection
- Permission checking
- Access control

**ocr.rs** (Rust)
- Scanned PDF detection
- Integration with Mistral OCR
- Handwriting support

**intelligence.rs** (Rust)
- Topic detection
- Entity extraction
- Relationship graphs
- Cost analytics

---

## Performance Characteristics

### Parsing Performance
| Operation | Target | Technology |
|-----------|--------|-----------|
| Parse 1000-page PDF | <500ms | pdfium-render + rayon parallelization |
| Generate page summaries | <2s | Sequential summarization |
| Index all pages | <2s | Batch SQLite inserts |

### Query Performance
| Operation | Target | Technology |
|-----------|--------|-----------|
| Full-text search | <50ms | SQLite FTS5 |
| Semantic search | <100ms | ONNX embeddings + vector ops |
| Top-K retrieval | <50ms | Indexed queries |

### Memory Characteristics
- **PDF Parsing:** Constant memory (streaming)
- **Indexing:** O(1) per page (not O(n))
- **Query:** <100MB for typical operations

---

## Data Flow

### Ingestion Pipeline
```
PDF File
  ↓ (pdfium-render)
PDF Structure
  ↓ (Page extraction)
Pages (individual)
  ↓ (Parallel processing)
Page Metadata
  ├─ Text regions
  ├─ Headings
  ├─ Tables
  ├─ Figures
  └─ Keywords
  ↓
SQLite Index
  ├─ Page metadata
  ├─ Full-text index
  ├─ Embeddings
  └─ Semantic index
```

### Query Pipeline
```
Query ("How to install?")
  ↓ (Embedding)
Query Vector
  ↓ (Similarity search)
Candidate Pages (ranked)
  ↓ (Selection)
Relevant Pages
  ↓ (Markdown generation)
Markdown Content
  ↓ (Context optimization)
Agent-Ready Context
```

---

## Deployment Options

### v1.0 (Local)
- Pure Rust/Python library
- Zero-configuration
- Single-machine deployment
- Pip install

### v1.5+ (Server)
- Rust web server (Actix or Axum)
- REST API
- Docker containerization
- Kubernetes ready

### v2.0+ (Cloud)
- SaaS deployment
- Multi-tenant
- Load balancing
- Caching layer

---

## Why Rust + Python

### Advantages
1. **Performance:** Rust core provides 10-100x speedup vs pure Python
2. **Memory Safety:** No segfaults, predictable behavior
3. **Python Ergonomics:** PyO3 makes Python API seamless
4. **Data Science Ecosystem:** Python users prefer this model (DuckDB, Polars, PyArrow)
5. **Deployment:** Single pip install for end users

### Tradeoffs
- **Development Speed:** Rust slower than Python initially (mitigated by PyO3 testing)
- **Team Requirements:** Need both Rust and Python expertise
- **Compilation:** Longer CI/CD times than pure Python

### Why Not Pure Python?
- PDF parsing and indexing needs performance (100x+ overhead in pure Python)
- Streaming architecture requires low-level control (Rust excels)
- Parallel processing needs efficient threading (GIL in Python is limiting)

### Why Not Pure Rust?
- Python ecosystem critical for ML/data science
- Agent builders expect Python APIs
- Integration with LlamaIndex, LangChain requires Python

**Conclusion:** Rust + Python is the optimal tradeoff for StreamPDF's requirements.

---

## Testing Strategy

### Unit Tests (Rust)
- PDF parsing edge cases
- Index operations
- Query correctness
- Performance benchmarks

### Integration Tests (Python)
- End-to-end workflows
- API compatibility
- Real PDFs (diverse types)
- Performance verification

### Benchmarks
- Parse speed (target: <500ms for 1000 pages)
- Query latency (target: <50ms)
- Memory usage (target: <500MB)
- Token accuracy (target: >98%)

---

## CI/CD

### Build Pipeline
```
Push to GitHub
  ↓
Rust: cargo test
  ↓
Rust: cargo clippy (linting)
  ↓
Python: maturin build (compile PyO3)
  ↓
Python: pytest (Python tests)
  ↓
Performance benchmarks
  ↓
Build wheels (multiple Python versions)
  ↓
PyPI upload (release builds)
```

### Supported Platforms
- Linux x86-64
- macOS x86-64 + ARM64 (M1/M2/M3)
- Windows x86-64

---

## Future Architecture Decisions

### v1.5: Distributed Indexing
- Redis caching layer
- Distributed search (Elasticsearch/Meilisearch)
- Sharding for 1000s of documents

### v2.0: Vector DB Integration
- Pinecone, Weaviate, Milvus support
- Hybrid search (metadata + embeddings)
- Scale to billions of pages

### Enterprise: Multi-tenant
- Kubernetes deployment
- Isolated indexes per tenant
- Custom fine-tuned embeddings per customer

---

## Security & Compliance

### v1.0
- Input validation (no malformed PDFs crash system)
- Output sanitization
- No external API calls (local-first)

### v1.5
- Encryption at rest (SQLite encryption)
- Encryption in transit (TLS)
- Audit logging
- Access control

### v2.0
- HIPAA compliance (healthcare data)
- SOC2 Type II certification
- Compliance dashboards
- Data retention policies

---

## Performance Optimization Roadmap

### v0.5
- Page-level parallelization (rayon)
- Query caching (Rust HashMap)
- Index optimization

### v1.0
- SIMD optimizations (vector operations)
- Memory pooling (reduce allocations)
- Lazy page loading

### v1.5
- Distributed indexing (multi-machine)
- GPU acceleration (optional, for embeddings)
- Incremental updates

### v2.0
- ML-based query optimization
- Predictive prefetching
- Adaptive indexing strategies
