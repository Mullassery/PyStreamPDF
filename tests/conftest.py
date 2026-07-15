import pytest
import tempfile
import os
from pathlib import Path

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    canvas = None


@pytest.fixture(scope="session")
def temp_pdf_dir():
    """Create a temporary directory for test PDFs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def simple_pdf(temp_pdf_dir):
    """Generate a simple single-page PDF"""
    if canvas is None:
        pytest.skip("reportlab not installed")

    pdf_path = os.path.join(temp_pdf_dir, "simple.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Test PDF Document")
    c.drawString(100, 700, "This is a simple test PDF for StreamPDF")
    c.save()
    return pdf_path


@pytest.fixture
def multi_page_pdf(temp_pdf_dir):
    """Generate a multi-page PDF"""
    if canvas is None:
        pytest.skip("reportlab not installed")

    pdf_path = os.path.join(temp_pdf_dir, "multipage.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)

    for page_num in range(1, 6):
        c.drawString(100, 750, f"Page {page_num}")
        c.drawString(100, 700, f"This is page {page_num} of the test PDF")
        c.showPage()

    c.save()
    return pdf_path


@pytest.fixture
def large_pdf(temp_pdf_dir):
    """Generate a large (100-page) PDF for performance testing"""
    if canvas is None:
        pytest.skip("reportlab not installed")

    pdf_path = os.path.join(temp_pdf_dir, "large.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)

    for page_num in range(1, 101):
        c.drawString(100, 750, f"Page {page_num}")
        c.drawString(100, 720, f"Content for page {page_num}")
        c.drawString(100, 690, "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
        c.showPage()

    c.save()
    return pdf_path
