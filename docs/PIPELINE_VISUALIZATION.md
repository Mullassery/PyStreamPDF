# Pipeline Visualization

PyStreamPDF now includes visualization of the complete PDF processing pipeline, showing how documents flow from extraction through to final LLM context.

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

### Python API

```python
import pystreampdf

# Open PDF and build index
doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
navigator = doc.navigator_with_index(index)

# Retrieve with pipeline flow visualization
context, flow = navigator.retrieve_with_flow("query text", max_tokens=2000)

# Display visualizations
flow.to_cli_table()      # Terminal-friendly table
flow.to_flow_diagram()   # ASCII flow diagram
flow.to_json()           # JSON for programmatic use
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
