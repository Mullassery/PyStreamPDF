# Competitive intelligence in roadmap and upgrade work

**Policy date:** 2026-10-19

Competitive findings are an input to product decisions, not a one-off report.
Every pending roadmap item, new feature, and routine dependency upgrade should
check the repository's [`AUDIT_FINDINGS.md`](AUDIT_FINDINGS.md) before work
starts, and record the decision in the PR or changelog.

## Required check before building

1. **Read `AUDIT_FINDINGS.md`.** Find the relevant competitor row and the
   ranked next actions. If the finding is stale, update it with a dated source.
2. **Name the competitor and the user problem.** A feature is not justified by
   "competitor has it". State the workflow it unlocks, who needs it, and how
   often. Mark unverified demand as a hypothesis.
3. **Prefer reuse over new code.** Check whether an existing Mullassery repo
   already provides the capability (see `BUNDLES.md` in the profile repo and
   the bundle role file in this repo, when present). Typical reuse:
   - crawling/fetching/robots/SSRF → **MudFish**
   - architecture maps / PR diffs → **CodeAtlas**
   - data-quality contracts / validation → **StatGuardian**
   - token counting / cost tables → **PyTokenCalc**
   - dependency graph / advisories / SBOM → **PyDeepMesh**
   - segmentation / CLV / churn → **ClusterAudienceKit**
   - activation / lineage / PII → **PyReverseETL**
   - fleet state sync → **SyncFleet** (only after conflict resolution)
4. **Choose one disposition:** build, integrate, defer, or reject. Write it
   down. A rejection with a reason is a successful outcome.
5. **For routine upgrades**, check whether the upgrade closes a known
   competitor gap or breaks a differentiated capability. Run the tests that
   cover the affected path; do not merge a green build that silently changes a
   user-visible contract.

## PR / changelog checklist

- [ ] Competitor and source URL/date recorded (or "no direct competitor").
- [ ] User impact and frequency stated; unverified demand labelled.
- [ ] Reuse check done against sibling repos/bundles.
- [ ] Failure mode and rollback considered (especially auth, PII, cost).
- [ ] Docs/roadmap status updated honestly.
- [ ] Tests or a manual verification command included.

## Review cadence

- Refresh the competitor row when a release changes the capability.
- Re-check the full `AUDIT_FINDINGS.md` at least quarterly and before a major
  release.
- If a finding is wrong or stale, correct it in the same PR that relies on it.

## Non-goals

- Copying features for parity.
- Adding a dependency just because a competitor uses it.
- Treating star counts or download counts as proof of user need.

## OSS gap analysis — 2026-10-24

**What matters most here:** install coverage and layout/OCR fidelity. macOS-arm64-only blocks CI/Docker, and PDFium heuristics trail Docling/Marker on multi-column, merged-cell, and scanned pages; ship wheels first, then integrate OCR/layout.

Scope: Compared PyStreamPDF's PDF parsing, layout/OCR, chunking, and caching against four maintained document-extraction projects, weighting what a RAG pipeline author would actually install and measure.

### Comparable OSS projects
| Project | GitHub | License | Last activity | Why it is the comparison |
| --- | --- | --- | --- | --- |
| Unstructured | https://github.com/Unstructured-IO/unstructured | Apache-2.0 | 0.27.34, 2026-10-22 | Broad document ETL + chunking for LLMs; same buyer |
| Docling | https://github.com/docling-project/docling | MIT | v2.142.1, 2026-10-23 | Strong PDF layout/tables/OCR; we already ship a Docling backend |
| PyMuPDF | https://github.com/pymupdf/PyMuPDF | AGPL-3.0 (commercial dual) | 2.0, 2026-10-19 | Fast PDF extraction/tables; the engine our OCR path rasterizes with |
| Marker | https://github.com/datalab-to/marker | Apache-2.0 code; OpenRAIL-M weights | v2.0.0, 2026-07-20 | High-accuracy PDF-to-markdown with selective OCR; direct quality rival |

### Capability comparison
| Capability | Ours | Unstructured | Docling | PyMuPDF | Marker | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| Born-digital text extraction | Yes | Yes | Yes | Yes | Yes | Parity |
| Layout / reading order | Partial | Partial | Yes | Partial | Yes | Large |
| Table extraction | Partial | Partial | Yes | Yes | Yes | Large |
| Scanned PDF OCR | Partial | Partial | Yes | Partial | Yes | Large |
| Format coverage (DOCX/PPTX/HTML) | No | Yes | Yes | Partial | Yes | Large |
| Token-budget chunking | Yes | Partial | Partial | Partial | Partial | Ahead |
| Encryption / permissions | Yes | No | No | Yes | No | Ahead |
| Tamper-evident disk cache | Yes | No | No | No | No | Ahead |
| Cross-platform wheels | No | Yes | Yes | Yes | Yes | Critical |
| Committed accuracy/savings benchmark | No | Yes | Yes | Yes | Yes | Large |

Nuance: "Ours" means PDF only; `pystreampdf[excel]` exports tables to xlsx but does not ingest non-PDF formats. Layout/tables are real (`TableExtractor`, span fixture) but rule-based on PDFium text positions, not a learned layout model. OCR is real Tesseract/Paddle but optional and skipped in CI without the binary. PyMuPDF is AGPL, so its capability lead is not directly reusable for closed-source products; that is a commercial opening for us.

### Gaps that matter (ranked)
1. **Install only works on macOS arm64** — README and `pyproject.toml` confirm one published wheel; every comparable installs on Linux/Windows from PyPI. This is the first blocker for any team evaluating us in CI or Docker. Effort M.
2. **Layout, table, and scan fidelity trail the field** — Docling/Marker use learned layout + OCR models and publish benchmark scores; our PDFium text-position heuristics degrade on multi-column, merged-cell, and scanned pages. This is a capability gap, not a weaker version. Effort L if built, S if integrated.
3. **No committed benchmark for token savings or extraction accuracy** — prior 50–70%/10–50x claims were retracted, and nothing replaced them. Unstructured, Docling, and Marker all publish reproducible harnesses, so buyers cannot compare us. Effort M.
4. **Format coverage is PDF-only** — RAG corpora mix DOCX, PPTX, HTML, and images; competitors ingest all of them. Effort L.
5. **Chunking is token-aware but not query-aware** — `SemanticChunker` splits by element type and `TokenBudgetConfig` scales a 500–1000 token range; there is no query-conditioned selection or reranking despite the "selective retrieval" tagline. Effort M.
6. **OCR path is optional and unmeasured** — tests skip without Tesseract and there is no OCR quality benchmark, so the claimed OCR support is unproven on real scans. Effort S/M.

### Where we are differentiated
- Token-budget chunking with field/keyword `BudgetRule` multipliers is more explicit than competitors' generic chunkers.
- HMAC-SHA256-signed, 0600 disk cache that rejects tampering before deserialization — no comparable ships this.
- PDFium encryption/permission handling that fails closed on a wrong password, under Apache-2.0 (PyMuPDF's equivalent is AGPL).
- Optional Docling backend lets users keep our budget/cache types while borrowing best-in-class layout.

### Disposition
- **Build:** manylinux/Windows wheels and a checked-in benchmark comparing token counts and extraction accuracy against Docling/PyMuPDF.
- **Integrate/reuse:** Docling for layout/tables/OCR (already optional); do not train our own layout model.
- **Defer/reject:** non-PDF ingestion and a full PDF RAG platform; stay a chunking/budget layer over best-in-class parsers.

### Sources
- https://github.com/Unstructured-IO/unstructured (accessed 2026-10-24)
- https://github.com/docling-project/docling (accessed 2026-10-24)
- https://github.com/pymupdf/PyMuPDF (accessed 2026-10-24)
- https://github.com/datalab-to/marker (accessed 2026-10-24)
- https://github.com/datalab-to/marker/releases (accessed 2026-10-24)
- Repo files inspected: `README.md`, `COMPETITIVE_INTELLIGENCE.md`, `AUDIT_FINDINGS.md`, `ARCHITECTURE.md`, `docs/PRODUCT_VISION.md`, `docs/ROADMAP.md`, `pyproject.toml`, `python/pystreampdf/__init__.py`, `python/pystreampdf/_mcp_tools.py`
