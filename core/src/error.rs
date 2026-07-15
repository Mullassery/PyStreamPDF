use thiserror::Error;

#[derive(Debug, Error)]
pub enum Error {
    #[error("PDF error: {0}")]
    Pdf(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Invalid page number: {0}")]
    InvalidPageNumber(u32),

    #[error("PDF structure error: {0}")]
    StructureError(String),

    #[error("Database error: {0}")]
    DatabaseError(String),

    #[error("PDF is encrypted: {0}")]
    EncryptedPdf(String),

    #[error("Permission denied: {0}")]
    PermissionDenied(String),
}

pub type Result<T> = std::result::Result<T, Error>;
