# OCR and PDF Parsing Issues Guide

When PyStreamPDF shows extraction loss (`[*]` markers in pipeline), it's often due to OCR or parsing issues. This guide explains what they are and how to fix them.

## Quick Reference

| Loss % | Likely Cause | What This Means | Fix |
|--------|--------------|-----------------|-----|
| <2% | Formatting | Minor text variations | None needed |
| 2-5% | Complex layout | Tables, columns cause issues | Verify in PDF viewer |
| 5-10% | Scanned PDF or complex | Text is images, not extractable | Apply OCR or increase budget |
| >10% | Scanned/encoded | Most/all text is images | Apply OCR tool |

---

## Understanding OCR

**OCR = Optical Character Recognition**

OCR is the technology that reads text from images.

### When is OCR needed?

**Scanned PDFs** contain photographs/scans of pages:
- Pages created by scanning paper documents
- Screenshots embedded as images
- Photos of documents (mobile scan apps)

**Text in images**: Some PDFs have text rendered as graphics/images:
- Logos with text
- Signatures with text
- Drawings with labels
- Screenshots embedded in document

**Without OCR:** These text elements cannot be extracted. PyStreamPDF sees them but can't read them.

**With OCR:** The images are converted to readable text, PyStreamPDF can extract it.

### Example

```
Scanned PDF (no OCR):
┌─────────────────────┐
│ [IMAGE of text]     │ ← PyStreamPDF sees image, can't read text
│                     │ ← Result: 0% extraction (appears as [*])
└─────────────────────┘

After OCR:
┌─────────────────────┐
│ Chapter 1: Intro    │ ← Now PyStreamPDF can read this text
│ Lorem ipsum dolor   │ ← Result: 100% extraction (no [*])
└─────────────────────┘
```

---

## Common Parsing Issues

### 1. **Scanned PDF (Most Common)**

**Diagnosis:** 5-50% extraction loss

**What it is:** PDF contains images of pages instead of actual text
- Created by scanning paper with document scanner
- Mobile apps that photo documents (Google Lens, CamScanner)
- Screenshots embedded in PDF

**How to identify:**
- Open PDF in reader, try to select/copy text → can't select
- Try in PyStreamPDF, see extraction loss > 5%
- Pages look like photographs

**How to fix:**
```
QUICK: Increase token budget (500→1000)
       Verify retrieval quality before sending to LLM

BETTER: Apply OCR to convert image→text
        Options:
        - Free: Tesseract OCR (command-line)
        - Cloud: Google Cloud Vision, AWS Textract
        - Desktop: Acrobat Pro, ABBYY FineReader
        
        Result: PDF with extractable text (no more [*])
```

### 2. **Complex Formatting**

**Diagnosis:** 2-10% extraction loss (or garbled text order)

**What it is:** Page layout confuses the parser
- Multi-column layouts
- Tables with merged cells
- Floating elements (text boxes)
- Unusual reading order

**How to identify:**
- Text extraction seems jumbled/out of order
- Specific sections have loss (not entire document)
- Looks fine visually but PyStreamPDF struggles

**How to fix:**
```
QUICK: Verify retrieval makes sense
       Increase token budget if needed

TRY: Export from original application
     If PDF was created in Word/Excel/PowerPoint:
     - Open original file
     - "Export as PDF" or "Print to PDF"
     - Use new PDF with PyStreamPDF
     
     This often fixes formatting issues

IF PERSISTS: PDF may have unusual structure
            Increase token budget to compensate
```

### 3. **Encoding/Compression Issues**

**Diagnosis:** Random loss or garbled text, 5-20% loss

**What it is:** PDF uses non-standard compression or encoding
- Unusual text encoding (not UTF-8)
- Corrupted PDF structure
- Encrypted content (without password)
- Custom compression algorithms

**How to identify:**
- Extracted text looks garbled/corrupted
- Text has strange characters
- Error messages when opening PDF
- Happens consistently with one PDF

**How to fix:**
```
QUICK: Download fresh copy of PDF
       (current copy may be corrupted)

IF SAME: Try accessing from original source
         Sometimes cloud storage/email corrupts PDFs

FALLBACK: Increase token budget
          Accept the corruption as unavoidable
```

### 4. **Embedded Images with Text**

**Diagnosis:** Specific sections have 10-50% loss

**What it is:** Text is drawn as part of images, not as text layer
- Diagrams with labels
- Flowcharts with text
- Infographics
- Embedded photos with captions

**How to identify:**
- Can select text in most of PDF
- Specific diagrams/images can't be selected
- Text in images looks clear but is image

**How to fix:**
```
QUICK: Increase token budget
       Accept that image text won't be extracted

BETTER: Apply OCR to extracted images
        Some OCR tools can process images from PDFs
        
NOTE: Manual inspection may be needed
      Some image text is inherently hard to extract
```

### 5. **Form Fields**

**Diagnosis:** Specific sections (forms) have loss

**What it is:** PDF form fields may not be extracted properly
- Fillable forms (AcroForms)
- Form data not in text layer
- Interactive PDFs

**How to identify:**
- PDF has form fields (boxes to fill)
- Loss occurs on form pages specifically
- Other pages work fine

**How to fix:**
```
QUICK: Increase token budget
       Get whatever text is extractable

BETTER: Fill form fields before extraction
        - Open PDF in Adobe Reader or Acrobat
        - Fill in visible form fields
        - Export/save completed form
        - Re-extract with PyStreamPDF

OR: Flatten the form
    Use PDF tool to flatten form fields
    (converts fields to regular text)
```

### 6. **Mixed Content**

**Diagnosis:** 10-30% loss, affects multiple sections inconsistently

**What it is:** Document has both regular text pages and scanned pages
- Report with some scanned appendices
- Book with photo inserts
- Mixed sources (some digital, some scanned)

**How to identify:**
- Most pages extract fine
- Some sections have 0% extraction ([*] only)
- Loss percentage inconsistent across document

**How to fix:**
```
QUICK: Increase token budget
       Get the text pages, accept loss on scanned pages

BETTER: Separate and process in parts
        1. Extract text pages → PyStreamPDF
        2. OCR scanned pages separately
        3. Combine results
        
TRY: Run entire PDF through OCR tool
     (handles both text and scanned)
     Produces new PDF with all text extractable
```

---

## When Extraction Loss Is OK

**You don't need to fix extraction loss if:**

1. **Loss < 2%**: Acceptable (minor formatting effects)

2. **Loss 2-5% and retrieval works**: OK to increase token budget

3. **Loss is in non-relevant sections**: If PyStreamPDF didn't select those sections for your query, loss doesn't matter

4. **Query matches remaining extracted text**: If your retrieval quality is good despite loss, increase token budget and proceed

**You DO need to fix if:**

1. **Loss > 5% AND loss affects query-relevant sections**: Risk of missing important content

2. **Retrieval quality degrades**: If increasing budget doesn't help

---

## Practical OCR Solutions

### Free Options

**Tesseract OCR** (command-line)
```bash
# Install: brew install tesseract (macOS)
#          apt-get install tesseract-ocr (Linux)
# Use:     tesseract input.pdf output pdf

tesseract scanned_document.pdf output pdf
# Creates: output.pdf (with extractable text)
```

**Python Option: pytesseract**
```python
from pdf2image import convert_from_path
from pytesseract import image_to_string
from reportlab.pdfgen import canvas

# Convert each page, apply OCR, rebuild PDF
pages = convert_from_path("scanned.pdf")
text_pages = [image_to_string(page) for page in pages]
# ...rebuild as PDF
```

### Cloud Options (pay-as-you-go)

- **Google Cloud Vision**: Fast, accurate, $1.50 per 1000 pages
- **AWS Textract**: Similar pricing, good for batch
- **Azure Computer Vision**: $2-3 per 1000 pages

### Desktop Apps (one-time purchase)

- **Adobe Acrobat Pro**: $180/year, "Recognize Text" feature
- **ABBYY FineReader**: $200-500, high accuracy

---

## Debugging Extraction Issues

### Step 1: Diagnose with PyStreamPDF

```python
context, flow = navigator.retrieve_with_flow(query, max_tokens=500)

# Check per-section diagnostics
for section in flow.sections:
    if section.extraction_diagnosis:
        diag = section.extraction_diagnosis
        print(f"\n{section.title}:")
        print(f"  Loss: {diag.loss_percentage:.1f}%")
        print(f"  Pages: {diag.page_range}")
        print(f"  Cause: {diag.primary_cause}")
        print(f"  Confidence: {diag.confidence:.0%}")
        print(f"  Fix: {diag.recommended_action}")
```

### Step 2: Verify in PDF Viewer

```
Look at pages mentioned in diagnosis:
1. Open PDF in Adobe Reader/Preview
2. Go to the pages listed in diagnosis
3. Try to select text with cursor
4. If you can't select → Scanned PDF (needs OCR)
5. If text is garbled → Encoding issue
6. If text is in images → Embedded images (needs OCR)
```

### Step 3: Test with OCR

```
If diagnosis suggests OCR:
1. Apply Tesseract or cloud OCR to PDF
2. Re-extract with PyStreamPDF
3. Compare extraction loss
4. Should drop significantly (5-50% → <2%)
```

### Step 4: Adjust Budget

```python
# If loss is acceptable, just increase budget
context, flow = navigator.retrieve_with_flow(
    query,
    max_tokens=1000  # Up from 500
)
# Verify retrieval quality is good before sending to LLM
```

---

## Summary Decision Tree

```
Extraction loss detected [*]

├─ Loss < 2%?
│  └─ YES → No action needed ✓
│
├─ Loss 2-10%?
│  ├─ Can see affected pages in PDF? (open in reader)
│  │  ├─ Can select text in those pages?
│  │  │  ├─ YES → Complex formatting
│  │  │  │         Try: Export from original app
│  │  │  │         Else: Increase budget
│  │  │  │
│  │  │  └─ NO → Scanned PDF or embedded images
│  │  │          Try: Apply OCR
│  │  │          Else: Increase budget
│  │  │
│  └─ Can't access PDF to verify?
│     └─ Increase budget (500→1000), verify retrieval
│
└─ Loss > 10%?
   └─ Likely scanned PDF
      Try: Apply OCR
      Else: Increase budget (1000→2000)
```

---

## FAQ

**Q: Will increasing token budget fix extraction loss?**
A: No, it compensates for it. If 7% of text is lost, increasing tokens helps you get more of the 93% that was extracted. To actually recover lost text, use OCR.

**Q: Is OCR always necessary?**
A: No. If retrieval quality is good and budget is sufficient, extraction loss doesn't hurt. Only apply OCR if:
- Loss >5% in query-relevant sections
- Retrieval quality is degraded

**Q: How do I know if my PDF is scanned?**
A: Open in PDF reader, try to select/copy text. If you can't, it's scanned (needs OCR).

**Q: Can PyStreamPDF do OCR internally?**
A: No, PyStreamPDF focuses on PDF parsing. Use external OCR tools (Tesseract, etc.) then re-extract.

**Q: How much will OCR cost?**
A: Tesseract (free), cloud services $1-3 per 1000 pages.

