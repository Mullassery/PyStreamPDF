# StreamPDF Research Methodology: Intention + Depth Framework

**Core Principle:** Every research task starts with INTENTION and DEPTH before any data collection.

---

## The Framework

```
Research Task
├─ INTENTION: What question are we answering?
├─ DEPTH: How thorough? (Shallow/Medium/Deep)
├─ RETRIEVE: Gather raw data from sources
├─ ARRANGE: Structure into organized format
├─ ANALYZE: Extract insights and patterns
└─ DISCARD: Remove noise, keep signal
```

---

## STEP 1: INTENTION
**Define the specific question we're answering.**

### Purpose
Prevents scope creep. We're not gathering "everything about LlamaParse," we're answering a specific yes/no question.

### Examples

**GOOD Intentions:**
- "Does LlamaParse mention token efficiency or content filtering?" → Yes/No answer
- "Can we extract structural metadata without reading content?" → Yes/No + evidence
- "What % of PDFs have Table of Contents?" → Quantified answer
- "Do competitors use structural navigation?" → Yes/No + competitor list

**VAGUE Intentions (❌ avoid):**
- "Research LlamaParse" (What aspect? How deep?)
- "Understand PDF parsing" (Topic is too broad)
- "Find out about competitors" (Which competitors? What aspect?)

### Formula
**INTENTION = SPECIFIC QUESTION + EXPECTED ANSWER FORMAT**

```
❌ "Research competitors"
✅ "Does any competitor explicitly claim to optimize for token efficiency? (YES/NO)"

❌ "Look into table extraction"
✅ "What % of competitor GitHub issues mention table extraction problems? (Quantified %)"

❌ "Check PDF structure"
✅ "Do 80%+ of business PDFs have at least one structural element (TOC/headings/footers)? (YES/NO + % by type)"
```

---

## STEP 2: DEPTH
**Define how thorough the research needs to be.**

### Three Depth Levels

#### Shallow Depth (Website Only)
- **Sources:** Official websites, public docs, marketing claims
- **Time per task:** 1-2 hours
- **Confidence:** 60%
- **Risk:** Misses nuance, only gets marketing claims
- **Use when:** We need quick positioning, official claims
- **Example:** "What do competitors claim they do best?"

#### Medium Depth (Docs + Community)
- **Sources:** GitHub repos, documentation, issues, discussions, benchmarks
- **Time per task:** 6-12 hours
- **Confidence:** 80%
- **Risk:** Misses sentiment, limited user feedback
- **Use when:** Validating technical claims, understanding capabilities
- **Example:** "Do competitors use structural navigation?" ← **OUR TYPICAL DEPTH**

#### Deep Depth (Everything + Sentiment)
- **Sources:** GitHub + Reddit + Stack Overflow + HackerNews + user interviews
- **Time per task:** 20-40 hours
- **Confidence:** 90%+
- **Risk:** Time-intensive, diminishing returns
- **Use when:** Major pivot decision, final validation before $$$
- **Example:** "How many teams would pay for token-efficient PDF retrieval?"

### Choosing Depth

**Ask:** "If the answer is wrong, what's the cost?"

| Cost of Wrong Answer | Depth Needed | Example |
|---|---|---|
| Misses market opportunity | Medium | "Do competitors address token efficiency?" |
| Wrong architecture choice | Medium | "Can we extract metadata without content?" |
| Wasted development time | Medium | "What content filtering approach works best?" |
| Ruins product launch | Deep | "What's the market price for this?" |
| Minimal impact | Shallow | "What does LlamaParse claim?" |

---

## STEP 3: RETRIEVE
**Systematically gather raw data from identified sources.**

### Before You Retrieve
- [ ] Intention is clear (specific question, expected answer format)
- [ ] Depth is defined (Shallow/Medium/Deep)
- [ ] Sources are identified (websites, GitHub, communities, etc.)
- [ ] Data format decided (spreadsheet, tree, list, etc.)

### During Retrieval
- Document source for every piece of data
- Capture exact quotes for analysis (not paraphrases)
- Note date/time of collection (data can change)
- Record: what was found + what was NOT found (gaps matter)

### Retrieval Checklist

**For Competitor Website Research:**
- [ ] Home page: What do they claim as core value?
- [ ] Pricing page: How do they charge? Any efficiency pricing?
- [ ] Features list: Token efficiency mentioned?
- [ ] Documentation: Token counting, cost optimization, selective extraction?
- [ ] Roadmap (if public): Any efficiency work planned?
- [ ] Blog/content: Do they discuss token efficiency?

**For GitHub Research:**
- [ ] README: Design philosophy, what they optimize for
- [ ] Issues: Search for "token", "cost", "efficiency", "table", "image", "filter"
- [ ] Top issues: By comments and reactions (signal of pain points)
- [ ] Discussions: Design decisions, user questions
- [ ] Pull requests: What are developers building?
- [ ] Performance benchmarks (if included)

**For Community Research:**
- [ ] Reddit: r/MachineLearning, r/LangChain, r/PromptEngineering (if time permits)
- [ ] HackerNews: Comments on relevant posts
- [ ] Stack Overflow: Questions tagged with tool name
- [ ] Capture sentiment: Positive, neutral, negative feedback

---

## STEP 4: ARRANGE
**Structure raw data into organized format.**

### Goals
- Make patterns visible
- Enable comparison
- Show what's missing (gaps)
- Prepare for analysis

### Formats by Task Type

**Comparative Analysis (Spreadsheet):**
```
Competitor | Token Efficiency | Content Filtering | Structural Nav | User Complaints
────────────────────────────────────────────────────────────────────────────────────
LlamaParse | NO | NO | NO | Cost, tables
Docling | NO | NO | NO | Memory, speed
Marker | NO | NO | NO | Incomplete
```

**Design Decision Grid (Architecture Analysis):**
```
Competitor | Design Choice | Rationale | Consequence | Gap
────────────────────────────────────────────────────────
Docling | Process all content | High accuracy | High compute | No filtering option
LlamaParse | Cloud conversion | Easy integration | Per-page billing | No efficiency |
```

**Timeline/Prevalence Analysis (Table):**
```
Content Type | Prevalence | Difficulty | Token Impact
───────────────────────────────────────
Tables | 60% of PDFs | High | 2-5x cost
Images | 70% of PDFs | Medium | 3-10x cost
Signatures | 45% of PDFs | Low | 1-2x cost
Text | 100% | Low | 1x cost
```

**Issue Categorization (Taxonomy):**
```
LlamaParse Issues
├─ Performance (12 issues)
│  ├─ Speed (8 issues)
│  └─ Memory (4 issues)
├─ Content Handling (25 issues)
│  ├─ Tables (15 issues)
│  ├─ Images (8 issues)
│  └─ Signatures (2 issues)
├─ Cost (8 issues)
│  └─ All: "Too expensive for full documents"
└─ Features (5 issues)
   └─ "Add selective extraction option"
```

### Arrangement Discipline
- Use same column names across all comparisons (enables analysis)
- Show data source for each cell
- Preserve original quotes (for later analysis)
- Mark unknowns as "?" not with assumptions
- Highlight gaps (where expected data is missing)

---

## STEP 5: ANALYZE
**Extract patterns, insights, and implications.**

### Pattern Recognition

**Look for:**
- What do ALL competitors do? (consensus)
- What do NO competitors do? (gap)
- What do users COMPLAIN about? (pain points)
- What do they NOT mention? (blindness)
- What contradicts marketing? (reality check)

### Analysis Example

```
DATA OBSERVED:
├─ LlamaParse: No mention of token efficiency, per-page pricing, user complaints about cost
├─ Docling: No mention of efficiency, processes everything, memory issues in GitHub
├─ Marker: No mention of efficiency, extracts full markdown, no filtering options
└─ PyMuPDF4LLM: No mention of efficiency, basic extraction, no intelligence layer

PATTERN RECOGNITION:
- Consensus: All competitors assume "extract 100%, let users filter"
- Gap: Nobody assumes "extract only what's needed"
- Pain point: Users pay for full documents, only need small parts
- Blindness: Industry doesn't think in terms of tokens, only markup quality

IMPLICATION:
Market opportunity: "Read least, parse minimum" is unaddressed

STREAMPDF INSIGHT:
All competitors optimize for: Speed, Quality, Format
Nobody optimizes for: Token efficiency
We own: "Token-aware PDF retrieval"
```

### Questions to Ask During Analysis

**For each finding:**
- "Is this consistent across sources?" (corroborating evidence)
- "What does this NOT tell us?" (limitations)
- "Why might this be true?" (reasoning)
- "What's the consequence?" (impact)
- "Does this conflict with anything?" (contradictions)

### Synthesis
**Combine patterns into strategic insight:**

```
Finding 1: No competitor mentions token efficiency
Finding 2: Users complain about cost on GitHub
Finding 3: All treat content as equal value
Finding 4: Market assumes "extract everything"

↓

INSIGHT: Token efficiency is an unaddressed market gap.
OPPORTUNITY: First-mover advantage in "token-aware PDF retrieval."
STRATEGIE: Compete on efficiency, not quality.
TIMELINE: 12-month window before competitors catch on.
```

---

## STEP 6: DISCARD
**Remove noise and noise, keep only signal.**

### What to Remove

**During Analysis:**
- Anecdotes without supporting data ("I tried it once...")
- Unrelated complaints (UI performance, integration issues)
- Feature requests that don't indicate pain (nice-to-haves)
- Historical context that doesn't affect strategy
- Speculation (assumptions without evidence)

**Example Discard:**
```
GitHub Issue: "LlamaParse dashboard is slow"
Relevant? NO — doesn't indicate efficiency gap, UI problem only
Discard? YES

GitHub Issue: "LlamaParse extracts 60 pages of markdown for 20-page doc, can't filter"
Relevant? YES — indicates lack of content filtering, token waste
Discard? NO
```

### What to Keep

**Evidence of gaps:**
- "We extract everything because that's our design" (confirms no filtering)
- User complaint: "Charged for full conversion, only needed 3 pages" (pain point)
- Feature request: "Option to extract just X sections" (user wants what we offer)
- Absence of mention: "No documentation on token efficiency" (gap)

### Discard Checklist

Before including in final report:
- [ ] Is this directly answering the INTENTION question?
- [ ] Is this supported by DEPTH (multiple sources)?
- [ ] Does this identify a GAP or PAIN POINT?
- [ ] Is this DATA, not OPINION?
- [ ] Would removing this change the conclusion?

If any "NO", consider discarding.

---

## COMPLETE EXAMPLE: Market Research Task

### INTENTION
**Question:** "What % of business PDFs contain Table of Contents, chapter headings, or running headers/footers that enable structural navigation?"

**Expected answer format:** Quantified percentages by content type and document category

### DEPTH
**Medium Depth:** 
- Sample 100 PDFs from 5 categories (financial, technical, legal, business, academic)
- Analyze document structure (automated + manual check)
- Extract metadata: TOC presence, heading hierarchy, headers/footers, appendix markers
- Confidence: 85% (sample represents general business PDFs)

### RETRIEVE
**Sources:**
- [ ] Public PDF repositories: academic (arXiv, SSRN), business (SEC filings, quarterly reports)
- [ ] Organization PDFs: manuals, policies, handbooks (request access or use public examples)
- [ ] Tool outputs: Extract metadata using PyMuPDF, analyze structure

**Data format:** Spreadsheet

```
File | Category | Has TOC | Heading Hierarchy | Has Headers/Footers | Has Appendix | Pages
────────────────────────────────────────────────────────────────────────────────────────
apple-10k.pdf | Financial | YES | YES | YES | YES | 85
...
```

### ARRANGE
**Structure:**
```
Document Category | Sample Size | TOC Present | Headings | Headers/Footers | Appendix | Any Element
──────────────────────────────────────────────────────────────────────────────────────────────────
Financial reports | 20 | 75% | 85% | 60% | 70% | 90%
Technical manuals | 20 | 95% | 100% | 80% | 40% | 100%
Legal documents | 20 | 40% | 70% | 50% | 20% | 70%
Business reports | 20 | 60% | 80% | 70% | 30% | 85%
Academic papers | 20 | 5% | 90% | 10% | 5% | 92%
────────────────────────────────────────────────────────────────────────────────────────────────────
OVERALL | 100 | 55% | 85% | 54% | 33% | 87%
```

### ANALYZE
**Patterns:**
- 87% of business PDFs have at least one structural element
- Technical documents almost always have structure (100% with headings)
- Academic papers: headings only (5% TOC, no headers/footers typical)
- Financial docs: very structured (75%+ TOC)

**Insight:**
"87% of business PDFs are navigable without reading content. Structural navigation alone enables 70-90% token reduction on majority of documents."

### DISCARD
**What we exclude:**
- PDF size, color, scanned status (irrelevant to structure)
- File name or source (not strategic)
- Creation date or author (not relevant to our question)

**What we include:**
- Structure prevalence (answers the intention)
- Variation by document type (affects routing strategy)
- Implication for token reduction (business value)

### OUTPUT
**Final report section (2 pages):**
```markdown
## Structural Metadata Prevalence

87% of business PDFs contain navigable structure (TOC, headings, or headers/footers).

| Category | Prevalence | Implication |
| --- | --- | --- |
| Technical manuals | 100% | Can always use structural routing |
| Financial reports | 90% | Reliable structure for financial queries |
| Business reports | 85% | Mostly navigable |
| Legal documents | 70% | Variable structure, may need fallback |
| Academic papers | 92% | Navigable, but different hierarchy |

**Key Finding:** Structural metadata exists in 87% of documents. A routing engine based on 
structure could eliminate 70-90% of token waste on these documents without content filtering.

**Validation:** This supports StreamPDF's hypothesis that navigation precedes extraction.
```

---

## Checklist for Every Research Task

**Before starting:**
- [ ] INTENTION is specific (question + expected answer format)
- [ ] DEPTH is defined (Shallow/Medium/Deep with time budget)
- [ ] Sources are identified and time-budgeted
- [ ] Data format is decided (spreadsheet, table, tree, list)

**During research:**
- [ ] Documenting source for every data point
- [ ] Recording both FOUND and NOT FOUND
- [ ] Capturing exact quotes (not paraphrasing)
- [ ] Noting gaps (missing data matters)

**During synthesis:**
- [ ] Patterns identified (consensus, gaps, pain points)
- [ ] Analysis complete (why this matters)
- [ ] Discard filter applied (remove noise)
- [ ] Conclusion directly answers INTENTION

**Before reporting:**
- [ ] Evidence is quantified (not anecdotal)
- [ ] Sources are traceable (not vague)
- [ ] Gap identification is clear (what nobody does)
- [ ] Length is justified (only signal, no noise)

---

## Why This Matters for StreamPDF Research

Our research succeeds when:

✅ **Intention is clear:** "Nobody addresses token efficiency" (YES/NO)  
✅ **Depth is sufficient:** Medium (80% confidence in findings)  
✅ **Data is organized:** Competitor comparison table with gaps highlighted  
✅ **Analysis is rigorous:** Pattern recognition shows consistent gap  
✅ **Noise is discarded:** Report is concise (15-20 pages, only signal)  
✅ **Conclusion is actionable:** "Proceed to Week 2" or "Pivot strategy"  

**This discipline prevents:**
- ❌ Gathering everything (information overload)
- ❌ Missing the real insight (noise blinds us)
- ❌ Taking too long (unfocused research)
- ❌ Wrong conclusions (unvalidated analysis)
- ❌ Wasted effort (research that doesn't inform decisions)

**This enables:**
- ✅ Fast, focused research
- ✅ Data-driven strategy
- ✅ Clear market positioning
- ✅ Confident development roadmap
