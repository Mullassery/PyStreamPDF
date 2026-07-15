use crate::error::Result;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FormFieldType {
    Text,
    Checkbox,
    RadioButton,
    Dropdown,
    Signature,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PdfFormField {
    pub name: String,
    pub field_type: FormFieldType,
    pub value: Option<String>,
    pub page_number: u32,
}

/// Extract all form fields from a PDF. Returns empty vec if no forms present.
pub fn extract_form_fields(_path: &str) -> Result<Vec<PdfFormField>> {
    // For now, return empty (pdfium-render doesn't expose form fields API)
    Ok(Vec::new())
}

/// Check if a PDF has interactive form elements.
pub fn has_forms(_path: &str) -> bool {
    // For now, assume no forms (pdfium-render doesn't expose form fields API)
    false
}
