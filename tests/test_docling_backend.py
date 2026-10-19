"""Docling adapter tests are dependency-free: a duck-typed fake document
exercises the mapping/normalization without downloading models."""

from __future__ import annotations

import pytest

from pystreampdf.docling_backend import (
    DoclingBackend,
    DoclingUnavailable,
    document_to_chunks,
)
from pystreampdf.extraction import ElementType


class _Prov:
    def __init__(self, page_no):
        self.page_no = page_no


class _Item:
    def __init__(self, text, label, page):
        self.text = text
        self.label = label
        self.prov = [_Prov(page)]


class _TableItem:
    label = "table"

    def __init__(self, markdown, page):
        self.markdown = markdown
        self.prov = [_Prov(page)]

    def export_to_markdown(self, **kwargs):
        return self.markdown


class _FakeDoc:
    def __init__(self):
        self.num_pages = lambda: 2

    def iterate_items(self):
        return [
            (_Item("# Results", "section_header", 1), 0),
            (_Item("Revenue grew.", "text", 2), 0),
            (_TableItem("|q|v|\n|-|-|\n|a|1|", 2), 0),
        ]


def test_document_to_chunks_preserves_pages_and_types():
    chunks = document_to_chunks(_FakeDoc(), target_tokens=100)
    assert [c.chunk_type for c in chunks] == [
        ElementType.HEADING,
        ElementType.TEXT,
        ElementType.TABLE,
    ]
    assert [c.page_start for c in chunks] == [1, 2, 2]
    assert chunks[2].content.startswith("|q|v|")


def test_docling_is_optional_and_fails_actionably(monkeypatch):
    import pystreampdf.docling_backend as mod

    monkeypatch.setattr(
        mod,
        "_require_docling",
        lambda: (_ for _ in ()).throw(DoclingUnavailable('pip install "pystreampdf[docling]"')),
    )
    with pytest.raises(DoclingUnavailable, match="pystreampdf\\[docling\\]"):
        DoclingBackend().extract("missing.pdf")


def test_docling_unavailable_reports_install_hint():
    if DoclingBackend.is_available():
        pytest.skip("docling is installed")
    with pytest.raises(DoclingUnavailable, match="pystreampdf\\[docling\\]"):
        DoclingBackend().extract("missing.pdf")
