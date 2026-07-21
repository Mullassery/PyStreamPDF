# PyStreamPDF: Caching and Token Budget Features

This document describes two complementary features that dramatically improve cost efficiency when processing PDFs repeatedly:

1. **PDF Caching** — Avoid re-processing identical PDFs
2. **Keyword-Driven Token Budgets** — Scale token allocation based on document type

Together, these features enable teams to:
- Process the same quarterly report 30 times per day with zero re-parsing
- Give financial reports 3× the token budget for legal/compliance content
- Automatically adjust budgets based on document metadata
- Track cache efficiency and token cost metrics

---

## Token Budget Configuration

Define rules that multiply the base token budget based on keywords in PDF metadata (filename, title, content preview).

### Quick Start

```python
from pystreampdf import TokenBudgetConfig, BudgetRule

# Define rules
rules = [
    BudgetRule("financial", 2.0, match_fields=["filename", "title"]),
    BudgetRule("summary", 0.5, match_fields=["filename"]),
]

# Create config
config = TokenBudgetConfig(base_budget=2000, rules=rules)

# Evaluate budget for a specific PDF
budget = config.evaluate(
    filename="financial_report_2024.pdf",
    title="Q4 Financial Summary",
    content_preview="This is our annual financial report..."
)
print(f"Evaluated budget: {budget} tokens")  # 4000 (2000 * 2.0)
```

### YAML Configuration

Store rules in a YAML file for easy management across teams:

```yaml
# budget_rules.yaml
base_budget: 2000

rules:
  - keyword: financial
    multiplier: 2.0
    match_fields: [filename, title]
    case_sensitive: false

  - keyword: summary
    multiplier: 0.5
    match_fields: [filename]

  - keyword: quarterly
    multiplier: 3.0
    match_fields: [content_preview]

  - keyword: legal
    multiplier: 2.5
    match_fields: [filename, title, content_preview]
```

Load the config:

```python
from pystreampdf import TokenBudgetConfig

config = TokenBudgetConfig.from_yaml("budget_rules.yaml")

# Use it
budget = config.evaluate("financial_quarterly_report.pdf")
print(f"Budget: {budget} tokens")  # 2000 * 2.0 * 3.0 = 12000
```

### Rule Matching

- **Keywords are case-insensitive by default** — set `case_sensitive: true` to match case exactly
- **Multiple rules stack multiplicatively** — if a file matches both "financial" (2.0x) and "quarterly" (3.0x), budget = base × 2.0 × 3.0
- **Empty/None fields are safe** — passing `None` for title or content_preview won't cause errors
- **Budgets are clamped** — results are bounded to [100, 32000] tokens to prevent runaway allocations

### API Reference

#### `TokenBudgetConfig`

```python
class TokenBudgetConfig:
    def __init__(self, base_budget: int = 2000, rules: Optional[List[BudgetRule]] = None)
    
    @classmethod
    def from_yaml(cls, path: str) -> "TokenBudgetConfig"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenBudgetConfig"
    
    def evaluate(
        self,
        filename: str,
        title: Optional[str] = None,
        content_preview: Optional[str] = None,
    ) -> int
        """Evaluate token budget. Returns clamped to [100, 32000]."""
    
    def to_yaml(self, path: str) -> None
    
    def to_dict(self) -> Dict[str, Any]
```

#### `BudgetRule`

```python
@dataclass
class BudgetRule:
    keyword: str
    multiplier: float
    match_fields: List[str] = field(default_factory=lambda: ["filename", "title"])
    case_sensitive: bool = False
```

---

## PDF Caching

Avoid re-processing identical PDFs by caching extracted chunks and metadata.

### How It Works

1. **Content-addressed** — PDFs are identified by SHA256 hash of their bytes, not filename
2. **Two-tier** — In-memory L1 cache (fast) + persistent disk L2 cache (survives restarts)
3. **Smart budgets** — Integrates with TokenBudgetConfig so budgets are re-evaluated on each access (config can change without invalidating cache)
4. **Automatic cleanup** — L1 evicts LRU entries when memory limit is exceeded

### Quick Start

```python
from pystreampdf import PDFCache, TokenBudgetConfig

# Create cache
budget_config = TokenBudgetConfig.from_yaml("budget_rules.yaml")
cache = PDFCache(
    memory_limit_mb=500,
    disk_cache_dir="/tmp/pystreampdf_cache",
    token_budget_config=budget_config,
)

# Define your extraction function
def process_pdf(pdf_path: str):
    # Extract chunks, title, preview, page_count
    # Return: (chunks, content_preview, title, page_count)
    ...
    return chunks, preview, title, pages

# Use cache
doc = cache.get_or_process("quarterly_report.pdf", process_pdf)
print(f"Budget for this doc: {doc.evaluated_budget} tokens")
print(f"Chunks cached: {len(doc.chunks)}")

# Second call: hits cache, no reprocessing
doc2 = cache.get_or_process("quarterly_report.pdf", process_pdf)
# process_pdf was NOT called this time

# Check cache performance
stats = cache.stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Disk used: {stats['disk_used_mb']:.1f} MB")
```

### API Reference

#### `PDFCache`

```python
class PDFCache:
    def __init__(
        self,
        memory_limit_mb: int = 500,
        disk_cache_dir: Optional[str] = None,  # ~/.cache/pystreampdf if None
        disk_limit_mb: int = 5000,
        token_budget_config: Optional[TokenBudgetConfig] = None,
        ttl_seconds: Optional[int] = None,  # None = never expire
    )
    
    def get_or_process(
        self,
        pdf_path: str,
        process_fn: Callable[[str], Tuple[List[ContentChunk], str, Optional[str], int]],
    ) -> CachedDocument
        """Get from cache or process if not cached."""
    
    def invalidate(self, pdf_path: str) -> bool
        """Remove cache entry. Returns True if found."""
    
    def clear(self) -> None
        """Clear all cache entries."""
    
    def stats(self) -> Dict[str, Any]
        """Return cache statistics."""
```

#### `CachedDocument`

```python
@dataclass
class CachedDocument:
    file_hash: str                         # SHA256 of PDF bytes
    evaluated_budget: int                  # Budget computed from token config
    filename: str                          # Extracted filename
    title: Optional[str]                   # Extracted title/metadata
    page_count: int                        # Number of pages
    content_preview: str                   # First ~500 chars of page 1
    chunks: List[ContentChunk]             # Extracted semantic chunks
    cached_at: float                       # Timestamp when cached
    last_accessed: float                   # Last access time
    access_count: int                      # Number of accesses
```

---

## Integration Examples

### Example 1: Basic Cache with Budget Config

```python
from pystreampdf import TokenBudgetConfig, PDFCache, SemanticChunker

# Setup
config = TokenBudgetConfig.from_yaml("budget_rules.yaml")
cache = PDFCache(token_budget_config=config)
chunker = SemanticChunker()

def extract_pdf(pdf_path):
    # Extract and chunk the PDF
    chunks = chunker.chunk_content(...)
    return chunks, preview, title, pages

# Use cache
doc = cache.get_or_process("report.pdf", extract_pdf)

print(f"Evaluated budget: {doc.evaluated_budget}")
print(f"Chunks: {len(doc.chunks)}")
```

### Example 2: Adaptive Budget Override in SemanticChunker

```python
from pystreampdf import SemanticChunker

chunker = SemanticChunker(target_tokens=500)

# For normal documents, use default budget
chunks1 = chunker.chunk_content(text, ElementType.TEXT, 1, 1)

# For important documents, override with larger budget
chunks2 = chunker.chunk_content(
    text,
    ElementType.TEXT,
    1,
    1,
    budget_override=2000,  # Use 2000 tokens instead of 500
)
```

### Example 3: Context Assembly with Budget Config

```python
from pystreampdf.semantic import ContextAssembler

assembler = ContextAssembler(token_budget_config=config)

# Provide document context so budget is auto-evaluated
context = assembler.assemble(
    query="What were Q4 results?",
    max_tokens=2000,  # Fallback if no context provided
    document_context={
        "filename": "Q4_Financial_Report.pdf",
        "title": "Quarterly Financial Summary",
        "content_preview": "This quarter revenue increased 15%...",
    }
)
# Budget automatically adjusted based on rules
```

### Example 4: Team-Wide Cache with Shared Rules

```python
from pathlib import Path
import json
from pystreampdf import TokenBudgetConfig, PDFCache

# Load shared config (e.g., from S3 or shared filesystem)
budget_config = TokenBudgetConfig.from_yaml("/shared/budget_rules.yaml")

# Create cache in shared location
cache = PDFCache(
    disk_cache_dir="/shared/pdf_cache",
    token_budget_config=budget_config,
)

# All team members use the same cache
doc = cache.get_or_process("report.pdf", extract_fn)
```

---

## Performance Tuning

### Memory vs. Disk Trade-offs

- **Small `memory_limit_mb`** (e.g., 100) — Aggressive L1 eviction; more disk I/O
- **Large `memory_limit_mb`** (e.g., 1000) — Keep more in memory; faster but uses more RAM

### Cache Invalidation Strategies

```python
# Option 1: Invalidate specific file
cache.invalidate("report.pdf")

# Option 2: Clear entire cache
cache.clear()

# Option 3: Time-based expiry (re-process after TTL)
cache = PDFCache(ttl_seconds=86400)  # 24 hours

# Option 4: Re-evaluate budget on every access (config can change)
# This happens automatically; budget_config is checked on every hit
```

---

## Cost Impact

For a team running the same 10 quarterly reports daily:

**Without caching:** 
- Parse 10 PDFs × 30 days = 300 parses/month
- Cost: ~300 × $0.01 per parse = $3/month

**With caching:**
- Parse 10 PDFs × 1 time = 10 parses/month
- Cost: ~10 × $0.01 per parse = $0.10/month
- **Savings: 97%**

**With smart budgets:**
- Allocate 2× tokens to financial reports (more context, better quality)
- Keep budgets low for summaries (fast, cheap)
- Total token cost reduced by 10-50% depending on document mix

---

## FAQ

**Q: How are two identical PDFs detected?**  
A: By SHA256 hash of file bytes. Renaming or moving the file won't invalidate the cache.

**Q: What if the PDF's content changes?**  
A: Hash changes → different cache entry → re-processed.

**Q: Can I use caching without token budgets?**  
A: Yes. `PDFCache` works standalone; `TokenBudgetConfig` is optional.

**Q: Where's the disk cache stored?**  
A: `~/.cache/pystreampdf` by default; override with `disk_cache_dir` parameter.

**Q: Will large PDFs blow up disk usage?**  
A: Monitor with `cache.stats()['disk_used_mb']`. Set `disk_limit_mb` to your quota.

**Q: How do budget multipliers stack?**  
A: Multiplicatively. If file matches both "financial" (2.0x) and "critical" (1.5x): base × 2.0 × 1.5.

---

## See Also

- `examples/token_budget_and_cache_example.py` — Complete runnable examples
- `tests/test_token_budget.py` — Unit tests for budget config
- `tests/test_cache.py` — Unit tests for caching layer
