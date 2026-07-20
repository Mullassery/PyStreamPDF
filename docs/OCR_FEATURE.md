# OCR Feature Guide

PyStreamPDF includes built-in OCR (Optical Character Recognition) support to convert scanned PDFs into text-extractable documents.

## Quick Start

### Installation

```bash
# Install PyStreamPDF with OCR support
pip install pystreampdf

# Install OCR backend (choose one):

# Option 1: Tesseract (free, recommended for Mac/Linux)
brew install tesseract  # macOS
apt-get install tesseract-ocr  # Linux

# Option 2: PaddleOCR (pure Python, no system dependencies)
pip install paddleocr
```

### Basic Usage

```python
from pystreampdf.ocr import process_scanned_pdf

# Process a scanned PDF
result = process_scanned_pdf(
    pdf_path="scanned_document.pdf",
    output_text_path="extracted_text.txt"  # Optional
)

# Check results
print(result.summary())
# Output:
# OCR Processing Summary
# ======================
# PDF: scanned_document.pdf
# Pages processed: 5/5
# Pages failed: 0
# Total words extracted: 12345
# 
# Per-page results:
#   ✓ Page 1: 2456 words
#   ✓ Page 2: 2389 words
#   ...
```

## Advanced Usage

### Configure OCR Backend

```python
from pystreampdf.ocr import OCRProcessor, OCRConfig, OCRBackend

# Use specific backend
config = OCRConfig(
    backend=OCRBackend.PADDLE,  # or TESSERACT
    language="eng",  # Language code
    confidence_threshold=0.5,  # Min confidence (0.0-1.0)
    page_indices=[0, 1, 2],  # Process only pages 1-3 (None = all)
)

processor = OCRProcessor(config)
text, page_results = processor.process_pdf_pages("scanned.pdf")
```

### Integrate with PyStreamPDF Pipeline

```python
import pystreampdf
from pystreampdf.ocr import process_scanned_pdf

# Step 1: Process scanned PDF with OCR
print("Step 1: Converting scanned PDF to text-extractable...")
ocr_result = process_scanned_pdf("scanned_document.pdf")

# Step 2: Extract with PyStreamPDF (now that text is extractable)
print("Step 2: Extracting with PyStreamPDF...")
doc = pystreampdf.open("scanned_document.pdf")
index = doc.build_index("index.db")
navigator = doc.navigator_with_index(index)

# Step 3: Retrieve with pipeline visualization
print("Step 3: Retrieving context...")
context, flow = navigator.retrieve_with_flow("your query", max_tokens=500)

# Step 4: Check for remaining extraction loss
if flow.summary.extraction_loss_pct() > 5:
    print(f"Warning: {flow.summary.extraction_loss_pct():.1f}% extraction loss")
    print("Some images may still have unextractable text")
else:
    print("✓ OCR successful, extraction loss minimal")

# Use context
print(f"Retrieved {len(context.sections)} sections, {context.total_tokens} tokens")
```

### Auto-Detect Best Backend

```python
from pystreampdf.ocr import OCRConfig

# Automatically select best available backend
backend = OCRConfig.auto_detect_backend()
print(f"Using backend: {backend}")

config = OCRConfig(backend=backend)
# ... process PDF
```

## OCR Engine Selection

PyStreamPDF automatically selects the best OCR engine available on your system.

### Auto-Detection (Recommended)

PyStreamPDF will automatically use whichever OCR engine is available:

```python
from pystreampdf.ocr import OCRConfig

# Auto-detects best available engine
backend = OCRConfig.auto_detect_backend()
config = OCRConfig(backend=backend)
processor = OCRProcessor(config)
```

### Performance vs Setup

**Quick Setup** (pure Python, no system dependencies)
- Install: `pip install pystreampdf[ocr]`
- First run: Downloads models (~400MB, happens once)
- Speed: 0.5-2 seconds per page
- Works on Mac/Linux/Windows identically

**System-Optimized** (higher accuracy, requires setup)
- Install: Follow platform-specific instructions
- Speed: 2-5 seconds per page
- Better handling of poor-quality scans
- Installation varies by OS

Most users should use quick setup. If you encounter accuracy issues, the library will guide you to system-optimized installation.

### Language Support

```python
config = OCRConfig(language="fra")  # French
# Supports 100+ languages
# Common: eng, fra, deu, spa, ita, rus, chi, jpn
```

## Performance Considerations

### Processing Time

- **Tesseract**: ~2-5 seconds per page
- **PaddleOCR**: ~0.5-2 seconds per page

For 100-page document:
- Tesseract: 3-8 minutes
- PaddleOCR: 1-3 minutes

### Memory Usage

- Tesseract: ~100-200MB
- PaddleOCR: ~500MB-1GB (for GPU acceleration)

### CPU vs GPU

PaddleOCR supports GPU acceleration:
```python
# Use CUDA GPU (if available)
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, use_gpu=True)
# 2-3x faster than CPU
```

## Quality Tuning

### Confidence Threshold

```python
# Only include OCR text with >60% confidence
config = OCRConfig(confidence_threshold=0.6)

# Default is 0.5, increase for cleaner output
# but may lose some text
```

### Language Specification

```python
# Process French document
config = OCRConfig(language="fra")

# Tesseract language codes:
# eng (English), fra (French), deu (German)
# spa (Spanish), ita (Italian), rus (Russian)
# See: https://github.com/UB-Mannheim/tesseract/wiki/Data-Files

# PaddleOCR language codes:
# "en" (English), "ch" (Chinese), "fr", "de", "es", etc.
```

### Process Specific Pages Only

```python
# Only process pages 5, 6, 7 (indices 4, 5, 6)
config = OCRConfig(page_indices=[4, 5, 6])

# Process only first 10 pages
config = OCRConfig(page_indices=list(range(10)))
```

## Workflow: When to Use OCR

### Diagnostic Approach

1. **Open PDF with PyStreamPDF:**
   ```python
   doc = pystreampdf.open("document.pdf")
   context, flow = navigator.retrieve_with_flow("query", max_tokens=500)
   print(flow.overall_extraction_diagnosis)
   ```

2. **Check extraction loss:**
   ```python
   if flow.summary.extraction_loss_pct() > 5:
       print("High extraction loss - likely scanned PDF")
       print("Consider running OCR first")
   ```

3. **Decide:**
   - **Loss < 5%**: Skip OCR, proceed with PyStreamPDF
   - **Loss 5-20%**: Try OCR for better quality
   - **Loss > 20%**: Must use OCR for acceptable results

### Complete Workflow

```python
import pystreampdf
from pystreampdf.ocr import process_scanned_pdf
from pystreampdf.config import TokenBudgetConfig

def extract_from_potentially_scanned_pdf(pdf_path, query):
    """
    Smart extraction: diagnose, OCR if needed, extract
    """
    
    # Step 1: Quick diagnostic
    print("Step 1: Diagnosing PDF...")
    doc = pystreampdf.open(pdf_path)
    
    try:
        index = doc.build_index("/tmp/index.db")
        nav = doc.navigator_with_index(index)
        context, flow = nav.retrieve_with_flow(query, max_tokens=250)  # minimal preset
        
        extraction_loss = flow.summary.extraction_loss_pct()
        print(f"Extraction loss: {extraction_loss:.1f}%")
        
        # Step 2: Decide if OCR needed
        if extraction_loss < 5:
            print("✓ PDF extracts well, no OCR needed")
            return context
        
        if extraction_loss < 20:
            print(f"⚠️ Moderate loss ({extraction_loss:.1f}%), considering OCR...")
            apply_ocr = True
        else:
            print(f"✗ High loss ({extraction_loss:.1f}%), OCR required")
            apply_ocr = True
            
    except Exception as e:
        print(f"Initial extraction failed: {e}, will try OCR")
        apply_ocr = True
    
    # Step 3: Apply OCR if needed
    if apply_ocr:
        print("\nStep 2: Running OCR (this may take a few minutes)...")
        result = process_scanned_pdf(pdf_path)
        
        if result.pages_failed > 0:
            print(f"⚠️ Warning: {result.pages_failed} pages failed OCR")
        
        print(f"✓ Extracted {result.total_words_extracted} words via OCR")
        
        # Re-extract after OCR
        print("\nStep 3: Re-extracting with PyStreamPDF...")
        doc = pystreampdf.open(pdf_path)
        index = doc.build_index("/tmp/index_ocr.db")
        nav = doc.navigator_with_index(index)
        context, flow = nav.retrieve_with_flow(query, max_tokens=500)
        
        print(f"✓ Retrieval complete: {context.total_tokens} tokens, {len(context.sections)} sections")
        return context
    
    # Step 4: Retrieve with full budget if no OCR needed
    print("\nStep 2: Final extraction...")
    context, flow = nav.retrieve_with_flow(query, max_tokens=500)
    print(f"✓ Retrieval complete: {context.total_tokens} tokens, {len(context.sections)} sections")
    return context
```

## Output Formats

### Get OCR Text as String

```python
from pystreampdf.ocr import process_scanned_pdf

result = process_scanned_pdf("scanned.pdf")
ocr_text = result.ocr_text
print(ocr_text[:500])
```

### Save OCR Text

```python
result = process_scanned_pdf("scanned.pdf", output_text_path="extracted.txt")
# Creates extracted.txt with all OCR text
```

### Per-Page Results

```python
result = process_scanned_pdf("scanned.pdf")

for page_num, page_result in result.page_results.items():
    print(f"Page {page_num + 1}:")
    print(f"  Status: {page_result['status']}")
    print(f"  Words: {page_result['word_count']}")
    if page_result['status'] == 'failed':
        print(f"  Error: {page_result['error']}")
```

## Troubleshooting

### "No OCR backend available" Error

```
Solution: Install one of the backends

Option 1 (Tesseract):
  brew install tesseract  # macOS
  apt-get install tesseract-ocr  # Linux

Option 2 (PaddleOCR):
  pip install paddleocr
```

### Tesseract Not Found

```
Error: "Tesseract not installed" or similar

Solution: Install Tesseract
  # macOS
  brew install tesseract
  
  # Linux
  sudo apt-get install tesseract-ocr
  
  # Windows
  Download from https://github.com/UB-Mannheim/tesseract/wiki
  Make sure path is in environment variables
```

### PaddleOCR Download Hangs

```
First run downloads model files (~400MB)
This is normal and only happens once

Solution: Wait for download to complete
          Or manually download: https://paddleocr.bj.bcebos.com/
```

### Low Quality OCR Results

```
Solutions:
1. Pre-process PDF (deskew, enhance contrast)
2. Specify correct language:
   config = OCRConfig(language="fra")  # For French
3. Adjust confidence threshold:
   config = OCRConfig(confidence_threshold=0.3)  # Lower = more text, lower quality
```

### Very Slow Processing

```
Solutions:
1. Process fewer pages:
   config = OCRConfig(page_indices=[0, 1, 2])  # First 3 pages
2. Use PaddleOCR instead of Tesseract (2-3x faster)
3. Use GPU acceleration for PaddleOCR:
   # Requires CUDA installation
```

## Best Practices

1. **Test on sample first:**
   ```python
   # Process just first 3 pages to test
   config = OCRConfig(page_indices=[0, 1, 2])
   ```

2. **Check results before using:**
   ```python
   result = process_scanned_pdf("scanned.pdf")
   if result.pages_failed > 0:
       print(f"Warning: {result.pages_failed} pages failed")
   ```

3. **Use appropriate language:**
   ```python
   # If PDF is in French, specify it
   config = OCRConfig(language="fra")
   ```

4. **Balance speed vs quality:**
   - Quick test: `confidence_threshold=0.3`
   - Production: `confidence_threshold=0.5`
   - High quality: `confidence_threshold=0.7`

5. **Cache results:**
   ```python
   # Save OCR text, don't re-process
   result = process_scanned_pdf("scanned.pdf", 
                                output_text_path="cached_ocr.txt")
   ```

