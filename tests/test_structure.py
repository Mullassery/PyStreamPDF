import pytest
import pystreampdf


def test_structure_toc(simple_pdf):
    """Test that structure includes table of contents"""
    doc = streampdf.open(simple_pdf)
    structure = doc.structure

    assert hasattr(structure, "toc")
    assert isinstance(structure.toc, list)


def test_structure_headings(simple_pdf):
    """Test that structure includes headings"""
    doc = streampdf.open(simple_pdf)
    structure = doc.structure

    assert hasattr(structure, "headings")
    assert isinstance(structure.headings, list)


def test_heading_node_fields(simple_pdf):
    """Test that heading nodes have required fields"""
    doc = streampdf.open(simple_pdf)
    structure = doc.structure

    if structure.headings:
        heading = structure.headings[0]
        assert hasattr(heading, "level")
        assert hasattr(heading, "text")
        assert hasattr(heading, "page_number")
        assert hasattr(heading, "children")

        assert isinstance(heading.level, int)
        assert isinstance(heading.text, str)
        assert isinstance(heading.page_number, int)
        assert isinstance(heading.children, list)


def test_toc_entry_fields(simple_pdf):
    """Test that TOC entries have required fields"""
    doc = streampdf.open(simple_pdf)
    structure = doc.structure

    if structure.toc:
        entry = structure.toc[0]
        assert hasattr(entry, "title")
        assert hasattr(entry, "page_number")
        assert hasattr(entry, "level")

        assert isinstance(entry.title, str)
        assert isinstance(entry.page_number, int)
        assert isinstance(entry.level, int)
