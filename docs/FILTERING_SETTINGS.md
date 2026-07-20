# Filtering Settings Guide

PyStreamPDF's filtering stage determines which sections to include in the final context based on relevance scores and selection constraints. This guide explains how to configure the filtering behavior.

## Quick Start

### Using Filtering Strategies

The simplest way to control filtering is with preset strategies:

```python
import pystreampdf
from pystreampdf.config import FilteringConfig

doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
navigator = doc.navigator_with_index(index)

# Get strategy configuration
strategy = FilteringConfig.get_strategy("balanced")  # RECOMMENDED

# Use with retrieval
context, flow = navigator.retrieve_with_flow(
    "your query",
    max_tokens=500,
    min_relevance_score=strategy["min_relevance_score"],
    max_sections=strategy["max_sections"]
)
```

## Filtering Strategies

### Preset Strategies

PyStreamPDF provides three filtering strategies with different strictness levels:

#### 1. **Strict** — Only Highest Relevance

```python
strategy = FilteringConfig.get_strategy("strict")
# {
#     "min_relevance_score": 0.7,
#     "max_sections": 3,
#     "require_threshold": True,
#     "description": "Only highest relevance - minimal, focused output"
# }
```

**Use when:**
- You want minimal output (1-2 sections max)
- You have very specific, narrow queries
- Context size is strictly limited
- You want to avoid irrelevant content

**Characteristics:**
- Only includes sections with >70% relevance confidence
- Returns at most 3 sections
- Must pass minimum threshold
- Lowest token usage, highest precision

**Example:**
```python
strategy = FilteringConfig.get_strategy("strict")
context, flow = navigator.retrieve_with_flow(
    "neural network activation function",
    max_tokens=500,
    min_relevance_score=strategy["min_relevance_score"],
    max_sections=strategy["max_sections"]
)
# Returns only 1-3 highly relevant sections
```

#### 2. **Balanced** — RECOMMENDED

```python
strategy = FilteringConfig.get_strategy("balanced")
# {
#     "min_relevance_score": 0.5,
#     "max_sections": 5,
#     "require_threshold": True,
#     "description": "RECOMMENDED: High-quality selections"
# }
```

**Use when:**
- Standard RAG/LLM queries
- You want good context without over-retrieving
- You need moderate coverage with precision
- Token budget allows 500+ tokens

**Characteristics:**
- Includes sections with >50% relevance confidence
- Returns up to 5 sections (often 2-4)
- Good balance of coverage and precision
- Recommended for most use cases

**Example:**
```python
strategy = FilteringConfig.get_strategy("balanced")
context, flow = navigator.retrieve_with_flow(
    "how does machine learning improve accuracy",
    max_tokens=500,
    min_relevance_score=strategy["min_relevance_score"],
    max_sections=strategy["max_sections"]
)
# Returns 2-5 high-quality sections
```

#### 3. **Lenient** — Broader Retrieval

```python
strategy = FilteringConfig.get_strategy("lenient")
# {
#     "min_relevance_score": 0.3,
#     "max_sections": 10,
#     "require_threshold": False,
#     "description": "Broader retrieval for comprehensive coverage"
# }
```

**Use when:**
- You need broader context
- Queries are ambiguous or multi-faceted
- You have large token budgets (750+)
- You want comprehensive coverage over precision

**Characteristics:**
- Includes sections with >30% relevance confidence
- Returns up to 10 sections
- More lenient on threshold requirement
- Higher token usage, broader coverage

**Example:**
```python
strategy = FilteringConfig.get_strategy("lenient")
context, flow = navigator.retrieve_with_flow(
    "machine learning",
    max_tokens=1000,
    min_relevance_score=strategy["min_relevance_score"],
    max_sections=strategy["max_sections"]
)
# Returns up to 10 sections covering broad ML topics
```

## Custom Filtering Configuration

For fine-grained control, configure filtering parameters directly:

### Relevance Score Threshold

The relevance score (0.0-1.0) indicates how well a section matches the query.

```python
# Conservative: only highest matches (score >0.75)
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=500,
    min_relevance_score=0.75  # Only very relevant sections
)

# Balanced: good matches (score >0.50)
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=500,
    min_relevance_score=0.50  # RECOMMENDED
)

# Liberal: broader matches (score >0.30)
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=500,
    min_relevance_score=0.30  # Include broader matches
)
```

**Valid range:** 0.1 - 1.0 (enforced by FilteringConfig.validate_relevance_score)

### Maximum Sections

Limit the number of sections returned:

```python
# Minimal: just the top section
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=500,
    max_sections=1  # Only top result
)

# Standard: a few sections
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=500,
    max_sections=5  # Top 5 sections
)

# Comprehensive: many sections
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=1000,
    max_sections=15  # Lots of coverage
)
```

**Valid range:** 1 - 20 (enforced by FilteringConfig.validate_max_sections)

## Filtering Strategy Selection Guide

### Query Type → Recommended Strategy

| Query Type | Strategy | Min Score | Max Sections | Reason |
|-----------|----------|-----------|--------------|--------|
| Specific fact ("What is X?") | **strict** | 0.7 | 3 | Single answer needed |
| Definition/explanation | **balanced** | 0.5 | 5 | RECOMMENDED default |
| How-to/tutorial | **balanced** | 0.5 | 5 | Moderate context needed |
| Comparison ("A vs B") | **balanced** | 0.5 | 5 | 2-3 sections each |
| Topic overview | **lenient** | 0.3 | 10 | Broad coverage |
| Research synthesis | **lenient** | 0.3 | 10 | Multiple perspectives |
| Quick lookup | **strict** | 0.7 | 1 | Just the answer |

### Token Budget → Strategy

| Budget | Strategy | Rationale |
|--------|----------|-----------|
| 250 (minimal) | **strict** | Limited space, high precision |
| 500 (standard) | **balanced** | Sweet spot for coverage/precision |
| 750 (rich) | **balanced** or **lenient** | Room for multiple sections |
| 1000 (comprehensive) | **lenient** | Budget allows extensive retrieval |

## Advanced: Custom Validation

Validate filtering parameters:

```python
from pystreampdf.config import FilteringConfig

# Validate relevance score
try:
    score = FilteringConfig.validate_relevance_score(0.65)
    print(f"Valid score: {score}")
except ValueError as e:
    print(f"Invalid: {e}")

# Validate max sections
try:
    sections = FilteringConfig.validate_max_sections(7)
    print(f"Valid section count: {sections}")
except ValueError as e:
    print(f"Invalid: {e}")
```

## Understanding Filtering in Pipeline Visualization

The pipeline shows filtering at the **Selection stage**:

```
Retrieval          Selection
[Retrieved]        [Selected]
  8 sections       5 sections (3 filtered due to token budget)
  4500 words       500 words (4000 words filtered)
```

### Selection Markers

In the pipeline table, the Select column shows:
- `[OK]` — Section selected for LLM
- `[--]` — Section not selected (didn't meet relevance threshold)
- `[X]` — Section would be selected but excluded due to token budget

### Analyzing Selection Loss

```python
context, flow = navigator.retrieve_with_flow("query", max_tokens=500)

for section in flow.sections:
    if not section.selected:
        if section.filtering_loss() > 0:
            print(f"{section.title}: Filtered (token budget)")
        else:
            print(f"{section.title}: Not relevant to query")

# Check summary
print(f"Filtering loss: {flow.summary.filtering_loss()} words")
print(f"Retrieval loss: {flow.summary.retrieval_loss()} words")
```

## Combining Token Budget + Filtering

For complete control, use both settings together:

```python
import pystreampdf
from pystreampdf.config import TokenBudgetConfig, FilteringConfig

doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
navigator = doc.navigator_with_index(index)

# High-quality extraction: strict filtering + minimal budget
strategy = FilteringConfig.get_strategy("strict")
context, flow = navigator.retrieve_with_flow(
    "specific question",
    max_tokens=TokenBudgetConfig.get_preset("minimal"),      # 250 tokens
    min_relevance_score=strategy["min_relevance_score"],      # 0.7
    max_sections=strategy["max_sections"]                     # 3
)

# Comprehensive extraction: lenient filtering + rich budget
strategy = FilteringConfig.get_strategy("lenient")
context, flow = navigator.retrieve_with_flow(
    "broad topic",
    max_tokens=TokenBudgetConfig.get_preset("comprehensive"), # 1000 tokens
    min_relevance_score=strategy["min_relevance_score"],      # 0.3
    max_sections=strategy["max_sections"]                     # 10
)
```

## Performance Implications

### Filtering Impact on Retrieval Time

| Strategy | Avg Sections | Avg Tokens | Processing Time |
|----------|--------------|------------|-----------------|
| strict | 1-2 | 150-300 | Fastest |
| balanced | 3-4 | 300-500 | Normal |
| lenient | 6-8 | 600-900 | Slower |

More sections → more processing time, but still <500ms for typical PDFs.

### Query Types That Need Adjustment

```python
# Generic query: may return too many sections
context, flow = navigator.retrieve_with_flow(
    "machine learning",  # Too broad, returns 10+ sections
    max_tokens=500
)

# Solution 1: Stricter filtering
context, flow = navigator.retrieve_with_flow(
    "machine learning",
    max_tokens=500,
    min_relevance_score=0.6,  # Higher threshold
    max_sections=3              # Fewer sections
)

# Solution 2: More specific query
context, flow = navigator.retrieve_with_flow(
    "neural network architectures",  # More specific
    max_tokens=500
)
```

## Troubleshooting Filtering

### Problem: Getting Too Few Sections

```python
# Current (returns 1-2 sections)
context, flow = navigator.retrieve_with_flow("query", max_tokens=500)

# Solutions:
# 1. Increase max_sections
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=500,
    max_sections=8  # Up from 5
)

# 2. Lower relevance threshold
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=500,
    min_relevance_score=0.4  # Down from 0.5
)

# 3. Increase token budget
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=750,  # More room
    min_relevance_score=0.5
)
```

### Problem: Getting Too Many Sections

```python
# Current (returns 10+ sections)
context, flow = navigator.retrieve_with_flow("query", max_tokens=1000)

# Solutions:
# 1. Reduce max_sections
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=1000,
    max_sections=3  # Down from 10
)

# 2. Raise relevance threshold
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=1000,
    min_relevance_score=0.6  # Up from 0.3
)

# 3. Use stricter strategy
strategy = FilteringConfig.get_strategy("strict")
context, flow = navigator.retrieve_with_flow(
    "query",
    max_tokens=1000,
    min_relevance_score=strategy["min_relevance_score"],
    max_sections=strategy["max_sections"]
)
```

## Configuration Best Practices

1. **Start with balanced strategy:**
   ```python
   strategy = FilteringConfig.get_strategy("balanced")
   # Works well for 80% of queries
   ```

2. **Adjust based on results:**
   ```python
   # If too few sections: use lenient strategy
   # If too many sections: use strict strategy
   ```

3. **Match token budget to strategy:**
   ```python
   # strict strategy → minimal (250) or standard (500) budget
   # lenient strategy → rich (750) or comprehensive (1000) budget
   ```

4. **Test on sample queries:**
   ```python
   queries = ["specific", "medium", "broad"]
   for q in queries:
       context, flow = navigator.retrieve_with_flow(q, max_tokens=500)
       print(f"{q}: {len(flow.sections)} sections")
   ```

## Implementation Details

The filtering configuration is implemented in:
- **Python**: `pystreampdf/config.py` — FilteringConfig class and strategies
- **Integration**: Filtering parameters passed to retrieval pipeline
- **Visualization**: Pipeline flow shows filtering impact per section

See PIPELINE_VISUALIZATION.md for details on understanding filtering in pipeline output.
