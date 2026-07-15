use crate::document::PdfDocument;
use crate::error::{Error, Result};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PageResult {
    pub page_number: u32,
    pub score: f32,
    pub snippet: String,
}

pub struct PdfIndex {
    conn: Connection,
}

impl PdfIndex {
    pub fn build(doc: &PdfDocument, path: &str) -> Result<Self> {
        let conn = Connection::open(path)
            .map_err(|e| Error::DatabaseError(format!("Failed to open database: {}", e)))?;

        conn.execute_batch("PRAGMA foreign_keys = ON;")
            .map_err(|e| Error::DatabaseError(format!("Failed to set PRAGMA: {}", e)))?;

        // Create schema
        Self::create_schema(&conn)?;

        // Insert document metadata
        let doc_metadata = doc.metadata();
        let _doc_id = conn
            .execute(
                "INSERT INTO documents (path, page_count, title, author, indexed_at)
                 VALUES (?1, ?2, ?3, ?4, datetime('now'))
                 ON CONFLICT(path) DO UPDATE SET indexed_at = datetime('now')",
                params![
                    doc.path(),
                    doc_metadata.page_count,
                    doc_metadata.title,
                    doc_metadata.author,
                ],
            )
            .map_err(|e| Error::DatabaseError(format!("Failed to insert document: {}", e)))?;

        // Get the actual doc_id for future use
        let doc_id: i64 = conn
            .query_row(
                "SELECT id FROM documents WHERE path = ?1",
                params![doc.path()],
                |row| row.get(0),
            )
            .map_err(|e| Error::DatabaseError(format!("Failed to fetch doc_id: {}", e)))?;

        // Insert pages and build FTS index
        let pages = doc.all_pages()?;
        for page in pages {
            conn.execute(
                "INSERT INTO pages (doc_id, page_num, width, height, rotation, word_count, text_preview, full_text)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
                params![
                    doc_id,
                    page.page_number,
                    page.width,
                    page.height,
                    page.rotation,
                    page.word_count,
                    page.text_preview,
                    page.text,
                ],
            )
            .map_err(|e| Error::DatabaseError(format!("Failed to insert page: {}", e)))?;
        }

        // Insert headings
        let structure = doc.structure()?;
        for heading in structure.headings {
            conn.execute(
                "INSERT INTO headings (doc_id, page_num, level, text)
                 VALUES (?1, ?2, ?3, ?4)",
                params![doc_id, heading.page_number, heading.level, heading.text],
            )
            .map_err(|e| Error::DatabaseError(format!("Failed to insert heading: {}", e)))?;
        }

        Ok(PdfIndex { conn })
    }

    pub fn load(path: &str) -> Result<Self> {
        let conn = Connection::open(path)
            .map_err(|e| Error::DatabaseError(format!("Failed to open database: {}", e)))?;

        conn.execute_batch("PRAGMA foreign_keys = ON;")
            .map_err(|e| Error::DatabaseError(format!("Failed to set PRAGMA: {}", e)))?;

        Ok(PdfIndex { conn })
    }

    pub fn search(&self, query: &str, top_k: usize) -> Result<Vec<PageResult>> {
        let mut stmt = self
            .conn
            .prepare(
                "SELECT p.page_num, bm25(pages_fts) as score,
                        snippet(pages_fts, 0, '[', ']', '...', 15) as snip
                 FROM pages_fts
                 JOIN pages p ON pages_fts.rowid = p.id
                 WHERE pages_fts MATCH ?1
                 ORDER BY score
                 LIMIT ?2",
            )
            .map_err(|e| Error::DatabaseError(format!("Failed to prepare statement: {}", e)))?;

        let results = stmt
            .query_map(params![query, top_k], |row| {
                Ok(PageResult {
                    page_number: row.get(0)?,
                    score: -row.get::<_, f32>(1)?, // BM25 returns negative scores
                    snippet: row.get(2)?,
                })
            })
            .map_err(|e| Error::DatabaseError(format!("Query execution failed: {}", e)))?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(|e| Error::DatabaseError(format!("Failed to collect results: {}", e)))?;

        Ok(results)
    }

    pub fn pages_with_heading(&self, heading: &str) -> Result<Vec<PageResult>> {
        let pattern = format!("%{}%", heading);
        let mut stmt = self
            .conn
            .prepare(
                "SELECT DISTINCT page_num, 0.0 as score, text as snippet
                 FROM headings
                 WHERE text LIKE ?1",
            )
            .map_err(|e| Error::DatabaseError(format!("Failed to prepare statement: {}", e)))?;

        let results = stmt
            .query_map(params![pattern], |row| {
                Ok(PageResult {
                    page_number: row.get(0)?,
                    score: row.get(1)?,
                    snippet: row.get(2)?,
                })
            })
            .map_err(|e| Error::DatabaseError(format!("Query execution failed: {}", e)))?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(|e| Error::DatabaseError(format!("Failed to collect results: {}", e)))?;

        Ok(results)
    }

    pub fn page_range(&self, start: u32, end: u32) -> Result<Vec<PageResult>> {
        let mut stmt = self
            .conn
            .prepare(
                "SELECT page_num, 0.0 as score, text_preview as snippet
                 FROM pages
                 WHERE page_num >= ?1 AND page_num <= ?2
                 ORDER BY page_num",
            )
            .map_err(|e| Error::DatabaseError(format!("Failed to prepare statement: {}", e)))?;

        let results = stmt
            .query_map(params![start, end], |row| {
                Ok(PageResult {
                    page_number: row.get(0)?,
                    score: row.get(1)?,
                    snippet: row.get(2)?,
                })
            })
            .map_err(|e| Error::DatabaseError(format!("Query execution failed: {}", e)))?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(|e| Error::DatabaseError(format!("Failed to collect results: {}", e)))?;

        Ok(results)
    }

    fn create_schema(conn: &Connection) -> Result<()> {
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                path        TEXT NOT NULL UNIQUE,
                page_count  INTEGER NOT NULL,
                title       TEXT,
                author      TEXT,
                indexed_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pages (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id       INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                page_num     INTEGER NOT NULL,
                width        REAL,
                height       REAL,
                rotation     INTEGER DEFAULT 0,
                word_count   INTEGER DEFAULT 0,
                text_preview TEXT DEFAULT '',
                full_text    TEXT DEFAULT '',
                UNIQUE(doc_id, page_num)
            );

            CREATE TABLE IF NOT EXISTS headings (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id   INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                page_num INTEGER NOT NULL,
                level    INTEGER NOT NULL,
                text     TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                full_text,
                content='pages',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
                INSERT INTO pages_fts(rowid, full_text) VALUES (new.id, new.full_text);
            END;",
        )
        .map_err(|e| {
            Error::DatabaseError(format!("Failed to create schema: {}", e))
        })
    }
}
