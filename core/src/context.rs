use crate::heading_extractor::{HeadingSection, HierarchicalHeadings};
use crate::index::PageResult;
use crate::markdown;
use crate::page::PageMetadata;
use crate::pipeline::{PipelineFlow, SectionFlow, PipelineSummary};
use crate::diagnostics::ExtractionDiagnostic;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextSection {
    pub heading_path: String,
    pub page_numbers: Vec<u32>,
    pub content: String,
    pub relevance_score: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentContext {
    pub query: String,
    pub total_tokens: u32,
    pub sections: Vec<ContextSection>,
}

/// Assemble an AgentContext from search results.
pub fn assemble(
    query: &str,
    results: &[PageResult],
    hierarchy: &HierarchicalHeadings,
    pages: &[PageMetadata],
    max_tokens: u32,
) -> AgentContext {
    if results.is_empty() {
        return AgentContext {
            query: query.to_string(),
            total_tokens: 0,
            sections: Vec::new(),
        };
    }

    // Map results to sections (dedup by page range)
    let mut section_map: HashMap<String, (f32, Vec<u32>)> = HashMap::new();

    for result in results {
        if let Some(section) = find_section_for_page(result.page_number, hierarchy) {
            let key = format!("{}-{}", section.start_page, section.end_page);
            let entry = section_map.entry(key).or_insert((0.0, Vec::new()));
            entry.0 = entry.0.max(result.score);
            entry.1.push(result.page_number);
        }
    }

    // Build sections with markdown content
    let mut sections = Vec::new();
    let mut total_tokens = 0u32;

    for section in &hierarchy.chapters {
        let key = format!("{}-{}", section.start_page, section.end_page);

        if let Some((score, _page_numbers)) = section_map.get(&key) {
            if total_tokens >= max_tokens {
                break; // Already hit token budget
            }

            let remaining_tokens = max_tokens.saturating_sub(total_tokens);
            let section_pages: Vec<&PageMetadata> = pages
                .iter()
                .filter(|p| p.page_number >= section.start_page && p.page_number < section.end_page)
                .collect();

            if !section_pages.is_empty() {
                let section_pages_owned: Vec<PageMetadata> = section_pages.iter().map(|p| (*p).clone()).collect();
                let md_output = markdown::section_to_markdown(section, &section_pages_owned, remaining_tokens);
                total_tokens += md_output.estimated_tokens;

                let heading_path = build_heading_path(section, &hierarchy.chapters);

                sections.push(ContextSection {
                    heading_path,
                    page_numbers: md_output.pages_included,
                    content: md_output.markdown,
                    relevance_score: *score,
                });
            }
        }
    }

    AgentContext {
        query: query.to_string(),
        total_tokens: total_tokens.min(max_tokens),
        sections,
    }
}

/// Build a breadcrumb path for a section (e.g., "Chapter 1 > Section 1.2").
fn build_heading_path(section: &HeadingSection, all_chapters: &[HeadingSection]) -> String {
    // Find any parent chapter (lower level heading that starts before this section)
    let parent = all_chapters.iter().rev().find(|ch| {
        ch.heading.level < section.heading.level
            && ch.start_page <= section.start_page
    });

    match parent {
        Some(p) => format!("{} > {}", p.heading.text, section.heading.text),
        None => section.heading.text.clone(),
    }
}

/// Find the section containing a given page.
fn find_section_for_page(page_num: u32, hierarchy: &HierarchicalHeadings) -> Option<HeadingSection> {
    for section in &hierarchy.chapters {
        if page_num >= section.start_page && page_num < section.end_page {
            return Some(section.clone());
        }
    }
    None
}

/// Build pipeline flow visualization data
pub fn build_pipeline_flow(
    query: &str,
    hierarchy: &HierarchicalHeadings,
    pages: &[PageMetadata],
    search_results: &[PageResult],
    context: &AgentContext,
    _max_tokens: u32,
) -> PipelineFlow {
    let mut section_flows = Vec::new();
    let mut total_raw = 0u32;
    let mut total_extracted = 0u32;
    let mut total_indexed = 0u32;
    let mut total_retrieved = 0u32;
    let mut total_selected = 0u32;

    // Build a map of selected sections for quick lookup
    let selected_sections: std::collections::HashSet<_> =
        context.sections.iter().map(|s| s.heading_path.clone()).collect();

    for chapter in &hierarchy.chapters {
        let heading_path = build_heading_path(chapter, &hierarchy.chapters);

        // Get pages in this section
        let section_pages: Vec<&PageMetadata> = pages
            .iter()
            .filter(|p| p.page_number >= chapter.start_page && p.page_number < chapter.end_page)
            .collect();

        // Calculate raw words (all text that exists in PDF)
        let raw_words: u32 = section_pages.iter().map(|p| p.word_count).sum();

        // Calculate extracted words (text that was successfully extracted by pdfium-render)
        let extracted_words: u32 = section_pages
            .iter()
            .map(|p| {
                // Count non-empty text from page
                if !p.text_preview.is_empty() {
                    p.text_preview.split_whitespace().count() as u32
                } else {
                    0
                }
            })
            .sum();

        // Indexed words = extracted words (we assume FTS5 preserves extracted text)
        let indexed_words = extracted_words;

        // Check if this section was retrieved
        let was_retrieved = search_results
            .iter()
            .any(|r| r.page_number >= chapter.start_page && r.page_number < chapter.end_page);

        let retrieved_words = if was_retrieved {
            indexed_words
        } else {
            0
        };

        // Check if this section was selected
        let (selected_words, relevance_score, reason) = if selected_sections.contains(&heading_path) {
            // Find the relevance score
            let score = context
                .sections
                .iter()
                .find(|s| s.heading_path == heading_path)
                .map(|s| s.relevance_score)
                .unwrap_or(0.0);
            (retrieved_words, Some(score), None)
        } else {
            if was_retrieved && retrieved_words > 0 {
                // Was retrieved but not selected -> must be due to token budget
                (0, None, Some("exceeds_token_budget".to_string()))
            } else if !was_retrieved {
                // Was not retrieved -> not relevant to query
                (0, None, Some("not_relevant".to_string()))
            } else {
                (0, None, None)
            }
        };

        total_raw += raw_words;
        total_extracted += extracted_words;
        total_indexed += indexed_words;
        total_retrieved += retrieved_words;
        total_selected += selected_words;

        // Generate extraction diagnosis for this section
        let extraction_diagnosis = if raw_words > 0 && raw_words > extracted_words {
            Some(ExtractionDiagnostic::diagnose(
                raw_words,
                extracted_words,
                &chapter.heading.text,
            ))
        } else {
            None
        };

        section_flows.push(SectionFlow {
            title: chapter.heading.text.clone(),
            pages: format!("{}-{}", chapter.start_page, chapter.end_page),
            raw_words,
            extracted_words,
            indexed_words,
            retrieved_words,
            selected_words,
            selected: selected_words > 0,
            relevance_score,
            reason,
            extraction_diagnosis,
        });
    }

    let summary = PipelineSummary {
        raw_words: total_raw,
        extracted_words: total_extracted,
        indexed_words: total_indexed,
        retrieved_words: total_retrieved,
        selected_words: total_selected,
    };

    // Generate overall extraction diagnosis
    let sections_with_loss = section_flows.iter().filter(|s| s.extraction_diagnosis.is_some()).count();
    let overall_extraction_diagnosis = if total_raw > total_extracted && !section_flows.is_empty() {
        let diag = crate::diagnostics::PipelineDiagnostics::diagnose(
            total_raw,
            total_extracted,
            sections_with_loss,
            section_flows.len(),
        );
        Some(format!(
            "{}\n\nDiagnosis: {}\nSeverity: {}/5\nRecommended actions:\n{}",
            diag.summary,
            diag.most_likely_cause.description(),
            diag.severity_level,
            diag.action_items.iter().enumerate()
                .map(|(i, action)| format!("{}. {}", i + 1, action))
                .collect::<Vec<_>>()
                .join("\n")
        ))
    } else {
        None
    };

    PipelineFlow {
        query: query.to_string(),
        sections: section_flows,
        summary,
        overall_extraction_diagnosis,
    }
}
