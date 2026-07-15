pub mod document;
pub mod error;
pub mod page;
pub mod structure;
pub mod pdf_parser;
pub mod index;

pub use document::PdfDocument;
pub use error::{Error, Result};
pub use page::{BoundingBox, ContentRegion, PageMetadata, RegionType};
pub use structure::{DocumentStructure, HeadingNode, TocEntry};
pub use index::{PdfIndex, PageResult};
