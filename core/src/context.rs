use crate::heading_extractor::{HeadingSection, HierarchicalHeadings};
use crate::index::PageResult;
use crate::markdown;
use crate::page::PageMetadata;
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
