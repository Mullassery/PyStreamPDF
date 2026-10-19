"""Multi-column PDF extraction using a real generated PDF.

This closes the "only single-glyph synthetic images/mocks" gap for *text*
layout with an actual two-column PDF. Scanned/rasterized OCR PDFs are **not**
covered here and remain untested.
"""

from __future__ import annotations

import pytest

pytest.importorskip("reportlab")

from reportlab.pdfgen import canvas  # noqa: E402

import pystreampdf  # noqa: E402


def test_extracts_both_columns_from_real_pdf(tmp_path):
    path = tmp_path / "two-column.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 750, "LEFT COLUMN ALPHA")
    pdf.drawString(320, 750, "RIGHT COLUMN BETA")
    pdf.showPage()
    pdf.save()

    doc = pystreampdf.open(str(path))
    text = doc.page(1).text

    assert "LEFT COLUMN ALPHA" in text
    assert "RIGHT COLUMN BETA" in text
