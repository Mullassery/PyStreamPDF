# Queue status — 2026-10-19

This file records what was shipped, what is blocked/failed, and what is rejected for this repository. It complements `AUDIT_FINDINGS.md`.

## Shipped
- No code changes; audit/bundle docs added.

## Blocked / failed
- Linux/Windows wheels, Docling/PyMuPDF benchmark, realistic OCR fixtures.

## Rejected / deferred
- A full PDF RAG platform; Docling owns layout understanding.

## Policy

Any future feature or upgrade must check `AUDIT_FINDINGS.md` and this file before implementation. A blocked item is retried only when its external dependency is available; a rejected item needs new user evidence or a design change to reopen.
