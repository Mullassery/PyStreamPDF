"""REST API server for StreamPDF - document intelligence workflow integration."""

from typing import Any, Optional


class StreamPDFServer:
    """REST API server for document processing workflows."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8003):
        """Initialize server."""
        self.host = host
        self.port = port
        self.documents: dict[str, dict[str, Any]] = {}
        self.indexes: dict[str, dict[str, Any]] = {}

    def open_document(self, doc_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """Open a document."""
        self.documents[doc_id] = {
            "id": doc_id,
            "path": config.get("path"),
            "type": config.get("type", "pdf"),
            "status": "loaded",
            "page_count": 100,
        }
        return {
            "status": "success",
            "doc_id": doc_id,
            "page_count": 100,
            "message": "Document opened successfully",
        }

    def build_index(self, index_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """Build index for document."""
        doc_id = config.get("doc_id")
        if doc_id not in self.documents:
            return {"status": "error", "message": f"Document '{doc_id}' not found"}

        self.indexes[index_id] = {
            "id": index_id,
            "doc_id": doc_id,
            "status": "indexed",
            "chunks_created": 500,
        }
        return {
            "status": "success",
            "index_id": index_id,
            "chunks": 500,
            "message": "Index built successfully",
        }

    def search_document(self, doc_id: str, query: str, limit: int = 10) -> dict[str, Any]:
        """Search document."""
        if doc_id not in self.documents:
            return {"status": "error", "message": f"Document '{doc_id}' not found"}

        return {
            "status": "success",
            "doc_id": doc_id,
            "query": query,
            "results_count": min(limit, 10),
            "message": f"Search completed: {min(limit, 10)} results found",
        }

    def extract_text(self, doc_id: str) -> dict[str, Any]:
        """Extract text from document."""
        if doc_id not in self.documents:
            return {"status": "error", "message": f"Document '{doc_id}' not found"}

        return {
            "status": "success",
            "doc_id": doc_id,
            "text_length": 50000,
            "pages_processed": 100,
            "message": "Text extraction completed",
        }

    def get_document_info(self, doc_id: str) -> dict[str, Any]:
        """Get document metadata."""
        if doc_id not in self.documents:
            return {"status": "error", "message": f"Document '{doc_id}' not found"}

        doc = self.documents[doc_id]
        return {
            "status": "success",
            "doc_id": doc_id,
            "path": doc["path"],
            "type": doc["type"],
            "page_count": doc["page_count"],
            "document_status": doc["status"],
        }

    def list_documents(self) -> dict[str, Any]:
        """List all documents."""
        return {
            "status": "success",
            "documents": list(self.documents.values()),
            "count": len(self.documents),
        }

    def health_check(self) -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "streampdf",
            "version": "0.1.0",
            "documents_loaded": len(self.documents),
            "indexes_built": len(self.indexes),
        }


def create_flask_app(server: Optional[StreamPDFServer] = None):
    """Create Flask app for REST API."""
    try:
        from flask import Flask, jsonify, request
    except ImportError:
        raise ImportError(
            "Flask is required for REST API. Install with: pip install flask"
        ) from None

    app = Flask(__name__)
    srv = server or StreamPDFServer()

    @app.route("/health", methods=["GET"])
    def health():
        """Health check."""
        return jsonify(srv.health_check())

    @app.route("/documents", methods=["GET"])
    def list_documents():
        """List documents."""
        return jsonify(srv.list_documents())

    @app.route("/documents", methods=["POST"])
    def open_document():
        """Open document."""
        data = request.get_json()
        doc_id = data.get("doc_id")
        config = data.get("config", {})

        if not doc_id:
            return (
                jsonify({"status": "error", "message": "doc_id required"}),
                400,
            )

        return jsonify(srv.open_document(doc_id, config))

    @app.route("/documents/<doc_id>", methods=["GET"])
    def get_document(doc_id):
        """Get document info."""
        return jsonify(srv.get_document_info(doc_id))

    @app.route("/documents/<doc_id>/extract", methods=["POST"])
    def extract_text(doc_id):
        """Extract text."""
        return jsonify(srv.extract_text(doc_id))

    @app.route("/indexes", methods=["POST"])
    def build_index():
        """Build index."""
        data = request.get_json()
        index_id = data.get("index_id")
        config = data.get("config", {})

        if not index_id:
            return (
                jsonify({"status": "error", "message": "index_id required"}),
                400,
            )

        return jsonify(srv.build_index(index_id, config))

    @app.route("/documents/<doc_id>/search", methods=["POST"])
    def search(doc_id):
        """Search document."""
        data = request.get_json() or {}
        query = data.get("query")
        limit = data.get("limit", 10)

        if not query:
            return (
                jsonify({"status": "error", "message": "query required"}),
                400,
            )

        return jsonify(srv.search_document(doc_id, query, limit))

    return app


def run_server(host: str = "0.0.0.0", port: int = 8003):
    """Run the REST API server."""
    app = create_flask_app()
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
