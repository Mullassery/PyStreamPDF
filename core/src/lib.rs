pub mod document;
pub mod error;
pub mod page;
pub mod structure;

pub use document::PdfDocument;
pub use error::{Error, Result};
pub use page::{BoundingBox, ContentRegion, PageMetadata, RegionType};
pub use structure::{DocumentStructure, HeadingNode, TocEntry};
