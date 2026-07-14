# StreamPDF: Caching & Pre-Processing Strategy

**Key Insight:** For frequently-used PDFs, pre-convert to markdown cache instead of on-demand extraction.

---

## The Decision Matrix: Extract On-Demand vs. Pre-Cache

```
PDF Usage Pattern | Frequency | Size | Strategy | Why
─────────────────────────────────────────────────────────────
One-time query | Low | Any | On-demand extraction | Cost minimal, cache waste
Reference manual | High | Large (100-300p) | Pre-cache markdown | Used repeatedly, amortize
API documentation | High | Medium (50-100p) | Pre-cache markdown | Accessed constantly, cache ROI
Contract upload | Single | Small (<30p) | On-demand | Low cost, not reused
Book (entire) | High | Very large (500+p) | Smart cache (by section) | Cache sections, not whole book
Repetitive SOP | High | Small (10-50p) | Pre-cache | High-frequency access
Quarterly reports | Medium | Large | On-demand + archive cache | Recent hot, archive cold
```

---

## When Pre-Caching Wins

### Calculation: Cache vs. Repeated Extraction

**Example: Technical Manual (200 pages)**

**Scenario 1: On-Demand Extraction (Repeated)**
```
First access:
  - Extract PDF → Markdown: 200p × 500 tokens/p = 100K tokens
  - User query: 2K tokens
  - Total: 102K tokens | Cost: $0.306 (Sonnet)

Second access (same day):
  - Extract PDF → Markdown AGAIN: 100K tokens
  - User query: 2K tokens
  - Total: 102K tokens | Cost: $0.306

Third access:
  - Extract PDF → Markdown AGAIN: 100K tokens
  - Total: 102K tokens | Cost: $0.306

Daily cost (3 queries): $0.918
Weekly cost: $6.43
Monthly cost: $27.54
```

**Scenario 2: Pre-Cache Markdown (Once)**
```
Setup (once):
  - Extract PDF → Markdown: 200p × 500 tokens/p = 100K tokens
  - Cache storage: ~50MB markdown file
  - Setup cost: $0.30

First query (uses cache):
  - Retrieve cached markdown: ~100K tokens (but cached via semantic caching)
  - With prompt caching (if 80% of content reused): 20K tokens × 0.1x = 2K tokens
  - User query: 2K tokens
  - Total: 4K tokens | Cost: $0.012

Second query (same day):
  - Cache hit on markdown: 4K tokens | Cost: $0.012

Third query:
  - Cache hit on markdown: 4K tokens | Cost: $0.012

Daily cost (3 queries): $0.036
Weekly cost: $0.252
Monthly cost: $1.08

Savings: 96% ($27.54 → $1.08)
Breakeven: After 2-3 queries
```

### Conditions for Pre-Caching ROI

✅ **Pre-cache if:**
- Accessed >2 times per day (breakeven is 2-3 accesses)
- Document size >30 pages (extraction cost justified by caching)
- Document is stable (doesn't change frequently)
- Access pattern is predictable (consistent queries)
- Examples: Manuals, documentation, reference materials, policies

❌ **Don't pre-cache if:**
- Accessed once and archived (single use)
- Document changes frequently (cache invalidation overhead)
- Document is very small (<10 pages, extraction cost low)
- Access pattern is unpredictable

---

## Caching Architecture

### Layer 1: Markdown Cache (File Storage)
```
PDF uploaded
├─ Detect usage pattern (first access)
└─ If high-frequency expected
   ├─ Extract PDF → Markdown
   ├─ Store in cache: /cache/pdf_digest.md
   └─ Index for retrieval
```

### Layer 2: Semantic Caching (Token Reduction)
```
Cached markdown in context
├─ Prompt caching: Prefix caching on stable markdown
│  └─ First query: Load 100K tokens
│  └─ Subsequent: Use cached prefix (0.1x cost)
│  └─ Savings: ~90% on repeated context
└─ Semantic caching: Hash similar queries to cached responses
   └─ "Tell me about authentication" → Cache hit if asked again
   └─ Savings: Eliminate LLM call entirely
```

### Layer 3: Section-Level Caching (for huge documents)
```
Large document (1000+ pages)
├─ Don't cache entire document
├─ Instead: Cache by section
│  ├─ Chapter 1: Cached separately
│  ├─ Chapter 2: Cached separately
│  └─ User query → identify relevant chapters → load only those
└─ Result: 95% token reduction (skip irrelevant chapters)
```

---

## Decision Tree: Extract Now or Cache

```
New PDF uploaded
│
├─ Q1: Will this be accessed again? 
│  │
│  ├─ NO → On-demand extraction (single use)
│  └─ YES → Q2
│
├─ Q2: How many times per day expected?
│  │
│  ├─ <2 times → On-demand (low ROI on caching)
│  └─ ≥2 times → Q3
│
├─ Q3: Document size?
│  │
│  ├─ <30 pages → On-demand (small extraction cost)
│  └─ ≥30 pages → Q4
│
├─ Q4: Does document change?
│  │
│  ├─ Frequently → On-demand (cache invalidation overhead)
│  ├─ Rarely/Never → Q5
│
├─ Q5: Document type?
│  │
│  ├─ Manual/Reference/Policy → PRE-CACHE MARKDOWN
│  ├─ Contract/Submission → On-demand
│  ├─ Report/Filing → Archive cache (keep recent, purge old)
│  └─ Book → Section-level cache
```

---

## Implementation Strategy

### v1.0 (MVP): On-Demand + Simple Pre-Cache

**Supported caching scenarios:**
- User manually marks PDF as "reference" → auto-pre-cache markdown
- Detect high-frequency PDFs (accessed >2 times/week) → offer pre-cache
- Cache storage: Simple directory structure
- Cache invalidation: Manual refresh or auto-purge after 30 days

**Example flow:**
```
1. User uploads technical_manual.pdf
2. System asks: "This looks like a reference document. Pre-cache markdown for faster access?"
3. User approves → Extract and cache
4. Queries 1-5: All use cached markdown (96% savings)
5. PDF unchanged for 30 days → Cache auto-refreshes on first access
```

### v1.1: Smart Detection + Archive Caching

**Features:**
- Auto-detect usage pattern (after 2-3 accesses)
- Offer pre-cache for high-frequency PDFs
- Archive cache for reports: Keep recent (30 days), compress older
- Track cache hit rate per PDF

### v2.0: Section-Level + Semantic Caching

**Features:**
- Section-level caching for documents >100 pages
- Semantic caching on frequently-asked questions
- Prompt caching integration (Anthropic API)
- Cache warming (pre-load for predictable queries)

---

## Cost Model Impact

### Current (No Caching)
```
100 users × 5 PDFs each (500 PDFs)
- 50% accessed once: $0.30/PDF extraction = $75
- 50% accessed 5× average: $0.30/PDF × 5 = $750

Monthly extraction cost: $825 just for initial parsing
```

### With Pre-Caching Strategy
```
Same 500 PDFs
- 50% one-time: $0.30/PDF extraction = $75
- 50% frequently-used (5× average):
  - Initial extraction: $0.30/PDF = $75
  - Subsequent queries: Semantic caching (90% reduction)
  - 4 queries × $0.030 (cached) = $0.12/PDF = $60

Monthly extraction cost: $210 (75% savings)
```

---

## Cache Metadata Strategy

**Store per-PDF:**
```json
{
  "file_id": "pdf_abc123",
  "filename": "technical_manual.pdf",
  "cached_at": "2026-07-15T10:00:00Z",
  "cache_version": 1,
  "usage": {
    "access_count": 12,
    "last_access": "2026-07-15T14:30:00Z",
    "access_frequency": "high",
    "queries": ["authentication", "configuration", "troubleshooting"]
  },
  "cache_strategy": "full_markdown",
  "cache_status": "active",
  "refresh_policy": "auto_30day",
  "cache_size_bytes": 50000,
  "markdown_tokens": 100000,
  "compression": "gzip",
  "semantic_cache_hits": 8,
  "extraction_cost_saved": 0.36
}
```

---

## Edge Cases

### Large Documents (1000+ pages)
**Strategy:** Section-level caching
```
Book.pdf (1000 pages, 500K tokens)
├─ Don't cache entire document
├─ Cache by section: Chapters 1-5, 6-10, etc.
├─ User query identifies relevant sections
└─ Load only needed sections (5-10% of document)
```

### Frequently-Changing Documents
**Strategy:** Time-based cache invalidation
```
Daily report (updated every 24h)
├─ Cache markdown
├─ Auto-invalidate at 24h mark
├─ Re-extract on first query after invalidation
└─ Result: 1 extraction per day (if accessed daily)
```

### Multi-User Access
**Strategy:** Shared cache with access controls
```
Shared resource PDF (policy manual)
├─ Cache once, share across team
├─ All users benefit from pre-cached markdown
├─ Reduces redundant extraction 100×
└─ Result: Extract once, serve 100 users
```

### Concurrent Access During Cache Extraction
**Strategy:** Queue-based extraction
```
Multiple users upload same PDF simultaneously
├─ First user triggers extraction
├─ Other users wait for cache completion
├─ All use same cached markdown
└─ Prevents duplicate extraction
```

---

## Monitoring & Optimization

### Metrics to Track
- Cache hit rate per PDF (% of queries using cached content)
- Cache size vs. savings (is cache justified?)
- Extraction cost saved (total cost reduction)
- Cache invalidation frequency (how often refreshed?)
- Multi-user cache reuse (how many users share cache?)

### Optimization Rules
```
If cache_hit_rate > 80% and access_frequency = "high":
  ✅ Cache is working, keep it

If cache_hit_rate < 20%:
  ⚠️ Cache not justified, consider invalidating

If cache_size > 100MB and rarely_used:
  ✅ Compress or delete

If pdf_changes frequently:
  ✅ Switch to shorter invalidation window (12h vs 30d)
```

---

## Integration with Research Phase

**Week 2 Content-Type Analysis should measure:**
- [ ] For each PDF category (manual, report, contract, etc.): access frequency pattern
- [ ] How many PDFs are used >2 times? (cache ROI trigger)
- [ ] Average document size by category (extraction cost)
- [ ] Document change frequency (cache invalidation cost)
- [ ] Multi-user sharing patterns (cache reuse potential)

**Result:** Data-driven caching strategy for Phase 1 implementation

---

## Summary: When to Pre-Cache

**YES, pre-cache if:**
- ✅ Document accessed >2 times daily (ROI within 1-2 queries)
- ✅ Document size >30 pages (extraction cost justified)
- ✅ Document is stable/rarely-changing (cache validity)
- ✅ Multiple users access same document (shared cache)

**NO, don't cache if:**
- ❌ Accessed once and archived
- ❌ Document <10 pages (extraction cost negligible)
- ❌ Document changes hourly (cache invalidation overhead)
- ❌ Private/sensitive document not shared

**For everything else:** On-demand extraction with semantic caching for similar queries.
