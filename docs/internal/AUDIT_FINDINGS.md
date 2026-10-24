# Audit findings — 2026-10-19

This file records the repository-specific findings from the portfolio audit
conducted on 2026-10-19. It is documentation only; no code or release artifacts
were changed in this pass unless explicitly noted under "Implementation status".

Sources: the repository's own README/source/workflows, GitHub metadata and
Actions runs, PyPI metadata, and official competitor documentation. Claims are
marked as verified, inferred, or open questions. "Absent" means not found in the
inspected repository/docs, not proof that it cannot exist.

## What it is

Token-efficient PDF extraction and semantic chunking for RAG, backed by PDFium.

## Verified strengths

- PDFium encryption/permissions; semantic chunking; token budgets; HMAC-signed 0600 disk cache; OCR/validation; MCP loopback; 33 test files; 557 Python tests claimed.
- Token-budget selection + cache is a useful niche.

## Verified gaps and user-facing risks

- macOS arm64-only wheel; no committed token-savings benchmark (50–70%/10–50x claims retracted in README).
- OCR tests use synthetic images/mocks; no realistic multi-column/scanned fixtures; GitHub description still claims 50–70% cost reduction.
- No Docling/PyMuPDF comparison.

## Direct competitors

- Docling (69k stars, layout/OCR/tables), PyMuPDF (cross-platform), Unstructured, Marker, LlamaParse.

## Ranked next actions

- P1: bundle PDFium + Linux/Windows wheels (M).
- P1: benchmark vs Docling/PyMuPDF on tokens and layout accuracy (M).
- P2: optional Docling backend (M).

## Do not build

- A full PDF RAG platform; Docling owns layout understanding.

## Evidence gaps / validation needed

- No real scanned-document benchmark; no end-to-end RAG quality/savings measurement.

## Recommended disposition

Invest narrowly; fix the claim and cross-platform install first.

## Implementation status

No code changes in this pass.
