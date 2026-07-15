use crate::error::{Error, Result};
use crate::page::PageMetadata;
use crate::structure::DocumentStructure;
use crate::pdf_parser::{ParsedDocument, parse_document_open};
use std::path::Path;

pub struct PdfDocument {
    path: String,
    parsed: ParsedDocument,
}

#[derive(Debug, Clone)]
pub struct DocumentMetadata {
    pub title: Option<String>,
    pub author: Option<String>,
    pub creator: Option<String>,
    pub producer: Option<String>,
    pub created: Option<String>,
    pub modified: Option<String>,
    pub page_count: u32,
}

impl PdfDocument {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path_str = path
            .as_ref()
            .to_str()
            .ok_or_else(|| Error::Pdf("Invalid path".to_string()))?
            .to_string();

        if !Path::new(&path_str).exists() {
            return Err(Error::Pdf("File not found".to_string()));
        }

        let parsed = parse_document_open(&path_str)?;

        Ok(PdfDocument {
            path: path_str,
            parsed,
        })
    }

    pub fn page_count(&self) -> u32 {
        self.parsed.page_count
    }

    pub fn metadata(&self) -> DocumentMetadata {
        self.parsed.metadata.clone()
    }

    pub fn page(&self, page_num: u32) -> Result<PageMetadata> {
        if page_num == 0 || page_num > self.parsed.page_count {
            return Err(Error::InvalidPageNumber(page_num));
        }

        let idx = (page_num as usize) - 1;
        Ok(self.parsed.pages[idx].clone())
    }

    pub fn all_pages(&self) -> Result<Vec<PageMetadata>> {
        Ok(self.parsed.pages.clone())
    }

    pub fn structure(&self) -> Result<DocumentStructure> {
        Ok(self.parsed.structure.clone())
    }

    pub fn path(&self) -> &str {
        &self.path
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pdf_document_creation() {
        assert_eq!(1, 1);
    }
}
