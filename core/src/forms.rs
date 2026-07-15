use serde::{Deserialize, Serialize};
use crate::Result;

/// Type of PDF form field
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FormFieldType {
    /// Text input field
    Text,
    /// Checkbox field
    Checkbox,
    /// Radio button field
    RadioButton,
    /// Dropdown/select field
    Dropdown,
    /// Signature field
    Signature,
    /// Unknown field type
    Unknown,
}

impl FormFieldType {
    pub fn as_str(&self) -> &str {
        match self {
            FormFieldType::Text => "text",
            FormFieldType::Checkbox => "checkbox",
            FormFieldType::RadioButton => "radio_button",
            FormFieldType::Dropdown => "dropdown",
            FormFieldType::Signature => "signature",
            FormFieldType::Unknown => "unknown",
        }
    }
}

/// A form field in a PDF document
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PdfFormField {
    /// Field name/identifier
    pub name: String,
    /// Type of form field
    pub field_type: FormFieldType,
    /// Current field value (if applicable)
    pub value: Option<String>,
    /// Page number where field appears
    pub page_number: u32,
}

impl PdfFormField {
    /// Create a new form field
    pub fn new(name: String, field_type: FormFieldType, page_number: u32) -> Self {
        Self {
            name,
            field_type,
            value: None,
            page_number,
        }
    }

    /// Set the field value
    pub fn with_value(mut self, value: String) -> Self {
        self.value = Some(value);
        self
    }
}

/// Extract all form fields from a PDF
pub fn extract_form_fields(path: &str) -> Result<Vec<PdfFormField>> {
    // Stub: will be implemented with pdfium-render
    Ok(Vec::new())
}

/// Check if a PDF has interactive form elements
pub fn has_forms(path: &str) -> bool {
    // Stub: will be implemented with pdfium-render
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_form_field_type_as_str() {
        assert_eq!(FormFieldType::Text.as_str(), "text");
        assert_eq!(FormFieldType::Checkbox.as_str(), "checkbox");
        assert_eq!(FormFieldType::RadioButton.as_str(), "radio_button");
        assert_eq!(FormFieldType::Dropdown.as_str(), "dropdown");
        assert_eq!(FormFieldType::Signature.as_str(), "signature");
        assert_eq!(FormFieldType::Unknown.as_str(), "unknown");
    }

    #[test]
    fn test_form_field_creation() {
        let field = PdfFormField::new(
            "email".to_string(),
            FormFieldType::Text,
            1,
        );
        assert_eq!(field.name, "email");
        assert_eq!(field.field_type, FormFieldType::Text);
        assert_eq!(field.page_number, 1);
        assert!(field.value.is_none());
    }

    #[test]
    fn test_form_field_with_value() {
        let field = PdfFormField::new(
            "email".to_string(),
            FormFieldType::Text,
            1,
        ).with_value("user@example.com".to_string());

        assert_eq!(field.value, Some("user@example.com".to_string()));
    }

    #[test]
    fn test_form_field_serialization() {
        let field = PdfFormField::new(
            "checkbox_field".to_string(),
            FormFieldType::Checkbox,
            2,
        );
        let json = serde_json::to_string(&field).unwrap();
        let deserialized: PdfFormField = serde_json::from_str(&json).unwrap();
        assert_eq!(field.name, deserialized.name);
    }

    #[test]
    fn test_form_field_type_serialization() {
        let field_type = FormFieldType::Signature;
        let json = serde_json::to_string(&field_type).unwrap();
        let deserialized: FormFieldType = serde_json::from_str(&json).unwrap();
        assert_eq!(field_type, deserialized);
    }

    #[test]
    fn test_multiple_field_types() {
        let fields = vec![
            PdfFormField::new("name".to_string(), FormFieldType::Text, 1),
            PdfFormField::new("agree".to_string(), FormFieldType::Checkbox, 1),
            PdfFormField::new("signature".to_string(), FormFieldType::Signature, 2),
        ];
        assert_eq!(fields.len(), 3);
        assert_eq!(fields[0].field_type, FormFieldType::Text);
        assert_eq!(fields[1].field_type, FormFieldType::Checkbox);
        assert_eq!(fields[2].field_type, FormFieldType::Signature);
    }
}
