"""PyStreamPDF ↔ PyStreamXL Integration - Extract and export tables from PDFs to Excel

This module provides functionality to extract structured data from PDFs and export
directly to Excel spreadsheets using PyStreamXL.
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    """Represents a cell in an extracted table."""
    value: Any
    is_header: bool = False
    row_index: int = 0
    col_index: int = 0

    def __post_init__(self):
        # Normalize value types for Excel
        # Note: bool check must come before int/float since bool is subclass of int
        if isinstance(self.value, bool):
            self.value = str(self.value)  # Convert to string
        elif isinstance(self.value, (int, float)):
            pass  # Keep as-is
        elif self.value is None:
            self.value = ""  # Empty string for None
        else:
            self.value = str(self.value)  # Convert to string


@dataclass
class ExtractedTable:
    """Represents a table extracted from a PDF."""
    rows: List[List[Any]]
    headers: Optional[List[str]] = None
    page_number: int = 0
    confidence: float = 1.0
    location: Optional[Tuple[float, float, float, float]] = None  # x1, y1, x2, y2

    def normalize_for_excel(self) -> List[List[Any]]:
        """Normalize table data for Excel export."""
        normalized = []

        # Add headers if present
        if self.headers:
            normalized.append(self.headers)

        # Add rows
        for row in self.rows:
            normalized_row = []
            for cell in row:
                if isinstance(cell, TableCell):
                    normalized_row.append(cell.value)
                else:
                    # Normalize cell values
                    if isinstance(cell, bool):
                        normalized_row.append(str(cell))
                    elif cell is None:
                        normalized_row.append("")
                    else:
                        normalized_row.append(cell)
            normalized.append(normalized_row)

        return normalized

    def to_dict_rows(self) -> List[Dict[str, Any]]:
        """Convert table to list of dictionaries (keyed by headers)."""
        if not self.headers:
            return []

        return [
            {header: row[i] if i < len(row) else None for i, header in enumerate(self.headers)}
            for row in self.rows
        ]


class TableExtractor:
    """Extracts tables from PDF documents."""

    def __init__(self):
        """Initialize the table extractor."""
        self.extracted_tables: List[ExtractedTable] = []

    def extract_tables_from_pdf(
        self,
        pdf_path: str,
        confidence_threshold: float = 0.7,
        page_range: Optional[Tuple[int, int]] = None,
    ) -> List[ExtractedTable]:
        """
        Extract tables from a PDF document.

        Args:
            pdf_path: Path to the PDF file
            confidence_threshold: Minimum confidence for table detection (0.0-1.0)
            page_range: Optional (start_page, end_page) tuple for page range

        Returns:
            List of ExtractedTable objects
        """
        try:
            import pystreampdf
        except ImportError:
            raise ImportError("PyStreamPDF is required for PDF table extraction")

        self.extracted_tables = []

        try:
            # Open PDF
            doc = pystreampdf.open(pdf_path)
            logger.info(f"Opened PDF: {pdf_path} ({doc.page_count} pages)")

            # Determine page range
            start_page = 1
            end_page = doc.page_count
            if page_range:
                start_page = max(1, page_range[0])
                end_page = min(doc.page_count, page_range[1])

            # Extract tables from each page
            for page_num in range(start_page, end_page + 1):
                tables = self._extract_tables_from_page(
                    doc,
                    page_num,
                    confidence_threshold
                )
                self.extracted_tables.extend(tables)

            logger.info(f"Extracted {len(self.extracted_tables)} tables from PDF")
            return self.extracted_tables

        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {e}")
            raise

    def _extract_tables_from_page(
        self,
        doc: Any,
        page_num: int,
        confidence_threshold: float,
    ) -> List[ExtractedTable]:
        """Extract tables from a single page."""
        tables = []

        try:
            # Get page content
            page = doc.page(page_num - 1)  # 0-indexed
            text = page.text

            # Simple table detection: look for structured text patterns
            # In a production system, this would use advanced table detection
            # For now, return sample table structure
            if text and len(text.strip()) > 0:
                # Try to detect tables in the text
                table = self._detect_table_in_text(text, page_num)
                if table and table.confidence >= confidence_threshold:
                    tables.append(table)

        except Exception as e:
            logger.debug(f"Error extracting table from page {page_num}: {e}")

        return tables

    def _detect_table_in_text(self, text: str, page_num: int) -> Optional[ExtractedTable]:
        """Detect table structure in text content."""
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return None

        # Simple heuristic: treat lines as rows, split by whitespace/tabs
        rows = []
        headers = None

        for i, line in enumerate(lines):
            # Split by multiple spaces/tabs
            cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
            if not cells:
                continue

            if i == 0:
                headers = cells
            else:
                rows.append(cells)

        if not rows or not headers:
            return None

        # Ensure all rows have same column count
        num_cols = len(headers)
        normalized_rows = []
        for row in rows:
            # Pad or truncate to match header count
            normalized_row = row[:num_cols] + [''] * (num_cols - len(row))
            normalized_rows.append(normalized_row)

        return ExtractedTable(
            rows=normalized_rows,
            headers=headers,
            page_number=page_num,
            confidence=0.8,  # Heuristic confidence
        )


class ExcelExporter:
    """Exports extracted tables to Excel using PyStreamXL."""

    def __init__(self):
        """Initialize the Excel exporter."""
        self.workbook_path: Optional[str] = None

    def export_tables_to_excel(
        self,
        tables: List[ExtractedTable],
        output_path: str,
        sheet_name: Optional[str] = None,
    ) -> None:
        """
        Export extracted tables to an Excel workbook.

        Args:
            tables: List of ExtractedTable objects to export
            output_path: Path to output Excel file
            sheet_name: Optional sheet name (default: "Tables")
        """
        try:
            import pystreamxl
        except ImportError:
            raise ImportError("PyStreamXL is required for Excel export")

        if not tables:
            logger.warning("No tables to export")
            return

        sheet_name = sheet_name or "Tables"

        try:
            with pystreamxl.writer(output_path) as writer:
                for i, table in enumerate(tables):
                    if i > 0:
                        # Add new sheet for each table
                        writer.add_sheet(f"{sheet_name}_{i + 1}")

                    # Export table
                    self._export_table_to_sheet(writer, table)

            self.workbook_path = output_path
            logger.info(f"Exported {len(tables)} tables to {output_path}")

        except Exception as e:
            logger.error(f"Error exporting tables to Excel: {e}")
            raise

    def _export_table_to_sheet(
        self,
        writer: Any,
        table: ExtractedTable,
    ) -> None:
        """Export a single table to a worksheet."""
        # Normalize data
        rows = table.normalize_for_excel()

        # Write rows
        for row in rows:
            writer.write_row(row)

        logger.debug(f"Exported table from page {table.page_number} ({len(rows)} rows)")


class PDFToExcelPipeline:
    """Complete pipeline for PDF to Excel conversion."""

    def __init__(self):
        """Initialize the PDF to Excel pipeline."""
        self.extractor = TableExtractor()
        self.exporter = ExcelExporter()
        self.quality_validator: Optional[Any] = None

    def set_quality_validator(self, validator: Any) -> "PDFToExcelPipeline":
        """Set a quality validator (e.g., from PyStreamMCP)."""
        self.quality_validator = validator
        return self

    def convert_pdf_to_excel(
        self,
        pdf_path: str,
        output_path: str,
        confidence_threshold: float = 0.7,
        validate_quality: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Convert PDF to Excel with optional quality validation.

        Args:
            pdf_path: Path to input PDF
            output_path: Path to output Excel file
            confidence_threshold: Minimum confidence for table detection
            validate_quality: Whether to validate extracted data quality
            **kwargs: Additional arguments (page_range, etc.)

        Returns:
            Dictionary with conversion metadata
        """
        result = {
            "pdf_path": pdf_path,
            "output_path": output_path,
            "tables_extracted": 0,
            "tables_validated": 0,
            "tables_exported": 0,
            "quality_scores": [],
            "errors": [],
        }

        try:
            # Extract tables from PDF
            logger.info(f"Extracting tables from {pdf_path}")
            tables = self.extractor.extract_tables_from_pdf(
                pdf_path,
                confidence_threshold=confidence_threshold,
                **kwargs
            )
            result["tables_extracted"] = len(tables)

            if not tables:
                logger.warning("No tables extracted from PDF")
                return result

            # Validate quality if requested
            if validate_quality and self.quality_validator:
                tables = self._validate_tables_quality(tables)
                result["tables_validated"] = len(tables)

            # Export to Excel
            logger.info(f"Exporting {len(tables)} tables to {output_path}")
            self.exporter.export_tables_to_excel(tables, output_path)
            result["tables_exported"] = len(tables)

        except Exception as e:
            logger.error(f"Error in PDF to Excel conversion: {e}")
            result["errors"].append(str(e))

        return result

    def _validate_tables_quality(self, tables: List[ExtractedTable]) -> List[ExtractedTable]:
        """Validate extracted tables using quality validator."""
        if not self.quality_validator:
            return tables

        validated_tables = []

        for i, table in enumerate(tables):
            # Convert table to validation format
            source_data = {
                "schema": {
                    "fields": [
                        {"name": f"col_{j}", "type": "string"}
                        for j in range(len(table.headers or []))
                    ]
                },
                "rows": table.to_dict_rows() if table.headers else [
                    {f"col_{j}": cell for j, cell in enumerate(row)}
                    for row in table.rows
                ]
            }

            # Validate
            try:
                result = self.quality_validator.validate(
                    f"pdf_table_{i}",
                    source_data
                )

                if self.quality_validator.should_include(f"pdf_table_{i}", result):
                    validated_tables.append(table)
                    logger.info(f"Table {i}: VALID (score: {result.quality_score:.2f})")
                else:
                    logger.warning(f"Table {i}: REJECTED (score: {result.quality_score:.2f})")

            except Exception as e:
                logger.debug(f"Quality validation error for table {i}: {e}")
                validated_tables.append(table)  # Include on validation error

        return validated_tables


# Convenience functions

def extract_tables_from_pdf(
    pdf_path: str,
    confidence_threshold: float = 0.7,
) -> List[ExtractedTable]:
    """Convenience function to extract tables from PDF."""
    extractor = TableExtractor()
    return extractor.extract_tables_from_pdf(pdf_path, confidence_threshold)


def export_tables_to_excel(
    tables: List[ExtractedTable],
    output_path: str,
) -> None:
    """Convenience function to export tables to Excel."""
    exporter = ExcelExporter()
    exporter.export_tables_to_excel(tables, output_path)


def convert_pdf_to_excel(
    pdf_path: str,
    output_path: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Convenience function for complete PDF to Excel conversion."""
    pipeline = PDFToExcelPipeline()
    return pipeline.convert_pdf_to_excel(pdf_path, output_path, **kwargs)
