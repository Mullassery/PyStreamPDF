"""Realistic scanned multi-column and table-span fixtures (C2).

The scanned fixture is a genuine rasterized PDF: reportlab renders a
two-column page with a real text layer, PyMuPDF rasterizes it at ~150 dpi,
and the resulting image is embedded in a new, text-free PDF. The OCR test uses
the actual OcrPipeline/Tesseract provider and skips when tesseract is not
installed; no OCR output is mocked or fabricated.
"""

from __future__ import annotations

import re

import pytest

pytest.importorskip("reportlab")
fitz = pytest.importorskip("fitz")

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle  # noqa: E402

import pystreampdf  # noqa: E402


def _write_two_column_source(path):
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.setTitle("Rasterized multi-column fixture")
    pdf.setFont("Helvetica", 14)
    left_lines = ["LEFT COLUMN ALPHA", "left line two", "left line three"]
    right_lines = ["RIGHT COLUMN BETA", "right line two", "right line three"]
    for index, (left, right) in enumerate(zip(left_lines, right_lines)):
        baseline = 720 - index * 24
        pdf.drawString(50, baseline, left)
        pdf.drawString(320, baseline, right)
    pdf.showPage()
    pdf.save()


def _rasterize_to_image_only(source, destination, dpi=150):
    with fitz.open(str(source)) as source_doc:
        source_page = source_doc[0]
        pixmap = source_page.get_pixmap(dpi=dpi)
        image_png = pixmap.tobytes("png")
        width, height = source_page.rect.width, source_page.rect.height

    with fitz.open() as scanned_doc:
        scanned_page = scanned_doc.new_page(width=width, height=height)
        scanned_page.insert_image(scanned_page.rect, stream=image_png)
        scanned_doc.save(str(destination))
    return destination


@pytest.fixture
def scanned_multi_column_pdf(tmp_path):
    source = tmp_path / "two-column-source.pdf"
    _write_two_column_source(source)
    return _rasterize_to_image_only(source, tmp_path / "scanned-two-column.pdf")


def _write_rotated_source(path):
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.setTitle("Mildly rotated scanned fixture")
    pdf.saveState()
    pdf.translate(306, 396)
    pdf.rotate(2.0)
    pdf.translate(-306, -396)
    pdf.setFont("Helvetica-Bold", 16)
    lines = [
        "ROTATED SKEW SAMPLE",
        "slightly tilted paragraph line",
        "third tilted line",
    ]
    for index, line in enumerate(lines):
        pdf.drawString(72, 680 - index * 28, line)
    pdf.restoreState()
    pdf.showPage()
    pdf.save()


@pytest.fixture
def rotated_scanned_pdf(tmp_path):
    source = tmp_path / "rotated-source.pdf"
    _write_rotated_source(source)
    return _rasterize_to_image_only(source, tmp_path / "scanned-rotated.pdf")


def _write_serif_source(path):
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.setTitle("Serif font scanned fixture")
    pdf.setFont("Times-Roman", 22)
    lines = [
        "SERIF FONT SAMPLE",
        "Times Roman at twenty two points",
        "different face and size",
    ]
    for index, line in enumerate(lines):
        pdf.drawString(72, 680 - index * 36, line)
    pdf.showPage()
    pdf.save()


@pytest.fixture
def serif_scanned_pdf(tmp_path):
    source = tmp_path / "serif-source.pdf"
    _write_serif_source(source)
    return _rasterize_to_image_only(source, tmp_path / "scanned-serif.pdf")


def test_scanned_multicolumn_pdf_is_a_real_image_only_pdf(scanned_multi_column_pdf):
    page = pystreampdf.open(str(scanned_multi_column_pdf)).page(1)

    assert page.text.strip() == ""
    assert page.is_likely_scanned is True

    with fitz.open(str(scanned_multi_column_pdf)) as source:
        assert source[0].get_images(full=True)


@pytest.mark.parametrize("fixture_name", ["rotated_scanned_pdf", "serif_scanned_pdf"])
def test_additional_scanned_fixtures_are_image_only(request, fixture_name):
    path = request.getfixturevalue(fixture_name)
    page = pystreampdf.open(str(path)).page(1)

    assert page.text.strip() == ""
    assert page.is_likely_scanned is True

    with fitz.open(str(path)) as source:
        assert source[0].get_images(full=True)


def _tesseract_available():
    try:
        from pystreampdf.ocr.providers.tesseract import TesseractProvider
    except ImportError:
        return False
    try:
        return TesseractProvider().is_available()
    except Exception:
        return False


@pytest.mark.skipif(
    not _tesseract_available(),
    reason="tesseract/pytesseract not installed",
)
def test_ocr_extracts_both_columns_from_rasterized_pdf(scanned_multi_column_pdf):
    from pystreampdf.ocr import OcrPipeline

    pages = OcrPipeline().process_document(str(scanned_multi_column_pdf))

    assert len(pages) == 1
    assert pages[0].source == "ocr"
    assert pages[0].is_scanned is True

    normalized = re.sub(r"\s+", " ", pages[0].text).upper()
    assert "LEFT COLUMN ALPHA" in normalized
    assert "RIGHT COLUMN BETA" in normalized


@pytest.mark.skipif(
    not _tesseract_available(),
    reason="tesseract/pytesseract not installed",
)
def test_ocr_reads_mildly_rotated_scanned_pdf(rotated_scanned_pdf):
    from pystreampdf.ocr import OcrPipeline

    pages = OcrPipeline().process_document(str(rotated_scanned_pdf))

    assert len(pages) == 1
    assert pages[0].source == "ocr"
    normalized = re.sub(r"\s+", " ", pages[0].text).upper()
    assert "ROTATED SKEW SAMPLE" in normalized
    assert "TILTED" in normalized


@pytest.mark.skipif(
    not _tesseract_available(),
    reason="tesseract/pytesseract not installed",
)
def test_ocr_reads_serif_font_scanned_pdf(serif_scanned_pdf):
    from pystreampdf.ocr import OcrPipeline

    pages = OcrPipeline().process_document(str(serif_scanned_pdf))

    assert len(pages) == 1
    assert pages[0].source == "ocr"
    normalized = re.sub(r"\s+", " ", pages[0].text).upper()
    assert "SERIF FONT SAMPLE" in normalized
    assert "TIMES ROMAN" in normalized


def _write_table_span_pdf(path):
    data = [
        ["FY2024 Revenue Summary", "", "", ""],
        ["Region", "Q1", "Q2", "Q3"],
        ["North America", "$120", "$130", "$140"],
        ["Europe", "$90", "$95", "$100"],
        ["Grand Total", "", "", "$510"],
    ]
    table = Table(data, colWidths=[150, 80, 80, 80])
    table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("SPAN", (0, 4), (2, 4)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("BACKGROUND", (0, 4), (-1, 4), colors.whitesmoke),
                ("GRID", (0, 1), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    doc.build([table])


@pytest.fixture
def table_span_pdf(tmp_path):
    path = tmp_path / "table-with-spans.pdf"
    _write_table_span_pdf(path)
    return path


def test_table_spans_keep_all_cell_text(table_span_pdf):
    text = pystreampdf.open(str(table_span_pdf)).page(1).text
    normalized = re.sub(r"\s+", " ", text)

    for expected in [
        "FY2024 Revenue Summary",
        "Region",
        "North America",
        "$120",
        "Europe",
        "$100",
        "Grand Total",
        "$510",
    ]:
        assert expected in normalized


@pytest.mark.skipif(
    not _tesseract_available(),
    reason="tesseract/pytesseract not installed",
)
def test_real_tesseract_ocr_reports_provider_and_word_regions(scanned_multi_column_pdf):
    from pystreampdf.ocr import OcrPipeline

    pages = OcrPipeline().process_document(str(scanned_multi_column_pdf), provider_name="tesseract")

    result = pages[0].ocr_result
    assert result is not None
    assert result.provider_name == "tesseract"
    assert result.confidence > 0.0
    assert result.regions
    words = {region.text.upper() for region in result.regions}
    assert "COLUMN" in words or any("COLUMN" in word for word in words)
