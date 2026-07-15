use pyo3::prelude::*;
use streampdf_core::{
    document::PdfDocument,
    page::{BoundingBox, ContentRegion, PageMetadata},
    structure::{DocumentStructure, HeadingNode, TocEntry},
};

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
    fn regions(&self) -> Vec<PyContentRegion> {
        self.inner
            .regions
            .iter()
            .map(|r| PyContentRegion {
                inner: r.clone(),
            })
            .collect()
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

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPdfDocument>()?;
    m.add_class::<PyPageMetadata>()?;
    m.add_class::<PyContentRegion>()?;
    m.add_class::<PyBoundingBox>()?;
    m.add_class::<PyDocumentStructure>()?;
    m.add_class::<PyTocEntry>()?;
    m.add_class::<PyHeadingNode>()?;

    m.add_function(wrap_pyfunction!(open, m)?)?;
    Ok(())
}

#[pyfunction]
fn open(path: String) -> PyResult<PyPdfDocument> {
    PyPdfDocument::open(path)
}
