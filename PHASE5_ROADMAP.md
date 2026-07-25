# PyStreamPDF Phase 5: Next-Generation Architecture Evolution

**Timeline:** 960-1200 hours | Q3 2026 - Q1 2027  
**Target Release:** v3.0.0 (Multi-provider intelligent document platform)  
**Status:** Planning & Design

---

## Executive Summary

Transform PyStreamPDF from a **single-provider PDF retrieval engine** into a **multi-provider intelligent document processing platform**. The shift is strategic: instead of competing with OCR vendors, we become the orchestration layer that leverages them while adding validation, intelligence, and RAG optimization that OCR vendors don't provide.

### The Strategic Insight

```
Before (v2.0):  PDF → pdfium-render → Text → Index → Retrieve
After (v3.0):   PDF → OCR Selection → Validation → Intelligence → Structure → Optimize → RAG
```

**Key Positioning:** PyStreamPDF is NOT an OCR engine. It's an intelligent document processing platform that happens to support multiple OCR backends.

---

## Current State (v2.0.0)

**What We Have:**
- ✅ PDF parsing via pdfium-render (Rust)
- ✅ Semantic intelligence (entities, relationships, knowledge graphs)
- ✅ Token-aware context assembly (core differentiator)
- ✅ Full-text search (SQLite FTS5)
- ✅ Security features (encryption, permissions, audit logging)
- ✅ 94 tests, production-ready
- ✅ PyO3 bindings, pip-installable

**What We Don't Have:**
- ❌ OCR provider abstraction
- ❌ OCR quality validation
- ❌ Technical content intelligence
- ❌ Document structure recovery as graph
- ❌ Pluggable provider system
- ❌ Intelligent OCR routing
- ❌ Multi-format output (JSON, YAML, graph)

---

## Phase 5 Breakdown

### Phase 5a: OCR Provider Framework (Weeks 1-4, ~160 hours)

**Goal:** Create pluggable OCR architecture that allows swapping OCR engines.

#### 5a.1: Abstract OCR Provider Interface (Week 1)

**Rust Module:** `core/src/ocr/provider.rs`

```rust
pub trait OcrProvider: Send + Sync {
    fn name(&self) -> &str;
    fn version(&self) -> &str;
    fn capabilities(&self) -> OcrCapabilities;
    fn extract(&self, image_data: &[u8]) -> Result<OcrResult>;
    fn extract_batch(&self, images: Vec<&[u8]>) -> Result<Vec<OcrResult>>;
    fn supports_language(&self, lang: &str) -> bool;
    fn supports_format(&self, format: ImageFormat) -> bool;
}

pub struct OcrResult {
    pub text: String,
    pub confidence: f32,
    pub regions: Vec<TextRegion>,
    pub metadata: OcrMetadata,
}

pub struct TextRegion {
    pub text: String,
    pub bbox: BoundingBox,
    pub confidence: f32,
    pub language: Option<String>,
}

pub struct OcrCapabilities {
    pub supports_handwriting: bool,
    pub supports_tables: bool,
    pub supports_formulas: bool,
    pub supported_languages: Vec<String>,
    pub max_image_size: (u32, u32),
}
```

**Deliverables:**
- [ ] Abstract trait definition
- [ ] Result types with rich metadata
- [ ] Capability descriptor
- [ ] Provider registration system

**Tests:** 8 unit tests

---

#### 5a.2: Tesseract Provider (Week 2)

**Rust Module:** `core/src/ocr/providers/tesseract.rs`

```rust
pub struct TesseractProvider {
    engine: Arc<Mutex<tesseract::Instance>>,
    config: TesseractConfig,
}

impl OcrProvider for TesseractProvider {
    fn extract(&self, image_data: &[u8]) -> Result<OcrResult> {
        // Use pytesseract or libtesseract FFI
        // Extract text + bounding boxes
        // Return rich OcrResult
    }
}
```

**Configuration:**
```python
from pystreampdf.ocr import TesseractProvider

provider = TesseractProvider(
    languages=["eng", "fra"],
    config="--psm 3",  # Page segmentation mode
    use_gpu=False
)
```

**Deliverables:**
- [ ] FFI binding to Tesseract (or pytesseract wrapper)
- [ ] Configuration support
- [ ] Language support
- [ ] Bounding box extraction
- [ ] Confidence scoring

**Tests:** 12 unit tests

---

#### 5a.3: PaddleOCR Provider (Week 2)

**Rust Module:** `core/src/ocr/providers/paddle.rs`

**Note:** PaddleOCR is Python-based. Two approaches:
1. **Bridge Pattern:** Call Python from Rust via PyO3 (simpler)
2. **Native Rust:** Use ONNX Runtime to load PaddleOCR models (faster)

**Recommended: Hybrid** - Python wrapper for v3.0, native ONNX for v3.1+

```python
# Python-side (pystreampdf/ocr/providers/paddle.py)
from paddleocr import PaddleOCR

class PaddleProvider:
    def __init__(self, languages=None, use_gpu=False):
        self.ocr = PaddleOCR(lang=languages, use_gpu=use_gpu)
    
    def extract(self, image_data: bytes) -> OcrResult:
        result = self.ocr.ocr(image_data)
        # Convert to OcrResult with confidence + regions
        return self._convert_result(result)
```

**Deliverables:**
- [ ] Python wrapper for PaddleOCR
- [ ] Configuration (language, GPU support)
- [ ] Result conversion to OcrResult format
- [ ] Batch processing

**Tests:** 12 unit tests

---

#### 5a.4: Provider Factory & Selection (Week 3)

**Rust Module:** `core/src/ocr/manager.rs`

```rust
pub struct OcrManager {
    providers: HashMap<String, Arc<dyn OcrProvider>>,
    default_provider: String,
}

impl OcrManager {
    pub fn register(&mut self, name: &str, provider: Arc<dyn OcrProvider>) {
        self.providers.insert(name.to_string(), provider);
    }
    
    pub fn select(&self, name: &str) -> Result<Arc<dyn OcrProvider>> {
        self.providers.get(name).cloned()
            .ok_or(OcrError::ProviderNotFound)
    }
    
    pub fn available_providers(&self) -> Vec<String> {
        self.providers.keys().cloned().collect()
    }
}
```

**Python API:**
```python
from pystreampdf.ocr import OcrManager

manager = OcrManager()
manager.register("tesseract", TesseractProvider())
manager.register("paddle", PaddleProvider())

# Manual selection
provider = manager.select("paddle")
result = provider.extract(image_data)

# Get available
print(manager.available_providers())  # ["tesseract", "paddle"]
```

**Deliverables:**
- [ ] Provider registry
- [ ] Provider factory
- [ ] Configuration file support (YAML/TOML)
- [ ] Environment variable overrides

**Tests:** 10 unit tests

---

#### 5a.5: Integration with PDF Parser (Week 4)

**Rust Module:** `core/src/pdf_parser.rs` (modifications)

```rust
pub struct PdfProcessor {
    pdf_parser: PdfiumParser,
    ocr_manager: Arc<OcrManager>,
    config: ProcessingConfig,
}

impl PdfProcessor {
    pub fn process_page(&self, page_index: usize) -> Result<ProcessedPage> {
        let page = self.pdf_parser.get_page(page_index)?;
        
        // Check if page is text-based or scanned
        if self.is_scanned(page) {
            let image = self.extract_image(page)?;
            let ocr_provider = self.select_ocr_provider(page)?;
            let ocr_result = ocr_provider.extract(&image)?;
            return self.build_processed_page_from_ocr(ocr_result);
        }
        
        // Text-based PDF
        self.build_processed_page_from_text(page)
    }
    
    fn is_scanned(&self, page: &PdfPage) -> bool {
        // Detect if page has no extractable text
        page.text_content().is_empty() && page.has_image()
    }
    
    fn select_ocr_provider(&self, page: &PdfPage) -> Result<Arc<dyn OcrProvider>> {
        // Use intelligent routing (Phase 5f) or default
        self.ocr_manager.select(&self.config.default_ocr)
    }
}
```

**Deliverables:**
- [ ] Scanned PDF detection
- [ ] Image extraction from PDF pages
- [ ] OCR invocation for scanned pages
- [ ] Hybrid processing (text + OCR)

**Tests:** 15 unit tests

**Total for Phase 5a:** ~40 tests, ~3500 LOC (Rust + Python)

---

### Phase 5b: OCR Validation Layer (Weeks 5-8, ~180 hours)

**Goal:** Quality gates for any OCR output, independent of provider.

#### 5b.1: Text Validation (Week 5)

**Python Module:** `pystreampdf/validation/text.py`

```python
class TextValidator:
    def validate(self, text: str, metadata: Dict) -> ValidationResult:
        issues = []
        
        # Detect truncation (incomplete sentences)
        if self._has_truncation(text):
            issues.append(ValidationIssue(
                type="truncation",
                severity="high",
                description="Text appears truncated at end",
                confidence=0.85
            ))
        
        # Detect repeated text
        if self._has_repetition(text):
            issues.append(ValidationIssue(
                type="repetition",
                severity="medium",
                description="Significant text repetition detected"
            ))
        
        # Detect corrupted characters
        corrupted = self._find_corrupted_chars(text)
        if corrupted:
            issues.append(ValidationIssue(
                type="corruption",
                severity="high",
                description=f"Found corrupted chars: {corrupted}"
            ))
        
        # Detect broken line sequences
        if self._has_broken_sequence(text):
            issues.append(ValidationIssue(
                type="line_sequence",
                severity="medium",
                description="Line reading order appears incorrect"
            ))
        
        return ValidationResult(
            status="valid" if not issues else "issues",
            confidence=1.0 - (len(issues) * 0.1),
            issues=issues
        )
```

**Detection Algorithms:**
- **Truncation:** Check for incomplete last sentence (no terminal punctuation)
- **Repetition:** Measure repeated n-grams (sliding window)
- **Corruption:** Detect mojibake, control characters, invalid UTF-8
- **Line Sequence:** Analyze line coordinate consistency

**Deliverables:**
- [ ] Truncation detector
- [ ] Repetition detector
- [ ] Character corruption detector
- [ ] Line sequence analyzer
- [ ] Confidence scoring

**Tests:** 18 unit tests

---

#### 5b.2: Table Validation (Week 6)

**Python Module:** `pystreampdf/validation/table.py`

```python
class TableValidator:
    def validate_table(self, table: Table) -> TableValidationResult:
        issues = []
        
        # Check for missing rows/columns
        expected_cols = self._infer_column_count(table)
        missing_cols = expected_cols - len(table.columns)
        if missing_cols > 0:
            issues.append(ValidationIssue(
                type="missing_columns",
                severity="high",
                description=f"Expected {expected_cols} cols, found {len(table.columns)}"
            ))
        
        # Check for broken cells
        for row_idx, row in enumerate(table.rows):
            if len(row) != len(table.columns):
                issues.append(ValidationIssue(
                    type="cell_count_mismatch",
                    severity="high",
                    row=row_idx,
                    description=f"Row {row_idx}: expected {len(table.columns)} cells, found {len(row)}"
                ))
        
        # Consistency check
        consistency = self._check_consistency(table)
        if consistency < 0.8:
            issues.append(ValidationIssue(
                type="inconsistent_structure",
                severity="medium",
                description=f"Table structure inconsistency: {consistency:.1%}"
            ))
        
        # Cell content plausibility
        for cell in table.all_cells():
            if not self._is_plausible_content(cell.value):
                issues.append(ValidationIssue(
                    type="implausible_content",
                    severity="low",
                    description=f"Cell value appears corrupted: {cell.value[:50]}"
                ))
        
        return TableValidationResult(
            status="valid" if len(issues) < 3 else "needs_review",
            confidence=max(0.5, 1.0 - (len(issues) * 0.15)),
            issues=issues,
            cell_accuracy=self._estimate_cell_accuracy(table)
        )
```

**Detection Algorithms:**
- **Missing rows/columns:** Statistical analysis of grid structure
- **Broken cells:** Validate cell count per row
- **Consistency:** Measure deviation from expected structure
- **Cell plausibility:** Validate data types, ranges, formats

**Deliverables:**
- [ ] Table structure validator
- [ ] Row/column consistency checker
- [ ] Cell validity checker
- [ ] Accuracy estimation

**Tests:** 16 unit tests

---

#### 5b.3: Layout Validation (Week 6)

**Python Module:** `pystreampdf/validation/layout.py`

```python
class LayoutValidator:
    def validate(self, document: Document) -> LayoutValidationResult:
        issues = []
        
        # Check heading hierarchy
        hierarchy_issues = self._validate_heading_hierarchy(document.headings)
        issues.extend(hierarchy_issues)
        
        # Check page transitions (orphaned sections)
        transition_issues = self._validate_page_transitions(document.pages)
        issues.extend(transition_issues)
        
        # Check figure-caption relationships
        caption_issues = self._validate_captions(document.figures)
        issues.extend(caption_issues)
        
        # Check document structure
        structure_issues = self._validate_structure(document)
        issues.extend(structure_issues)
        
        return LayoutValidationResult(
            status="valid" if not issues else "issues",
            confidence=self._calculate_confidence(issues),
            issues=issues,
            structure_score=self._score_structure(document)
        )
    
    def _validate_heading_hierarchy(self, headings: List[Heading]) -> List[ValidationIssue]:
        # H1 -> H2 -> H3 (no jumps like H1 -> H3)
        # All H1s at start
        issues = []
        
        levels = [h.level for h in headings]
        for i, level in enumerate(levels[:-1]):
            next_level = levels[i + 1]
            if next_level > level + 1:
                issues.append(ValidationIssue(
                    type="hierarchy_jump",
                    severity="medium",
                    description=f"Heading hierarchy jump: H{level} -> H{next_level}"
                ))
        
        return issues
```

**Detection Algorithms:**
- **Heading Hierarchy:** Validate H1 → H2 → H3 progression (no jumps)
- **Page Transitions:** Detect orphaned sections or missing transitions
- **Figure-Caption Matching:** Link figures to nearby captions
- **Structure Integrity:** Validate document outline

**Deliverables:**
- [ ] Heading hierarchy validator
- [ ] Page transition checker
- [ ] Figure-caption matcher
- [ ] Structure integrity checker

**Tests:** 14 unit tests

---

#### 5b.4: Confidence Scoring & Recommendations (Week 7-8)

**Python Module:** `pystreampdf/validation/scorer.py`

```python
class ConfidenceScorer:
    def score_page(self, page: ProcessedPage) -> PageConfidenceScore:
        text_score = self._score_text(page.text)  # 0-1
        table_score = self._score_tables(page.tables)  # 0-1
        layout_score = self._score_layout(page)  # 0-1
        
        # Weighted average
        overall = (
            text_score * 0.5 +
            table_score * 0.3 +
            layout_score * 0.2
        )
        
        return PageConfidenceScore(
            overall=overall,
            text=text_score,
            tables=table_score,
            layout=layout_score,
            grade=self._grade_confidence(overall)  # "A", "B", "C", "D", "F"
        )
    
    def recommendation(self, score: PageConfidenceScore) -> Recommendation:
        if score.overall < 0.7:
            return Recommendation(
                action="re_run",
                suggested_provider="unlimited_ocr",  # Based on issues
                reason="Low confidence detected in text extraction",
                confidence=0.85
            )
        
        if score.overall < 0.85:
            return Recommendation(
                action="review",
                reason="Page passed validation but has minor issues",
                issues_to_check=[...]
            )
        
        return Recommendation(
            action="accept",
            reason="Page passed validation with high confidence"
        )
```

**Deliverables:**
- [ ] Multi-dimensional confidence scoring
- [ ] Page confidence grading (A-F)
- [ ] Recommendation engine
- [ ] OCR re-run suggestion logic

**Tests:** 12 unit tests

**Total for Phase 5b:** ~60 tests, ~4000 LOC

---

### Phase 5c: Technical Content Intelligence (Weeks 9-14, ~240 hours)

**Goal:** Understand and correct technical content (code, config, logs).

#### 5c.1: YAML Intelligence (Week 9)

**Python Module:** `pystreampdf/intelligence/yaml_intelligence.py`

```python
class YAMLIntelligence:
    def analyze(self, text: str) -> YAMLAnalysis:
        # Parse YAML structure
        try:
            yaml_obj = yaml.safe_load(text)
        except yaml.YAMLError as e:
            return YAMLAnalysis(
                is_valid=False,
                error=str(e),
                suggestions=self._suggest_fixes(text, e)
            )
        
        # Validate structure
        issues = []
        
        # Check indentation consistency
        if not self._consistent_indentation(text):
            issues.append(Issue(
                type="indentation",
                severity="high",
                description="Inconsistent indentation detected"
            ))
        
        # Check for common OCR errors
        if "costrnap" in text:  # Typo example
            issues.append(Issue(
                type="likely_ocr_error",
                original="costrnap",
                corrected="costmap",
                confidence=0.95
            ))
        
        return YAMLAnalysis(
            is_valid=True if not issues else "conditional",
            issues=issues,
            corrected_text=self._correct_yaml(text),
            structure=self._extract_structure(yaml_obj)
        )
```

**Features:**
- **Syntax Validation:** Valid YAML structure
- **Indentation Check:** Consistent 2/4-space indentation
- **Key Validation:** Required keys, naming conventions
- **Type Checking:** Value types (strings, numbers, booleans, lists)
- **OCR Error Detection:** Common patterns (e.g., "costrnap" → "costmap")
- **Auto-Correction:** Fix common issues

**Deliverables:**
- [ ] YAML parser + validator
- [ ] Indentation analyzer
- [ ] OCR error detector
- [ ] Auto-corrector
- [ ] Structure extractor

**Tests:** 20 unit tests

---

#### 5c.2: JSON Intelligence (Week 9)

**Python Module:** `pystreampdf/intelligence/json_intelligence.py`

```python
class JSONIntelligence:
    def analyze(self, text: str) -> JSONAnalysis:
        # Try to parse
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            # Attempt recovery
            recovery = self._attempt_recovery(text, e)
            if recovery.success:
                return JSONAnalysis(
                    is_valid=True,
                    issues=[Issue(
                        type="syntax_error_fixed",
                        original_error=str(e),
                        fix_applied=recovery.fix
                    )],
                    corrected_text=recovery.corrected
                )
        
        # Validate structure
        issues = self._validate_structure(text, obj)
        
        return JSONAnalysis(
            is_valid=True,
            issues=issues,
            schema=self._infer_schema(obj),
            format=self._detect_format(obj)  # API response? Config? Data?
        )
    
    def _attempt_recovery(self, text: str, error):
        # Fix common OCR issues:
        # - Missing commas: } {\n → },\n{
        # - Missing quotes: key: value → "key": "value"
        # - Mismatched brackets: [[[]
        pass
```

**Features:**
- **Syntax Validation:** Valid JSON structure
- **Bracket Matching:** Detect missing/mismatched brackets
- **Comma Detection:** Identify missing commas between pairs
- **Quote Validation:** Proper string quoting
- **OCR Recovery:** Fix common OCR mistakes
- **Schema Inference:** Detect JSON structure (API response, config, etc.)

**Deliverables:**
- [ ] JSON parser + validator
- [ ] Bracket matcher
- [ ] Syntax error recovery
- [ ] Schema inferencer
- [ ] Format detector

**Tests:** 18 unit tests

---

#### 5c.3: Source Code Intelligence (Weeks 10-11)

**Python Module:** `pystreampdf/intelligence/code_intelligence.py`

```python
class CodeIntelligence:
    LANGUAGES = ["python", "rust", "cpp", "javascript", "shell"]
    
    def analyze(self, text: str) -> CodeAnalysis:
        # Detect language
        language = self._detect_language(text)
        
        if language == "python":
            return self._analyze_python(text)
        elif language == "rust":
            return self._analyze_rust(text)
        # ... etc
    
    def _detect_language(self, text: str) -> str:
        # Look for language-specific patterns
        if "#!/usr/bin/env python" in text:
            return "python"
        if "fn main()" in text:
            return "rust"
        # Use keyword frequency heuristics
        return self._detect_by_keywords(text)
    
    def _analyze_python(self, text: str) -> CodeAnalysis:
        issues = []
        
        # Check indentation
        if not self._consistent_indentation(text, indent_size=4):
            issues.append(Issue(
                type="indentation",
                severity="high",
                description="Python indentation inconsistent"
            ))
        
        # Syntax validation
        try:
            ast.parse(text)
        except SyntaxError as e:
            issues.append(Issue(
                type="syntax_error",
                severity="high",
                line=e.lineno,
                description=str(e)
            ))
        
        # Check for common OCR errors in identifiers
        for line_no, line in enumerate(text.split('\n')):
            suspicious = self._detect_suspicious_identifiers(line)
            if suspicious:
                issues.extend(suspicious)
        
        return CodeAnalysis(
            language="python",
            is_valid=len(issues) == 0,
            issues=issues,
            indentation=self._analyze_indentation(text),
            imports=self._extract_imports(text),
            functions=self._extract_functions(text)
        )
```

**Languages to Support:**
1. **Python:** Indentation, syntax, imports, decorators
2. **Rust:** Syntax, lifetimes, type annotations
3. **C++:** Headers, namespaces, templates
4. **JavaScript:** Syntax, async/await, imports
5. **Shell:** Syntax, pipes, redirects

**Features:**
- **Language Detection:** Identify from keywords and syntax
- **Syntax Validation:** Use language parser
- **Indentation Analysis:** Detect and fix indentation issues
- **Import/Declaration Extraction:** Find functions, classes, imports
- **OCR Error Detection:** Common typos (e.g., "O" ← "0")

**Deliverables:**
- [ ] Language detector
- [ ] Per-language analyzers (Python, Rust, C++, JS, Shell)
- [ ] Indentation validator
- [ ] Structure extractor (imports, functions, classes)
- [ ] Syntax error detector

**Tests:** 30 unit tests

---

#### 5c.4: ROS Intelligence (Week 12)

**Python Module:** `pystreampdf/intelligence/ros_intelligence.py`

```python
class ROSIntelligence:
    def analyze(self, text: str, doc_type: str = None) -> ROSAnalysis:
        # Detect ROS content type
        ros_type = self._detect_ros_type(text, doc_type)
        
        if ros_type == "launch_file":
            return self._analyze_launch_file(text)
        elif ros_type == "nav2_config":
            return self._analyze_nav2_config(text)
        elif ros_type == "topic_definition":
            return self._analyze_topic_definition(text)
        # ... etc
    
    def _detect_ros_type(self, text: str, hint: str = None) -> str:
        if hint and hint in ["launch", "config", "topic", "service"]:
            return hint
        
        # Heuristics
        if "<launch>" in text:
            return "launch_file"
        if "controller_server:" in text or "planner_server:" in text:
            return "nav2_config"
        if "std_msgs/String" in text:
            return "topic_definition"
        
        return "unknown"
    
    def _analyze_launch_file(self, text: str) -> ROSAnalysis:
        # Parse XML structure
        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            return ROSAnalysis(
                ros_type="launch_file",
                is_valid=False,
                error=str(e)
            )
        
        issues = []
        
        # Check required tags
        nodes = root.findall(".//node")
        if not nodes:
            issues.append(Issue(
                type="missing_nodes",
                severity="high",
                description="Launch file has no <node> elements"
            ))
        
        # Validate node attributes
        for node in nodes:
            if "pkg" not in node.attrib or "type" not in node.attrib:
                issues.append(Issue(
                    type="invalid_node",
                    severity="high",
                    description="Node missing 'pkg' or 'type' attribute"
                ))
        
        return ROSAnalysis(
            ros_type="launch_file",
            is_valid=len(issues) == 0,
            issues=issues,
            nodes=len(nodes),
            remappings=self._extract_remappings(root)
        )
```

**ROS Support:**
- **Launch Files:** XML structure, node definitions, parameters
- **Nav2 Configs:** YAML, controller/planner parameters
- **Topic Definitions:** Message format validation
- **Service Definitions:** Request/response structure
- **ROS Logs:** Parse timestamps, severity levels

**Deliverables:**
- [ ] ROS type detector
- [ ] Launch file validator
- [ ] Nav2 config validator
- [ ] Topic/service definition parser
- [ ] ROS log parser

**Tests:** 20 unit tests

---

#### 5c.5: Linux Log Intelligence (Week 13-14)

**Python Module:** `pystreampdf/intelligence/log_intelligence.py`

```python
class LogIntelligence:
    LOG_FORMATS = {
        "syslog": r"(\w+ \d+ \d+:\d+:\d+) (\S+) (\S+): (.+)",
        "journalctl": r"(\w+ \d+ \d+:\d+:\d+\.\d+) (\S+) (\S+)\[(\d+)\]: (.+)",
        "kernel": r"\[[ \d]+\.\d+\] (.+)",
        "docker": r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) (.+)",
        "kubernetes": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.+)",
    }
    
    def analyze(self, text: str, format_hint: str = None) -> LogAnalysis:
        log_format = self._detect_format(text, format_hint)
        
        entries = self._parse_entries(text, log_format)
        
        issues = []
        
        # Detect errors
        errors = [e for e in entries if e.level == "ERROR" or e.level == "CRITICAL"]
        if errors:
            issues.append(Issue(
                type="errors_found",
                severity="high",
                count=len(errors),
                examples=[e.message for e in errors[:3]]
            ))
        
        # Detect warnings
        warnings = [e for e in entries if e.level == "WARN"]
        if len(warnings) > len(entries) * 0.2:  # >20% warnings
            issues.append(Issue(
                type="excessive_warnings",
                severity="medium",
                count=len(warnings)
            ))
        
        # Detect crash patterns
        crash_patterns = self._detect_crashes(entries)
        if crash_patterns:
            issues.extend(crash_patterns)
        
        # Detect resource exhaustion
        resource_issues = self._detect_resource_issues(entries)
        if resource_issues:
            issues.extend(resource_issues)
        
        return LogAnalysis(
            format=log_format,
            entry_count=len(entries),
            issues=issues,
            timeline=self._extract_timeline(entries),
            top_errors=self._summarize_errors(errors)
        )
```

**Log Support:**
- **Syslog:** Standard system logs
- **Journalctl:** Systemd logs
- **Kernel Logs:** dmesg output
- **Docker Logs:** Container logs
- **Kubernetes Logs:** K8s pod logs

**Features:**
- **Format Detection:** Identify log type
- **Entry Parsing:** Extract timestamp, level, component, message
- **Error Detection:** Find ERROR/CRITICAL entries
- **Pattern Matching:** Detect crashes, resource exhaustion, stack traces
- **Timeline Analysis:** Extract time range, frequency

**Deliverables:**
- [ ] Format detector
- [ ] Entry parser (for each format)
- [ ] Error/warning detector
- [ ] Pattern matcher (crashes, resource issues)
- [ ] Timeline extractor

**Tests:** 18 unit tests

**Total for Phase 5c:** ~106 tests, ~6500 LOC

---

### Phase 5d: Structure Recovery Engine (Weeks 15-18, ~200 hours)

**Goal:** Reconstruct document structure as queryable graph.

#### 5d.1: Document Graph Builder (Weeks 15-16)

**Python Module:** `pystreampdf/structure/graph.py`

```python
class DocumentGraph:
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, List[GraphEdge]] = {}
    
    def add_section(self, id: str, title: str, level: int, page_range: Tuple[int, int]):
        node = GraphNode(
            id=id,
            type="section",
            title=title,
            level=level,
            page_range=page_range
        )
        self.nodes[id] = node
        self.edges[id] = []
    
    def add_figure(self, id: str, caption: str, page: int, bbox: Tuple):
        node = GraphNode(
            id=id,
            type="figure",
            caption=caption,
            page=page,
            bbox=bbox
        )
        self.nodes[id] = node
    
    def add_table(self, id: str, title: str, page: int):
        node = GraphNode(
            id=id,
            type="table",
            title=title,
            page=page
        )
        self.nodes[id] = node
    
    def add_reference(self, source_id: str, target_id: str, rel_type: str, confidence: float = 1.0):
        edge = GraphEdge(
            source=source_id,
            target=target_id,
            type=rel_type,  # "references", "caption_of", "appendix_of", etc.
            confidence=confidence
        )
        self.edges[source_id].append(edge)
    
    def to_json(self) -> Dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for edge_list in self.edges.values() for e in edge_list]
        }
```

**Deliverables:**
- [ ] Graph node types (section, figure, table, appendix, etc.)
- [ ] Edge types (references, caption_of, cites, appends, etc.)
- [ ] Graph construction from document
- [ ] Traversal methods (DFS, BFS)
- [ ] Serialization (JSON, GraphML)

**Tests:** 20 unit tests

---

#### 5d.2: Relationship Recovery (Weeks 16-17)

**Python Module:** `pystreampdf/structure/relationships.py`

```python
class RelationshipRecovery:
    def recover_figure_captions(self, doc: Document) -> List[Relationship]:
        relationships = []
        
        for fig in doc.figures:
            # Find nearest caption (within 200px)
            caption = self._find_nearest_caption(fig, doc.text_regions)
            if caption:
                relationships.append(Relationship(
                    source="figure",
                    target="text_region",
                    type="has_caption",
                    confidence=self._calc_confidence(fig, caption)
                ))
        
        return relationships
    
    def recover_citations(self, doc: Document) -> List[Relationship]:
        # Find references like "See Figure 3"
        relationships = []
        
        for page_no, page_text in enumerate(doc.pages):
            citations = self._find_citations(page_text)
            for citation in citations:
                target = self._find_referenced_item(citation)
                if target:
                    relationships.append(Relationship(
                        source=("page", page_no),
                        target=target,
                        type="cites",
                        text=citation
                    ))
        
        return relationships
    
    def recover_appendix_links(self, doc: Document) -> List[Relationship]:
        # Link main text to appendices
        relationships = []
        
        for heading in doc.headings:
            if heading.level == 1 and "appendix" in heading.text.lower():
                # Find references to this appendix
                appendix_id = heading.id
                refs = self._find_appendix_refs(heading.page_range)
                
                for ref in refs:
                    relationships.append(Relationship(
                        source=ref,
                        target=appendix_id,
                        type="references_appendix"
                    ))
        
        return relationships
```

**Deliverables:**
- [ ] Figure-caption matcher
- [ ] Citation extractor (See Figure X, Appendix Y)
- [ ] Footnote/endnote linker
- [ ] Cross-reference resolver
- [ ] Appendix linker

**Tests:** 18 unit tests

---

#### 5d.3: Format Exporters (Week 17-18)

**Python Module:** `pystreampdf/structure/exporters.py`

```python
class MarkdownExporter:
    def export(self, graph: DocumentGraph, doc: Document) -> str:
        sections = sorted(
            [n for n in graph.nodes.values() if n.type == "section"],
            key=lambda x: x.page_range[0]
        )
        
        output = []
        for section in sections:
            output.append(f"{'#' * section.level} {section.title}\n")
            # Add content from doc
            content = self._extract_section_content(doc, section)
            output.append(content)
            output.append("\n")
        
        return "\n".join(output)

class JSONStructureExporter:
    def export(self, graph: DocumentGraph) -> Dict:
        return graph.to_json()

class GraphMLExporter:
    def export(self, graph: DocumentGraph) -> str:
        # Export as GraphML for visualization in Gephi, etc.
        pass

class RAGOptimizedExporter:
    def export(self, graph: DocumentGraph, doc: Document) -> List[ChunkWithMetadata]:
        # Export as RAG-ready chunks with relationships
        chunks = []
        for section in graph.sections():
            chunk = ChunkWithMetadata(
                content=self._extract_content(doc, section),
                metadata={
                    "section": section.title,
                    "level": section.level,
                    "page_range": section.page_range,
                    "related": self._find_related(section, graph)
                }
            )
            chunks.append(chunk)
        return chunks
```

**Deliverables:**
- [ ] Markdown exporter (preserve hierarchy)
- [ ] JSON exporter (full structure)
- [ ] GraphML exporter (for visualization)
- [ ] RAG-optimized exporter (chunks + metadata)

**Tests:** 12 unit tests

**Total for Phase 5d:** ~50 tests, ~3500 LOC

---

### Phase 5e: Token Budget & RAG Optimization (Weeks 19-22, ~160 hours)

**Goal:** Enhance token optimization and RAG-specific outputs.

#### 5e.1: Adaptive Budget Allocation (Week 19)

**Python Module:** `pystreampdf/optimization/budget.py`

```python
class AdaptiveBudgetAllocator:
    def allocate(self, doc: Document, total_budget: int) -> BudgetAllocation:
        # Analyze document structure
        sections = doc.sections_by_type()
        
        allocation = BudgetAllocation()
        
        # Critical sections get more budget
        critical_sections = sections.get("critical", [])  # Findings, Results, etc.
        allocation.allocate_to("critical", total_budget * 0.5)
        
        # Supporting sections
        supporting = sections.get("supporting", [])  # Methods, background
        allocation.allocate_to("supporting", total_budget * 0.3)
        
        # Context sections
        context = sections.get("context", [])  # Introduction
        allocation.allocate_to("context", total_budget * 0.2)
        
        return allocation
    
    def _analyze_section_importance(self, section: Section) -> float:
        # Calculate importance based on:
        # - Information density
        # - Citation count (if available)
        # - Keyword relevance to query
        # - Position in document
        importance = 0.0
        
        importance += section.information_density * 0.4
        importance += (section.citation_count / max_citations) * 0.3
        importance += (1.0 - section.position_ratio) * 0.3  # Earlier = more important
        
        return importance
```

**Deliverables:**
- [ ] Budget allocation engine
- [ ] Section importance scorer
- [ ] Query-specific allocation
- [ ] Dynamic reallocation based on retrieval

**Tests:** 12 unit tests

---

#### 5e.2: Semantic Compression (Week 20)

**Python Module:** `pystreampdf/optimization/compression.py`

```python
class SemanticCompressor:
    def compress(self, text: str, target_ratio: float = 0.5) -> CompressedText:
        # Use abstractive summarization to replace repetitive sections
        # with concise summaries while preserving information value
        
        sentences = self._split_into_sentences(text)
        
        # Detect repetitive groups
        groups = self._cluster_similar_sentences(sentences)
        
        compressed_parts = []
        
        for group in groups:
            if len(group) == 1:
                # Keep unique sentences
                compressed_parts.append(group[0])
            else:
                # Summarize repetitive group
                summary = self._summarize_group(group)
                compressed_parts.append(f"[SUMMARY: {summary}]")
        
        compressed = " ".join(compressed_parts)
        
        return CompressedText(
            original=text,
            compressed=compressed,
            compression_ratio=len(compressed) / len(text),
            information_preserved=self._estimate_preservation(text, compressed)
        )
```

**Deliverables:**
- [ ] Sentence similarity scorer
- [ ] Repetition detector
- [ ] Abstractive summarizer
- [ ] Information preservation estimator

**Tests:** 10 unit tests

---

#### 5e.3: Information Density Scoring (Week 21)

**Python Module:** `pystreampdf/optimization/density.py`

```python
class InformationDensity:
    def score_chunk(self, chunk: str) -> DensityScore:
        # Calculate information value / token cost ratio
        
        tokens = self._count_tokens(chunk)
        
        # Factors that increase density:
        # - Specific numbers/metrics
        # - Named entities
        # - Unique concepts
        # - Technical terms
        density_score = 0.0
        
        # Number density
        numbers = self._extract_numbers(chunk)
        density_score += len(numbers) / tokens * 0.2
        
        # Entity density
        entities = self._extract_entities(chunk)
        density_score += len(entities) / tokens * 0.3
        
        # Unique term density
        unique_terms = self._extract_unique_terms(chunk)
        density_score += len(unique_terms) / tokens * 0.3
        
        # Keyword relevance (if query provided)
        if self.query:
            relevance = self._calc_relevance(chunk, self.query)
            density_score += relevance * 0.2
        
        return DensityScore(
            overall=min(1.0, density_score),
            breakdown={
                "numbers": len(numbers) / tokens,
                "entities": len(entities) / tokens,
                "unique_terms": len(unique_terms) / tokens
            }
        )
```

**Deliverables:**
- [ ] Density scorer
- [ ] Number/entity/concept extractor
- [ ] Relevance calculator
- [ ] Ranking based on density

**Tests:** 14 unit tests

---

#### 5e.4: Metadata-Rich RAG Output (Weeks 21-22)

**Python Module:** `pystreampdf/rag/output.py`

```python
class RAGOptimizedOutput:
    def generate(self, doc: Document, retrieval_context: RetrievalContext) -> RAGOutput:
        chunks = []
        
        for chunk_text in retrieval_context.chunks:
            metadata = {
                # Location
                "page": chunk_text.page_number,
                "section": chunk_text.section_title,
                "section_level": chunk_text.section_level,
                "page_range": chunk_text.page_range,
                
                # Confidence
                "ocr_confidence": chunk_text.ocr_confidence,
                "extraction_confidence": chunk_text.extraction_confidence,
                "validation_confidence": chunk_text.validation_confidence,
                
                # Content type
                "content_type": chunk_text.type,  # "text", "table", "figure"
                "has_table": chunk_text.has_table,
                "table_count": chunk_text.table_count,
                "figure_count": chunk_text.figure_count,
                
                # Intelligence
                "information_density": self._calc_density(chunk_text),
                "technical_content": self._detect_technical(chunk_text),
                
                # Relationships
                "related_sections": self._find_related(chunk_text, doc),
                "citations": self._find_citations_in_chunk(chunk_text),
                
                # Provider info
                "ocr_provider": chunk_text.ocr_provider,
                "processing_time_ms": chunk_text.processing_time_ms
            }
            
            chunk = ChunkWithMetadata(
                content=chunk_text.text,
                metadata=metadata,
                token_count=self._count_tokens(chunk_text.text),
                breadcrumb_path=self._build_breadcrumb(chunk_text, doc)
            )
            chunks.append(chunk)
        
        return RAGOutput(
            chunks=chunks,
            total_tokens=sum(c.token_count for c in chunks),
            coverage=self._estimate_coverage(chunks, doc),
            summary={
                "pages_covered": len(set(c.metadata["page"] for c in chunks)),
                "avg_confidence": sum(c.metadata["ocr_confidence"] for c in chunks) / len(chunks),
                "has_tables": any(c.metadata["has_table"] for c in chunks),
                "has_figures": any(c.metadata["figure_count"] > 0 for c in chunks)
            }
        )
```

**Deliverables:**
- [ ] Metadata-rich chunk format
- [ ] Confidence tracking (OCR + extraction + validation)
- [ ] Content type detection
- [ ] Relationship metadata
- [ ] Breadcrumb paths
- [ ] Summary statistics

**Tests:** 16 unit tests

**Total for Phase 5e:** ~52 tests, ~3500 LOC

---

### Phase 5f: Intelligent OCR Routing (Weeks 23-24, ~80 hours)

**Goal:** Auto-select OCR based on document analysis.

#### 5f.1: Document Classifier (Week 23)

**Python Module:** `pystreampdf/routing/classifier.py`

```python
class DocumentClassifier:
    CATEGORIES = [
        "scanned_book",
        "research_paper",
        "financial_report",
        "technical_manual",
        "robotics_documentation",
        "linux_documentation",
        "engineering_drawing",
        "form",
        "handwritten_notes"
    ]
    
    def classify(self, doc: Document) -> DocumentClass:
        features = self._extract_features(doc)
        
        # Simple rule-based classifier (can be upgraded to ML)
        scores = {}
        
        # Check for handwriting
        if self._has_handwriting(doc):
            scores["handwritten_notes"] = 0.9
        
        # Check for tables/forms
        if self._has_many_tables(doc):
            scores["form"] = 0.8
            scores["financial_report"] = 0.6
        
        # Check for robotics-specific content
        if self._has_robotics_keywords(doc):
            scores["robotics_documentation"] = 0.9
        
        # Check for Linux content
        if self._has_linux_keywords(doc):
            scores["linux_documentation"] = 0.9
        
        # Check for scanned text
        if self._is_low_quality_scan(doc):
            scores["scanned_book"] = 0.7
        
        # Default to technical manual for mixed content
        best_category = max(scores, key=scores.get) if scores else "technical_manual"
        
        return DocumentClass(
            category=best_category,
            confidence=scores.get(best_category, 0.5),
            scores=scores,
            features=features
        )
```

**Deliverables:**
- [ ] Document feature extractor
- [ ] Category classifier (rule-based)
- [ ] Confidence scoring
- [ ] Feature importance ranking

**Tests:** 16 unit tests

---

#### 5f.2: OCR Recommendation Engine (Week 24)

**Python Module:** `pystreampdf/routing/recommender.py`

```python
class OCRRecommender:
    RECOMMENDATIONS = {
        "scanned_book": [
            ("unlimited_ocr", 0.9, "Best for scanned text quality"),
            ("tesseract", 0.7, "Good fallback"),
            ("paddle", 0.6, "Fast alternative")
        ],
        "research_paper": [
            ("deepseek_ocr", 0.9, "Excellent with technical layout"),
            ("unlimited_ocr", 0.8, "High quality alternative"),
            ("paddle", 0.6, "Fast fallback")
        ],
        "financial_report": [
            ("mistral_ocr", 0.9, "Best for tables and financial data"),
            ("deepseek_ocr", 0.8, "Good table handling"),
            ("paddle", 0.6, "Fast alternative")
        ],
        "technical_manual": [
            ("deepseek_ocr", 0.9, "Excellent with diagrams"),
            ("unlimited_ocr", 0.8, "High quality"),
            ("paddle", 0.6, "Fast")
        ],
        "robotics_documentation": [
            ("deepseek_ocr", 0.95, "Best for technical diagrams"),
            ("unlimited_ocr", 0.85, "High quality"),
        ],
        "form": [
            ("mistral_ocr", 0.95, "Best for structured form data"),
            ("deepseek_ocr", 0.85, "Good alternative"),
        ],
        "handwritten_notes": [
            ("unlimited_ocr", 0.85, "Best handwriting support"),
            ("mistral_ocr", 0.75, "Good alternative"),
        ],
    }
    
    def recommend(self, doc_class: DocumentClass, available_providers: List[str]) -> List[Recommendation]:
        recommendations = self.RECOMMENDATIONS.get(
            doc_class.category,
            [("paddle", 0.5, "Default")]
        )
        
        result = []
        for provider, confidence, reason in recommendations:
            if provider in available_providers:
                result.append(Recommendation(
                    provider=provider,
                    confidence=confidence,
                    reason=reason,
                    estimated_quality=self._estimate_quality(doc_class, provider)
                ))
        
        return result
    
    def _estimate_quality(self, doc_class: DocumentClass, provider: str) -> QualityEstimate:
        # Estimate expected output quality for this provider on this document type
        return QualityEstimate(
            text_accuracy=self._calc_accuracy(doc_class, provider),
            table_accuracy=self._calc_table_accuracy(doc_class, provider),
            layout_preservation=self._calc_layout(doc_class, provider),
            processing_time_estimate_ms=self._calc_time(doc_class, provider)
        )
```

**Deliverables:**
- [ ] Recommendation engine
- [ ] Quality estimator
- [ ] Confidence scoring
- [ ] Processing time estimation

**Tests:** 12 unit tests

**Total for Phase 5f:** ~28 tests, ~2000 LOC

---

## Implementation Summary

| Phase | Focus | Weeks | Hours | Tests | LOC | Status |
|-------|-------|-------|-------|-------|-----|--------|
| 5a | OCR Providers | 1-4 | 160 | 40 | 3500 | Design |
| 5b | Validation | 5-8 | 180 | 60 | 4000 | Design |
| 5c | Technical Intelligence | 9-14 | 240 | 106 | 6500 | Design |
| 5d | Structure Recovery | 15-18 | 200 | 50 | 3500 | Design |
| 5e | Token Optimization | 19-22 | 160 | 52 | 3500 | Design |
| 5f | Intelligent Routing | 23-24 | 80 | 28 | 2000 | Design |
| **Total** | **v3.0** | **24** | **1020** | **336** | **23000** | **Design** |

---

## Dependencies & Infrastructure

### New External Dependencies

**Python:**
- `tesseract-ocr` (Tesseract OCR)
- `paddleocr` (PaddleOCR)
- `pyyaml` (YAML parsing)
- `networkx` (Graph operations)
- `pillow` (Image processing)
- `python-dotenv` (Environment config)

**Rust:**
- `tesseract` crate (Tesseract FFI)
- `image` crate (Image processing)
- `petgraph` (Graph algorithms)

### Infrastructure

- No breaking changes to existing APIs
- Backward compatible with v2.0
- Opt-in feature flags for OCR providers

---

## Success Metrics

### Code Quality
- [ ] 336+ tests passing (100% pass rate)
- [ ] >85% code coverage
- [ ] Zero security vulnerabilities
- [ ] All benchmarks passing

### Performance
- [ ] OCR provider selection: <100ms
- [ ] Validation layer: <500ms per page
- [ ] Document classification: <1s
- [ ] End-to-end processing: <5s for typical 50-page PDF

### Usability
- [ ] Clear documentation for each provider
- [ ] Example notebooks for common workflows
- [ ] CLI tools for standalone testing
- [ ] Easy provider configuration (env vars, config files)

### Quality
- [ ] OCR validation catches >90% of errors
- [ ] Technical intelligence >85% accuracy
- [ ] Structure recovery >95% correctness
- [ ] RAG optimization >50% token reduction

---

## Risk Mitigation

### Challenge: Complexity
- **Risk:** Feature scope becomes unmanageable
- **Mitigation:** Phase-based delivery, MVP for each provider

### Challenge: Performance
- **Risk:** Validation/intelligence layers add latency
- **Mitigation:** Async processing, caching, benchmarking

### Challenge: Accuracy
- **Risk:** OCR recommendation misses optimal provider
- **Mitigation:** Confidence scoring, manual override, feedback loop

### Challenge: Dependencies
- **Risk:** Too many external dependencies
- **Mitigation:** Optional providers, vendor-neutral architecture

---

## Next Steps

1. **Week 1:** Finalize architecture design, create issues
2. **Week 2:** Begin Phase 5a (OCR framework)
3. **Weekly:** Progress reviews, documentation updates
4. **Week 24:** v3.0 release candidate

---

## Success Criteria for v3.0

Phase 5 complete when:

- ✅ All 336 tests passing
- ✅ OCR providers (Tesseract + PaddleOCR) integrated
- ✅ Validation layer catching real-world errors
- ✅ Technical intelligence (YAML, JSON, code, ROS, logs) working
- ✅ Document structure recovered as queryable graph
- ✅ Token budget optimization enhanced
- ✅ Intelligent OCR routing recommending correct providers
- ✅ v3.0.0 released on PyPI
- ✅ Documentation complete (API docs + examples)
- ✅ No regressions in v2.0 functionality

---

**PyStreamPDF Phase 5 will transform the platform from a PDF retrieval engine into an intelligent, multi-provider document processing orchestrator.**
