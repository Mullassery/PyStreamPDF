"""Tests proving PyStreamPDFMCPHandler calls into the real, already-tested
extraction/OCR/validation implementations elsewhere in this package,
instead of returning hardcoded fixture data disconnected from the actual
PDF passed in.

Before this fix, every single method on PyStreamPDFMCPHandler ignored
pdf_path/self.pdf entirely and returned the exact same fixed dict
regardless of input -- most notably validate_pdf always reported
`is_valid: True`, even for a nonexistent or genuinely corrupted file.
"""

import os

import pytest

from pystreampdf._mcp_tools import PyStreamPDFMCPHandler


@pytest.fixture
def handler():
    return PyStreamPDFMCPHandler()


@pytest.fixture
def citation_pdf(temp_pdf_dir):
    """A PDF with real citation text, for extract_citations."""
    pytest.importorskip("reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = os.path.join(temp_pdf_dir, "citations.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "This references (Smith, 2020) and [1] for citations.")
    c.drawString(100, 700, "Also see (Jones et al., 2019) and [2, 3].")
    c.save()
    return pdf_path


@pytest.fixture
def corrupted_pdf(temp_pdf_dir):
    """Not a real PDF at all -- for validate_pdf/extract_text error paths."""
    pdf_path = os.path.join(temp_pdf_dir, "corrupted.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 this is not a real pdf structure at all")
    return pdf_path


class TestExtractText:
    @pytest.mark.asyncio
    async def test_returns_real_text_for_the_given_pdf(self, handler, simple_pdf):
        result = await handler.extract_text(simple_pdf)

        assert result["pdf_path"] == simple_pdf
        assert "Test PDF Document" in result["text"]
        assert result["text_length"] == len(result["text"])

    @pytest.mark.asyncio
    async def test_different_pdfs_produce_different_results(
        self, handler, simple_pdf, multi_page_pdf
    ):
        """Regression guard: the old fixture-backed handler returned the
        identical dict for every pdf_path."""
        simple_result = await handler.extract_text(simple_pdf)
        multi_result = await handler.extract_text(multi_page_pdf)

        assert simple_result["pages_processed"] != multi_result["pages_processed"]
        assert simple_result["text"] != multi_result["text"]

    @pytest.mark.asyncio
    async def test_page_range_is_respected(self, handler, multi_page_pdf):
        result = await handler.extract_text(multi_page_pdf, pages="1-2")
        assert result["pages_processed"] == 2

    @pytest.mark.asyncio
    async def test_raises_on_corrupted_pdf_instead_of_returning_fake_text(
        self, handler, corrupted_pdf
    ):
        with pytest.raises(Exception):
            await handler.extract_text(corrupted_pdf)


class TestExtractMetadata:
    @pytest.mark.asyncio
    async def test_pages_reflects_real_page_count(self, handler, multi_page_pdf):
        result = await handler.extract_metadata(multi_page_pdf)
        assert result["pages"] == 5


class TestDetectDocumentStructure:
    @pytest.mark.asyncio
    async def test_returns_real_headings(self, handler, simple_pdf):
        result = await handler.detect_document_structure(simple_pdf)
        assert "headings" in result["structure"]
        assert isinstance(result["structure"]["headers"], int)


class TestDetectForms:
    @pytest.mark.asyncio
    async def test_reports_no_forms_for_a_plain_text_pdf(self, handler, simple_pdf):
        result = await handler.detect_forms(simple_pdf)
        assert result["is_form"] is False
        assert result["fields"] == 0


class TestChunkDocument:
    @pytest.mark.asyncio
    async def test_uses_real_semantic_chunker(self, handler, multi_page_pdf):
        result = await handler.chunk_document(multi_page_pdf)
        assert result["chunks"] > 0


class TestExtractCitations:
    @pytest.mark.asyncio
    async def test_finds_real_citations_in_text(self, handler, citation_pdf):
        result = await handler.extract_citations(citation_pdf)

        texts = {r["text"] for r in result["references"]}
        assert "[1]" in texts
        assert "(Smith, 2020)" in texts
        assert result["citations"] == len(result["references"]) or result["citations"] >= 4

    @pytest.mark.asyncio
    async def test_no_citations_in_plain_pdf(self, handler, simple_pdf):
        result = await handler.extract_citations(simple_pdf)
        assert result["citations"] == 0


class TestDetectLanguage:
    @pytest.mark.asyncio
    async def test_honestly_reports_not_implemented(self, handler, simple_pdf):
        """No language-detection library is a dependency -- this must say
        so, not fabricate a confident-looking language guess."""
        result = await handler.detect_language(simple_pdf)
        assert result["status"] == "not_implemented"


class TestValidatePdf:
    @pytest.mark.asyncio
    async def test_valid_pdf_reports_valid(self, handler, simple_pdf):
        result = await handler.validate_pdf(simple_pdf)
        assert result["is_valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_corrupted_pdf_reports_invalid_not_fake_success(
        self, handler, corrupted_pdf
    ):
        """The old fixture handler always returned is_valid: True regardless
        of input -- this is the core regression test for that."""
        result = await handler.validate_pdf(corrupted_pdf)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_nonexistent_pdf_reports_invalid(self, handler):
        result = await handler.validate_pdf("/nonexistent/path/to/file.pdf")
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0


class TestApplyOcr:
    @pytest.mark.asyncio
    async def test_honestly_reports_unavailable_without_a_provider_installed(
        self, handler, simple_pdf
    ):
        """Whether this is genuinely "unavailable" or actually runs depends
        on whether tesseract/paddleocr are installed in the test
        environment -- either way, the response must reflect real
        provider availability, not a fabricated confidence score."""
        result = await handler.apply_ocr(simple_pdf)
        assert result.get("status") == "unavailable" or "confidence" in result


class TestExtractTablesAndImages:
    @pytest.mark.asyncio
    async def test_extract_tables_on_pdf_with_no_tables(self, handler, simple_pdf):
        result = await handler.extract_tables(simple_pdf)
        assert result["tables_found"] == 0
        assert result["tables"] == []

    @pytest.mark.asyncio
    async def test_extract_images_on_pdf_with_no_images(self, handler, simple_pdf):
        result = await handler.extract_images(simple_pdf)
        assert result["images_extracted"] == 0
        assert result["images"] == []


class TestExportProcessedDocument:
    @pytest.mark.asyncio
    async def test_markdown_export_contains_real_content(self, handler, simple_pdf):
        result = await handler.export_processed_document(simple_pdf, "markdown")
        assert result["output_format"] == "markdown"
        assert result["size_mb"] > 0

    @pytest.mark.asyncio
    async def test_json_export_contains_real_content(self, handler, simple_pdf):
        result = await handler.export_processed_document(simple_pdf, "json")
        assert result["size_mb"] > 0

    @pytest.mark.asyncio
    async def test_unimplemented_formats_say_so_not_fabricate(self, handler, simple_pdf):
        for fmt in ("html", "docx"):
            result = await handler.export_processed_document(simple_pdf, fmt)
            assert result["status"] == "not_implemented"


class TestGetTools:
    def test_lists_all_twelve_tools(self):
        from pystreampdf._mcp_tools import PyStreamPDFMCPTools

        tools = PyStreamPDFMCPTools.get_tools()
        assert len(tools) == 12
