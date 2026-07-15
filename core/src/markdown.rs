use crate::heading_extractor::HeadingSection;
use crate::page::PageMetadata;
use crate::structure::HeadingNode;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarkdownOutput {
    pub markdown: String,
    pub estimated_tokens: u32,
    pub pages_included: Vec<u32>,
}

/// Convert a single page's text to markdown.
pub fn page_to_markdown(page: &PageMetadata) -> MarkdownOutput {
    let markdown = format_text_as_markdown(&page.text);
    let estimated_tokens = estimate_tokens(&markdown);

    MarkdownOutput {
        markdown,
        estimated_tokens,
        pages_included: vec![page.page_number],
    }
}

/// Convert a section (heading + its pages) to markdown, respecting max_tokens.
pub fn section_to_markdown(
    section: &HeadingSection,
    pages: &[PageMetadata],
    max_tokens: u32,
) -> MarkdownOutput {
    let mut markdown = String::new();
    let mut estimated_tokens = 0u32;
    let mut pages_included = Vec::new();

    // Add heading
    let heading_md = heading_to_markdown(&section.heading);
    markdown.push_str(&heading_md);
    estimated_tokens += estimate_tokens(&heading_md);

    // Add pages until we hit max_tokens
    for page in pages {
        if page.page_number < section.start_page || page.page_number >= section.end_page {
            continue;
        }

        let page_md = format_text_as_markdown(&page.text);
        let page_tokens = estimate_tokens(&page_md);

        if estimated_tokens + page_tokens > max_tokens && !pages_included.is_empty() {
            // Would exceed max_tokens; stop and truncate
            markdown.push_str("\n\n... [truncated]\n");
            break;
        }

        markdown.push_str("\n\n");
        markdown.push_str(&page_md);
        estimated_tokens += page_tokens + 1; // +1 for separator
        pages_included.push(page.page_number);
    }

    MarkdownOutput {
        markdown,
        estimated_tokens: estimated_tokens.min(max_tokens),
        pages_included,
    }
}

/// Convert a HeadingNode to markdown heading syntax.
fn heading_to_markdown(node: &HeadingNode) -> String {
    let prefix = "#".repeat(node.level as usize);
    format!("{} {}\n", prefix, node.text)
}

/// Format plain text as markdown (preserve paragraph breaks).
fn format_text_as_markdown(text: &str) -> String {
    text.lines()
        .filter(|line| !line.trim().is_empty())
        .collect::<Vec<_>>()
        .join("\n\n")
}

/// Estimate token count (simple: text_len / 4 for English).
fn estimate_tokens(text: &str) -> u32 {
    (text.len() as u32).div_ceil(4).max(1)
}
