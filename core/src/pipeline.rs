use serde::{Deserialize, Serialize};
use crate::diagnostics::{ExtractionDiagnostic, ExtractionLossCause};

/// Tracks a section's journey through the extraction/retrieval pipeline
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SectionFlow {
    pub title: String,
    pub pages: String,
    pub raw_words: u32,
    pub extracted_words: u32,
    pub indexed_words: u32,
    pub retrieved_words: u32,
    pub selected_words: u32,
    pub selected: bool,
    pub relevance_score: Option<f32>,
    pub reason: Option<String>, // why it was filtered (e.g., "exceeds_token_budget", "not_relevant")
    pub extraction_diagnosis: Option<ExtractionDiagnostic>, // why text was lost
}

impl SectionFlow {
    pub fn extraction_loss(&self) -> u32 {
        self.raw_words.saturating_sub(self.extracted_words)
    }

    pub fn indexing_loss(&self) -> u32 {
        self.extracted_words.saturating_sub(self.indexed_words)
    }

    pub fn retrieval_loss(&self) -> u32 {
        self.indexed_words.saturating_sub(self.retrieved_words)
    }

    pub fn filtering_loss(&self) -> u32 {
        self.retrieved_words.saturating_sub(self.selected_words)
    }

    pub fn extraction_loss_pct(&self) -> f32 {
        if self.raw_words == 0 {
            0.0
        } else {
            (self.extraction_loss() as f32 / self.raw_words as f32) * 100.0
        }
    }
}

/// Complete pipeline flow showing extraction → indexing → retrieval → selection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineFlow {
    pub query: String,
    pub sections: Vec<SectionFlow>,
    pub summary: PipelineSummary,
    pub overall_extraction_diagnosis: Option<String>, // Why overall extraction loss happened
}

/// Summary statistics for the entire pipeline
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineSummary {
    pub raw_words: u32,
    pub extracted_words: u32,
    pub indexed_words: u32,
    pub retrieved_words: u32,
    pub selected_words: u32,
}

impl PipelineSummary {
    pub fn extraction_loss(&self) -> u32 {
        self.raw_words.saturating_sub(self.extracted_words)
    }

    pub fn indexing_loss(&self) -> u32 {
        self.extracted_words.saturating_sub(self.indexed_words)
    }

    pub fn retrieval_loss(&self) -> u32 {
        self.indexed_words.saturating_sub(self.retrieved_words)
    }

    pub fn filtering_loss(&self) -> u32 {
        self.retrieved_words.saturating_sub(self.selected_words)
    }

    pub fn extraction_loss_pct(&self) -> f32 {
        if self.raw_words == 0 {
            0.0
        } else {
            (self.extraction_loss() as f32 / self.raw_words as f32) * 100.0
        }
    }

    pub fn retrieval_loss_pct(&self) -> f32 {
        if self.indexed_words == 0 {
            0.0
        } else {
            (self.retrieval_loss() as f32 / self.indexed_words as f32) * 100.0
        }
    }

    pub fn filtering_loss_pct(&self) -> f32 {
        if self.retrieved_words == 0 {
            0.0
        } else {
            (self.filtering_loss() as f32 / self.retrieved_words as f32) * 100.0
        }
    }
}

impl PipelineFlow {
    /// Format pipeline flow as CLI table (terminal-friendly)
    pub fn to_cli_table(&self) -> String {
        let mut output = String::new();
        output.push_str(&format!(
            "\n{}\n",
            "=".repeat(140)
        ));
        output.push_str(&format!(
            "PDF PROCESSING PIPELINE: \"{}\"\n",
            self.query
        ));
        output.push_str(&format!("{}\n", "=".repeat(140)));
        output.push_str("\n");

        // Headers
        output.push_str(&format!(
            "{:<40} | {:<6} | {:<12} | {:<12} | {:<12} | {:<12}\n",
            "Section", "Raw", "Extract", "Index", "Retrieve", "Select"
        ));
        output.push_str(&format!("{}\n", "-".repeat(140)));

        for section in &self.sections {
            let name = if section.title.len() > 35 {
                format!("{}...", &section.title[..32])
            } else {
                section.title.clone()
            };

            let raw_col = format!("{:4}w", section.raw_words);

            let extract_marker = if section.extraction_loss() > 0 {
                "[*]"
            } else {
                "[OK]"
            };
            let extract_col = if section.extraction_loss() > 0 {
                format!(
                    "{} {:4}w (-{})",
                    extract_marker, section.extracted_words, section.extraction_loss()
                )
            } else {
                format!("{} {:4}w", extract_marker, section.extracted_words)
            };

            let index_marker = if section.indexing_loss() > 0 {
                "[*]"
            } else {
                "[OK]"
            };
            let index_col = if section.indexing_loss() > 0 {
                format!(
                    "{} {:4}w (-{})",
                    index_marker, section.indexed_words, section.indexing_loss()
                )
            } else {
                format!("{} {:4}w", index_marker, section.indexed_words)
            };

            let retrieve_col = if section.retrieved_words > 0 {
                format!("[OK] {:4}w", section.retrieved_words)
            } else {
                "[--]    0w".to_string()
            };

            let select_col = if section.selected_words > 0 {
                format!("[OK] {:4}w", section.selected_words)
            } else if section.filtering_loss() > 0 {
                format!("[X]     0w")
            } else {
                "[--]    0w".to_string()
            };

            output.push_str(&format!(
                "{:<40} p.{:<8} | {:<6} | {:<12} | {:<12} | {:<12} | {:<12}\n",
                name, section.pages, raw_col, extract_col, index_col, retrieve_col, select_col
            ));
        }

        output.push_str("\n");
        output.push_str(&format!("{}\n", "=".repeat(140)));
        output.push_str("LEGEND:\n");
        output.push_str("  [OK]  = Passed through this stage\n");
        output.push_str("  [*]   = Data loss at this stage (text missed during extraction/indexing)\n");
        output.push_str("  [--]  = Filtered out at this stage (intentional filtering)\n");
        output.push_str("  [X]   = Exceeds token budget constraint\n");
        output.push_str(&format!("{}\n\n", "=".repeat(140)));

        output
    }

    /// Format pipeline flow as a text flow diagram
    pub fn to_flow_diagram(&self) -> String {
        let mut output = String::new();
        output.push_str("\n");
        output.push_str(&format!("{}\n", "=".repeat(140)));
        output.push_str("PIPELINE SUMMARY: Complete Text Flow\n");
        output.push_str(&format!("{}\n\n", "=".repeat(140)));

        let s = &self.summary;

        output.push_str("                       PDF Content\n");
        output.push_str("                            |\n");
        output.push_str(&format!("                    {} words [RAW PDF]\n", s.raw_words));
        output.push_str("                            |\n");
        output.push_str("                      Extraction\n");
        output.push_str("                      pdfium-render\n");
        output.push_str("                            v\n");

        if s.extraction_loss() > 0 {
            output.push_str(&format!(
                "  [WARNING] Lost {} words ({:.1}%) during parsing\n",
                s.extraction_loss(),
                s.extraction_loss_pct()
            ));
            output.push_str("            -> Likely causes: scanned PDF, embedded images, complex formatting\n");
        }
        output.push_str(&format!(
            "                    {} words [EXTRACTED]\n",
            s.extracted_words
        ));
        output.push_str("                            |\n");
        output.push_str("                         Indexing\n");
        output.push_str("                       FTS5 cleanup\n");
        output.push_str("                            v\n");

        if s.indexing_loss() > 0 {
            output.push_str(&format!(
                "  [INFO] Normalized {} words during indexing\n",
                s.indexing_loss()
            ));
        }
        output.push_str(&format!("                    {} words [INDEXED]\n", s.indexed_words));
        output.push_str("                            |\n");
        output.push_str("                    Query Matching\n");
        output.push_str("                      (keyword/score)\n");
        output.push_str("                            v\n");

        output.push_str(&format!(
            "  [FILTER] {} words ({:.1}%) not relevant to query\n",
            s.retrieval_loss(),
            s.retrieval_loss_pct()
        ));
        output.push_str(&format!(
            "                    {} words [RETRIEVED]\n",
            s.retrieved_words
        ));
        output.push_str("                            |\n");
        output.push_str("                     Token Budget\n");
        output.push_str("                      (max_tokens constraint)\n");
        output.push_str("                            v\n");

        if s.filtering_loss() > 0 {
            output.push_str(&format!(
                "  [FILTER] {} words ({:.1}%) exceeds budget\n",
                s.filtering_loss(),
                s.filtering_loss_pct()
            ));
        }
        output.push_str(&format!(
            "                    {} words [SELECTED]\n",
            s.selected_words
        ));
        output.push_str("                            |\n");
        output.push_str("                       Send to LLM\n\n");
        output.push_str(&format!("{}\n\n", "=".repeat(140)));

        output
    }

    /// Format pipeline flow as JSON
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }
}
