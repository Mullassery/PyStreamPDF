import pytest
import os
import streampdf


def test_open_simple_pdf(simple_pdf):
    """Test opening a simple PDF"""
    doc = streampdf.open(simple_pdf)
    assert doc is not None
    assert doc.path == simple_pdf


def test_open_nonexistent_pdf():
    """Test that opening a non-existent PDF raises an error"""
    with pytest.raises(Exception):
        streampdf.open("/nonexistent/path/to/pdf.pdf")


def test_page_count_simple(simple_pdf):
    """Test getting page count from simple PDF"""
    doc = streampdf.open(simple_pdf)
    count = doc.page_count
    assert count >= 1  # Single-page PDF


def test_metadata(simple_pdf):
    """Test getting metadata from PDF"""
    doc = streampdf.open(simple_pdf)
    meta = doc.metadata
    assert isinstance(meta, dict)
    assert "page_count" in meta


def test_get_page(simple_pdf):
    """Test getting a specific page"""
    doc = streampdf.open(simple_pdf)
    page = doc.page(1)
    assert page is not None
    assert page.page_number == 1
    assert page.width > 0
    assert page.height > 0


def test_get_page_invalid(simple_pdf):
    """Test that getting an invalid page number raises an error"""
    doc = streampdf.open(simple_pdf)
    with pytest.raises(Exception):
        # page(999) should raise since simple_pdf only has ~5 pages
        doc.page(999)


def test_all_pages(multi_page_pdf):
    """Test getting all pages"""
    doc = streampdf.open(multi_page_pdf)
    pages = doc.all_pages
    assert isinstance(pages, list)
    assert len(pages) == 5  # Multi-page PDF has 5 pages


def test_page_metadata_fields(simple_pdf):
    """Test that page metadata has required fields"""
    doc = streampdf.open(simple_pdf)
    page = doc.page(1)

    assert hasattr(page, "page_number")
    assert hasattr(page, "width")
    assert hasattr(page, "height")
    assert hasattr(page, "rotation")
    assert hasattr(page, "word_count")
    assert hasattr(page, "text_preview")
    assert hasattr(page, "regions")

    assert page.page_number > 0
    assert page.width > 0
    assert page.height > 0
    assert page.rotation in [0, 90, 180, 270]
    # Word count should be > 0 for real PDFs
    assert page.word_count > 0
    assert len(page.text_preview) > 0
    assert isinstance(page.regions, list)


def test_document_structure(simple_pdf):
    """Test getting document structure"""
    doc = streampdf.open(simple_pdf)
    structure = doc.structure
    assert structure is not None
    assert hasattr(structure, "toc")
    assert hasattr(structure, "headings")
    assert isinstance(structure.toc, list)
    assert isinstance(structure.headings, list)


def test_page_text_field(simple_pdf):
    """Test that pages have full text field"""
    doc = streampdf.open(simple_pdf)
    page = doc.page(1)
    assert hasattr(page, "text")
    assert isinstance(page.text, str)
    assert len(page.text) > 0


def test_fingerprint(simple_pdf):
    """Test PDF fingerprinting"""
    doc = streampdf.open(simple_pdf)
    fp = doc.fingerprint()
    assert isinstance(fp, str)
    assert len(fp) == 64  # SHA-256 in hex


def test_has_forms(simple_pdf):
    """Test form detection"""
    doc = streampdf.open(simple_pdf)
    has_forms = doc.has_forms()
    assert isinstance(has_forms, bool)


def test_form_fields(simple_pdf):
    """Test form field extraction"""
    doc = streampdf.open(simple_pdf)
    fields = doc.form_fields()
    assert isinstance(fields, list)
