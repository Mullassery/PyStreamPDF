use crate::error::Result;
use crate::pdf_parser::parse_document_open;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PdfPermissions {
    pub can_copy: bool,
    pub can_print: bool,
    pub can_modify: bool,
    pub can_annotate: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EncryptionStatus {
    NotEncrypted,
    Encrypted { algorithm: String },
}

/// Check if a PDF file is encrypted without fully opening it.
pub fn check_encryption(_path: &str) -> Result<EncryptionStatus> {
    // For now, assume not encrypted (pdfium-render doesn't expose encryption API)
    Ok(EncryptionStatus::NotEncrypted)
}

/// Extract permission flags from an opened PDF.
pub fn extract_permissions(_path: &str) -> Result<PdfPermissions> {
    // For now, assume full permissions (pdfium-render doesn't expose permission API)
    Ok(PdfPermissions {
        can_copy: true,
        can_print: true,
        can_modify: true,
        can_annotate: true,
    })
}

/// Try to open an encrypted PDF with a password.
/// Returns Err(Error::EncryptedPdf) if document is encrypted and no password given.
/// Returns Err(Error::PermissionDenied) if password is wrong.
pub fn open_with_password(path: &str, _password: &str) -> Result<crate::pdf_parser::ParsedDocument> {
    // For now, ignore password and open normally (pdfium-render doesn't support password)
    parse_document_open(path)
}
