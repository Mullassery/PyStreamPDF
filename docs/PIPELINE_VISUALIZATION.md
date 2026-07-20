# Pipeline Visualization

PyStreamPDF now includes visualization of the complete PDF processing pipeline, showing how documents flow from extraction through to final LLM context.

## Quick Reference: Common Issues & Solutions

| Issue | Indicator | Solution |
|-------|-----------|----------|
| **Losing important context** | `[X]` markers in Select column | Increase `max_tokens` parameter |
| **Query returns nothing** | All `[--]` in Retrieve column | Query doesn't match document; try different keywords |
| **Extraction quality low** | High `[*]` count in Extract column | PDF is scanned/complex; requires OCR or conversion |
| **Token budget unknown** | Unsure what to set | Use `s.retrieved_words` as `max_tokens` value |

## Overview

The pipeline visualization reveals what happens at each stage:

1. **Raw PDF** — What actually exists in the document
2. **Extraction** — Text extracted by pdfium-render (reveals parsing losses)
3. **Indexing** — Text made searchable via FTS5
4. **Retrieval** — Sections matching the query
5. **Selection** — Final sections sent to LLM (respecting token budget)

This helps answer critical questions:
- **Are we losing text during PDF parsing?** (scanned PDFs, embedded images, complex formatting)
- **Is the query finding relevant content?** (retrieval quality)
- **Are we hitting token limits?** (budget constraints)

## Usage

### Setting Token Budget

The **token budget** is the `max_tokens` parameter. You must use preset values within allowed range.

```python
import pystreampdf
from pystreampdf.config import TokenBudgetConfig, RetrievalConfig

doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
navigator = doc.navigator_with_index(index)

# Use presets (only valid option)
context, flow = navigator.retrieve_with_flow(
    "query", 
    max_tokens=TokenBudgetConfig.get_preset("standard")  # 500 (recommended)
)

# Available presets: minimal (250), standard (500), rich (750), comprehensive (1000)
context, flow = navigator.retrieve_with_flow(
    "query", 
    max_tokens=TokenBudgetConfig.get_preset("rich")  # 750 for complex queries
)

# Use profiles for semantic naming
profile = RetrievalConfig.get_profile("rich")
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=profile["max_tokens"]  # 750
)
```

**Available Presets (only these work):**
- `minimal` (250): Essential facts only
- `standard` (500): RECOMMENDED - core relevant content
- `rich` (750): Richer context for complex queries
- `comprehensive` (1000): Full context if needed

**Absolute Limits (enforced):**
- Below 250: Not allowed (loses too much context)
- Above 2000: Not allowed (defeats selective extraction)
- Custom values outside presets: Raises error

No exceptions to these limits. They define PyStreamPDF's selectivity mission.

### Full Example

```python
import pystreampdf

# Open PDF and build index
doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
navigator = doc.navigator_with_index(index)

# Retrieve with pipeline flow visualization
context, flow = navigator.retrieve_with_flow("your query", max_tokens=2000)

# Display visualizations
flow.to_cli_table()      # Terminal-friendly table
flow.to_flow_diagram()   # ASCII flow diagram
flow.to_json()           # JSON for programmatic use

# Check if you're hitting token limit
s = flow.summary
if s.filtering_loss() > 0:
    print(f"⚠️ {s.filtering_loss()} words filtered due to token budget")
    print(f"  Increase max_tokens to {s.retrieved_words} to include all matches")
```

### CLI Output Example

#### Table View

```
PDF PROCESSING PIPELINE: "neural networks"
============================================================================...

Section                                  | Raw    | Extract      | Index        | Retrieve     | Select      
------------ ...
Introduction                        p.1-2    |  850w  | [*]  800w (-50) | [OK]  800w   | [--]    0w   | [--]    0w  
Chapter 3: Neural Networks          p.9-12   | 2100w  | [*] 2050w (-50) | [OK] 2050w   | [OK] 2050w   | [OK] 2050w  
Chapter 4: Deep Learning            p.13-16  | 2300w  | [*] 2250w (-50) | [OK] 2250w   | [OK] 2250w   | [X]     0w  

LEGEND:
  [OK]  = Passed through this stage
  [*]   = Data loss at this stage (text missed during extraction/indexing)
  [--]  = Filtered out at this stage (intentional filtering)
  [X]   = Exceeds token budget constraint
```

#### Flow Diagram

```
                       PDF Content
                            |
                    10400 words [RAW PDF]
                            |
                      Extraction
                      pdfium-render
                            v
  [WARNING] Lost 800 words (7.7%) during parsing
            -> Likely causes: scanned PDF, embedded images, complex formatting
                    9600 words [EXTRACTED]
                            |
                         Indexing
                       FTS5 cleanup
                            v
  [INFO] Normalized 100 words during indexing
                    9500 words [INDEXED]
                            |
                    Query Matching
                      (keyword/score)
                            v
  [FILTER] 5200 words (54.7%) not relevant to query
                    4300 words [RETRIEVED]
                            |
                     Token Budget
                      (max_tokens=2000)
                            v
  [FILTER] 2250 words (52.3%) exceeds budget
                    2050 words [SELECTED]
                            |
                       Send to LLM
```

## Understanding the Metrics

### Loss Types

1. **Extraction Loss** ⚠️
   - Text that exists in PDF but wasn't extracted by pdfium-render
   - Non-intentional data loss (quality issue)
   - Causes: scanned PDFs, embedded images, complex formatting, encoding issues
   - **Action**: High extraction loss indicates PDF quality problems

2. **Indexing Loss**
   - Minor text normalization during FTS5 indexing
   - Usually <2% (punctuation, special chars, whitespace normalization)
   - Intentional for search quality

3. **Retrieval Loss**
   - Sections not matching the search query
   - Intentional filtering (relevance constraint)
   - Indicates query specificity and document coverage

4. **Filtering Loss**
   - Sections matching query but excluded due to token budget
   - Intentional constraint (LLM context limits)
   - Indicates need for larger token budget or more selective filtering

## Data Access

### Python Object Hierarchy

```python
flow: PyPipelineFlow
  ├── query: str
  ├── sections: List[PySectionFlow]
  │   ├── title: str
  │   ├── pages: str
  │   ├── raw_words: int
  │   ├── extracted_words: int
  │   ├── indexed_words: int
  │   ├── retrieved_words: int
  │   ├── selected_words: int
  │   ├── selected: bool
  │   ├── relevance_score: Optional[float]
  │   ├── reason: Optional[str]
  │   └── Methods:
  │       ├── extraction_loss() -> int
  │       ├── indexing_loss() -> int
  │       ├── retrieval_loss() -> int
  │       ├── filtering_loss() -> int
  │       └── extraction_loss_pct() -> float
  │
  └── summary: PyPipelineSummary
      ├── raw_words: int
      ├── extracted_words: int
      ├── indexed_words: int
      ├── retrieved_words: int
      ├── selected_words: int
      └── Methods:
          ├── extraction_loss() -> int
          ├── indexing_loss() -> int
          ├── retrieval_loss() -> int
          ├── filtering_loss() -> int
          ├── extraction_loss_pct() -> float
          ├── retrieval_loss_pct() -> float
          └── filtering_loss_pct() -> float
```

### JSON Structure

```json
{
  "query": "neural networks",
  "sections": [
    {
      "title": "Chapter 3: Neural Networks",
      "pages": "9-12",
      "raw_words": 2100,
      "extracted_words": 2050,
      "indexed_words": 2050,
      "retrieved_words": 2050,
      "selected_words": 2050,
      "selected": true,
      "relevance_score": 0.95,
      "reason": null
    }
  ],
  "summary": {
    "raw_words": 10400,
    "extracted_words": 9600,
    "indexed_words": 9500,
    "retrieved_words": 4300,
    "selected_words": 2050,
    "losses": {
      "extraction_words": 800,
      "extraction_pct": 7.7,
      "indexing_words": 100,
      "retrieval_words": 5200,
      "filtering_words": 2250
    }
  }
}
```

## Use Cases

### 1. Debugging Poor Retrieval

If your queries return irrelevant sections:
- Check **retrieval_loss_pct** — high loss means poor query-document fit
- Check **relevance_score** values for selected sections
- Verify section titles match expected content

### 2. Detecting PDF Quality Issues

High **extraction_loss_pct** signals:
- Scanned PDFs without OCR
- Complex layouts (multi-column, floating elements)
- Embedded images with text
- Non-standard encoding

**Fix**: Re-process PDF (OCR if scanned, convert if formatting issue)

### 3. Optimizing Token Budget

If important sections are filtered:
- Increase **max_tokens** parameter
- Use stricter relevance_score threshold
- Break retrieval into multiple queries
- Implement section ranking/prioritization

### 4. Auditing RAG System

For production RAG pipelines:
- Export **flow.to_json()** for each query
- Monitor extraction loss over time
- Track retrieval quality metrics
- Alert on unexpected loss patterns

## Extraction Loss Diagnosis

When the pipeline shows text loss during extraction (the `[*]` marker), PyStreamPDF automatically diagnoses the likely cause:

### Automatic Diagnosis

```python
context, flow = navigator.retrieve_with_flow("query", max_tokens=2000)

# Check per-section diagnosis
for section in flow.sections:
    if section.extraction_diagnosis:
        diag = section.extraction_diagnosis
        print(f"{section.title}:")
        print(f"  Loss: {diag.loss_percentage:.1f}%")
        print(f"  Likely cause: {diag.primary_cause}")  # (enum)
        print(f"  Explanation: {diag.explanation}")
        print(f"  Action: {diag.recommended_action}")
```

### Diagnosis Types

| Loss % | Likely Cause | Explanation | Quick Fix |
|--------|--------------|-------------|-----------|
| <2% | Minor formatting | Punctuation/whitespace normalization | None needed |
| 2-5% | Complex formatting | Tables, multi-column, floating elements | Increase token budget if needed |
| 5-10% | Scanned or complex | PDF parsing limitations | Increase token budget |
| 10-25% | Mixed content | Scanned pages mixed with text | Increase token budget + preview before LLM |
| >25% | Scanned/encoded | PDF is primarily image-based | Significant token budget increase required |

### Diagnosis Confidence

Each diagnosis includes a confidence score (0.0-1.0):
- `>0.8`: High confidence (likely accurate)
- `0.6-0.8`: Medium confidence (probable, but verify)
- `<0.6`: Low confidence (ambiguous, needs verification)

### Overall Pipeline Diagnosis

Check the overall extraction diagnosis:

```python
if flow.overall_extraction_diagnosis:
    print(flow.overall_extraction_diagnosis)
```

Example output:
```
Extraction quality degraded - 7.7% loss affecting 50% of sections

Diagnosis: PDF is scanned or image-based (no OCR applied)
Severity: 3/5
Recommended actions:
1. Increase token budget to compensate
2. Verify retrieval quality in pipeline visualization
```

## Troubleshooting

### Problem: Seeing `[X]` in Select column (sections filtered due to token budget)

**Diagnosis:**
```python
context, flow = navigator.retrieve_with_flow("query", max_tokens=2000)
s = flow.summary

if s.filtering_loss() > 0:
    print(f"Problem: {s.filtering_loss()} words excluded due to token budget")
```

**Solution: Increase max_tokens**
```python
# Option 1: Use exact amount needed for all retrieved sections
context, flow = navigator.retrieve_with_flow("query", max_tokens=s.retrieved_words)

# Option 2: Use generous buffer (10x safety margin)
context, flow = navigator.retrieve_with_flow("query", max_tokens=s.retrieved_words * 10)

# Option 3: No limit (include everything matching query)
context, flow = navigator.retrieve_with_flow("query", max_tokens=999999)
```

### Problem: Seeing high extraction loss `[*]` (7-15%)

**Automatic Diagnosis:**
PyStreamPDF automatically identifies the cause. Check the diagnosis:

```python
context, flow = navigator.retrieve_with_flow("query", max_tokens=2000)

# Overall diagnosis
print(flow.overall_extraction_diagnosis)

# Per-section diagnosis
for section in flow.sections:
    if section.extraction_diagnosis:
        print(f"\n{section.title}:")
        print(f"  Loss: {section.extraction_diagnosis.loss_percentage:.1f}%")
        print(f"  Cause: {section.extraction_diagnosis.primary_cause}")
        print(f"  Confidence: {section.extraction_diagnosis.confidence:.0%}")
        print(f"  Fix: {section.extraction_diagnosis.recommended_action}")
```

**Most Common Fix:** Increase `max_tokens` parameter
```python
# Quick fix - use auto-suggested budget
context, flow = navigator.retrieve_with_flow("query", max_tokens=flow.summary.retrieved_words)
```

**If Problem Persists:**
- Scanned PDF: Consider OCR tool (Tesseract, but optional - token budget increase often sufficient)
- Complex formatting: Try exporting PDF from original source first
- Encoding issue: Download fresh copy of PDF

### Problem: Query returns nothing (all `[--]` in Retrieve)

**Diagnosis:** Your query doesn't match the document

**Solutions:**
```python
# Try different keywords
context, flow = navigator.retrieve_with_flow("machine learning", max_tokens=2000)

# Check what sections exist
nav = doc.navigator()
for section in nav.chapters():
    print(f"- {section.heading.text}")

# Try broader query
context, flow = navigator.retrieve_with_flow("learning", max_tokens=2000)  # More general
```

## Example: Full Workflow

```python
import pystreampdf
from pystreampdf.pipeline import PipelineFlowVisualizer

# Setup
doc = pystreampdf.open("large_document.pdf")
index = doc.build_index("index.db")
navigator = doc.navigator_with_index(index)

# Retrieve with visualization
context, flow = navigator.retrieve_with_flow("your query", max_tokens=2000)

# Analyze
s = flow.summary
print(f"Extraction loss: {s.extraction_loss_pct():.1f}%")  # PDF quality indicator
print(f"Retrieval loss: {s.retrieval_loss_pct():.1f}%")    # Query-document fit
print(f"Budget loss: {s.filtering_loss_pct():.1f}%")       # Token constraint impact

# Display for debugging
flow.to_cli_table()    # See all sections and losses
flow.to_flow_diagram() # See overall flow

# Store for auditing
import json
metrics = json.loads(flow.to_json())
log_audit_metrics(metrics)
```

## Limitations & Future Work

- Currently tracks top-level chapters only (full hierarchy planned for Phase 4)
- Extraction loss estimate based on text_preview word count (full text parsing coming)
- No ranking/scoring of filtered sections (planned)
- No export to HTML/interactive dashboard (can be added)

## Implementation Details

The pipeline tracking is implemented in:
- **Rust**: `core/src/pipeline.rs` — data structures and formatting
- **Python**: `pystreampdf/pipeline.py` — visualization helpers
- **Bindings**: `python/src/lib.rs` — PyO3 wrapper classes
