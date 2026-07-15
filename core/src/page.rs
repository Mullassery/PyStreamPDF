use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum RegionType {
    Text,
    Heading,
    Image,
    Table,
    Header,
    Footer,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct BoundingBox {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentRegion {
    pub region_type: RegionType,
    pub bounds: BoundingBox,
    pub text: Option<String>,
    pub font_size: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PageMetadata {
    pub page_number: u32,
    pub width: f32,
    pub height: f32,
    pub rotation: u32,
    pub label: Option<String>,
    pub word_count: u32,
    pub text_preview: String,
    pub regions: Vec<ContentRegion>,
}
