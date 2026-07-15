use crate::error::Result;
use serde::{Deserialize, Serialize};
use std::fs::OpenOptions;
use std::io::Write;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AuditEventKind {
    DocumentOpened,
    DocumentIndexed,
    SearchPerformed { query: String, results_count: usize },
    ContextRetrieved { query: String, tokens: u32 },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEvent {
    pub timestamp: String,
    pub doc_path: String,
    pub kind: AuditEventKind,
}

/// Audit log that appends events as JSON lines.
pub struct AuditLog {
    path: String,
}

impl AuditLog {
    pub fn new<P: AsRef<Path>>(path: P) -> Self {
        AuditLog {
            path: path.as_ref().to_string_lossy().to_string(),
        }
    }

    /// Record an audit event (append as JSON line).
    pub fn record(&self, event: AuditEvent) -> Result<()> {
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)
            .map_err(crate::error::Error::Io)?;

        let json_line = serde_json::to_string(&event)
            .map_err(|e| crate::error::Error::Pdf(format!("JSON serialization failed: {}", e)))?;

        writeln!(file, "{}", json_line)
            .map_err(crate::error::Error::Io)?;

        Ok(())
    }

    /// Read all audit events from the log.
    pub fn events(&self) -> Result<Vec<AuditEvent>> {
        let content = std::fs::read_to_string(&self.path)
            .map_err(crate::error::Error::Io)?;

        let mut events = Vec::new();
        for line in content.lines() {
            if !line.trim().is_empty() {
                let event: AuditEvent = serde_json::from_str(line)
                    .map_err(|e| crate::error::Error::Pdf(format!("JSON parse failed: {}", e)))?;
                events.push(event);
            }
        }

        Ok(events)
    }
}
