# Changelog

All notable changes to StreamPDF are documented here.

---

## [1.5.0] - 2026-07-15 - Enterprise Features

### Added

#### Security Module
- `PdfPermissions` struct with permission flags (can_copy, can_print, can_modify, can_annotate)
- `EncryptionStatus` enum (NotEncrypted, Encrypted)
- `open_with_password()` function for password-protected PDFs
- `check_encryption()` to detect encryption without opening
- `extract_permissions()` to get PDF permission flags
- Python bindings: `PyPdfPermissions` class

#### Audit Module
- `AuditLog` for JSON-lines event logging
- `AuditEvent` with timestamp, doc_path, and event kind
- Event types: DocumentOpened, DocumentIndexed, SearchPerformed, ContextRetrieved
- `record()` and `events()` methods for audit trail management
- Python bindings: `PyAuditLog` class with record_open(), record_search()

#### Forms Module
- `PdfFormField` struct for form field metadata
- `FormFieldType` enum (Text, Checkbox, RadioButton, Dropdown, Signature, Unknown)
- `extract_form_fields()` and `has_forms()` for form detection
- Python bindings: `PyPdfFormField` class
- Note: Implementation stub ready for Phase 4 form extraction

#### Document Enhancements
- `PdfDocument::open_with_password()` for encrypted PDFs
- `PdfDocument::is_encrypted()` static method
- `PdfDocument::permissions()` static method
- `PdfDocument::fingerprint()` via SHA-256 hash
- `PdfDocument::form_fields()` and `has_forms()` methods
- `PageMetadata::is_likely_scanned` flag (true when word_count == 0)

### Changed

#### Phase 2 Fixes

**Full-Text Search**
- FTS5 now indexes `page.text` (full) instead of `text_preview` (300 chars)
- Added `full_text` column to pages table
- Updated schema and trigger to use full text

**Navigator Thread Safety**
- Changed `PdfNavigator.index` from `Option<PdfIndex>` to `Option<Arc<Mutex<PdfIndex>>>`
- New method: `with_shared_index()` for thread-safe index passing
- Fixed `retrieve()` to lock index before searching
- Python binding `navigator_with_index()` now properly shares index

**Heading Level Detection**
- Wired `detect_heading_level()` from `heading_extractor` into parser
- Replaced inline H1 heuristic with H1-H4 classification
- Numeric prefix patterns: 1.→H1, 1.1.→H2, 1.1.1.→H3, 1.1.1.1.→H4
- ALL-CAPS and Title-Case detection for fallback levels

**Breadcrumb Paths**
- `build_heading_path()` now generates real breadcrumbs: "Chapter > Section"
- Finds parent heading with lower level number
- Replaces simple heading text with hierarchical path

**Section Word Counts**
- `extract_hierarchy()` now accepts optional `pages` parameter
- Populates `HeadingSection::total_words` by summing page word counts in section range
- All callers updated to pass pages where available

#### Code Quality
- Fixed all clippy warnings (9 issues resolved)
- Used `is_some_and()` instead of `map_or()`
- Used `div_ceil()` for token estimation
- Removed redundant closures in error handling
- Removed unnecessary type casts
- Simplified match expressions

### Dependencies Added
- `sha2 = "0.10"` for SHA-256 fingerprinting
- `chrono = "0.4"` for timestamp generation (audit logs)

### Testing
- Added 16 new tests (48/48 total passing)
- Security tests (6): encryption, permissions, fingerprint
- Audit tests (5): log creation, event recording, event reading
- Index tests (1): full-text FTS verification
- Document tests (2): fingerprint, forms
- Navigator tests (1): index integration

### Documentation
- Comprehensive README update with:
  - Installation via pip, uv, from source
  - Quick start examples for all major features
  - Enterprise feature examples
  - Current status and roadmap
  - Strategic pillars explained
- New PUBLISHING.md with release instructions
- New CHANGELOG.md (this file)

### Build & Release
- Version bumped to 1.5.0
- Wheel built: `pystreampdf-1.5.0-cp313-cp313-macosx_11_0_arm64.whl` (1.4 MB)
- Source distribution: `pystreampdf-1.5.0.tar.gz` (27 KB)
- Ready for PyPI publication

---

## [1.0.0] - 2026-07-15 - Agent Integration

### Added

#### Agent Navigation
- `PdfNavigator` for hierarchical document browsing
- `chapters()` to get top-level sections
- `pages_for()` to retrieve pages in a section
- `retrieve()` for token-budgeted context assembly
- `section_to_markdown()` for section-specific markdown
- `page_to_markdown()` for single-page markdown
- Python bindings: `PyPdfNavigator` class

#### Hierarchical Structure
- `HeadingSection` struct with heading + page ranges
- `HierarchicalHeadings` for chapter organization
- `extract_hierarchy()` to build H1-H4 structure
- `detect_heading_level()` heuristics (numeric prefix, ALL-CAPS, Title-Case)
- Python bindings: `PyHeadingSection` class

#### Dynamic Markdown
- `MarkdownOutput` with markdown content, token count, page list
- `page_to_markdown()` for page-level conversion
- `section_to_markdown()` with max_tokens budget enforcement
- `heading_to_markdown()` for heading formatting
- `estimate_tokens()` via text.len() / 4 approximation
- Python bindings: `PyMarkdownOutput` class

#### Context Assembly
- `AgentContext` for structured retrieval results
- `ContextSection` with heading path, page numbers, content, relevance
- `assemble()` to map search results to sections
- Breadcrumb path building
- Deduplication by page range
- Token budget enforcement
- Python bindings: `PyAgentContext`, `PyContextSection` classes

#### Page Enhancements
- `PageMetadata.text` field with full page text
- Kept `text_preview` as 300-char summary
- Python binding: `.text` getter on `PyPageMetadata`

### Changed
- `PdfNavigator` architecture designed for document path reconstruction
- No owned document clone required (uses reference pattern)
- Thread-safe Python integration via Arc<Mutex>

---

## [0.5.0] - 2026-07-15 - Intelligent Indexing

### Added

#### SQLite Index
- `PdfIndex` with SQLite backend
- FTS5 full-text search on page text
- `build()` to index documents
- `load()` to reload persisted indexes
- `search()` with BM25 scoring
- `pages_with_heading()` for heading lookup
- `page_range()` for range queries
- Python bindings: `PyPdfIndex`, `PyPageResult` classes

#### Real PDF Parsing
- `parse_document_open()` with pdfium-render integration
- Fallback to synthetic documents if PDFium unavailable
- Text extraction from PDF pages
- Metadata extraction (title, author, creation date)
- Heading detection from document text
- Python bindings: `build_index()` method on PyPdfDocument

#### Performance
- Page-level parsing optimization
- Index persistence to disk or memory (`:memory:`)
- BM25 relevance ranking
- Snippet extraction via FTS triggers

### Dependencies
- `pdfium-render` for real PDF processing
- `rusqlite` for SQLite indexing

---

## [0.1.0] - 2026-07-15 - Foundation

### Added

#### Core Architecture
- `PdfDocument` for document representation
- `PageMetadata` with dimensions, rotation, text preview
- `ContentRegion` for layout analysis
- `BoundingBox` for spatial data
- `RegionType` enum (Text, Heading, Image, Table, Header, Footer)
- `DocumentStructure` for TOC and heading hierarchy
- `HeadingNode` for recursive heading structure
- `TocEntry` for table of contents

#### Error Handling
- Custom `Error` type with specific variants
- `Result<T>` type alias for ergonomic error handling

#### Python Bindings
- Full PyO3 integration via maturin
- 14 Python classes exposing all Rust types
- Getters for all public fields
- Static methods for construction

#### Project Setup
- Cargo workspace with core + python packages
- maturin build system
- pyproject.toml with PyPI metadata
- Python 3.9+ support
- MIT License

#### Testing
- 15 integration tests
- Conftest fixtures for test PDFs
- Simple, multi-page, and large PDF test cases
- reportlab for synthetic PDF generation

#### Documentation
- README with strategic vision
- Architecture overview
- API examples

---

## Future Roadmap

- **v2.0** (Phase 4) — Semantic understanding, citation networks, topic hierarchies
- **v2.5** (Phase 5+) — Advanced cost optimization, multi-format support, OCR integration

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon)

## License

MIT License — See [LICENSE](LICENSE)
