use serde::{Deserialize, Serialize};
use crate::error::Error;
use crate::Result;
use pdfium_render::prelude::{PdfiumError, PdfiumInternalError, PdfSecurityHandlerRevision};

/// PDF encryption status indicator
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum EncryptionStatus {
    /// PDF is not encrypted
    NotEncrypted,
    /// PDF is encrypted with specified algorithm
    Encrypted { algorithm: String },
}

/// PDF access permissions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PdfPermissions {
    /// User can copy text from PDF
    pub can_copy: bool,
    /// User can print PDF
    pub can_print: bool,
    /// User can modify PDF content
    pub can_modify: bool,
    /// User can add annotations to PDF
    pub can_annotate: bool,
}

impl Default for PdfPermissions {
    fn default() -> Self {
        Self {
            can_copy: true,
            can_print: true,
            can_modify: false,
            can_annotate: true,
        }
    }
}

impl PdfPermissions {
    /// Check if all permissions are granted
    pub fn all_allowed(&self) -> bool {
        self.can_copy && self.can_print && self.can_modify && self.can_annotate
    }

    /// Check if any permission is restricted
    pub fn any_restricted(&self) -> bool {
        !self.all_allowed()
    }
}

/// Human-readable label for a PDF standard security handler revision.
fn describe_security_handler(revision: PdfSecurityHandlerRevision) -> String {
    match revision {
        PdfSecurityHandlerRevision::Unprotected => "None".to_string(),
        PdfSecurityHandlerRevision::Revision2 => {
            "RC4-40 (Standard Security Handler, Revision 2)".to_string()
        }
        PdfSecurityHandlerRevision::Revision3 => {
            "RC4-128 (Standard Security Handler, Revision 3)".to_string()
        }
        PdfSecurityHandlerRevision::Revision4 => {
            "RC4/AES-128 (Standard Security Handler, Revision 4)".to_string()
        }
    }
}

/// Check if a PDF file is encrypted, using PDFium's real document/security handler
/// metadata. This opens the document without a password: if PDFium reports that a
/// password is required, the file is reported as encrypted with an unknown algorithm
/// (we can't inspect the security handler without decrypting first). If the document
/// opens without a password but PDFium reports a security handler revision other than
/// `Unprotected`, the file is still encrypted (e.g. owner-password-only protection).
pub fn check_encryption(path: &str) -> Result<EncryptionStatus> {
    let pdfium = crate::pdf_parser::init_pdfium()?;
    let open_result = pdfium.load_pdf_from_file(path, None);

    match open_result {
        Ok(document) => {
            let revision = document
                .permissions()
                .security_handler_revision()
                .map_err(|e| {
                    Error::Pdf(format!(
                        "Failed to read security handler revision for '{}': {:?}",
                        path, e
                    ))
                })?;

            match revision {
                PdfSecurityHandlerRevision::Unprotected => Ok(EncryptionStatus::NotEncrypted),
                other => Ok(EncryptionStatus::Encrypted {
                    algorithm: describe_security_handler(other),
                }),
            }
        }
        Err(PdfiumError::PdfiumLibraryInternalError(PdfiumInternalError::PasswordError)) => {
            Ok(EncryptionStatus::Encrypted {
                algorithm: "Unknown (password required to open document)".to_string(),
            })
        }
        Err(e) => Err(crate::pdf_parser::map_pdfium_open_error(path, e)),
    }
}

/// Extract real permission flags from a PDF document using PDFium's permission bitflags
/// (`FPDF_GetDocPermissions`). If the document requires a password we don't have, this
/// fails closed with `Error::EncryptedPdf` rather than returning default/all-permissive
/// values.
pub fn extract_permissions(path: &str) -> Result<PdfPermissions> {
    let pdfium = crate::pdf_parser::init_pdfium()?;

    let document = pdfium
        .load_pdf_from_file(path, None)
        .map_err(|e| crate::pdf_parser::map_pdfium_open_error(path, e))?;

    let perms = document.permissions();

    let can_print = perms.can_print_high_quality().unwrap_or(false)
        || perms.can_print_only_low_quality().unwrap_or(false);

    Ok(PdfPermissions {
        can_copy: perms.can_extract_text_and_graphics().unwrap_or(false),
        can_print,
        can_modify: perms.can_modify_document_content().unwrap_or(false),
        can_annotate: perms.can_add_or_modify_text_annotations().unwrap_or(false),
    })
}

/// Try to open a (possibly encrypted) PDF with a password. This fails closed: if the
/// password is wrong (or the document is encrypted and no password was supplied), the
/// underlying PDFium `PasswordError` is surfaced as `Error::EncryptedPdf` — it never
/// silently falls back to an unauthenticated parse.
pub fn open_with_password(path: &str, password: &str) -> Result<crate::pdf_parser::ParsedDocument> {
    crate::pdf_parser::parse_document_open_with_password(path, Some(password))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encryption_status_not_encrypted() {
        let status = EncryptionStatus::NotEncrypted;
        assert_eq!(status, EncryptionStatus::NotEncrypted);
    }

    #[test]
    fn test_encryption_status_encrypted() {
        let status = EncryptionStatus::Encrypted {
            algorithm: "AES-256".to_string(),
        };
        assert!(matches!(status, EncryptionStatus::Encrypted { .. }));
    }

    #[test]
    fn test_pdf_permissions_default() {
        let perms = PdfPermissions::default();
        assert!(perms.can_copy);
        assert!(perms.can_print);
        assert!(!perms.can_modify);
        assert!(perms.can_annotate);
    }

    #[test]
    fn test_pdf_permissions_all_allowed() {
        let perms = PdfPermissions {
            can_copy: true,
            can_print: true,
            can_modify: true,
            can_annotate: true,
        };
        assert!(perms.all_allowed());
    }

    #[test]
    fn test_pdf_permissions_any_restricted() {
        let perms = PdfPermissions {
            can_copy: false,
            can_print: true,
            can_modify: true,
            can_annotate: true,
        };
        assert!(perms.any_restricted());
    }

    #[test]
    fn test_pdf_permissions_serialization() {
        let perms = PdfPermissions::default();
        let json = serde_json::to_string(&perms).unwrap();
        let deserialized: PdfPermissions = serde_json::from_str(&json).unwrap();
        assert_eq!(perms.can_copy, deserialized.can_copy);
    }

    #[test]
    fn test_check_encryption_nonexistent_file_is_error() {
        let result = check_encryption("/nonexistent/path/does-not-exist.pdf");
        assert!(result.is_err());
    }

    #[test]
    fn test_extract_permissions_nonexistent_file_is_error() {
        let result = extract_permissions("/nonexistent/path/does-not-exist.pdf");
        assert!(result.is_err());
    }
}
