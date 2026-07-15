use crate::structure::{DocumentStructure, HeadingNode};
use crate::page::PageMetadata;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeadingSection {
    pub heading: HeadingNode,
    pub start_page: u32,
    pub end_page: u32,
    pub total_words: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HierarchicalHeadings {
    pub chapters: Vec<HeadingSection>,
}

impl HierarchicalHeadings {
    pub fn new() -> Self {
        Self {
            chapters: Vec::new(),
        }
    }
}

impl Default for HierarchicalHeadings {
    fn default() -> Self {
        Self::new()
    }
}

/// Extract a hierarchical heading structure from flat headings.
/// Returns chapters (H1 nodes) with proper page ranges and word counts assigned.
pub fn extract_hierarchy(
    structure: &DocumentStructure,
    page_count: u32,
    pages: Option<&[PageMetadata]>,
) -> HierarchicalHeadings {
    if structure.headings.is_empty() {
        return HierarchicalHeadings::new();
    }

    let mut chapters = Vec::new();

    // Convert flat headings to sections
    for (idx, heading) in structure.headings.iter().enumerate() {
        let start_page = heading.page_number;
        // End page is either the next heading's page - 1, or the last page
        let end_page = if idx + 1 < structure.headings.len() {
            structure.headings[idx + 1].page_number
        } else {
            page_count
        };

        // Count words in this section
        let total_words = if let Some(ps) = pages {
            ps.iter()
                .filter(|p| p.page_number >= start_page && p.page_number < end_page)
                .map(|p| p.word_count)
                .sum()
        } else {
            0
        };

        chapters.push(HeadingSection {
            heading: heading.clone(),
            start_page,
            end_page,
            total_words,
        });
    }

    HierarchicalHeadings { chapters }
}

/// Detect heading level from line characteristics.
/// Returns 1-4 for H1-H4, or None if not a heading.
pub fn detect_heading_level(text: &str) -> Option<u8> {
    let trimmed = text.trim();

    if trimmed.is_empty() || trimmed.len() > 200 {
        return None;
    }

    // Numeric prefix patterns: 1., 1.1., 1.1.1., 1.1.1.1.
    if let Some(first_space) = trimmed.find(' ') {
        let prefix = &trimmed[..first_space];
        let dots = prefix.matches('.').count();

        // Check if starts with digits and dots
        if prefix.chars().all(|c| c.is_numeric() || c == '.') && !prefix.is_empty() {
            match dots {
                1 => return Some(1),  // "1. ..."
                2 => return Some(2),  // "1.1. ..."
                3 => return Some(3),  // "1.1.1. ..."
                4 => return Some(4),  // "1.1.1.1. ..."
                _ => {}
            }
        }
    }

    // ALL-CAPS lines < 50 chars → likely H1
    if trimmed.len() < 50 && trimmed.chars().all(|c| c.is_uppercase() || c.is_whitespace()) {
        return Some(1);
    }

    // Title-Case lines < 40 chars (first char uppercase, no trailing period) → likely H2
    if trimmed.len() < 40
        && trimmed.chars().next().is_some_and(|c| c.is_uppercase())
        && !trimmed.ends_with('.')
    {
        let words: Vec<&str> = trimmed.split_whitespace().collect();
        if words.iter().all(|w| {
            w.chars()
                .next()
                .is_some_and(|c| c.is_uppercase() || c.is_numeric())
        }) {
            return Some(2);
        }
    }

    None
}
