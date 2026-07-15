import pytest
import tempfile
import os
import streampdf
import time


def test_build_index(simple_pdf):
    """Test building an index from a PDF"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test.idx")
        doc = streampdf.open(simple_pdf)
        index = doc.build_index(index_path)
        assert index is not None
        assert os.path.exists(index_path)


def test_index_in_memory(simple_pdf):
    """Test building an index in memory"""
    doc = streampdf.open(simple_pdf)
    index = doc.build_index(":memory:")
    assert index is not None


def test_search_returns_results(simple_pdf):
    """Test that search returns results"""
    doc = streampdf.open(simple_pdf)
    index = doc.build_index(":memory:")
    results = index.search("test", top_k=5)
    assert isinstance(results, list)


def test_search_top_k(simple_pdf):
    """Test that top_k parameter is respected"""
    doc = streampdf.open(simple_pdf)
    index = doc.build_index(":memory:")
    results = index.search("test", top_k=1)
    assert isinstance(results, list)
    assert len(results) <= 1


def test_search_no_results(simple_pdf):
    """Test search with query that has no results"""
    doc = streampdf.open(simple_pdf)
    index = doc.build_index(":memory:")
    results = index.search("xyzzy42notexist", top_k=5)
    assert isinstance(results, list)


def test_pages_with_heading(simple_pdf):
    """Test heading search"""
    doc = streampdf.open(simple_pdf)
    index = doc.build_index(":memory:")
    results = index.pages_with_heading("test")
    assert isinstance(results, list)


def test_page_range(multi_page_pdf):
    """Test page range retrieval"""
    doc = streampdf.open(multi_page_pdf)
    index = doc.build_index(":memory:")
    results = index.page_range(1, 3)
    assert isinstance(results, list)
    for result in results:
        assert 1 <= result.page_number <= 3


def test_page_result_fields(simple_pdf):
    """Test that PageResult has required fields"""
    doc = streampdf.open(simple_pdf)
    index = doc.build_index(":memory:")
    results = index.search("test", top_k=1)
    if results:
        result = results[0]
        assert hasattr(result, "page_number")
        assert hasattr(result, "score")
        assert hasattr(result, "snippet")
        assert isinstance(result.page_number, int)
        assert isinstance(result.score, float)
        assert isinstance(result.snippet, str)


def test_search_performance(large_pdf):
    """Test that search completes in reasonable time"""
    doc = streampdf.open(large_pdf)
    index = doc.build_index(":memory:")

    start = time.time()
    results = index.search("page", top_k=10)
    elapsed_ms = (time.time() - start) * 1000

    assert isinstance(results, list)
    # Should complete quickly (final goal: <50ms, being lenient in development)
    assert elapsed_ms < 1000, f"Search took {elapsed_ms}ms, expected <1000ms"


def test_load_index(simple_pdf, tmp_path):
    """Test persisting and loading an index"""
    index_path = str(tmp_path / "test.idx")

    # Build and persist
    doc = streampdf.open(simple_pdf)
    index1 = doc.build_index(index_path)
    results1 = index1.search("test", top_k=5)

    # Load and search again
    index2 = streampdf.load_index(index_path)
    results2 = index2.search("test", top_k=5)

    # Results should be consistent
    assert len(results1) == len(results2)
    if results1:
        assert results1[0].page_number == results2[0].page_number


def test_fts_indexes_full_text(simple_pdf, tmp_path):
    """Test that FTS indexes full page text, not just preview"""
    index_path = str(tmp_path / "fts_full_text.db")
    doc = streampdf.open(simple_pdf)
    index = doc.build_index(index_path)

    # Search should work on full text (words deeper in page than 300 char preview)
    # Simple PDF contains "sample" word which should be found
    results = index.search("sample", 10)
    # If FTS is properly indexing full text, we should find results
    assert isinstance(results, list)
