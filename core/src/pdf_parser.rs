use crate::document::DocumentMetadata;
use crate::page::PageMetadata;
use crate::structure::{DocumentStructure, HeadingNode};
use crate::error::{Error, Result};
use crate::heading_extractor::detect_heading_level;
use pdfium_render::prelude::*;
use std::panic;

#[derive(Debug, Clone)]
pub struct ParsedDocument {
    pub page_count: u32,
    pub metadata: DocumentMetadata,
    pub pages: Vec<PageMetadata>,
    pub structure: DocumentStructure,
}

/// Bind to the PDFium native library, converting a missing/corrupt binary into a
/// proper `Error` instead of letting the process panic. `Pdfium::default()` panics
/// internally (via `.unwrap()`) when no PDFium library can be located, so we catch
/// that panic here and surface it as an honest error to the caller.
pub(crate) fn init_pdfium() -> Result<Pdfium> {
    panic::catch_unwind(Pdfium::default).map_err(|_| {
        Error::Pdf(
            "PDFium native library could not be loaded. Install libpdfium (see \
             scripts/download_pdfium.sh) and ensure it is discoverable (current working \
             directory or system library path)."
                .to_string(),
        )
    })
}

/// Map a `PdfiumError` returned while opening a document into our own `Error` type.
/// Wrong/missing password is surfaced distinctly (`Error::EncryptedPdf`) so callers can
/// tell "this file needs a password" apart from "this file is broken".
pub(crate) fn map_pdfium_open_error(path: &str, err: PdfiumError) -> Error {
    match err {
        PdfiumError::PdfiumLibraryInternalError(PdfiumInternalError::PasswordError) => {
            Error::EncryptedPdf(format!(
                "'{}' is password-protected and no valid password was supplied.",
                path
            ))
        }
        other => Error::Pdf(format!("Failed to load PDF '{}': {:?}", path, other)),
    }
}

/// Parse a PDF document from disk. On any real failure (corrupt file, missing PDFium
/// library, wrong password, etc.) this returns a proper `Error` — it never fabricates
/// placeholder content.
pub fn parse_document_open(path: &str) -> Result<ParsedDocument> {
    parse_document_open_with_password(path, None)
}

/// Parse a PDF document from disk, optionally supplying a password for encrypted
/// documents. Fails closed: a missing/incorrect password for an encrypted document
/// returns `Error::EncryptedPdf` rather than silently succeeding or fabricating content.
pub fn parse_document_open_with_password(path: &str, password: Option<&str>) -> Result<ParsedDocument> {
    let path_owned = path.to_string();
    let password_owned = password.map(|p| p.to_string());

    let result = panic::catch_unwind(panic::AssertUnwindSafe(|| {
        try_parse_with_pdfium(&path_owned, password_owned.as_deref())
    }));

    match result {
        Ok(inner) => inner,
        Err(_) => Err(Error::Pdf(format!(
            "PDFium panicked while parsing '{}'. The file is likely corrupted, truncated, or not a valid PDF.",
            path
        ))),
    }
}

fn try_parse_with_pdfium(path: &str, password: Option<&str>) -> Result<ParsedDocument> {
    let pdfium = init_pdfium()?;

    // Load and process document in its own scope
    let (page_count, pages, headings) = {
        let document = pdfium
            .load_pdf_from_file(path, password)
            .map_err(|e| map_pdfium_open_error(path, e))?;

        let page_count = document.pages().len() as u32;
        let mut pages = Vec::with_capacity(page_count as usize);
        let mut headings = Vec::new();

        for (page_idx, page) in document.pages().iter().enumerate() {
            let page_number = (page_idx + 1) as u32;
            let width = page.width().value;
            let height = page.height().value;

            // Extract text from page - convert to owned String immediately
            let text = page.text()
                .ok()
                .map(|t| t.to_string())
                .unwrap_or_default();

            let word_count = text.split_whitespace().count() as u32;
            let text_preview = text.chars().take(300).collect::<String>();
            let is_likely_scanned = word_count == 0;

            pages.push(PageMetadata {
                page_number,
                width,
                height,
                rotation: 0,
                label: None,
                word_count,
                text_preview,
                text: text.clone(),
                regions: Vec::new(),
                is_likely_scanned,
            });

            for line in text.lines() {
                let trimmed = line.trim();
                if trimmed.is_empty() || trimmed.len() > 200 {
                    continue;
                }
                if let Some(level) = detect_heading_level(trimmed) {
                    headings.push(HeadingNode {
                        level,
                        text: trimmed.to_string(),
                        page_number,
                        children: Vec::new(),
                    });
                }
            }
        }

        (page_count, pages, headings)
    };

    // Extract metadata (basic - no fancy properties since pdfium-render doesn't expose them)
    let metadata = DocumentMetadata {
        title: None,
        author: None,
        creator: None,
        producer: None,
        created: None,
        modified: None,
        page_count,
    };

    let structure = DocumentStructure {
        toc: Vec::new(),
        headings,
    };

    Ok(ParsedDocument {
        page_count,
        metadata,
        pages,
        structure,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_nonexistent_file_returns_error() {
        let result = parse_document_open("/nonexistent/path/does-not-exist.pdf");
        assert!(result.is_err(), "parsing a nonexistent file must return an Error, not fabricated content");
    }

    #[test]
    fn test_parse_garbage_file_returns_error_not_fake_content() {
        // A file that exists but is not a valid PDF at all.
        let dir = std::env::temp_dir();
        let path = dir.join("pystreampdf_test_garbage_not_a_pdf.pdf");
        std::fs::write(&path, b"this is not a pdf file, just plain text garbage").unwrap();

        let result = parse_document_open(path.to_str().unwrap());
        let _ = std::fs::remove_file(&path);

        assert!(
            result.is_err(),
            "parsing an invalid PDF must return an Error rather than a fabricated fallback document"
        );
    }
}
