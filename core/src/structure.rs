use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TocEntry {
    pub title: String,
    pub page_number: u32,
    pub level: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeadingNode {
    pub level: u8,
    pub text: String,
    pub page_number: u32,
    pub children: Vec<HeadingNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentStructure {
    pub toc: Vec<TocEntry>,
    pub headings: Vec<HeadingNode>,
}

impl DocumentStructure {
    pub fn new() -> Self {
        Self {
            toc: Vec::new(),
            headings: Vec::new(),
        }
    }
}

impl Default for DocumentStructure {
    fn default() -> Self {
        Self::new()
    }
}
