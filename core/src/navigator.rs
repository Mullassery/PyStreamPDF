use crate::context::{self, AgentContext};
use crate::document::PdfDocument;
use crate::error::Result;
use crate::heading_extractor::{extract_hierarchy, HeadingSection, HierarchicalHeadings};
use crate::index::PdfIndex;
use crate::markdown::{self, MarkdownOutput};
use crate::page::PageMetadata;
use std::sync::{Arc, Mutex};

/// Wrapper to hold references for the navigator, since owned types can't be cloned for Python.
pub struct PdfNavigatorData {
    pub doc_path: String,
    pub page_count: u32,
    pub hierarchy: HierarchicalHeadings,
}

pub struct PdfNavigator {
    data: PdfNavigatorData,
    index: Option<Arc<Mutex<PdfIndex>>>,
}

impl PdfNavigator {
    /// Create a navigator without an index (for browsing only).
    pub fn new(doc: &PdfDocument) -> Result<Self> {
        let pages = doc.all_pages()?;
        let hierarchy = extract_hierarchy(&doc.structure()?, doc.page_count(), Some(&pages));
        Ok(PdfNavigator {
            data: PdfNavigatorData {
                doc_path: doc.path().to_string(),
                page_count: doc.page_count(),
                hierarchy,
            },
            index: None,
        })
    }

    /// Create a navigator with a shared index (for search + retrieval).
    pub fn with_shared_index(doc: &PdfDocument, index: Arc<Mutex<PdfIndex>>) -> Result<Self> {
        let pages = doc.all_pages()?;
        let hierarchy = extract_hierarchy(&doc.structure()?, doc.page_count(), Some(&pages));
        Ok(PdfNavigator {
            data: PdfNavigatorData {
                doc_path: doc.path().to_string(),
                page_count: doc.page_count(),
                hierarchy,
            },
            index: Some(index),
        })
    }

    /// Get top-level chapters.
    pub fn chapters(&self) -> &[HeadingSection] {
        &self.data.hierarchy.chapters
    }

    /// Get sub-sections within a chapter (all chapters at once for now).
    pub fn sections_in(&self, _chapter_idx: usize) -> Vec<HeadingSection> {
        // Return all top-level sections; full hierarchy support for Phase 4
        self.data.hierarchy.chapters.clone()
    }

    /// Get pages for a section (requires reopening the document).
    pub fn pages_for(&self, section: &HeadingSection) -> Result<Vec<PageMetadata>> {
        let doc = PdfDocument::open(&self.data.doc_path)?;
        let mut pages = Vec::new();
        for page_num in section.start_page..section.end_page {
            if let Ok(page) = doc.page(page_num) {
                pages.push(page);
            }
        }
        Ok(pages)
    }

    /// Retrieve context for a query (requires index).
    pub fn retrieve(&self, query: &str, max_tokens: u32) -> Result<AgentContext> {
        let index_arc = self.index.as_ref().ok_or_else(|| {
            crate::error::Error::StructureError("No index available; call with_shared_index() first".to_string())
        })?;

        let index = index_arc
            .lock()
            .map_err(|_| crate::error::Error::StructureError("Index lock poisoned".to_string()))?;

        let results = index.search(query, 10)?;
        drop(index); // Release lock

        let doc = PdfDocument::open(&self.data.doc_path)?;
        let pages = doc.all_pages()?;

        Ok(context::assemble(
            query,
            &results,
            &self.data.hierarchy,
            &pages,
            max_tokens,
        ))
    }

    /// Generate markdown for a section.
    pub fn section_to_markdown(&self, section: &HeadingSection, max_tokens: u32) -> Result<MarkdownOutput> {
        let pages = self.pages_for(section)?;
        Ok(markdown::section_to_markdown(section, &pages, max_tokens))
    }

    /// Generate markdown for a single page.
    pub fn page_to_markdown(&self, page_num: u32) -> Result<MarkdownOutput> {
        let doc = PdfDocument::open(&self.data.doc_path)?;
        let page = doc.page(page_num)?;
        Ok(markdown::page_to_markdown(&page))
    }
}
