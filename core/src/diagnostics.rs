use serde::{Deserialize, Serialize};

/// Diagnosis of why text was lost during PDF parsing
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ExtractionLossCause {
    /// Scanned/image-based PDF without OCR (Optical Character Recognition)
    /// The PDF contains images of pages instead of actual text
    ScannedPdf,
    /// Complex layout: tables, multi-column, floating elements
    /// Parser can't extract text in correct reading order
    ComplexFormatting,
    /// Encoded/compressed content that pdfium-render couldn't decompress
    /// PDF has unusual compression or encoding
    EncodingIssue,
    /// Embedded images with text overlay (no OCR applied)
    /// Text is rendered as images, not extractable
    EmbeddedImages,
    /// Form fields or interactive elements
    /// Text in form fields not being extracted
    FormFields,
    /// Mixed content (some pages text, some scanned)
    /// Document has both regular pages and scanned pages
    MixedContent,
    /// Unknown/cannot determine
    Unknown,
}

impl ExtractionLossCause {
    /// Human-readable description with brief explanation
    pub fn description(&self) -> &'static str {
        match self {
            Self::ScannedPdf => {
                "PDF is scanned or image-based (no OCR applied)\n\
                 The PDF contains photographs/scans of pages instead of actual text.\n\
                 Text cannot be extracted without OCR (Optical Character Recognition)."
            }
            Self::ComplexFormatting => {
                "Complex page layout (tables, multi-column, floating elements)\n\
                 Parser struggles to extract text in correct order from complex layouts.\n\
                 Some text may be missed or garbled."
            }
            Self::EncodingIssue => {
                "Text encoding or compression issue in PDF\n\
                 PDF uses non-standard or corrupted encoding that parser cannot read.\n\
                 Text may be compressed or encrypted in unusual ways."
            }
            Self::EmbeddedImages => {
                "Images with embedded text (no OCR applied)\n\
                 Text is rendered as part of image graphics, not as extractable text.\n\
                 Requires OCR to read text from images."
            }
            Self::FormFields => {
                "Form fields or interactive elements\n\
                 Text stored in form fields may not be extracted by standard parsing.\n\
                 Fill fields before extraction or flatten form."
            }
            Self::MixedContent => {
                "Mixed content (some pages are scanned, some are text)\n\
                 Document contains both regular text pages and scanned/image pages.\n\
                 Scanned portions require OCR for text extraction."
            }
            Self::Unknown => {
                "Text loss detected but cause is unclear\n\
                 Review PDF manually to identify specific issues."
            }
        }
    }

    /// Practical remediation advice with options
    pub fn remediation(&self) -> &'static str {
        match self {
            Self::ScannedPdf => {
                "QUICK FIX: Increase token budget (500→1000) to compensate for missing text.\n\
                 BETTER: Apply OCR to convert image→text (Tesseract free, or cloud OCR).\n\
                 HOW: Use OCR tool on scanned PDF, produces new PDF with extractable text."
            }
            Self::ComplexFormatting => {
                "QUICK FIX: Verify retrieval quality is acceptable despite parsing issues.\n\
                 TRY: Export PDF from original application (Word→PDF, Excel→PDF).\n\
                 IF PERSISTS: Increase token budget to ensure full context."
            }
            Self::EncodingIssue => {
                "QUICK FIX: Download fresh copy of PDF, re-extract.\n\
                 IF SAME: Try accessing PDF from original source.\n\
                 FALLBACK: Increase token budget to compensate for extraction loss."
            }
            Self::EmbeddedImages => {
                "QUICK FIX: Increase token budget (500→1000).\n\
                 BETTER: Apply OCR to extracted images to recover text.\n\
                 NOTE: Some embedded text may be unrecoverable without visual inspection."
            }
            Self::FormFields => {
                "QUICK FIX: Increase token budget to get remaining content.\n\
                 BETTER: Fill visible form fields before extraction.\n\
                 OR: Use PDF tool to 'flatten' form (converts fields to regular text)."
            }
            Self::MixedContent => {
                "QUICK FIX: Increase token budget (1000→2000) to compensate.\n\
                 BETTER: Separate scanned pages, apply OCR, then recombine PDF.\n\
                 TRY: Run PDF through OCR tool (handles both text and scanned)."
            }
            Self::Unknown => {
                "1. Verify retrieval in pipeline visualization before sending to LLM.\n\
                 2. Increase token budget cautiously (150→500→1000).\n\
                 3. If loss persists, inspect PDF manually for formatting issues."
            }
        }
    }

    /// Severity level (1-5, where 5 is critical)
    pub fn severity(&self) -> u8 {
        match self {
            Self::ScannedPdf => 5,
            Self::ComplexFormatting => 3,
            Self::EncodingIssue => 4,
            Self::EmbeddedImages => 4,
            Self::FormFields => 2,
            Self::MixedContent => 4,
            Self::Unknown => 2,
        }
    }
}

/// Diagnosis of section-level extraction quality
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtractionDiagnostic {
    pub loss_percentage: f32,
    pub primary_cause: ExtractionLossCause,
    pub confidence: f32, // 0.0-1.0
    pub page_range: Option<String>, // e.g., "9-12" for context
    pub explanation: String,
    pub recommended_action: String,
}

impl ExtractionDiagnostic {
    /// Diagnose extraction loss for a section
    pub fn diagnose(
        raw_words: u32,
        extracted_words: u32,
        section_title: &str,
        page_range: Option<&str>,
    ) -> Self {
        let loss = (raw_words as i32 - extracted_words as i32).max(0) as u32;
        let loss_pct = if raw_words > 0 {
            (loss as f32 / raw_words as f32) * 100.0
        } else {
            0.0
        };

        // Diagnosis logic
        let (cause, confidence, explanation) = if loss_pct < 2.0 {
            (
                ExtractionLossCause::Unknown,
                0.9,
                "Minimal loss detected, likely minor formatting variations".to_string(),
            )
        } else if loss_pct < 5.0 {
            (
                ExtractionLossCause::ComplexFormatting,
                0.7,
                "Low-moderate loss, likely some formatting complexity".to_string(),
            )
        } else if loss_pct < 10.0 {
            // Could be scanned or complex formatting
            let is_likely_scanned = section_title.to_lowercase().contains("scan")
                || section_title.to_lowercase().contains("image")
                || loss_pct > 7.0; // >7% more likely scanned

            if is_likely_scanned {
                (
                    ExtractionLossCause::ScannedPdf,
                    0.8,
                    format!(
                        "Moderate loss ({:.1}%) suggests scanned PDF or OCR-needing content",
                        loss_pct
                    ),
                )
            } else {
                (
                    ExtractionLossCause::ComplexFormatting,
                    0.7,
                    format!("Moderate loss ({:.1}%) likely due to complex layout", loss_pct),
                )
            }
        } else if loss_pct < 20.0 {
            (
                ExtractionLossCause::ScannedPdf,
                0.85,
                format!(
                    "High loss ({:.1}%) strongly suggests scanned PDF without OCR",
                    loss_pct
                ),
            )
        } else if loss_pct < 40.0 {
            (
                ExtractionLossCause::MixedContent,
                0.75,
                format!(
                    "Very high loss ({:.1}%) indicates mixed scanned/text content or poor encoding",
                    loss_pct
                ),
            )
        } else {
            (
                ExtractionLossCause::ScannedPdf,
                0.9,
                format!(
                    "Critical loss ({:.1}%) - PDF is primarily scanned or encoded content",
                    loss_pct
                ),
            )
        };

        // Add page context to explanation
        let explanation_with_pages = if let Some(pages) = page_range {
            format!("Pages {}: {}", pages, explanation)
        } else {
            explanation
        };

        let recommended_action = if loss_pct < 2.0 {
            "No action needed - extraction quality is acceptable".to_string()
        } else if loss_pct < 5.0 {
            format!(
                "Optional: Review pages {} to verify quality is acceptable",
                page_range.unwrap_or("?")
            )
        } else {
            format!(
                "Recommended: {}. Loss is {:.1}% on pages {} - action needed to improve retrieval quality",
                cause.remediation(),
                loss_pct,
                page_range.unwrap_or("?")
            )
        };

        ExtractionDiagnostic {
            loss_percentage: loss_pct,
            primary_cause: cause,
            confidence,
            page_range: page_range.map(|s| s.to_string()),
            explanation: explanation_with_pages,
            recommended_action,
        }
    }
}

/// Pipeline-level extraction diagnostics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineDiagnostics {
    pub overall_extraction_loss_pct: f32,
    pub most_likely_cause: ExtractionLossCause,
    pub confidence: f32,
    pub sections_with_loss: usize,
    pub severity_level: u8, // 1-5
    pub summary: String,
    pub action_items: Vec<String>,
}

impl PipelineDiagnostics {
    /// Diagnose entire pipeline extraction quality
    pub fn diagnose(
        raw_words: u32,
        extracted_words: u32,
        affected_sections: usize,
        total_sections: usize,
    ) -> Self {
        let loss = (raw_words as i32 - extracted_words as i32).max(0) as u32;
        let loss_pct = if raw_words > 0 {
            (loss as f32 / raw_words as f32) * 100.0
        } else {
            0.0
        };

        let affected_ratio = if total_sections > 0 {
            affected_sections as f32 / total_sections as f32
        } else {
            0.0
        };

        // Determine cause and action items
        let (cause, confidence, severity, summary, actions) = if loss_pct < 2.0 {
            (
                ExtractionLossCause::Unknown,
                0.95,
                1,
                "Extraction quality is excellent - minimal text loss detected".to_string(),
                vec!["No action required - proceed with confidence".to_string()],
            )
        } else if loss_pct < 5.0 {
            (
                ExtractionLossCause::ComplexFormatting,
                0.7,
                2,
                format!(
                    "Extraction quality is good - {:.1}% loss detected, likely minor formatting issues",
                    loss_pct
                ),
                vec!["No action required. Loss is within acceptable range".to_string()],
            )
        } else if loss_pct < 10.0 {
            if affected_ratio > 0.5 {
                (
                    ExtractionLossCause::ScannedPdf,
                    0.8,
                    3,
                    format!(
                        "Extraction quality degraded - {:.1}% loss affecting {:.0}% of sections",
                        loss_pct, affected_ratio * 100.0
                    ),
                    vec![
                        "Increase token budget to compensate".to_string(),
                        "Verify retrieval quality in pipeline visualization".to_string(),
                    ],
                )
            } else {
                (
                    ExtractionLossCause::ComplexFormatting,
                    0.7,
                    2,
                    format!(
                        "Mixed extraction quality - {:.1}% loss in specific sections",
                        loss_pct
                    ),
                    vec![
                        "Increase token budget for affected sections".to_string(),
                    ],
                )
            }
        } else if loss_pct < 25.0 {
            (
                ExtractionLossCause::MixedContent,
                0.8,
                4,
                format!(
                    "Extraction quality degraded - {:.1}% loss indicates complex/scanned content",
                    loss_pct
                ),
                vec![
                    "Increase token budget significantly to maintain quality".to_string(),
                    "Preview retrieved sections before sending to LLM".to_string(),
                ],
            )
        } else {
            (
                ExtractionLossCause::ScannedPdf,
                0.9,
                5,
                format!(
                    "Extraction quality poor - {:.1}% loss, PDF is likely scanned or highly encoded",
                    loss_pct
                ),
                vec![
                    "Increase token budget substantially to compensate".to_string(),
                    "Verify retrieved content is relevant before LLM processing".to_string(),
                    "Consider obtaining digital version of document if possible".to_string(),
                ],
            )
        };

        PipelineDiagnostics {
            overall_extraction_loss_pct: loss_pct,
            most_likely_cause: cause,
            confidence,
            sections_with_loss: affected_sections,
            severity_level: severity,
            summary,
            action_items: actions,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scanned_pdf_diagnosis() {
        let diag = ExtractionDiagnostic::diagnose(1000, 650, "Scanned Document");
        assert_eq!(diag.primary_cause, ExtractionLossCause::ScannedPdf);
        assert!(diag.confidence > 0.7);
    }

    #[test]
    fn test_minimal_loss() {
        let diag = ExtractionDiagnostic::diagnose(1000, 990, "Chapter 1");
        assert!(diag.loss_percentage < 2.0);
    }

    #[test]
    fn test_complex_formatting() {
        let diag = ExtractionDiagnostic::diagnose(1000, 960, "Table of Contents");
        assert_eq!(diag.loss_percentage, 4.0);
    }
}
