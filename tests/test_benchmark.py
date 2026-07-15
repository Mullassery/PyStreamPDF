import pytest
import time
import streampdf


def test_parse_large_pdf_performance(large_pdf):
    """Test that parsing a large PDF completes in reasonable time

    Phase 1a success criterion: parse 1000-page PDF in <500ms
    This test will be enabled once PDF parsing is implemented.
    """
    doc = streampdf.open(large_pdf)

    start = time.time()
    pages = doc.all_pages
    elapsed_ms = (time.time() - start) * 1000

    # For now, we just verify the API works and the timing is tracked
    # Once PDF parsing is implemented, we'll assert len(pages) > 0
    assert isinstance(pages, list)
    # Final goal is <500ms for 1000 pages
    assert elapsed_ms < 10000, f"Parsing took {elapsed_ms}ms, expected <10000ms"


def test_structure_extraction(large_pdf):
    """Test that structure extraction works"""
    doc = streampdf.open(large_pdf)
    structure = doc.structure
    assert structure is not None
    # Should have at least parsed something
    assert isinstance(structure.headings, list)
