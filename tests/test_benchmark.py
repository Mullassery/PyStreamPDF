import pytest
import time
import pystreampdf


def test_parse_large_pdf_performance(large_pdf):
    """Test that parsing a ~100-page PDF completes in reasonable time.

    This is a smoke test against the `large_pdf` fixture (100 pages,
    reportlab-generated), not a benchmark of the "parse a 1000-page PDF in
    <500ms" target — we don't have a 1000-page fixture in this suite, and the
    assertion below (<10s) is deliberately generous for CI stability rather
    than a tight performance SLA. If/when a real 1000-page fixture is added,
    this should be tightened to actually assert the <500ms goal.
    """
    doc = pystreampdf.open(large_pdf)

    start = time.time()
    pages = doc.all_pages
    elapsed_ms = (time.time() - start) * 1000

    assert isinstance(pages, list)
    # Test fixture generates either 5 or 100 pages depending on file size
    assert len(pages) >= 5, f"Expected at least 5 pages, got {len(pages)}"
    # Generous CI-stability bound, not a performance target (see docstring).
    assert elapsed_ms < 10000, f"Parsing took {elapsed_ms}ms, expected <10000ms"


def test_structure_extraction(large_pdf):
    """Test that structure extraction works"""
    doc = pystreampdf.open(large_pdf)
    structure = doc.structure
    assert structure is not None
    # Should have at least parsed something
    assert isinstance(structure.headings, list)
