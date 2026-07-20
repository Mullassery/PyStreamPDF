# Automatic Token Budget Selection

PyStreamPDF can automatically detect query complexity and select appropriate token budgets. This removes the need to manually specify token limits and optimizes extraction for each query's specific needs.

## Quick Start

### Auto-Detection (Recommended)

```python
import pystreampdf
from pystreampdf.query_analyzer import auto_select_budget

# Query automatically selects budget
budget, analysis = auto_select_budget("What is machine learning?")
print(f"Budget: {budget} tokens")
print(f"Rationale: {analysis.rationale}")

# Use selected budget
doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
navigator = doc.navigator_with_index(index)

context, flow = navigator.retrieve_with_flow(
    "What is machine learning?",
    max_tokens=budget  # Auto-selected: 500 tokens
)
```

### Force Specific Budget (Override)

```python
from pystreampdf.query_analyzer import auto_select_budget

# Override auto-detection with specific level
budget, analysis = auto_select_budget(
    "What is machine learning?",
    force_level="comprehensive"  # Force max budget
)
# Budget is now 2750, not 500
```

## How It Works

### Query Analysis

The system analyzes queries for keywords and patterns to determine complexity:

```python
from pystreampdf.query_analyzer import QueryAnalyzer

query = "Compare supervised and unsupervised learning approaches"
analysis = QueryAnalyzer.analyze(query)

print(f"Detected Level: {analysis.detected_level.value}")      # "rich"
print(f"Confidence: {analysis.confidence:.0%}")                # "78%"
print(f"Complexity: {analysis.query_complexity}")              # "complex"
print(f"Matched Keywords: {analysis.matched_keywords}")        # ["compare", "learning"]
print(f"Rationale: {analysis.rationale}")                      # "Detected complex query (compare, learning)"
```

### Budget Levels

Auto-detection maps to 4 budget levels:

| Query Type | Level | Budget | Characteristics |
|-----------|-------|--------|-----------------|
| **What is X?** | minimal | 500 | Simple lookup, single answer |
| **Explain/How to** | standard | 1500 | Moderate complexity, overview |
| **Analyze/Compare** | rich | 2000 | Complex, multi-section context |
| **Deep dive/Research** | comprehensive | 2750 | Exhaustive analysis, all aspects |

### Keyword Examples

**Minimal (500 tokens):**
- "what is", "define", "explain briefly", "quick answer", "lookup"
- Single question mark: "Who invented X?"

**Standard (1500 tokens):**
- "explain", "how", "describe", "overview", "why", "understand"
- "Compare briefly", "pros and cons"

**Rich (2000 tokens):**
- "analyze", "detail", "complex", "compare", "contrast"
- "relationship", "impact", "implementation", "example"

**Comprehensive (2750 tokens):**
- "deep dive", "thorough", "exhaustive", "research"
- "best practices", "architecture", "system design"

## Usage Patterns

### Pattern 1: Simple Auto-Detection

```python
from pystreampdf.query_analyzer import auto_select_budget

def search_with_auto_budget(pdf_path, query):
    """Search PDF with auto-selected budget"""
    import pystreampdf

    # Auto-select budget
    budget, analysis = auto_select_budget(query)

    # Setup
    doc = pystreampdf.open(pdf_path)
    index = doc.build_index("/tmp/index.db")
    navigator = doc.navigator_with_index(index)

    # Retrieve with auto budget
    context, flow = navigator.retrieve_with_flow(query, max_tokens=budget)

    # Show analysis
    print(f"Query: {query}")
    print(f"Detected: {analysis.query_complexity} ({analysis.confidence:.0%} confidence)")
    print(f"Budget: {budget} tokens")
    print(flow.to_cli_table())

    return context
```

### Pattern 2: With Programmatic Override

```python
from pystreampdf.query_analyzer import AutoBudgetSelector

# Create selector with specific overrides
selector = AutoBudgetSelector(
    auto_detect=True,
    force_level=None  # Can be "minimal", "standard", "rich", "comprehensive"
)

# Analyze multiple queries
queries = [
    "What is X?",
    "Explain how X works",
    "Detailed analysis of X",
]

for query in queries:
    budget, analysis = selector.select(query)
    print(f"{query} → {budget} tokens ({analysis.query_complexity})")
```

### Pattern 3: Custom Keywords

Add domain-specific keywords to improve detection:

```python
from pystreampdf.query_analyzer import QueryAnalyzer

# Add custom keywords for your domain
QueryAnalyzer.add_keywords("rich", [
    "debugging", "optimization", "refactoring",
    "performance", "scalability"
])

# Now these queries detect as "rich" level
analysis = QueryAnalyzer.analyze("How to optimize database queries?")
# → Detected as "rich" (2000 tokens)
```

### Pattern 4: Conditional Force Override

```python
from pystreampdf.query_analyzer import AutoBudgetSelector

selector = AutoBudgetSelector(auto_detect=True, force_level=None)

def search_with_conditional_override(query, requires_deep_analysis=False):
    """Search with conditional override"""
    if requires_deep_analysis:
        selector.update_force_level("comprehensive")
    else:
        selector.update_force_level(None)  # Use auto-detection

    budget, analysis = selector.select(query)
    print(f"Budget selected: {budget} tokens")
    print(f"Rationale: {analysis.rationale}")
    return budget
```

## Programmatic Control

### Modify Keywords

```python
from pystreampdf.query_analyzer import QueryAnalyzer

# Add keywords
QueryAnalyzer.add_keywords("standard", [
    "tutorial", "guide", "walkthrough"
])

# Remove keywords
QueryAnalyzer.remove_keywords("rich", ["compare"])

# Replace all keywords
QueryAnalyzer.set_keywords("minimal", [
    "quick", "fast", "simple"
])
```

### Using AutoBudgetSelector

```python
from pystreampdf.query_analyzer import AutoBudgetSelector

# Create selector
selector = AutoBudgetSelector(
    auto_detect=True,
    force_level=None
)

# Enable/disable auto-detection
selector.enable_auto_detect(False)  # Disable, use fallback
selector.enable_auto_detect(True)   # Re-enable

# Force specific level
selector.update_force_level("rich")

# Clear force override
selector.update_force_level(None)
```

## Query Analysis Details

### QueryAnalysis Object

```python
@dataclass
class QueryAnalysis:
    detected_level: TokenBudgetLevel  # "minimal", "standard", "rich", "comprehensive"
    confidence: float                 # 0.0-1.0
    matched_keywords: List[str]       # Keywords that triggered detection
    query_complexity: str             # "simple", "moderate", "complex", "deep"
    rationale: str                    # Human-readable explanation
```

### Confidence Scores

Confidence indicates how certain the detection is:

- **>0.8** — High confidence (clear pattern match)
- **0.6-0.8** — Medium confidence (some keywords matched)
- **<0.6** — Low confidence (ambiguous query)

```python
from pystreampdf.query_analyzer import QueryAnalyzer

queries = [
    "What is X?",                  # High confidence → minimal
    "Tell me about X",             # Medium confidence → standard
    "X and Y",                     # Low confidence → standard (fallback)
]

for query in queries:
    analysis = QueryAnalyzer.analyze(query)
    if analysis.confidence > 0.8:
        confidence_text = "High"
    elif analysis.confidence > 0.6:
        confidence_text = "Medium"
    else:
        confidence_text = "Low"

    print(f"{query} → {analysis.detected_level.value} ({confidence_text})")
```

## Complete Example

```python
import pystreampdf
from pystreampdf.query_analyzer import QueryAnalyzer, AutoBudgetSelector
from pystreampdf.config import TokenBudgetConfig

# Initialize selector
selector = AutoBudgetSelector(auto_detect=True, force_level=None)

# Sample queries
queries = [
    "What is neural networks?",
    "Explain how CNNs work",
    "Compare supervised vs unsupervised learning",
    "Deep dive into transformer architectures",
]

# Setup
doc = pystreampdf.open("ML_Handbook.pdf")
index = doc.build_index("/tmp/ml_index.db")
navigator = doc.navigator_with_index(index)

# Process each query
for query in queries:
    # Auto-select budget
    budget, analysis = selector.select(query)

    # Retrieve
    context, flow = navigator.retrieve_with_flow(query, max_tokens=budget)

    # Display results
    print("\n" + "=" * 100)
    print(f"Query: {query}")
    print(f"Analysis: {analysis.query_complexity} ({analysis.confidence:.0%})")
    print(f"Budget: {budget} tokens ({TokenBudgetConfig.PRESETS[analysis.detected_level.value]})")
    print(f"Retrieved: {len(context.sections)} sections, {context.total_tokens} tokens")
    print("=" * 100)
```

## Advanced: Integration with Navigator

Create a convenience method on navigator:

```python
class EnhancedNavigator:
    def __init__(self, navigator, auto_budget=True):
        self.navigator = navigator
        self.auto_budget = auto_budget

    def retrieve_smart(self, query, force_level=None):
        """Retrieve with auto-selected budget"""
        from pystreampdf.query_analyzer import auto_select_budget

        budget, analysis = auto_select_budget(query, force_level=force_level)
        context, flow = self.navigator.retrieve_with_flow(query, max_tokens=budget)

        return context, flow, analysis

# Usage
nav = EnhancedNavigator(navigator)
context, flow, analysis = nav.retrieve_smart("Compare two approaches")
print(f"Confidence: {analysis.confidence:.0%}")
```

## Performance

Auto-detection has minimal overhead:

- **Analysis time**: <5ms for typical queries
- **Memory**: ~1KB per query
- **Caching**: Results can be cached for repeated queries

```python
from pystreampdf.query_analyzer import QueryAnalyzer

# Cache analysis results
cache = {}

def cached_analyze(query):
    if query not in cache:
        cache[query] = QueryAnalyzer.analyze(query)
    return cache[query]
```

## Customization

### Company-Specific Keywords

```python
from pystreampdf.query_analyzer import QueryAnalyzer

# Configure for your domain
if domain == "finance":
    QueryAnalyzer.set_keywords("rich", [
        "portfolio", "risk", "return", "dividend",
        "valuation", "earnings", "cash flow"
    ])
elif domain == "medicine":
    QueryAnalyzer.set_keywords("rich", [
        "diagnosis", "treatment", "prognosis",
        "pathology", "clinical", "symptoms"
    ])
```

## Troubleshooting

### Query Detected Incorrectly

```python
from pystreampdf.query_analyzer import QueryAnalyzer, AutoBudgetSelector

# Check what was detected
query = "Kubernetes configuration"
analysis = QueryAnalyzer.analyze(query)
print(f"Detected: {analysis.detected_level.value}")
print(f"Confidence: {analysis.confidence:.0%}")
print(f"Matched: {analysis.matched_keywords}")

# Override if needed
selector = AutoBudgetSelector(force_level="rich")
budget, _ = selector.select(query)
```

### Add More Specific Keywords

```python
from pystreampdf.query_analyzer import QueryAnalyzer

# Your queries are being detected as "standard" but need "rich"?
QueryAnalyzer.add_keywords("rich", [
    "implementation", "best practice",
    "architecture", "design pattern"
])

# Re-analyze
analysis = QueryAnalyzer.analyze("Best practices for implementation")
# Now detected as "rich"
```

## Summary

| Feature | Use Case |
|---------|----------|
| **Auto-detect** | Most queries, optimal for general use |
| **Force level** | Known complexity, explicit control needed |
| **Custom keywords** | Domain-specific terminology |
| **Confidence score** | Deciding when to override detection |
| **Programmatic control** | Batch processing, conditional logic |

Auto-budget selection makes PyStreamPDF smarter and reduces manual tuning!
