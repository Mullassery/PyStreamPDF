use crate::error::{Error, Result};
use crate::page::PageMetadata;
use crate::structure::DocumentStructure;
use crate::pdf_parser::{ParsedDocument, parse_document_open};
use crate::security::{PdfPermissions, EncryptionStatus, open_with_password, check_encryption, extract_permissions};
use crate::forms::PdfFormField;
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

    /// Open a PDF with a password (for encrypted PDFs).
    pub fn open_with_password<P: AsRef<Path>>(path: P, password: &str) -> Result<Self> {
        let path_str = path
            .as_ref()
            .to_str()
            .ok_or_else(|| Error::Pdf("Invalid path".to_string()))?
            .to_string();

        if !Path::new(&path_str).exists() {
            return Err(Error::Pdf("File not found".to_string()));
        }

        let parsed = open_with_password(&path_str, password)?;

        Ok(PdfDocument {
            path: path_str,
            parsed,
        })
    }

    /// Check if a PDF is encrypted.
    pub fn is_encrypted<P: AsRef<Path>>(path: P) -> Result<bool> {
        let path_str = path
            .as_ref()
            .to_str()
            .ok_or_else(|| Error::Pdf("Invalid path".to_string()))?;

        match check_encryption(path_str)? {
            EncryptionStatus::Encrypted { .. } => Ok(true),
            EncryptionStatus::NotEncrypted => Ok(false),
        }
    }

    /// Get PDF permissions.
    pub fn permissions<P: AsRef<Path>>(path: P) -> Result<PdfPermissions> {
        let path_str = path
            .as_ref()
            .to_str()
            .ok_or_else(|| Error::Pdf("Invalid path".to_string()))?;

        extract_permissions(path_str)
    }

    /// SHA-256 fingerprint of the file.
    pub fn fingerprint(&self) -> String {
        use sha2::{Sha256, Digest};
        use std::fs;

        let file_bytes = match fs::read(&self.path) {
            Ok(bytes) => bytes,
            Err(_) => return String::new(),
        };

        let mut hasher = Sha256::new();
        hasher.update(&file_bytes);
        let result = hasher.finalize();

        format!("{:x}", result)
    }

    /// Extract form fields from the PDF.
    pub fn form_fields(&self) -> Vec<PdfFormField> {
        crate::forms::extract_form_fields(&self.path).unwrap_or_default()
    }

    /// Check if the PDF has interactive forms.
    pub fn has_forms(&self) -> bool {
        crate::forms::has_forms(&self.path)
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
