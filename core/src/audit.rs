use serde::{Deserialize, Serialize};

/// Type of audit event
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum AuditEventKind {
    /// PDF document opened
    DocumentOpened,
    /// PDF index built
    DocumentIndexed,
    /// Search performed on document
    SearchPerformed { query: String, results_count: usize },
    /// Context retrieved from document
    ContextRetrieved { query: String, tokens: u32 },
}

/// Single audit event for governance tracking
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEvent {
    /// When event occurred (ISO 8601 string)
    pub timestamp: String,
    /// Document path or identifier
    pub doc_path: String,
    /// Event type and details
    pub kind: AuditEventKind,
}

impl AuditEvent {
    /// Create a new audit event with current timestamp
    pub fn new(doc_path: String, kind: AuditEventKind) -> Self {
        Self {
            timestamp: chrono::Utc::now().to_rfc3339(),
            doc_path,
            kind,
        }
    }

    /// Create a document opened event
    pub fn document_opened(doc_path: String) -> Self {
        Self::new(doc_path, AuditEventKind::DocumentOpened)
    }

    /// Create a document indexed event
    pub fn document_indexed(doc_path: String) -> Self {
        Self::new(doc_path, AuditEventKind::DocumentIndexed)
    }

    /// Create a search performed event
    pub fn search_performed(doc_path: String, query: String, results_count: usize) -> Self {
        Self::new(
            doc_path,
            AuditEventKind::SearchPerformed { query, results_count },
        )
    }

    /// Create a context retrieved event
    pub fn context_retrieved(doc_path: String, query: String, tokens: u32) -> Self {
        Self::new(
            doc_path,
            AuditEventKind::ContextRetrieved { query, tokens },
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audit_event_creation() {
        let event = AuditEvent::new(
            "document.pdf".to_string(),
            AuditEventKind::DocumentOpened,
        );
        assert_eq!(event.doc_path, "document.pdf");
        assert_eq!(event.kind, AuditEventKind::DocumentOpened);
        assert!(!event.timestamp.is_empty());
    }

    #[test]
    fn test_audit_event_document_opened() {
        let event = AuditEvent::document_opened("doc.pdf".to_string());
        assert_eq!(event.kind, AuditEventKind::DocumentOpened);
    }

    #[test]
    fn test_audit_event_search_performed() {
        let event = AuditEvent::search_performed(
            "doc.pdf".to_string(),
            "machine learning".to_string(),
            42,
        );
        match event.kind {
            AuditEventKind::SearchPerformed { query, results_count } => {
                assert_eq!(query, "machine learning");
                assert_eq!(results_count, 42);
            }
            _ => panic!("Expected SearchPerformed event"),
        }
    }

    #[test]
    fn test_audit_event_context_retrieved() {
        let event = AuditEvent::context_retrieved(
            "doc.pdf".to_string(),
            "AI summary".to_string(),
            1500,
        );
        match event.kind {
            AuditEventKind::ContextRetrieved { query, tokens } => {
                assert_eq!(query, "AI summary");
                assert_eq!(tokens, 1500);
            }
            _ => panic!("Expected ContextRetrieved event"),
        }
    }

    #[test]
    fn test_audit_event_serialization() {
        let event = AuditEvent::document_indexed("research.pdf".to_string());
        let json = serde_json::to_string(&event).unwrap();
        let deserialized: AuditEvent = serde_json::from_str(&json).unwrap();
        assert_eq!(event.doc_path, deserialized.doc_path);
        assert_eq!(event.kind, deserialized.kind);
    }

    #[test]
    fn test_audit_log_event() {
        let event = AuditEvent::search_performed(
            "search_test.pdf".to_string(),
            "test query".to_string(),
            5,
        );
        assert_eq!(event.doc_path, "search_test.pdf");
    }
}
