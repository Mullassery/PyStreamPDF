import pytest
import tempfile
import os
from pathlib import Path

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.pdfencrypt import StandardEncryption
except ImportError:
    canvas = None
    StandardEncryption = None


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


# --- Adversarial / security fixtures -----------------------------------

ENCRYPTED_PDF_CORRECT_PASSWORD = "correct-horse-battery-staple"
ENCRYPTED_PDF_WRONG_PASSWORD = "wrong-password-123"


@pytest.fixture
def encrypted_pdf(temp_pdf_dir):
    """Generate a genuinely password-protected PDF (user password required to open)."""
    if canvas is None or StandardEncryption is None:
        pytest.skip("reportlab not installed")

    pdf_path = os.path.join(temp_pdf_dir, "encrypted.pdf")
    enc = StandardEncryption(
        userPassword=ENCRYPTED_PDF_CORRECT_PASSWORD,
        ownerPassword="owner-secret-password",
        canPrint=1,
        canModify=0,
        canCopy=1,
        canAnnotate=1,
    )
    c = canvas.Canvas(pdf_path, pagesize=letter, encrypt=enc)
    c.drawString(100, 750, "This document requires a password to open.")
    c.drawString(100, 700, "Confidential content.")
    c.save()
    return pdf_path


@pytest.fixture
def permission_restricted_pdf(temp_pdf_dir):
    """Generate a PDF that opens with no user password but has restricted
    permissions (owner-password-only protection) — copy/print/modify/annotate
    all disallowed."""
    if canvas is None or StandardEncryption is None:
        pytest.skip("reportlab not installed")

    pdf_path = os.path.join(temp_pdf_dir, "permission_restricted.pdf")
    enc = StandardEncryption(
        userPassword="",  # empty user password: opens without prompting
        ownerPassword="owner-secret-password",
        canPrint=0,
        canModify=0,
        canCopy=0,
        canAnnotate=0,
    )
    c = canvas.Canvas(pdf_path, pagesize=letter, encrypt=enc)
    c.drawString(100, 750, "This document has restricted permissions.")
    c.drawString(100, 700, "Copy/print/modify/annotate are all disallowed.")
    c.save()
    return pdf_path


@pytest.fixture
def malformed_pdf(temp_pdf_dir):
    """A file with a .pdf extension that is not valid PDF content at all."""
    pdf_path = os.path.join(temp_pdf_dir, "malformed.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.7\nThis is not actually a well-formed PDF body.\ngarbage garbage garbage")
    return pdf_path


@pytest.fixture
def truncated_pdf(temp_pdf_dir, simple_pdf):
    """A validly-started PDF that is truncated mid-stream (simulates a
    partial/interrupted download or write)."""
    pdf_path = os.path.join(temp_pdf_dir, "truncated.pdf")
    with open(simple_pdf, "rb") as f:
        data = f.read()
    # Cut off the second half, including the xref table / trailer.
    truncated = data[: len(data) // 2]
    with open(pdf_path, "wb") as f:
        f.write(truncated)
    return pdf_path


@pytest.fixture
def deeply_nested_pdf(temp_pdf_dir):
    """A hand-crafted PDF with a deeply nested array object, to exercise
    parser robustness against pathological structures."""
    pdf_path = os.path.join(temp_pdf_dir, "deeply_nested.pdf")

    depth = 500
    nested = "0"
    for _ in range(depth):
        nested = f"[{nested}]"

    body = (
        "%PDF-1.7\n"
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        f"/Nested {nested} >>\nendobj\n"
        "trailer\n<< /Root 1 0 R >>\n"
    )
    with open(pdf_path, "wb") as f:
        f.write(body.encode("latin-1"))
    return pdf_path
