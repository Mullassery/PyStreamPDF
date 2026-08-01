# PyStreamPDF v2.1.0: Product Vision

## Mission

**Intelligent PDF Processing with Smart Token Budget Management**

Optimize LLM context usage through dynamic token allocation and semantic document understanding. Part of the unified MCP 2.0 Platform (207 tools across 18 projects).

## Core Innovation: Token Budget Multipliers

PyStreamPDF introduces intelligent token allocation that adapts to document complexity:

- **Base allocation**: 1000 tokens (configurable via base_budget)
- **Dynamic scaling**: 500-1000 tokens via keyword-based multiplier rules
- **Hard constraints**: Prevents token overflow and under-allocation
- **Zero configuration**: Works out-of-the-box with sensible defaults

Example: Financial reports automatically receive higher allocation (1.2× multiplier) while summaries receive lower allocation (0.8× multiplier), all within the fixed 500-1000 range.

## Product Role in MCP 2.0 Platform

### Architecture Position
- **Layer:** Document Processing & Context Optimization
- **Port:** 8780 (MCP endpoint)
- **Tools:** 12 MCP tools + token budget management
- **Status:** Production Ready (v2.1.0)

### Core Capabilities
1. **Token Budget Management** (NEW)
   - Keyword-based multiplier rules
   - Automatic scaling within constraints
   - Multi-field matching (filename, title, content)
   - YAML and Python configuration

2. **Document Processing**
   - Multi-format extraction (text, tables, images, OCR)
   - Semantic chunking with token awareness
   - Layout preservation and heading hierarchy

3. **Intelligent Caching**
   - L1 memory + L2 disk dual-tier caching
   - Budget re-evaluation on cache hits
   - File hash-based invalidation

4. **Quality Assurance**
   - Text, table, and image validation
   - Confidence scoring
   - Corruption detection

### Integration Points
- **Depends on:** StatGuardian (quality metrics)
- **Used by:** PyInferenceManager (inference optimization), PyStreamMCP (context orchestration)

## Key Capabilities (v2.1.0)

- **Smart token budgeting** (500-1000 range with multiplier scaling)
- **Semantic chunking** with budget constraints
- **PDF extraction** (text, tables, images, OCR)
- **Dual-tier caching** with budget awareness
- **Multi-field matching** for keyword rules
- **Production validation** (quality checks with confidence)
- **Zero configuration** defaults

## MCP 2.0 Integration

### Port Assignment
- **Port:** 8780
- **Tools:** 12 discoverable via MCP protocol
- **Protocol:** Model Context Protocol 2.0
- **Status:** Live & production-ready

### AI Agent Integration
Accessible via Claude and other AI agents through the unified MCP 2.0 Platform.

## Roadmap

### Phase 1: Complete ✓ (v2.0.0)
- [x] Core features implemented
- [x] MCP 2.0 integration
- [x] 12 MCP tools live
- [x] Production-ready deployment

### Phase 2: In Progress (Q3 2026)
  [ ] 99%+ extraction accuracy
  [ ] Sub-100ms retrieval latency
  [ ] Multi-document reasoning
  [ ] Visual document understanding

### Phase 3: Planned (Q4 2026)
- [ ] Advanced features
- [ ] Enterprise deployment
- [ ] Performance optimization
- [ ] Platform federation

### Phase 4: Strategic (2027)
- [ ] AI-native enhancements
- [ ] Autonomous optimization
- [ ] Predictive capabilities
- [ ] Next-generation features

## Dependencies

### Inbound
['StatGuardian']

### Outbound
['PyInferenceManager', 'PyStreamMCP']

## Success Metrics

### Performance
- Target: Sub-100ms tool execution latency
- Current: Baseline established
- Goal: Optimize through Phase 2

### Adoption
- Target: Integrated with all dependent projects
- Current: 2 projects
- Goal: 100% integration

### Quality
- Test coverage: >80%
- MCP tool coverage: 100%
- Documentation: Complete

---

**Status:** Production Ready (v2.0.0)  
**Last Updated:** 2026-07-31  
**Next Review:** 2026-10-31 (Phase 2 completion)
