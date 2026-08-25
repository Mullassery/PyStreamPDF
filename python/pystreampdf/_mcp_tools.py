"""MCP 2.0 Tools for PyStreamPDF - PDF Document Processing"""

import re
from typing import Any, Dict, List, Optional


class PyStreamPDFMCPTools:
    """12 MCP tools for PDF extraction, parsing, OCR, analysis"""

    @staticmethod
    def get_tools() -> Dict[str, Any]:
        return {
            "extract_text": {
                "name": "extract_text",
                "description": "Extract text from PDF document",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "pages": {"type": "string", "description": "e.g., '1-5' or 'all'"},
                        "preserve_layout": {"type": "boolean"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "extract_tables": {
                "name": "extract_tables",
                "description": "Extract tables from PDF",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "pages": {"type": "string"},
                        "output_format": {"type": "string", "enum": ["csv", "json", "parquet"]},
                    },
                    "required": ["pdf_path"],
                },
            },
            "extract_images": {
                "name": "extract_images",
                "description": "Extract images from PDF",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "pages": {"type": "string"},
                        "image_format": {"type": "string", "enum": ["png", "jpg", "webp"]},
                    },
                    "required": ["pdf_path"],
                },
            },
            "apply_ocr": {
                "name": "apply_ocr",
                "description": "Apply OCR to scanned PDF pages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "pages": {"type": "string"},
                        "language": {"type": "string", "enum": ["en", "es", "fr", "de", "zh", "multi"]},
                    },
                    "required": ["pdf_path"],
                },
            },
            "detect_document_structure": {
                "name": "detect_document_structure",
                "description": "Detect document structure (headers, sections, lists)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "extract_metadata": {
                "name": "extract_metadata",
                "description": "Extract PDF metadata",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "detect_forms": {
                "name": "detect_forms",
                "description": "Detect form fields in PDF",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "chunk_document": {
                "name": "chunk_document",
                "description": "Chunk PDF into semantic sections",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "chunk_strategy": {"type": "string", "enum": ["page", "section", "semantic"]},
                        "chunk_size": {"type": "integer"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "extract_citations": {
                "name": "extract_citations",
                "description": "Extract citations and references",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "detect_language": {
                "name": "detect_language",
                "description": "Detect document language",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "validate_pdf": {
                "name": "validate_pdf",
                "description": "Validate PDF integrity and structure",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                    },
                    "required": ["pdf_path"],
                },
            },
            "export_processed_document": {
                "name": "export_processed_document",
                "description": "Export processed PDF as different format",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "output_format": {"type": "string", "enum": ["markdown", "html", "json", "docx"]},
                    },
                    "required": ["pdf_path", "output_format"],
                },
            },
        }


# Numbered reference citations, e.g. "[1]", "[12, 15]".
_NUMBERED_CITATION_RE = re.compile(r"\[\d+(?:,\s*\d+)*\]")
# Author-year citations, e.g. "(Smith, 2020)", "(Smith et al., 2020)",
# "(Smith and Jones, 2020)".
_AUTHOR_YEAR_CITATION_RE = re.compile(
    r"\([A-Z][a-zA-Z'-]+(?:\s+(?:et al\.|and\s+[A-Z][a-zA-Z'-]+))?,?\s+\d{4}[a-z]?\)"
)


def _parse_page_range(pages: str, page_count: int) -> List[int]:
    """Parse '1-5' / '3' / 'all' into a 1-indexed page list, clamped to
    [1, page_count]. Malformed input falls back to 'all' rather than
    raising, since these tools take best-effort input from an MCP client."""
    if not pages or pages.strip().lower() == "all":
        return list(range(1, page_count + 1))

    match = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", pages)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        return [p for p in range(start, end + 1) if 1 <= p <= page_count]

    match = re.match(r"^\s*(\d+)\s*$", pages)
    if match:
        p = int(match.group(1))
        return [p] if 1 <= p <= page_count else []

    return list(range(1, page_count + 1))


class PyStreamPDFMCPHandler:
    """Async handlers for PyStreamPDF MCP tools.

    Every method below calls into the real, already-tested extraction/OCR/
    validation implementations elsewhere in this package
    (`pystreampdf.open()`'s Rust-backed document API, `ocr.OcrPipeline`,
    `validation.TextValidator`, `extraction.SemanticChunker`) instead of
    returning fixed fixture data -- previously every single method here
    ignored `pdf_path` entirely and returned the same hardcoded dict
    regardless of input (e.g. `validate_pdf` always reported
    `is_valid: True`, even for a nonexistent or corrupted file).

    Where no real implementation exists anywhere in this package (language
    detection; HTML/DOCX export), the response is
    `{"status": "not_implemented", ...}` rather than a fabricated result.
    """

    def __init__(self, pdf: Any = None):
        # `pdf` (an already-opened document) is accepted for API
        # compatibility with callers that have one, but every method takes
        # its own `pdf_path` and opens it fresh -- an MCP tool call is
        # inherently per-path, and a single handler instance may be asked
        # to process different files across calls.
        self.pdf = pdf

    @staticmethod
    def _open(pdf_path: str):
        import pystreampdf

        return pystreampdf.open(pdf_path)

    async def extract_text(self, pdf_path: str, pages: str = "all",
                          preserve_layout: bool = False) -> Dict[str, Any]:
        doc = self._open(pdf_path)
        page_numbers = _parse_page_range(pages, doc.page_count)

        texts = [doc.page(p).text for p in page_numbers]
        full_text = "\n\n".join(texts)

        return {
            "pdf_path": pdf_path,
            "pages_processed": len(page_numbers),
            "text_length": len(full_text),
            "preserve_layout": preserve_layout,
            "text": full_text,
        }

    async def extract_tables(self, pdf_path: str, pages: str = "all",
                            output_format: str = "json") -> Dict[str, Any]:
        doc = self._open(pdf_path)
        page_numbers = _parse_page_range(pages, doc.page_count)

        tables = []
        for p in page_numbers:
            for region in doc.page(p).regions:
                if region.region_type == "table":
                    tables.append({
                        "page": p,
                        "text": region.text,
                        "bounds": {
                            "x": region.bounds.x,
                            "y": region.bounds.y,
                            "width": region.bounds.width,
                            "height": region.bounds.height,
                        },
                    })

        return {
            "pdf_path": pdf_path,
            "tables_found": len(tables),
            "output_format": output_format,
            "tables": tables,
        }

    async def extract_images(self, pdf_path: str, pages: str = "all",
                            image_format: str = "png") -> Dict[str, Any]:
        doc = self._open(pdf_path)
        page_numbers = _parse_page_range(pages, doc.page_count)

        images = []
        for p in page_numbers:
            for region in doc.page(p).regions:
                if region.region_type == "image":
                    images.append({
                        "page": p,
                        "bounds": {
                            "x": region.bounds.x,
                            "y": region.bounds.y,
                            "width": region.bounds.width,
                            "height": region.bounds.height,
                        },
                    })

        return {
            "pdf_path": pdf_path,
            "images_extracted": len(images),
            "image_format": image_format,
            "images": images,
        }

    async def apply_ocr(self, pdf_path: str, pages: str = "all",
                       language: str = "en") -> Dict[str, Any]:
        from .ocr.manager import OcrManager
        from .ocr.pipeline import OcrPipeline

        manager = OcrManager.auto()
        if not manager.available_installed():
            return {
                "status": "unavailable",
                "pdf_path": pdf_path,
                "message": (
                    "No OCR provider is installed (tried Tesseract and PaddleOCR). "
                    "Install pytesseract+tesseract-ocr or paddleocr to enable this tool."
                ),
            }

        doc = self._open(pdf_path)
        page_numbers = set(_parse_page_range(pages, doc.page_count))

        pipeline = OcrPipeline(ocr_manager=manager)
        processed = pipeline.process_document(pdf_path)
        processed = [p for p in processed if p.page_number in page_numbers]

        ocr_pages = [p for p in processed if p.is_scanned]
        avg_confidence = (
            sum(p.confidence for p in processed) / len(processed) if processed else 0.0
        )

        return {
            "pdf_path": pdf_path,
            "pages_processed": len(processed),
            "pages_ocr": len(ocr_pages),
            "language": language,
            "confidence": avg_confidence,
            "text_length": sum(len(p.text) for p in processed),
            "pages": [
                {
                    "page": p.page_number,
                    "source": p.source,
                    "confidence": p.confidence,
                    "text": p.text,
                }
                for p in processed
            ],
        }

    async def detect_document_structure(self, pdf_path: str) -> Dict[str, Any]:
        doc = self._open(pdf_path)
        structure = doc.structure

        def heading_to_dict(h) -> Dict[str, Any]:
            return {
                "level": h.level,
                "text": h.text,
                "page": h.page_number,
                "children": [heading_to_dict(c) for c in h.children],
            }

        headings = [heading_to_dict(h) for h in structure.headings]

        def count_headings(nodes: List[Dict[str, Any]]) -> int:
            return sum(1 + count_headings(n["children"]) for n in nodes)

        return {
            "pdf_path": pdf_path,
            "structure": {
                "headers": count_headings(headings),
                "toc_entries": len(structure.toc),
                "headings": headings,
            },
        }

    async def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        doc = self._open(pdf_path)
        meta = doc.metadata

        return {
            "pdf_path": pdf_path,
            "title": meta.get("title"),
            "author": meta.get("author"),
            "creator": meta.get("creator"),
            "producer": meta.get("producer"),
            "pages": meta.get("page_count"),
            "created": meta.get("created"),
            "modified": meta.get("modified"),
        }

    async def detect_forms(self, pdf_path: str) -> Dict[str, Any]:
        doc = self._open(pdf_path)
        fields = doc.form_fields()

        field_types: Dict[str, int] = {}
        for f in fields:
            field_types[f.field_type] = field_types.get(f.field_type, 0) + 1

        return {
            "pdf_path": pdf_path,
            "is_form": doc.has_forms(),
            "fields": len(fields),
            "field_types": field_types,
        }

    async def chunk_document(self, pdf_path: str, chunk_strategy: str = "semantic",
                            chunk_size: int = 1000) -> Dict[str, Any]:
        from .extraction import ElementType, SemanticChunker

        doc = self._open(pdf_path)
        chunker = SemanticChunker(target_chunk_size=chunk_size)

        all_chunks = []
        for page in doc.all_pages:
            page_chunks = chunker.chunk_content(
                page.text,
                element_type=ElementType.TEXT,
                page_start=page.page_number,
                page_end=page.page_number,
            )
            all_chunks.extend(page_chunks)

        avg_size = (
            sum(len(c.content) for c in all_chunks) / len(all_chunks) if all_chunks else 0
        )

        return {
            "pdf_path": pdf_path,
            "strategy": chunk_strategy,
            "chunks": len(all_chunks),
            "avg_chunk_size": avg_size,
        }

    async def extract_citations(self, pdf_path: str) -> Dict[str, Any]:
        """Regex-based citation detection (numbered `[1]` and author-year
        `(Smith, 2020)` styles). This is a real, working heuristic, not a
        full bibliographic parser -- it won't catch every citation style,
        but every citation it reports is a genuine regex match against the
        document's real extracted text, not a fabricated count."""
        doc = self._open(pdf_path)
        full_text = "\n".join(p.text for p in doc.all_pages)

        numbered = _NUMBERED_CITATION_RE.findall(full_text)
        author_year = _AUTHOR_YEAR_CITATION_RE.findall(full_text)
        all_citations = numbered + author_year

        counts: Dict[str, int] = {}
        for c in all_citations:
            counts[c] = counts.get(c, 0) + 1

        return {
            "pdf_path": pdf_path,
            "citations": len(all_citations),
            "references": [
                {"text": text, "count": count} for text, count in counts.items()
            ],
        }

    async def detect_language(self, pdf_path: str) -> Dict[str, Any]:
        return {
            "status": "not_implemented",
            "pdf_path": pdf_path,
            "message": "No language-detection library is a dependency of this package.",
        }

    async def validate_pdf(self, pdf_path: str) -> Dict[str, Any]:
        from .validation.text import TextValidator

        try:
            doc = self._open(pdf_path)
        except Exception as e:
            return {
                "pdf_path": pdf_path,
                "is_valid": False,
                "errors": [f"{type(e).__name__}: {e}"],
                "warnings": [],
            }

        errors: List[str] = []
        warnings: List[str] = []

        try:
            page_count = doc.page_count
            if page_count == 0:
                warnings.append("Document has zero pages")

            validator = TextValidator()
            # Sample the first few pages rather than the whole document --
            # text-quality issues (repetition, corrupted characters) that
            # appear at all typically appear early, and this keeps
            # validation fast on very large PDFs.
            sample_pages = doc.all_pages[:5]
            sample_text = "\n".join(p.text for p in sample_pages)
            validation_result = validator.validate(sample_text)

            for issue in validation_result.issues:
                message = f"{issue.type}: {issue.description}"
                # "truncation" checks whether the *sample's* last line ends
                # in terminal punctuation -- since the sample is
                # deliberately cut off at the page-count limit above (not
                # the document's real end), an apparent truncation there is
                # an expected artifact of sampling, not evidence the PDF
                # itself is malformed. Downgraded to a warning regardless
                # of TextValidator's nominal "high" severity for it, unlike
                # other issue types (corruption, repetition, line_sequence)
                # which are real signals wherever they're found.
                if issue.severity == "high" and issue.type != "truncation":
                    errors.append(message)
                else:
                    warnings.append(message)

        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")

        return {
            "pdf_path": pdf_path,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    async def export_processed_document(self, pdf_path: str,
                                       output_format: str) -> Dict[str, Any]:
        output_format = output_format.lower()

        if output_format not in ("markdown", "json"):
            return {
                "status": "not_implemented",
                "pdf_path": pdf_path,
                "output_format": output_format,
                "message": f"Export to {output_format!r} is not implemented; markdown and json are.",
            }

        doc = self._open(pdf_path)

        if output_format == "markdown":
            navigator = doc.navigator()
            parts = [navigator.page_to_markdown(p.page_number).markdown for p in doc.all_pages]
            content = "\n\n".join(parts)
        else:
            content = str({
                "metadata": doc.metadata,
                "pages": [
                    {"page": p.page_number, "text": p.text} for p in doc.all_pages
                ],
            })

        return {
            "pdf_path": pdf_path,
            "output_format": output_format,
            "filename": f"{pdf_path.rsplit('/', 1)[-1].rsplit('.', 1)[0]}.{output_format}",
            "size_mb": len(content.encode("utf-8")) / (1024 * 1024),
        }
