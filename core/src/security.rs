use serde::{Deserialize, Serialize};
use crate::Error;
use crate::Result;

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

/// Check if a PDF file is encrypted without fully opening it
pub fn check_encryption(path: &str) -> Result<EncryptionStatus> {
    // Stub: will be implemented with pdfium-render
    // For now, assume unencrypted
    Ok(EncryptionStatus::NotEncrypted)
}

/// Extract permission flags from a PDF document
pub fn extract_permissions(path: &str) -> Result<PdfPermissions> {
    // Stub: will be implemented with pdfium-render
    // For now, return default permissions
    Ok(PdfPermissions::default())
}

/// Try to open an encrypted PDF with a password
pub fn open_with_password(path: &str, password: &str) -> Result<Vec<u8>> {
    // Stub: will be implemented with pdfium-render
    std::fs::read(path).map_err(|e| Error::Io(e))
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
}
