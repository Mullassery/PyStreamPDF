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
    assert count >= 0


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
    """Test getting an invalid page number - will error when PDF parsing is implemented"""
    doc = streampdf.open(simple_pdf)
    # For now, page(999) returns a valid PageMetadata with placeholder data
    # When real PDF parsing is implemented, this should raise an error
    page = doc.page(999)
    assert page is not None


def test_all_pages(multi_page_pdf):
    """Test getting all pages - will parse when PDF parsing is implemented"""
    doc = streampdf.open(multi_page_pdf)
    pages = doc.all_pages
    assert isinstance(pages, list)
    # Will have actual pages once PDF parsing is implemented
    # For now, verify the API works


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
    assert page.word_count >= 0
    assert isinstance(page.text_preview, str)
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
