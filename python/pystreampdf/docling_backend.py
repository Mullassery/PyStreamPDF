"""Optional Docling backend for high-fidelity layout, table and OCR extraction.

PyStreamPDF's native Rust/PDFium path is fast and remains the default.  For
complex documents (multi-column layouts, tables, scanned pages) users can opt
into Docling (MIT) and receive the same ``ContentChunk`` objects, so caching,
budgeting and downstream RAG code keep working unchanged.

Docling is an optional dependency::

    pip install "pystreampdf[docling]"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .extraction import ContentChunk, ElementType, SemanticChunker
from .tokenizer import count_tokens

logger = logging.getLogger(__name__)


class DoclingUnavailable(RuntimeError):
    """Raised when Docling is requested but not installed."""


@dataclass
class DoclingExtraction:
    """Result metadata for a Docling extraction."""

    chunks: list[ContentChunk]
    page_count: int = 0
    backend: str = "docling"


def _require_docling():
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise DoclingUnavailable(
            "Docling is not installed. Install the optional backend with "
            '`pip install "pystreampdf[docling]"` (or `pip install docling`).'
        ) from exc
    return DocumentConverter


def _page_no(item: Any) -> int:
    prov = getattr(item, "prov", None) or []
    if prov:
        page = getattr(prov[0], "page_no", None)
        if page is not None:
            try:
                return int(page)
            except (TypeError, ValueError):
                pass
    return 1


def _item_text(item: Any, document: Any) -> str:
    # TextItem/TitleItem/SectionHeaderItem expose .text; TableItem and
    # PictureItem expose export_to_markdown.
    text = getattr(item, "text", None)
    if isinstance(text, str) and text.strip():
        return text
    export = getattr(item, "export_to_markdown", None)
    if callable(export):
        for kwargs in ({"doc": document}, {}):
            try:
                value = export(**kwargs)
            except TypeError:
                continue
            except Exception:
                break
            if isinstance(value, str) and value.strip():
                return value
    caption = getattr(item, "caption_text", None)
    if callable(caption):
        try:
            value = caption(document)
            if isinstance(value, str) and value.strip():
                return value
        except Exception:
            pass
    return ""


def _element_type(label: str, item: Any) -> ElementType:
    label = (label or "").lower()
    if "table" in label:
        return ElementType.TABLE
    if "picture" in label or "image" in label:
        return ElementType.IMAGE
    if "header" in label or "title" in label:
        return ElementType.HEADING
    if "list" in label:
        return ElementType.LIST
    if "form" in label:
        return ElementType.FORM
    return ElementType.TEXT


def document_to_chunks(
    document: Any,
    *,
    target_tokens: int = 500,
    split_large_text: bool = True,
) -> list[ContentChunk]:
    """Convert a Docling ``DoclingDocument`` into PyStreamPDF chunks.

    This function is intentionally duck-typed so it can be tested without
    installing the heavy Docling dependency.
    """
    chunks: list[ContentChunk] = []
    chunker = SemanticChunker(target_tokens=target_tokens)

    def add_chunk(text: str, label: str, item: Any) -> None:
        text = text.strip()
        if not text:
            return
        page = _page_no(item)
        element_type = _element_type(label, item)
        # Do not split tables/structural objects; split long prose so the
        # existing token-budget contract is preserved.
        if (
            split_large_text
            and element_type in (ElementType.TEXT, ElementType.HEADING, ElementType.LIST)
            and count_tokens(text) > target_tokens
        ):
            chunks.extend(
                chunker.chunk_content(
                    text,
                    element_type=element_type,
                    page_start=page,
                    page_end=page,
                )
            )
            return
        chunks.append(
            ContentChunk(
                content=text,
                chunk_type=element_type,
                page_start=page,
                page_end=page,
                estimated_tokens=count_tokens(text),
                confidence=1.0,
            )
        )

    iterate = getattr(document, "iterate_items", None)
    if callable(iterate):
        for entry in iterate():
            # Docling yields (item, level) tuples in current releases; be
            # tolerant of a bare item for forward/backward compatibility.
            item = entry[0] if isinstance(entry, tuple) and entry else entry
            if item is None:
                continue
            label = str(getattr(item, "label", "") or "")
            add_chunk(_item_text(item, document), label, item)
    else:
        export = getattr(document, "export_to_markdown", None)
        if not callable(export):
            raise TypeError(
                "document must be a DoclingDocument (iterate_items or "
                "export_to_markdown required)"
            )
        text = export()
        chunks.extend(
            chunker.chunk_content(
                text,
                element_type=ElementType.TEXT,
                page_start=1,
                page_end=(
                    max(1, getattr(document, "num_pages", lambda: 1)())
                    if callable(getattr(document, "num_pages", None))
                    else 1
                ),
            )
        )

    return chunks


class DoclingBackend:
    """Opt-in Docling extraction backend."""

    name = "docling"

    def __init__(self, target_tokens: int = 500):
        self.target_tokens = target_tokens

    @staticmethod
    def is_available() -> bool:
        try:
            import docling  # noqa: F401
        except ImportError:
            return False
        return True

    def extract(self, pdf_path: str | Path) -> DoclingExtraction:
        DocumentConverter = _require_docling()
        path = Path(pdf_path)
        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {path}")
        result = DocumentConverter().convert(str(path))
        document = result.document
        chunks = document_to_chunks(document, target_tokens=self.target_tokens)
        pages = getattr(document, "num_pages", None)
        page_count = pages() if callable(pages) else getattr(document, "page_count", 0) or 0
        return DoclingExtraction(chunks=chunks, page_count=int(page_count or 0))


def extract_with_docling(
    pdf_path: str | Path,
    *,
    target_tokens: int = 500,
) -> DoclingExtraction:
    """Extract a PDF through Docling and return PyStreamPDF chunks."""
    return DoclingBackend(target_tokens=target_tokens).extract(pdf_path)


__all__ = [
    "DoclingBackend",
    "DoclingExtraction",
    "DoclingUnavailable",
    "document_to_chunks",
    "extract_with_docling",
]
