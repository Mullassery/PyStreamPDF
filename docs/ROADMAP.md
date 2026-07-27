# StreamPDF Roadmap

**Current Version:** v1.5.0

## Vision

StreamPDF provides intelligent document retrieval and extraction with selective conversion, token-efficient RAG integration, and enterprise security.

## Completed Milestones

✅ **v1.0-1.4** — Core Features
- PDF parsing and text extraction
- Semantic indexing (FTS5)
- Token-efficient retrieval
- Heading hierarchy extraction
- Document navigation

✅ **v1.5 (July 2026)** — Workflow Integration
- CLI: `streampdf open`, `index`, `search`, `extract`, `info`, `list`
- REST API (Port 8003) for automation
- n8n, Power Automate, Airflow integration
- Document processing pipelines

## In Progress

⏳ **v1.6 (Aug 2026)** — Security & Encryption
- Encrypted PDF support
- Password-based opening
- Permission flags extraction
- Audit logging

## Planned

📅 **v2.0 (Sep 2026)** — Large Document Optimization
- Lazy page loading
- Page-range opening
- SHA-256 fingerprinting
- Memory efficiency for 10k+ page documents

📅 **v2.1 (Oct 2026)** — OCR & Scanning
- Scanned PDF detection
- OCR integration (Tesseract, PaddleOCR)
- Mixed document handling
- Quality estimation

📅 **v2.5 (Q4 2026)** — Form & Metadata
- PDF form field extraction
- Metadata enrichment
- Invoice/receipt parsing
- Table extraction & structure

📅 **v3.0 (Q1 2027)** — Enterprise Features
- Multi-tenant isolation
- Fine-grained access control
- Compliance reporting
- Advanced search capabilities

## Integration Points

- **RAG Frameworks:** LangChain, LlamaIndex, Semantic Kernel
- **Workflow Tools:** n8n, Power Automate, Temporal, Airflow
- **Storage:** S3, GCS, Azure Blob
- **Indexes:** Pinecone, Weaviate, Chroma

## Priority Features

1. **Security & Encryption** (Q3 2026) — Enterprise security
2. **Large Document Optimization** (Q3 2026) — Memory efficiency
3. **OCR Support** (Q4 2026) — Scanned document handling
4. **Form Extraction** (Q4 2026) — Structured data

## Known Limitations

- Complex PDFs with embedded images have extraction issues
- OCR accuracy limited without preprocessing
- Very large documents (10k+ pages) require indexing time
- Form extraction accuracy ~85-90%

## Community

Contribute:
https://github.com/Mullassery/StreamPDF/issues
