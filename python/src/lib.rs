use pyo3::prelude::*;
use streampdf_core::{
    document::PdfDocument,
    page::{BoundingBox, ContentRegion, PageMetadata},
    structure::{DocumentStructure, HeadingNode, TocEntry},
    index::{PdfIndex, PageResult},
    navigator::PdfNavigator,
    heading_extractor::HeadingSection,
    markdown::MarkdownOutput,
    context::{AgentContext, ContextSection},
    security::PdfPermissions,
    audit::{AuditLog, AuditEvent, AuditEventKind},
    forms::PdfFormField,
};
use std::sync::{Arc, Mutex};

#[pyclass]
struct PyPdfDocument {
    inner: PdfDocument,
}

#[pymethods]
impl PyPdfDocument {
    #[staticmethod]
    fn open(path: String) -> PyResult<Self> {
        let doc = PdfDocument::open(&path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyPdfDocument { inner: doc })
    }

    #[getter]
    fn page_count(&self) -> u32 {
        self.inner.page_count()
    }

    #[getter]
    fn metadata(&self) -> PyResult<PyObject> {
        let meta = self.inner.metadata();
        Python::with_gil(|py| {
            let dict = pyo3::types::PyDict::new(py);
            dict.set_item("title", meta.title)?;
            dict.set_item("author", meta.author)?;
            dict.set_item("creator", meta.creator)?;
            dict.set_item("producer", meta.producer)?;
            dict.set_item("created", meta.created)?;
            dict.set_item("modified", meta.modified)?;
            dict.set_item("page_count", meta.page_count)?;
            Ok(dict.into())
        })
    }

    fn page(&self, page_num: u32) -> PyResult<PyPageMetadata> {
        let page = self
            .inner
            .page(page_num)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(PyPageMetadata { inner: page })
    }

    #[getter]
    fn all_pages(&self) -> PyResult<Vec<PyPageMetadata>> {
        let pages = self
            .inner
            .all_pages()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(pages.into_iter().map(|p| PyPageMetadata { inner: p }).collect())
    }

    #[getter]
    fn structure(&self) -> PyResult<PyDocumentStructure> {
        let structure = self
            .inner
            .structure()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyDocumentStructure { inner: structure })
    }

    #[getter]
    fn path(&self) -> String {
        self.inner.path().to_string()
    }

    fn build_index(&self, path: String) -> PyResult<PyPdfIndex> {
        let index = PdfIndex::build(&self.inner, &path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyPdfIndex {
            inner: std::sync::Arc::new(std::sync::Mutex::new(index)),
        })
    }

    fn navigator(&self) -> PyResult<PyPdfNavigator> {
        let nav = PdfNavigator::new(&self.inner)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyPdfNavigator {
            inner: Arc::new(Mutex::new(nav)),
        })
    }

    fn navigator_with_index(&self, index: &PyPdfIndex) -> PyResult<PyPdfNavigator> {
        let shared = Arc::clone(&index.inner);
        let nav = PdfNavigator::with_shared_index(&self.inner, shared)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyPdfNavigator {
            inner: Arc::new(Mutex::new(nav)),
        })
    }

    #[staticmethod]
    fn open_with_password(path: String, password: String) -> PyResult<Self> {
        let doc = PdfDocument::open_with_password(&path, &password)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyPdfDocument { inner: doc })
    }

    #[staticmethod]
    fn is_encrypted(path: String) -> PyResult<bool> {
        PdfDocument::is_encrypted(&path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))
    }

    #[staticmethod]
    fn permissions(path: String) -> PyResult<PyPdfPermissions> {
        let perms = PdfDocument::permissions(&path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyPdfPermissions { inner: perms })
    }

    fn fingerprint(&self) -> String {
        self.inner.fingerprint()
    }

    fn form_fields(&self) -> Vec<PyPdfFormField> {
        self.inner
            .form_fields()
            .iter()
            .map(|f| PyPdfFormField { inner: f.clone() })
            .collect()
    }

    fn has_forms(&self) -> bool {
        self.inner.has_forms()
    }
}

#[pyclass]
struct PyPageMetadata {
    inner: PageMetadata,
}

#[pymethods]
impl PyPageMetadata {
    #[getter]
    fn page_number(&self) -> u32 {
        self.inner.page_number
    }

    #[getter]
    fn width(&self) -> f32 {
        self.inner.width
    }

    #[getter]
    fn height(&self) -> f32 {
        self.inner.height
    }

    #[getter]
    fn rotation(&self) -> u32 {
        self.inner.rotation
    }

    #[getter]
    fn label(&self) -> Option<String> {
        self.inner.label.clone()
    }

    #[getter]
    fn word_count(&self) -> u32 {
        self.inner.word_count
    }

    #[getter]
    fn text_preview(&self) -> String {
        self.inner.text_preview.clone()
    }

    #[getter]
    fn text(&self) -> String {
        self.inner.text.clone()
    }

    #[getter]
    fn regions(&self) -> Vec<PyContentRegion> {
        self.inner
            .regions
            .iter()
            .map(|r| PyContentRegion {
                inner: r.clone(),
            })
            .collect()
    }

    #[getter]
    fn is_likely_scanned(&self) -> bool {
        self.inner.is_likely_scanned
    }

    fn __repr__(&self) -> String {
        format!(
            "PageMetadata(page={}, size={}x{}, words={})",
            self.inner.page_number, self.inner.width, self.inner.height, self.inner.word_count
        )
    }
}

#[pyclass]
struct PyContentRegion {
    inner: ContentRegion,
}

#[pymethods]
impl PyContentRegion {
    #[getter]
    fn region_type(&self) -> String {
        format!("{:?}", self.inner.region_type).to_lowercase()
    }

    #[getter]
    fn bounds(&self) -> PyBoundingBox {
        PyBoundingBox {
            inner: self.inner.bounds,
        }
    }

    #[getter]
    fn text(&self) -> Option<String> {
        self.inner.text.clone()
    }

    #[getter]
    fn font_size(&self) -> Option<f32> {
        self.inner.font_size
    }
}

#[pyclass]
struct PyBoundingBox {
    inner: BoundingBox,
}

#[pymethods]
impl PyBoundingBox {
    #[getter]
    fn x(&self) -> f32 {
        self.inner.x
    }

    #[getter]
    fn y(&self) -> f32 {
        self.inner.y
    }

    #[getter]
    fn width(&self) -> f32 {
        self.inner.width
    }

    #[getter]
    fn height(&self) -> f32 {
        self.inner.height
    }
}

#[pyclass]
struct PyDocumentStructure {
    inner: DocumentStructure,
}

#[pymethods]
impl PyDocumentStructure {
    #[getter]
    fn toc(&self) -> Vec<PyTocEntry> {
        self.inner
            .toc
            .iter()
            .map(|t| PyTocEntry {
                inner: t.clone(),
            })
            .collect()
    }

    #[getter]
    fn headings(&self) -> Vec<PyHeadingNode> {
        self.inner
            .headings
            .iter()
            .map(|h| PyHeadingNode {
                inner: h.clone(),
            })
            .collect()
    }
}

#[pyclass]
struct PyTocEntry {
    inner: TocEntry,
}

#[pymethods]
impl PyTocEntry {
    #[getter]
    fn title(&self) -> String {
        self.inner.title.clone()
    }

    #[getter]
    fn page_number(&self) -> u32 {
        self.inner.page_number
    }

    #[getter]
    fn level(&self) -> u8 {
        self.inner.level
    }
}

#[pyclass]
struct PyHeadingNode {
    inner: HeadingNode,
}

#[pymethods]
impl PyHeadingNode {
    #[getter]
    fn level(&self) -> u8 {
        self.inner.level
    }

    #[getter]
    fn text(&self) -> String {
        self.inner.text.clone()
    }

    #[getter]
    fn page_number(&self) -> u32 {
        self.inner.page_number
    }

    #[getter]
    fn children(&self) -> Vec<PyHeadingNode> {
        self.inner
            .children
            .iter()
            .map(|c| PyHeadingNode {
                inner: c.clone(),
            })
            .collect()
    }
}

#[pyclass]
struct PyPageResult {
    inner: PageResult,
}

#[pymethods]
impl PyPageResult {
    #[getter]
    fn page_number(&self) -> u32 {
        self.inner.page_number
    }

    #[getter]
    fn score(&self) -> f32 {
        self.inner.score
    }

    #[getter]
    fn snippet(&self) -> String {
        self.inner.snippet.clone()
    }
}

#[pyclass]
struct PyPdfIndex {
    inner: std::sync::Arc<std::sync::Mutex<PdfIndex>>,
}

#[pymethods]
impl PyPdfIndex {
    #[staticmethod]
    fn load(path: String) -> PyResult<Self> {
        let index = PdfIndex::load(&path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyPdfIndex {
            inner: std::sync::Arc::new(std::sync::Mutex::new(index)),
        })
    }

    fn search(&self, query: String, top_k: usize) -> PyResult<Vec<PyPageResult>> {
        let index = self
            .inner
            .lock()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyIOError, _>("Lock poisoned"))?;
        let results = index
            .search(&query, top_k)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(results.into_iter().map(|r| PyPageResult { inner: r }).collect())
    }

    fn pages_with_heading(&self, heading: String) -> PyResult<Vec<PyPageResult>> {
        let index = self
            .inner
            .lock()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyIOError, _>("Lock poisoned"))?;
        let results = index
            .pages_with_heading(&heading)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(results
            .into_iter()
            .map(|r| PyPageResult { inner: r })
            .collect())
    }

    fn page_range(&self, start: u32, end: u32) -> PyResult<Vec<PyPageResult>> {
        let index = self
            .inner
            .lock()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyIOError, _>("Lock poisoned"))?;
        let results = index
            .page_range(start, end)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(results
            .into_iter()
            .map(|r| PyPageResult { inner: r })
            .collect())
    }
}

#[pyclass]
struct PyMarkdownOutput {
    inner: MarkdownOutput,
}

#[pymethods]
impl PyMarkdownOutput {
    #[getter]
    fn markdown(&self) -> String {
        self.inner.markdown.clone()
    }

    #[getter]
    fn estimated_tokens(&self) -> u32 {
        self.inner.estimated_tokens
    }

    #[getter]
    fn pages_included(&self) -> Vec<u32> {
        self.inner.pages_included.clone()
    }
}

#[pyclass]
struct PyContextSection {
    inner: ContextSection,
}

#[pymethods]
impl PyContextSection {
    #[getter]
    fn heading_path(&self) -> String {
        self.inner.heading_path.clone()
    }

    #[getter]
    fn page_numbers(&self) -> Vec<u32> {
        self.inner.page_numbers.clone()
    }

    #[getter]
    fn content(&self) -> String {
        self.inner.content.clone()
    }

    #[getter]
    fn relevance_score(&self) -> f32 {
        self.inner.relevance_score
    }
}

#[pyclass]
struct PyAgentContext {
    inner: AgentContext,
}

#[pymethods]
impl PyAgentContext {
    #[getter]
    fn query(&self) -> String {
        self.inner.query.clone()
    }

    #[getter]
    fn total_tokens(&self) -> u32 {
        self.inner.total_tokens
    }

    #[getter]
    fn sections(&self) -> Vec<PyContextSection> {
        self.inner
            .sections
            .iter()
            .map(|s| PyContextSection {
                inner: s.clone(),
            })
            .collect()
    }
}

#[pyclass]
struct PyHeadingSection {
    inner: HeadingSection,
}

#[pymethods]
impl PyHeadingSection {
    #[getter]
    fn heading(&self) -> PyHeadingNode {
        PyHeadingNode {
            inner: self.inner.heading.clone(),
        }
    }

    #[getter]
    fn start_page(&self) -> u32 {
        self.inner.start_page
    }

    #[getter]
    fn end_page(&self) -> u32 {
        self.inner.end_page
    }

    #[getter]
    fn total_words(&self) -> u32 {
        self.inner.total_words
    }
}

#[pyclass]
struct PyPdfNavigator {
    inner: Arc<Mutex<PdfNavigator>>,
}

#[pymethods]
impl PyPdfNavigator {
    fn chapters(&self) -> PyResult<Vec<PyHeadingSection>> {
        let nav = self
            .inner
            .lock()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyIOError, _>("Lock poisoned"))?;
        Ok(nav
            .chapters()
            .iter()
            .map(|s| PyHeadingSection {
                inner: s.clone(),
            })
            .collect())
    }

    fn retrieve(&self, query: String, max_tokens: u32) -> PyResult<PyAgentContext> {
        let nav = self
            .inner
            .lock()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyIOError, _>("Lock poisoned"))?;
        let ctx = nav
            .retrieve(&query, max_tokens)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyAgentContext { inner: ctx })
    }

    fn section_to_markdown(&self, section: &PyHeadingSection, max_tokens: u32) -> PyResult<PyMarkdownOutput> {
        let nav = self
            .inner
            .lock()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyIOError, _>("Lock poisoned"))?;
        let md = nav
            .section_to_markdown(&section.inner, max_tokens)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyMarkdownOutput { inner: md })
    }

    fn page_to_markdown(&self, page_num: u32) -> PyResult<PyMarkdownOutput> {
        let nav = self
            .inner
            .lock()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyIOError, _>("Lock poisoned"))?;
        let md = nav
            .page_to_markdown(page_num)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(PyMarkdownOutput { inner: md })
    }
}

#[pyclass]
struct PyPdfPermissions {
    inner: PdfPermissions,
}

#[pymethods]
impl PyPdfPermissions {
    #[getter]
    fn can_copy(&self) -> bool {
        self.inner.can_copy
    }

    #[getter]
    fn can_print(&self) -> bool {
        self.inner.can_print
    }

    #[getter]
    fn can_modify(&self) -> bool {
        self.inner.can_modify
    }

    #[getter]
    fn can_annotate(&self) -> bool {
        self.inner.can_annotate
    }
}

#[pyclass]
struct PyAuditLog {
    inner: AuditLog,
}

#[pymethods]
impl PyAuditLog {
    #[staticmethod]
    fn new(path: String) -> Self {
        PyAuditLog {
            inner: AuditLog::new(&path),
        }
    }

    fn record_open(&self, doc_path: String) -> PyResult<()> {
        let event = AuditEvent {
            timestamp: chrono::Utc::now().to_rfc3339(),
            doc_path,
            kind: AuditEventKind::DocumentOpened,
        };
        self.inner
            .record(event)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))
    }

    fn record_search(&self, doc_path: String, query: String, results_count: usize) -> PyResult<()> {
        let event = AuditEvent {
            timestamp: chrono::Utc::now().to_rfc3339(),
            doc_path,
            kind: AuditEventKind::SearchPerformed {
                query,
                results_count,
            },
        };
        self.inner
            .record(event)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))
    }

    fn events(&self) -> PyResult<Vec<PyObject>> {
        let events = self
            .inner
            .events()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

        Python::with_gil(|py| {
            let mut result = Vec::new();
            for event in events {
                let dict = pyo3::types::PyDict::new(py);
                dict.set_item("timestamp", &event.timestamp)?;
                dict.set_item("doc_path", &event.doc_path)?;
                match &event.kind {
                    AuditEventKind::DocumentOpened => {
                        dict.set_item("kind", "DocumentOpened")?;
                    }
                    AuditEventKind::DocumentIndexed => {
                        dict.set_item("kind", "DocumentIndexed")?;
                    }
                    AuditEventKind::SearchPerformed {
                        query,
                        results_count,
                    } => {
                        dict.set_item("kind", "SearchPerformed")?;
                        dict.set_item("query", query)?;
                        dict.set_item("results_count", results_count)?;
                    }
                    AuditEventKind::ContextRetrieved { query, tokens } => {
                        dict.set_item("kind", "ContextRetrieved")?;
                        dict.set_item("query", query)?;
                        dict.set_item("tokens", tokens)?;
                    }
                }
                result.push(dict.into());
            }
            Ok(result)
        })
    }
}

#[pyclass]
struct PyPdfFormField {
    inner: PdfFormField,
}

#[pymethods]
impl PyPdfFormField {
    #[getter]
    fn name(&self) -> String {
        self.inner.name.clone()
    }

    #[getter]
    fn field_type(&self) -> String {
        format!("{:?}", self.inner.field_type).to_lowercase()
    }

    #[getter]
    fn value(&self) -> Option<String> {
        self.inner.value.clone()
    }

    #[getter]
    fn page_number(&self) -> u32 {
        self.inner.page_number
    }
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPdfDocument>()?;
    m.add_class::<PyPageMetadata>()?;
    m.add_class::<PyContentRegion>()?;
    m.add_class::<PyBoundingBox>()?;
    m.add_class::<PyDocumentStructure>()?;
    m.add_class::<PyTocEntry>()?;
    m.add_class::<PyHeadingNode>()?;
    m.add_class::<PyPageResult>()?;
    m.add_class::<PyPdfIndex>()?;
    m.add_class::<PyMarkdownOutput>()?;
    m.add_class::<PyContextSection>()?;
    m.add_class::<PyAgentContext>()?;
    m.add_class::<PyHeadingSection>()?;
    m.add_class::<PyPdfNavigator>()?;
    m.add_class::<PyPdfPermissions>()?;
    m.add_class::<PyAuditLog>()?;
    m.add_class::<PyPdfFormField>()?;

    m.add_function(wrap_pyfunction!(open, m)?)?;
    m.add_function(wrap_pyfunction!(load_index, m)?)?;
    Ok(())
}

#[pyfunction]
fn open(path: String) -> PyResult<PyPdfDocument> {
    PyPdfDocument::open(path)
}

#[pyfunction]
fn load_index(path: String) -> PyResult<PyPdfIndex> {
    PyPdfIndex::load(path)
}
