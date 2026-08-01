# Token Budget Multipliers Guide

This guide explains how to configure token budget multipliers for specific keywords to automatically scale token allocation based on document content.

## Overview

PyStreamPDF's token budget system allows you to define keyword-based rules that multiply the base token budget. This enables intelligent allocation where complex documents (financial reports, legal contracts) receive more tokens, while simpler documents (summaries, excerpts) receive fewer tokens.

**Default Configuration:**
- Minimum budget: 500 tokens
- Maximum budget: 1000 tokens
- Default base budget: 1000 tokens

## Basic Multiplier Configuration

### Python Configuration

```python
from pystreampdf import TokenBudgetConfig, BudgetRule

# Define rules with multipliers
rules = [
    BudgetRule("financial", 1.2, match_fields=["filename", "title"]),
    BudgetRule("legal", 1.3, match_fields=["filename", "title"]),
    BudgetRule("summary", 0.8, match_fields=["filename"]),
]

config = TokenBudgetConfig(base_budget=800, rules=rules)

# Evaluate budget for a document
budget = config.evaluate("financial_report.pdf")
# Result: 800 * 1.2 = 960 tokens
```

### YAML Configuration

```yaml
base_budget: 800
rules:
  - keyword: financial
    multiplier: 1.2
    match_fields: [filename, title]
    case_sensitive: false
    
  - keyword: legal
    multiplier: 1.3
    match_fields: [filename, title]
    case_sensitive: false
    
  - keyword: summary
    multiplier: 0.8
    match_fields: [filename]
    case_sensitive: false
```

## Multiplier Stacking

When multiple rules match, multipliers stack multiplicatively:

```python
rules = [
    BudgetRule("financial", 1.1, match_fields=["filename"]),
    BudgetRule("quarterly", 1.05, match_fields=["filename"]),
]

config = TokenBudgetConfig(base_budget=800, rules=rules)

# File: "financial_quarterly_report.pdf"
# Calculation: 800 * 1.1 * 1.05 = 924 tokens
budget = config.evaluate("financial_quarterly_report.pdf")
```

## Common Keywords & Recommended Multipliers

### High-Complexity Documents (Multiplier: 1.2 - 1.5)
- `financial` - Financial reports, statements, analyses
- `legal` - Contracts, agreements, legal documents
- `compliance` - Regulatory documents, audit reports
- `technical` - Technical specifications, architectural docs
- `medical` - Medical reports, clinical documentation

### Medium-Complexity Documents (Multiplier: 1.0 - 1.1)
- `report` - General reports
- `analysis` - Data analysis documents
- `proposal` - Business proposals
- `audit` - Audit documentation

### Low-Complexity Documents (Multiplier: 0.6 - 0.9)
- `summary` - Document summaries
- `abstract` - Abstracts and overviews
- `excerpt` - Document excerpts
- `draft` - Draft versions

## Field Matching Options

Rules can match against three fields:

1. **filename** - PDF filename (without path)
2. **title** - PDF metadata title
3. **content_preview** - First ~500 characters of document text

```python
# Match multiple fields
rule = BudgetRule(
    keyword="financial",
    multiplier=1.3,
    match_fields=["filename", "title", "content_preview"]
)
```

## Case-Sensitive Matching

By default, keyword matching is case-insensitive:

```python
# Case-insensitive (default)
rule1 = BudgetRule("Financial", 1.2, case_sensitive=False)
# Matches: "financial_report.pdf", "FINANCIAL_REPORT.PDF"

# Case-sensitive
rule2 = BudgetRule("Financial", 1.2, case_sensitive=True)
# Matches: "Financial_report.pdf" only
```

## Practical Examples

### Example 1: Document Classification

```python
from pystreampdf import TokenBudgetConfig, BudgetRule, PDFCache

# Define comprehensive rules
rules = [
    # High-priority documents get more tokens
    BudgetRule("financial", 1.3, match_fields=["filename", "title"]),
    BudgetRule("legal", 1.3, match_fields=["filename", "title"]),
    BudgetRule("contract", 1.25, match_fields=["filename"]),
    
    # Medium-priority documents
    BudgetRule("proposal", 1.1, match_fields=["filename"]),
    BudgetRule("report", 1.05, match_fields=["filename"]),
    
    # Low-priority documents get fewer tokens
    BudgetRule("summary", 0.7, match_fields=["filename"]),
    BudgetRule("draft", 0.8, match_fields=["filename"]),
]

config = TokenBudgetConfig(base_budget=800, rules=rules)

# Use with PDFCache
cache = PDFCache(
    memory_limit_mb=500,
    disk_cache_dir="./cache",
    token_budget_config=config
)
```

### Example 2: Multi-Field Matching

```python
# Match across filename, title, and content
rules = [
    BudgetRule(
        keyword="acquisition",
        multiplier=1.4,
        match_fields=["filename", "title", "content_preview"]
    ),
    BudgetRule(
        keyword="earnings",
        multiplier=1.3,
        match_fields=["title", "content_preview"]
    ),
]

config = TokenBudgetConfig(base_budget=800, rules=rules)

# These all trigger the "acquisition" rule
budget1 = config.evaluate("acquisition_analysis.pdf")
budget2 = config.evaluate("report.pdf", title="Q3 Acquisition Strategy")
budget3 = config.evaluate("q3.pdf", content_preview="...acquisition of Acme Corp...")
```

### Example 3: Load from YAML

```python
from pystreampdf import TokenBudgetConfig

# Load configuration from file
config = TokenBudgetConfig.from_yaml("budget_config.yaml")

# Evaluate documents
budget = config.evaluate(
    filename="quarterly_financial_report.pdf",
    title="Q3 2024 Financial Report",
    content_preview="Revenue and expense analysis for Q3..."
)
```

## Budget Constraints

All evaluated budgets are clamped to the configured range:

```python
config = TokenBudgetConfig(base_budget=800, rules=[
    BudgetRule("massive", 2.0, match_fields=["filename"])
])

# Input: 800 * 2.0 = 1600
# Output: 1000 (clamped to MAX_BUDGET)
budget = config.evaluate("massive_document.pdf")
```

Budgets below the minimum are also adjusted:

```python
config = TokenBudgetConfig(base_budget=600, rules=[
    BudgetRule("tiny", 0.7, match_fields=["filename"])
])

# Input: 600 * 0.7 = 420
# Output: 500 (clamped to MIN_BUDGET)
budget = config.evaluate("tiny_document.pdf")
```

## Adjusting Budgets via Python Configuration

The primary way to adjust token budgets is through the `base_budget` parameter and multiplier rules:

```python
from pystreampdf import TokenBudgetConfig, BudgetRule

# Adjust base budget (500-1000 range maintained)
config1 = TokenBudgetConfig(base_budget=600, rules=[])

# Add multipliers for specific contexts
config2 = TokenBudgetConfig(
    base_budget=800,
    rules=[BudgetRule("complex", 1.2, match_fields=["filename"])]
)
```

**Note:** The minimum budget of 500 tokens and maximum of 1000 tokens are fixed constraints designed for optimal performance. Use multipliers to adjust within this range.

## Best Practices

1. **Start with base_budget near MAX_BUDGET** - Use 800-1000 as base, scale down with multipliers < 1.0
2. **Use meaningful keywords** - Match common document patterns in your corpus
3. **Keep multipliers moderate** - Use 0.7-1.5 range; avoid extreme values
4. **Match multiple fields** - Increases accuracy of keyword detection
5. **Test before production** - Verify rules match expected documents
6. **Document your rules** - Include comments explaining why each multiplier exists

## Integration with SemanticChunker

Token budgets can be overridden at extraction time:

```python
from pystreampdf import SemanticChunker

chunker = SemanticChunker(target_tokens=500)

chunks = chunker.chunk_content(
    text=content,
    element_type=ElementType.TEXT,
    page_start=1,
    page_end=10,
    budget_override=800  # Override config budget
)
```

## Troubleshooting

**Rule not matching?**
- Check keyword spelling and case sensitivity setting
- Verify document has the field you're matching (filename, title, or preview)
- Use `rule.matches()` to test matching directly

**Budget always at max/min?**
- Multipliers may be too large/small
- Check MIN_BUDGET and MAX_BUDGET constraints
- Verify base_budget value

**Unexpected budget calculation?**
- Remember multipliers stack multiplicatively
- Check all matching rules, not just obvious ones
- Verify field order: matches any field in match_fields list

