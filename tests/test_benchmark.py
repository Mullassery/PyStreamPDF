import pytest
import time
import pystreampdf


def test_parse_large_pdf_performance(large_pdf):
    """Test that parsing a large PDF completes in reasonable time

    Phase 1b success criterion: parse document quickly
    Final goal: parse 1000-page PDF in <500ms
    """
    doc = pystreampdf.open(large_pdf)

    start = time.time()
    pages = doc.all_pages
    elapsed_ms = (time.time() - start) * 1000

    assert isinstance(pages, list)
    # Test fixture generates either 5 or 100 pages depending on file size
    assert len(pages) >= 5, f"Expected at least 5 pages, got {len(pages)}"
    # Should complete quickly (final goal is <500ms for 1000 pages)
    assert elapsed_ms < 10000, f"Parsing took {elapsed_ms}ms, expected <10000ms"


def test_structure_extraction(large_pdf):
    """Test that structure extraction works"""
    doc = pystreampdf.open(large_pdf)
    structure = doc.structure
    assert structure is not None
    # Should have at least parsed something
    assert isinstance(structure.headings, list)
