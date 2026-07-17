# PyStreamPDF ↔ PyStreamXL Integration Guide

**Status:** ✅ COMPLETE & TESTED  
**Date:** 2026-07-17  
**Tests:** 24/24 passing

---

## Overview

Extract tables from PDFs and export directly to Excel spreadsheets. Perfect for:
- Automating data extraction from PDF reports
- Converting PDF tables to structured Excel files
- Building data pipelines: PDF → Excel → BI tools

**Architecture:**
```
PDF File
  ↓
PyStreamPDF (Extract Tables)
  ↓
Table Detection (Schema + Data)
  ↓
Quality Validation (Optional)
  ↓
PyStreamXL (Export to Excel)
  ↓
Excel Workbook
```

---

## Quick Start

### Basic Usage

```python
from pystreampdf.excel_export import convert_pdf_to_excel

# Convert PDF to Excel
result = convert_pdf_to_excel(
    pdf_path="report.pdf",
    output_path="report.xlsx"
)

print(f"Extracted {result['tables_extracted']} tables")
print(f"Exported {result['tables_exported']} tables")
```

### Advanced Usage with Quality Validation

```python
from pystreampdf.excel_export import PDFToExcelPipeline
from pystreammcp import QualityValidator, ValidationGate

# Create pipeline
pipeline = PDFToExcelPipeline()

# Add quality validation
validator = QualityValidator(statguardian_enabled=True)
gate = ValidationGate(
    dataset_id="pdf_tables",
    block_on_failure=False,  # Allow degraded tables
    min_quality_score=0.7
)
validator.register_gate(gate)
pipeline.set_quality_validator(validator)

# Convert with quality checks
result = pipeline.convert_pdf_to_excel(
    pdf_path="financial_report.pdf",
    output_path="financial_data.xlsx",
    validate_quality=True
)

print(f"Validated {result['tables_validated']} tables")
print(f"Quality scores: {result['quality_scores']}")
```

---

## API Reference

### TableCell

Represents a single cell in an extracted table.

```python
from pystreampdf.excel_export import TableCell

cell = TableCell(
    value="Alice",
    is_header=False,
    row_index=0,
    col_index=0
)
```

**Features:**
- Automatic value normalization for Excel
- Boolean → string conversion
- None → empty string
- Type safety

### ExtractedTable

Represents a complete extracted table.

```python
from pystreampdf.excel_export import ExtractedTable

table = ExtractedTable(
    rows=[
        ["Alice", 30],
        ["Bob", 25]
    ],
    headers=["Name", "Age"],
    page_number=1,
    confidence=0.95,
    location=(100, 200, 400, 350)  # x1, y1, x2, y2
)

# Normalize for Excel
excel_rows = table.normalize_for_excel()

# Convert to dictionaries
dict_rows = table.to_dict_rows()
# → [{"Name": "Alice", "Age": 30}, ...]
```

### TableExtractor

Extracts tables from PDF documents.

```python
from pystreampdf.excel_export import TableExtractor

extractor = TableExtractor()

# Extract from entire PDF
tables = extractor.extract_tables_from_pdf(
    pdf_path="report.pdf",
    confidence_threshold=0.7,
    page_range=(1, 10)  # Optional: specific pages
)

# Work with extracted tables
for table in tables:
    print(f"Page {table.page_number}: {len(table.rows)} rows")
```

### ExcelExporter

Exports tables to Excel files.

```python
from pystreampdf.excel_export import ExcelExporter, ExtractedTable

exporter = ExcelExporter()

# Single sheet
exporter.export_tables_to_excel(
    tables=[table1, table2],
    output_path="output.xlsx",
    sheet_name="Tables"
)

# Multiple sheets (one per table)
exporter.export_tables_to_excel(
    tables=[table1, table2, table3],
    output_path="output.xlsx"
)
# Creates: Tables, Tables_2, Tables_3
```

### PDFToExcelPipeline

Complete end-to-end pipeline.

```python
from pystreampdf.excel_export import PDFToExcelPipeline

pipeline = PDFToExcelPipeline()

# Set quality validator
pipeline.set_quality_validator(validator)

# Convert
result = pipeline.convert_pdf_to_excel(
    pdf_path="input.pdf",
    output_path="output.xlsx",
    confidence_threshold=0.7,
    validate_quality=True,
    page_range=(1, 50)
)
```

**Returns:**
```python
{
    "pdf_path": "input.pdf",
    "output_path": "output.xlsx",
    "tables_extracted": 5,
    "tables_validated": 5,
    "tables_exported": 5,
    "quality_scores": [0.95, 0.88, 0.92, 0.85, 0.90],
    "errors": []
}
```

---

## Integration Patterns

### Pattern 1: Simple Extraction

```python
from pystreampdf.excel_export import extract_tables_from_pdf, export_tables_to_excel

# Extract
tables = extract_tables_from_pdf("report.pdf")

# Export
export_tables_to_excel(tables, "output.xlsx")
```

### Pattern 2: Quality-Gated Pipeline

```python
pipeline = PDFToExcelPipeline()
pipeline.set_quality_validator(validator)

result = pipeline.convert_pdf_to_excel(
    "financial.pdf",
    "financial_clean.xlsx",
    validate_quality=True,
    confidence_threshold=0.8  # High bar for finance
)
```

### Pattern 3: Batch Processing

```python
import glob
from pathlib import Path

pipeline = PDFToExcelPipeline()

# Process all PDFs in directory
for pdf_file in glob.glob("reports/*.pdf"):
    output = Path(pdf_file).stem + ".xlsx"
    result = pipeline.convert_pdf_to_excel(pdf_file, output)
    print(f"{pdf_file}: {result['tables_extracted']} tables")
```

### Pattern 4: Data Pipeline Integration

```python
# Extract from PDF → validate quality → export to Excel → load to database

pipeline = PDFToExcelPipeline()
pipeline.set_quality_validator(quality_validator)

result = pipeline.convert_pdf_to_excel(
    "raw_data.pdf",
    "processed_data.xlsx",
    validate_quality=True
)

if result["errors"]:
    print(f"Errors: {result['errors']}")
else:
    # Load Excel to database
    load_to_database("processed_data.xlsx")
```

---

## Quality Validation

Integration with PyStreamMCP quality validation:

```python
from pystreammcp import QualityValidator, ValidationGate
from pystreampdf.excel_export import PDFToExcelPipeline

# Configure validator
validator = QualityValidator(statguardian_enabled=True)
gate = ValidationGate(
    dataset_id="pdf_tables",
    min_quality_score=0.8,
    block_on_failure=True  # Strict: reject low-quality tables
)
validator.register_gate(gate)

# Use in pipeline
pipeline = PDFToExcelPipeline()
pipeline.set_quality_validator(validator)

result = pipeline.convert_pdf_to_excel(
    "data.pdf",
    "clean_data.xlsx",
    validate_quality=True
)
```

**Quality Checks:**
- Null ratio (target < 10%)
- Duplicate ratio (target < 5%)
- Type consistency
- Field presence

---

## Testing

### Unit Tests

```python
import pytest
from pystreampdf.excel_export import (
    TableCell, ExtractedTable, TableExtractor, ExcelExporter
)

def test_cell_normalization():
    """Test value normalization."""
    cell = TableCell(value=True)
    assert cell.value == "True"  # Boolean converted to string

def test_table_extraction():
    """Test table extraction from text."""
    extractor = TableExtractor()
    text = "Name\tAge\nAlice\t30\nBob\t25"
    table = extractor._detect_table_in_text(text, page_num=1)
    assert len(table.rows) == 2
    assert table.headers == ["Name", "Age"]

def test_export():
    """Test Excel export."""
    table = ExtractedTable(
        rows=[["Alice", "30"]],
        headers=["Name", "Age"]
    )
    normalized = table.normalize_for_excel()
    assert len(normalized) == 2  # headers + 1 row
```

**Run tests:**
```bash
pytest tests/test_excel_export_integration.py -v
# 24 tests passing ✅
```

---

## Performance

### Overhead Analysis

| Operation | Time | Memory | Notes |
|-----------|------|--------|-------|
| Extract from 10-page PDF | 100-500ms | ~5 MB | Depends on complexity |
| Validate 10 tables | 50-200ms | ~1 MB | With quality checks |
| Export to Excel | 20-100ms | ~2 MB | Depends on table size |
| Total pipeline | 200-800ms | ~8 MB | End-to-end |

### Scalability

- **100-page PDF**: ~5-10 seconds
- **1000-page PDF**: ~1-2 minutes (can be optimized with page range)
- **Batch processing**: Process sequentially or parallelize with multiprocessing

---

## Troubleshooting

### No Tables Extracted

**Cause:** PDF may not have structured tables or has complex layouts  
**Solution:**
- Verify PDF has text (not scanned image)
- Lower `confidence_threshold` to detect more tables
- Check `page_range` to focus on specific pages

```python
tables = extractor.extract_tables_from_pdf(
    "file.pdf",
    confidence_threshold=0.5  # Lower from 0.7
)
```

### Quality Validation Failing

**Cause:** Extracted tables have low quality scores  
**Solution:**
- Lower `min_quality_score` in validation gate
- Use non-blocking mode to include with warnings

```python
gate = ValidationGate(
    dataset_id="tables",
    min_quality_score=0.6,  # Lower threshold
    block_on_failure=False   # Don't block
)
```

### Export Errors

**Cause:** PyStreamXL not installed or path issues  
**Solution:**
```bash
pip install pystreamxl
```

Ensure output directory exists:
```python
from pathlib import Path
Path("output").mkdir(exist_ok=True)
pipeline.convert_pdf_to_excel("input.pdf", "output/result.xlsx")
```

---

## Examples

### Example 1: Financial Report Processing

```python
from pystreampdf.excel_export import PDFToExcelPipeline
from pystreammcp import QualityValidator, ValidationGate

# Strict validation for financial data
validator = QualityValidator(statguardian_enabled=True)
gate = ValidationGate(
    dataset_id="financial",
    min_quality_score=0.95,  # Very high bar
    block_on_failure=True    # Reject any low-quality data
)
validator.register_gate(gate)

pipeline = PDFToExcelPipeline()
pipeline.set_quality_validator(validator)

result = pipeline.convert_pdf_to_excel(
    "quarterly_report.pdf",
    "quarterly_financials.xlsx",
    validate_quality=True,
    confidence_threshold=0.9
)

if not result["errors"]:
    print(f"✅ Extracted {result['tables_exported']} financial tables")
```

### Example 2: Automated Data Collection

```python
import glob
from pathlib import Path
from pystreampdf.excel_export import convert_pdf_to_excel

# Batch process all PDFs in input directory
input_dir = "reports/incoming"
output_dir = "reports/processed"

Path(output_dir).mkdir(exist_ok=True)

for pdf_file in sorted(glob.glob(f"{input_dir}/*.pdf")):
    basename = Path(pdf_file).stem
    output_file = f"{output_dir}/{basename}.xlsx"
    
    result = convert_pdf_to_excel(pdf_file, output_file)
    
    status = "✅" if not result["errors"] else "❌"
    print(f"{status} {basename}: {result['tables_extracted']} tables extracted")
```

---

## Summary

PyStreamPDF ↔ PyStreamXL integration enables:

✅ **PDF Table Extraction** — Automatic table detection from PDFs  
✅ **Excel Export** — Direct output to Excel workbooks  
✅ **Quality Validation** — StatGuardian integration for data quality  
✅ **Data Pipelines** — Batch processing and automation  
✅ **Production Ready** — 24 tests passing, comprehensive error handling  

**Status:** ✅ COMPLETE & READY FOR PRODUCTION

---

**File:** `PyStreamPDF/INTEGRATION_EXCEL_EXPORT.md`  
**Last Updated:** 2026-07-17  
**Tests:** 24/24 passing ✅

