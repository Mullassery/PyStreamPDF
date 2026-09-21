# Changelog

All notable changes to StreamPDF are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Fixed

- `Cargo.toml` and `pyproject.toml` `repository`/`Issues` URLs pointed at
  `github.com/Mullassery/StreamPDF` (missing the `Py` prefix) instead of
  the actual repo, `github.com/Mullassery/PyStreamPDF` — wrong metadata on
  crates.io/PyPI project pages.
- README.md's Documentation section linked to `docs/QUICKSTART.md`,
  `docs/EXTRACTION.md`, and `docs/TOKEN_BUDGETS.md`, none of which exist
  in this repo — replaced with links to the docs and examples that
  actually exist.
- `CONTRIBUTING.md` still said contributions are licensed "MIT" after the
  project relicensed to Apache-2.0 (commit `5c3a6de`) — corrected.
- `docs/PRODUCT_VISION.md` described the project's status as "Actively
  maintained" — removed per this repo's own honesty policy (see
  `docs/ROADMAP.md`'s "Honest status" section); status is whatever the
  itemized lists in that file and README's "Known Issues" actually say.
- README.md described the test suite as "Production-Ready" — reworded to
  "Tested" since "production-ready" isn't a claim this repo backs with
  anything beyond the test count itself.
- `.github/workflows/ci.yml` used `actions/setup-python@v4`, which
  `actionlint` flags as too old to run on GitHub Actions' current
  runners — bumped to `@v7`.

### Added

- `.github/workflows/audit.yml` — `cargo audit` (Rust) and `pip-audit`
  (Python) dependency vulnerability scan, on push/PR to `main` and a
  weekly schedule. Not runnable/verified in this sandbox (no network
  access to the crates.io/PyPI advisory databases here) — needs a real
  CI run to confirm it passes.
- `[tool.maturin] include = ["LICENSE"]` in `pyproject.toml` as a
  precaution against sdist builds omitting `LICENSE` (a recurring issue
  in sibling projects using the same maturin/PyO3 setup); not confirmed
  broken here specifically (maturin isn't installed in this sandbox to
  test), but cheap and safe to add regardless.
- `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/pull_request_template.md`.

---

## [2.3.0] - 2026-08-25 - Real MCP Tool Implementations

`PyStreamPDFMCPHandler` (`python/pystreampdf/_mcp_tools.py`) previously
ignored `pdf_path` entirely in every one of its 12 tool methods and
returned the exact same hardcoded fixture dict regardless of input --
most notably `validate_pdf` always reported `is_valid: True`, even for a
nonexistent or genuinely corrupted file, and `apply_ocr` always reported
`confidence: 0.92` without ever running OCR.

### Fixed (correctness / honesty)

- All 12 MCP tool handlers now call into the real, already-tested
  implementations elsewhere in this package instead of returning fixture
  data:
  - `extract_text` / `extract_metadata` / `detect_document_structure` /
    `detect_forms` -- the Rust-backed `pystreampdf.open()` document API
    (`.page()`, `.metadata`, `.structure`, `.form_fields()`).
  - `extract_tables` / `extract_images` -- real content regions
    (`page.regions`, filtered by `region_type`).
  - `apply_ocr` -- the real hybrid `ocr.OcrPipeline` (routes scanned pages
    through Tesseract/PaddleOCR via `is_likely_scanned`, text pages through
    the existing fast Rust extraction). Honestly reports
    `{"status": "unavailable"}` if no OCR provider is installed, rather
    than fabricating a confidence score.
  - `chunk_document` -- the real, already-exported `SemanticChunker`.
  - `validate_pdf` -- attempts a real `pystreampdf.open()` (reporting the
    real PDFium error on failure) and runs `validation.TextValidator`
    against sampled page text for corruption/repetition signals.
  - `extract_citations` -- a real (regex-based, not fabricated-count)
    citation detector for numbered (`[1]`) and author-year
    (`(Smith, 2020)`) styles.
  - `export_processed_document` -- real markdown (via the Rust navigator's
    `page_to_markdown`) and JSON export.
- `detect_language` and `export_processed_document(output_format="html"|"docx")`
  have no real implementation anywhere in this package (no
  language-detection library is a dependency; no HTML/DOCX writer exists)
  -- these now return `{"status": "not_implemented", ...}` rather than a
  fabricated result.
- New `tests/test_mcp_tools.py` (21 tests) exercises all of the above
  against real PDFs generated with `reportlab`, including the corrupted-
  and nonexistent-file cases that the old fixture-backed `validate_pdf`
  could never actually fail.

## [2.2.0] - 2026-08-12 - Real Security Behavior, Honest Failure Signaling

This release fixes security-behavior bugs from earlier versions where the
security module's public API existed but was backed by stubs. Callers'
security assumptions materially change with this release, hence the minor
version bump rather than a patch.

### Fixed (security / correctness)

- **`check_encryption()` / `PdfDocument::is_encrypted()`**: previously always
  returned `NotEncrypted` regardless of the actual file. Now uses PDFium's
  real document open + security-handler-revision APIs to detect encryption,
  including PDFs that are encrypted but openable with an empty user password
  (owner-password-only / permission-only protection).
- **`extract_permissions()` / `PdfDocument::permissions()`**: previously
  always returned a hardcoded, mostly-permissive default. Now reads PDFium's
  real permission bitflags (`FPDF_GetDocPermissions`) via the document's
  security handler revision.
- **`open_with_password()` / `PdfDocument::open_with_password()`**:
  previously ignored the supplied password entirely and parsed the document
  unauthenticated. Now passes the password through to PDFium and **fails
  closed** (`Error::EncryptedPdf`) on a missing or incorrect password.
- **Silent content fabrication removed**: `pdf_parser.rs` no longer falls
  back to a fabricated placeholder document ("Page N content goes here...")
  with a guessed page count when PDFium fails to parse a file. Parse
  failures (corrupt/truncated/malformed files, wrong password, missing
  PDFium library) now return a real `Error`, never fake-but-plausible data.
- **Cache deserialization hardening**: the L2 disk cache no longer calls
  `pickle.load()` on unverified bytes. Every cache entry is now HMAC-SHA256
  signed with a key generated on first use and stored with owner-only (0600)
  permissions; the signature is verified with a constant-time comparison
  before any unpickling, and a missing/invalid signature is treated as a
  cache miss (and the file is deleted) rather than deserialized.
- **MCP/DAB connector hardened**: default bind host changed from `0.0.0.0`
  to `127.0.0.1`, CORS defaults to no cross-origin access instead of `*`,
  and default permissions are scoped to a read-only "local" role instead of
  wildcard `actions: ["*"], roles: ["*"]`. Wider exposure now requires an
  explicit `allow_remote=True` opt-in.
- **Removed `shell=True` subprocess pattern** in `cli_daemon.py` in favor of
  an argv list (no shell involved).
- **Fixed CI Python test wiring**: the pytest step checked for tests at
  `python/tests/` (which doesn't exist) instead of the real suite at
  repo-root `tests/`, so CI was silently running zero Python tests. CI now
  builds the native extension via `maturin develop` and runs the real suite.
- **Fixed missing `pyyaml` dependency**: `token_budget.py` imports `yaml`
  unconditionally at package-import time, but `pyyaml` was never declared as
  a dependency in `pyproject.toml` -- a clean `pip install pystreampdf`
  could fail to import. Added `pyyaml>=6.0` to `dependencies`.
- **Resolved duplicate/shadowing `pystreampdf` package**: a stray
  repo-root `pystreampdf/` directory (containing only the MCP connector
  modules, no `__init__.py`) shadowed the real, packaged `python/pystreampdf/`
  source directory. Moved those modules into the real package and removed
  the root-level duplicate.
- **Real tokenization**: added `pystreampdf.tokenizer`, which uses
  `tiktoken` (optional dependency) for exact BPE token counts when
  installed, falling back to the previous `len(text) / 4` heuristic
  (explicitly labeled as approximate) otherwise. Wired into
  `extraction.py`, `optimization/metadata.py`, and `semantic/assembler.py`.

### Added

- Real adversarial PDF test fixtures: genuinely password-protected PDFs
  (correct/incorrect password), permission-restricted PDFs, malformed PDFs,
  truncated PDFs, and a deeply-nested-object PDF, exercising the real
  `security.rs` implementation end-to-end.

### Hygiene

- Removed stray `.bak` files (`README.md.bak`,
  `python/pystreampdf/intelligence/__init__.py.bak`).
- Synced `Cargo.toml` / `python/pystreampdf/__init__.py` version strings
  (previously drifted: 2.1.2 vs 2.1.1).

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

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Apache License 2.0 — See [LICENSE](LICENSE)
