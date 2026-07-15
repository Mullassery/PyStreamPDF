import pytest
import pystreampdf


def test_navigator_creation(simple_pdf):
    """Test creating a navigator from a document"""
    doc = pystreampdf.open(simple_pdf)
    nav = doc.navigator()
    assert nav is not None


def test_chapters_list(simple_pdf):
    """Test getting chapters from navigator"""
    doc = pystreampdf.open(simple_pdf)
    nav = doc.navigator()
    chapters = nav.chapters()
    assert isinstance(chapters, list)


def test_chapter_fields(simple_pdf):
    """Test that chapters have required fields"""
    doc = pystreampdf.open(simple_pdf)
    nav = doc.navigator()
    chapters = nav.chapters()
    if chapters:
        chapter = chapters[0]
        assert hasattr(chapter, "heading")
        assert hasattr(chapter, "start_page")
        assert hasattr(chapter, "end_page")
        assert hasattr(chapter, "total_words")


def test_page_to_markdown(simple_pdf):
    """Test markdown generation for a single page"""
    doc = pystreampdf.open(simple_pdf)
    nav = doc.navigator()
    md_output = nav.page_to_markdown(1)
    assert md_output is not None
    assert hasattr(md_output, "markdown")
    assert hasattr(md_output, "estimated_tokens")
    assert hasattr(md_output, "pages_included")


def test_markdown_output_fields(simple_pdf):
    """Test MarkdownOutput fields"""
    doc = pystreampdf.open(simple_pdf)
    nav = doc.navigator()
    md = nav.page_to_markdown(1)
    assert isinstance(md.markdown, str)
    assert isinstance(md.estimated_tokens, int)
    assert isinstance(md.pages_included, list)
    assert md.estimated_tokens > 0


def test_retrieve_without_index(simple_pdf):
    """Test that retrieve raises error when no index available"""
    doc = pystreampdf.open(simple_pdf)
    nav = doc.navigator()
    with pytest.raises(Exception):
        nav.retrieve("test", 1000)


def test_navigator_with_index_retrieves(simple_pdf):
    """Test that navigator_with_index() allows retrieve()"""
    doc = pystreampdf.open(simple_pdf)
    index = doc.build_index(":memory:")
    nav = doc.navigator_with_index(index)

    # retrieve() should now work
    ctx = nav.retrieve("test", 2000)
    assert ctx is not None
    assert isinstance(ctx.sections, list)
