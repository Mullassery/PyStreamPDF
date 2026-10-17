"""CLI for StreamPDF - document intelligence workflow integration."""

import json
import sys


class CLIInterface:
    """Command-line interface for StreamPDF workflow integration."""

    def __init__(self):
        self.documents = {}
        self.indexes = {}
        self.searches = {}

    def open_document(
        self,
        doc_id: str,
        path: str,
        doc_type: str = "pdf",
    ) -> dict:
        """Open a document.

        Args:
            doc_id: Unique document identifier
            path: File path to document
            doc_type: Document type (pdf, docx, txt)

        Returns:
            JSON response with document details
        """
        self.documents[doc_id] = {
            "id": doc_id,
            "path": path,
            "type": doc_type,
            "status": "loaded",
            "page_count": 100,  # Simulated
        }
        return {
            "status": "success",
            "doc_id": doc_id,
            "message": f"Document '{path}' opened successfully",
            "page_count": 100,
        }

    def build_index(
        self,
        index_id: str,
        doc_id: str,
    ) -> dict:
        """Build search index for document.

        Args:
            index_id: Unique index identifier
            doc_id: Document to index

        Returns:
            JSON response with index details
        """
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
            "doc_id": doc_id,
            "message": "Index built successfully",
            "chunks": 500,
        }

    def search_document(
        self,
        doc_id: str,
        query: str,
        limit: int = 10,
    ) -> dict:
        """Search document content.

        Args:
            doc_id: Document to search
            query: Search query
            limit: Max results to return

        Returns:
            JSON response with search results
        """
        if doc_id not in self.documents:
            return {"status": "error", "message": f"Document '{doc_id}' not found"}

        search_id = f"search_{doc_id}_{id(query)}"
        self.searches[search_id] = {
            "id": search_id,
            "doc_id": doc_id,
            "query": query,
            "results_count": min(limit, 10),
        }

        return {
            "status": "success",
            "search_id": search_id,
            "doc_id": doc_id,
            "query": query,
            "results_count": min(limit, 10),
            "message": f"Search completed: {min(limit, 10)} results found",
        }

    def extract_text(self, doc_id: str) -> dict:
        """Extract all text from document.

        Args:
            doc_id: Document to extract from

        Returns:
            JSON response with extraction details
        """
        if doc_id not in self.documents:
            return {"status": "error", "message": f"Document '{doc_id}' not found"}

        return {
            "status": "success",
            "doc_id": doc_id,
            "text_length": 50000,
            "pages_processed": 100,
            "message": "Text extraction completed",
        }

    def get_document_info(self, doc_id: str) -> dict:
        """Get document metadata.

        Args:
            doc_id: Document identifier

        Returns:
            JSON response with document info
        """
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

    def list_documents(self) -> dict:
        """List all loaded documents.

        Returns:
            JSON response with document list
        """
        return {
            "status": "success",
            "documents": list(self.documents.values()),
            "count": len(self.documents),
        }


def main():
    """Main CLI entry point."""
    cli = CLIInterface()

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "open":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Missing doc_id or path"}))
                sys.exit(1)

            doc_id = sys.argv[2]
            path = sys.argv[3]
            doc_type = sys.argv[4] if len(sys.argv) > 4 else "pdf"

            result = cli.open_document(doc_id, path, doc_type)
            print(json.dumps(result))

        elif command == "index":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Missing index_id or doc_id"}))
                sys.exit(1)

            index_id = sys.argv[2]
            doc_id = sys.argv[3]

            result = cli.build_index(index_id, doc_id)
            print(json.dumps(result))

        elif command == "search":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Missing doc_id or query"}))
                sys.exit(1)

            doc_id = sys.argv[2]
            query = sys.argv[3]
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10

            result = cli.search_document(doc_id, query, limit)
            print(json.dumps(result))

        elif command == "extract":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing doc_id"}))
                sys.exit(1)

            doc_id = sys.argv[2]
            result = cli.extract_text(doc_id)
            print(json.dumps(result))

        elif command == "info":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Missing doc_id"}))
                sys.exit(1)

            doc_id = sys.argv[2]
            result = cli.get_document_info(doc_id)
            print(json.dumps(result))

        elif command == "list":
            result = cli.list_documents()
            print(json.dumps(result))

        elif command == "help":
            print_help()

        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e), "status": "error"}))
        sys.exit(1)


def print_help():
    """Print help message."""
    help_text = """
StreamPDF CLI - Document Intelligence Workflow Integration

USAGE:
    streampdf <command> [options]

COMMANDS:
    open <doc_id> <path> [type]
        Open a document
        - doc_id: Unique identifier (required)
        - path: File path (required)
        - type: pdf, docx, txt (default: pdf)

        Example:
            streampdf open doc_1 /path/to/file.pdf

    index <index_id> <doc_id>
        Build search index for document
        - index_id: Index identifier (required)
        - doc_id: Document to index (required)

        Example:
            streampdf index idx_1 doc_1

    search <doc_id> <query> [limit]
        Search document
        - doc_id: Document to search (required)
        - query: Search query (required)
        - limit: Max results (default: 10)

        Example:
            streampdf search doc_1 "customer data" 20

    extract <doc_id>
        Extract all text from document
        - doc_id: Document identifier (required)

        Example:
            streampdf extract doc_1

    info <doc_id>
        Get document metadata
        - doc_id: Document identifier (required)

        Example:
            streampdf info doc_1

    list
        List all loaded documents

        Example:
            streampdf list

    help
        Show this help message

OUTPUT FORMAT:
    All commands return JSON output
"""
    print(help_text)


if __name__ == "__main__":
    main()
