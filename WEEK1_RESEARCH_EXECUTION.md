# StreamPDF Week 1 Research Execution Plan
## Research Methodology: Retrieve → Arrange → Analyze → Discard

**Timeline:** July 15-22, 2026  
**Goal:** Complete competitive intelligence research validating that no competitor addresses token efficiency  
**Deliverable:** COMPETITIVE_INTELLIGENCE_REPORT_WEEK1.md with data-driven findings

---

## Research Framework: Intention & Depth

**Intention:** Does anyone in the market (competitors, communities, benchmarks) explicitly address token efficiency, selective processing, or structural navigation for PDFs?

**Depth of Information:** 
- **Shallow:** Website claims only (60% confidence)
- **Medium:** Docs + GitHub (80% confidence) ← **THIS IS OUR TARGET**
- **Deep:** Community feedback + Reddit + Stack Overflow (90% confidence, phase 2)

For Week 1: Focus on Medium depth (docs + GitHub issues).

---

# TASK 1: LlamaParse Research (12 hours)

## Phase 1: Retrieve

**Sources:**
- llamaparse.ai (website, pricing, features, docs)
- GitHub: llamaindex/llama_parse (issues, discussions, PRs)
- Reddit: r/MachineLearning, r/LangChain (search: "llamaparse")
- HackerNews (search: "llamaparse")

**Data to Collect (use spreadsheet):**
| Aspect | Finding | Source |
|--------|---------|--------|
| Cost model | Per-page, no efficiency options | Website pricing page |
| Token efficiency mentioned? | (Yes/No) | Docs + pricing |
| Content filtering available? | (Yes/No) | Feature list |
| Top user complaints | (List top 3) | GitHub issues |
| Performance claims | (What they claim) | Docs |
| Table extraction | (Works? Limitations?) | Issues + docs |

## Phase 2: Arrange

**Spreadsheet Structure:**
```
LlamaParse Competitive Analysis
─────────────────────────────────
Feature | Claimed | Mentioned | Hidden Gap?
─────────────────────────────────
Token efficiency | NO | NO | BLANK
Content filtering | NO | NO | BLANK
Table extraction | YES | "Works well" | User issues say otherwise
Selective processing | NO | NO | BLANK
Structural nav | NO | NO | BLANK
```

## Phase 3: Analyze

**Pattern Recognition:**
- What do they CLAIM? (quality, speed, format conversions)
- What do they NOT mention? (token efficiency, selective extraction, cost optimization)
- What do users COMPLAIN about? (cost spikes, table quality, unnecessary content)
- What's the GAP? (they optimize quality, nobody optimizes cost)

**Example Analysis:**
```
CLAIM: "LlamaParse produces clean, high-quality markdown"
NOT MENTIONED: How to reduce tokens if you don't need full document
USER COMPLAINT: "Costs $X per PDF, extract 20 pages, get 60 pages of markdown"
GAP: No way to say "just extract what I need" → must pay for full processing
STREAMPDF OPPORTUNITY: Token-aware extraction
```

## Phase 4: Discard

**What to REMOVE from final report:**
- UI complaints ("dashboard is slow")
- Integration issues ("doesn't work with LangChain v0.1")
- Feature requests unrelated to efficiency ("add webhook support")
- Anecdotes without data ("I tried it once and...") 

**What to KEEP:**
- Pricing structure (relevant: how do they charge?)
- Cost complaints (relevant: users unhappy with spend)
- Content type problems (relevant: what's hard to parse?)
- Token count data (relevant: how much do they produce?)

---

# TASK 2: Docling Research (12 hours)

## Phase 1: Retrieve

**Sources:**
- GitHub: DS4SD/docling (README, docs, architecture)
- GitHub issues (search: "token", "cost", "efficiency", "table")
- GitHub discussions (search: "large documents", "memory")
- Papers/benchmarks (if linked from repo)

**Data to Collect:**
```
Docling Research
────────────────────────
Aspect | Finding | Source | Notes
────────────────────────
Design goal | "High accuracy parsing" | README | Extracted from intro
Memory usage | Heavy, values? | Issues | Look for "memory", "RAM"
Table handling | Method | Docs | How do they approach tables?
Token output | Typical counts | Issues/benchmarks | Real-world measurements
Efficiency claims | (Any?) | Docs + discussions | Token optimization mentioned?
Performance targets | Speed metrics | Docs | What do they optimize for?
```

## Phase 2: Arrange

**Architecture Analysis Grid:**
```
Docling Design Decisions
─────────────────────────────────────────
Decision | Choice | Rationale | Trade-off
─────────────────────────────────────────
Content handling | Process everything | "High accuracy" | High compute, no filtering
Model selection | Heavy SOTA models | "Best accuracy" | Slow, expensive
Output format | Complete markdown | "Preserve structure" | Token bloat
Content filtering | None | Not mentioned | Users get irrelevant content
─────────────────────────────────────────
```

## Phase 3: Analyze

**Pattern Recognition:**
```
OBSERVATION: Docling uses SOTA models for every content type
REASONING: Want highest accuracy on everything
CONSEQUENCE: Heavy resource usage, processes everything
GAP: No "I only need X content" option
STREAMPDF: "Use right tool for each content type; skip what's not needed"
```

## Phase 4: Discard

**Remove:**
- Code quality issues ("this function has a bug")
- Development process ("PR review takes too long")
- Unrelated feature requests ("add JSON export")

**Keep:**
- Architecture choices and rationale
- Performance characteristics and constraints
- Accuracy vs speed trade-offs
- Content type coverage and limitations
- Any efficiency-related discussions

---

# TASK 3: Marker Research (8 hours)

## Phase 1: Retrieve

**Sources:**
- GitHub: VikParuchuri/marker (README, benchmarks)
- GitHub issues (top 20 by comments)
- Benchmarks: marker vs nougat vs surya

**Data to Collect:**
```
Marker Speed Analysis
──────────────────────
Metric | Value | Source
──────────────────────
Speed | 300 pages/hour | README
Quality | SOTA markdown | Benchmarks
Model size | GPU needed? | Docs
Content filtering | YES/NO | Feature list
Token efficiency | Mentioned? | Docs
```

## Phase 2: Arrange

**Speed vs Quality Trade-off:**
```
Tool | Speed | Quality | Method | Filters?
────────────────────────────────────────
Marker | Fast | High | Nougat | NO
PyMuPDF4LLM | Very Fast | Medium | PDF libs | NO
SOTA | Slow | Highest | Heavy models | NO
────────────────────────────────────────
Note: All assume "extract everything"
```

## Phase 3: Analyze

```
SPEED FOCUS: Marker optimizes for throughput, not relevance
OUTPUT: Markdown for entire document (default)
EFFICIENCY: No mention of token optimization
GAP: Can't say "only extract methodology section" → must process whole document
```

## Phase 4: Discard

**Remove:** Niche use-cases, academic paper details, model architecture discussions  
**Keep:** Performance benchmarks, what content types it handles, any efficiency discussions

---

# TASK 4: PyMuPDF4LLM Research (6 hours)

**Quick Assessment (Medium depth):**
- README: What's the core value prop?
- Benchmarks: Speed claim validation
- Issues: Content type problems?
- Conclusion: Lightweight, fast, no intelligence → not a threat, complementary

```
Summary: PyMuPDF4LLM is fast + basic, treats all content equally (no filtering)
```

---

# TASK 5: Quick Assessment of Others (8 hours)

**Per competitor: 1 hour each**

| Competitor | Depth | Focus | Finding |
|---|---|---|---|
| Unstructured.io | 1 hour | Breadth: how many formats? PDF quality? | Multi-format, not PDF-specific |
| Azure Document Intelligence | 1 hour | Pricing: per-page billing? | Cloud-only, expensive, no efficiency |
| AWS Textract | 1 hour | Form extraction focus? | Document forms, not book/manual focus |
| Reducto | 1 hour | Any efficiency focus? | Visual understanding, not structural |
| PDFMux | 1 hour | Positioning? | Limited GitHub activity |

---

# SYNTHESIS: Competitive Intelligence Report (6 hours)

## Phase 1: Retrieve (Raw Data Compilation)

**Create master spreadsheet:**
```
Competitor | Cost Model | Efficiency Mentioned | Content Filtering | User Complaints | Token Optimization | Structural Nav
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
LlamaParse | Per-page | NO | NO | Cost spikes, table quality | NO | NO
Docling | Free/OSS | NO | NO | Heavy, slow, memory | NO | NO
Marker | Free/OSS | NO | NO | Basic, no filtering | NO | NO
PyMuPDF4LLM | Free | NO | NO | Limited features | NO | NO
Azure DI | Per-page | NO | NO | Expensive | NO | NO
AWS Textract | Per-page | NO | NO | Form-focused | NO | NO
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
STREAMPDF | Token-aware | YES | YES | (Future) | YES | YES
```

## Phase 2: Arrange (Categorize Findings)

**Gap Analysis:**
```
What All Competitors Do:
├─ Extract/convert everything
├─ Optimize for quality or speed
├─ Charge per document/page
└─ No token awareness

What NONE Do:
├─ Ask "do we need this content?"
├─ Use structural navigation
├─ Optimize for token efficiency
├─ Skip irrelevant sections
└─ Provide "minimal extraction" mode
```

## Phase 3: Analyze (Find the Insight)

```
MARKET CONSENSUS: "Extract everything, parse everything, hope agent uses what matters"

STREAMPDF INSIGHT: "Ask what's needed, navigate by structure, extract minimum"

COMPETITIVE GAP: All competitors assume content extraction cost is free.
                 StreamPDF assumes content access cost is high (tokens).

MARKET OPPORTUNITY: $1B+ in PDF-processing tokens wasted annually on irrelevant content.
                    No competitor addresses this.
                    First mover can own "token efficiency" category.
```

## Phase 4: Discard & Report

**Final Report Structure:**
```markdown
# Competitive Intelligence Report - Week 1

## Executive Summary
- No competitor mentions token efficiency
- No competitor uses structural navigation
- Market opportunity: All process 100%, customers need <10%

## Competitor Analysis
[Table with gaps]

## The Market Gap
LlamaParse: "High quality markdown" (includes everything)
Docling: "Accurate parsing" (processes everything)
Marker: "Fast markdown" (still extracts everything)
PyMuPDF4LLM: "Lightweight extraction" (includes everything)

Shared assumption: Content extraction cost ≈ $0, access cost = ∞
StreamPDF hypothesis: Content access cost = ∞, extraction cost = free

## Validation Targets (Week 2)
- [ ] 85%+ of business PDFs have structural elements (TOC, headings, etc.)
- [ ] Structural navigation alone saves 70-90% tokens
- [ ] No competitor implements structure-based routing

## Next: Week 2 (Content-Type Analysis)
```

---

# Week 1 Execution Schedule

| Day | Task | Hours | Deliverable |
|-----|------|-------|-------------|
| Tue 7/15 | LlamaParse (Retrieve + Arrange) | 6 | Spreadsheet with website/docs/issue data |
| Wed 7/16 | LlamaParse (Analyze + Discard) | 6 | Pattern analysis, gap identification |
| Thu 7/17 | Docling (Retrieve + Arrange) | 6 | Architecture + issues spreadsheet |
| Fri 7/18 | Docling + Marker (Analyze + Discard) | 8 | Docling gaps + Marker quick-scan |
| Mon 7/21 | Others (PyMuPDF4LLM, Azure, AWS, etc.) | 8 | Quick assessments for each |
| Tue 7/22 | Synthesis (Create final report) | 6 | COMPETITIVE_INTELLIGENCE_REPORT_WEEK1.md |
| | | **44 hours** | **Week 1 complete** |

---

# Success Criteria for Week 1

✅ **Evidence:** Can we clearly show that competitors don't address token efficiency?  
✅ **Data:** Is each finding sourced and traceable (not opinions)?  
✅ **Gaps:** Have we identified what no competitor does?  
✅ **Report:** Is it concise (10-15 pages) with only signal?  

**If Week 1 findings:**
- No competitor mentions token efficiency: ✅ Proceed to Week 2
- Market gap confirmed: ✅ Proceed to Week 2
- Structural metadata strategy is unique: ✅ Proceed to Week 2

---

# Output for Week 1

**Commit to GitHub:**
```
COMPETITIVE_INTELLIGENCE_REPORT_WEEK1.md
├─ Executive Summary (1 page)
├─ Competitor Analysis (5 pages, with data tables)
├─ Market Gap Analysis (2 pages)
├─ Week 2 Validation Targets (1 page)
└─ Raw Research Data (spreadsheets, links, quotes)
```

**Size Target:** 15-20 pages (only signal, no noise)

**Key Message:** "All competitors extract everything. None optimize for token efficiency. We have a clear, unaddressed market gap."
