"""SQL content intelligence and validation."""

import re
from typing import Dict, List, Optional, Set

from .types import IntelligenceResult


class SQLAnalyzer:
    """Analyzes SQL queries for dialect, syntax, and structure."""

    KEYWORDS = {
        "select": {"select", "from", "where", "join", "group by", "order by"},
        "insert": {"insert", "into", "values"},
        "update": {"update", "set", "where"},
        "delete": {"delete", "from", "where"},
        "create": {"create", "table", "index", "view", "database"},
        "alter": {"alter", "table", "column", "add", "drop", "modify"},
        "drop": {"drop", "table", "index", "view", "database"},
        "transactions": {"begin", "commit", "rollback", "savepoint"},
    }

    DIALECTS = {
        "postgresql": {"RETURNING", "::text", "->", "->>", "jsonb", "serial", "uuid", "interval"},
        "mysql": {"LIMIT", "AUTO_INCREMENT", "CHARSET", "COLLATE", "UNSIGNED", "ENUM"},
        "sqlite": {"AUTOINCREMENT", "INTEGER PRIMARY KEY", "WITHOUT ROWID", "PRAGMA"},
        "tsql": {"SELECT TOP", "NVARCHAR", "VARCHAR(MAX)", "DECLARE", "@@", "dbo."},
        "oracle": {"CONNECT BY", "ROWNUM", "TO_DATE", "NUMBER", "VARCHAR2", "CLOB"},
    }

    def analyze(self, text: str) -> IntelligenceResult:
        """Analyze SQL content."""
        if not text or not text.strip():
            return IntelligenceResult(content_type="unknown", is_valid=True, confidence=0.0)

        issues = []
        metadata = {"line_count": len(text.split("\n"))}

        # Detect SQL dialect
        dialect = self._detect_dialect(text)
        metadata["dialect"] = dialect

        # Parse queries
        queries = self._parse_queries(text)
        metadata["query_count"] = len(queries)

        # Validate syntax
        for i, query in enumerate(queries):
            query_type = self._detect_query_type(query)
            if query_type:
                metadata.setdefault("query_types", []).append(query_type)

            # Check for common issues
            query_issues = self._validate_query(query)
            issues.extend(query_issues)

        # Extract structural info
        self._extract_structure(text, metadata)

        is_valid = len(issues) == 0
        confidence = 1.0 if is_valid else max(0.0, 1.0 - (len(issues) * 0.15))

        return IntelligenceResult(
            content_type="sql",
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            metadata=metadata
        )

    def _detect_dialect(self, text: str) -> str:
        """Detect SQL dialect from keywords and functions."""
        text_upper = text.upper()
        scores = {}

        for dialect, patterns in self.DIALECTS.items():
            score = sum(1 for pattern in patterns if pattern.upper() in text_upper)
            if score > 0:
                scores[dialect] = score

        if scores:
            return max(scores, key=scores.get)

        return "unknown"

    def _parse_queries(self, text: str) -> List[str]:
        """Split text into individual SQL queries."""
        # Split by semicolon, but respect quoted strings
        queries = []
        current = []
        in_quote = False
        quote_char = None

        for char in text:
            if char in ("'", '"') and (not in_quote or quote_char == char):
                in_quote = not in_quote
                quote_char = char if in_quote else None
            elif char == ";" and not in_quote:
                query = "".join(current).strip()
                if query:
                    queries.append(query)
                current = []
                continue

            current.append(char)

        # Add final query
        query = "".join(current).strip()
        if query:
            queries.append(query)

        return queries

    def _detect_query_type(self, query: str) -> Optional[str]:
        """Detect the type of SQL query."""
        query_upper = query.strip().upper()

        if query_upper.startswith("SELECT"):
            return "SELECT"
        if query_upper.startswith("INSERT"):
            return "INSERT"
        if query_upper.startswith("UPDATE"):
            return "UPDATE"
        if query_upper.startswith("DELETE"):
            return "DELETE"
        if query_upper.startswith("CREATE"):
            return "CREATE"
        if query_upper.startswith("ALTER"):
            return "ALTER"
        if query_upper.startswith("DROP"):
            return "DROP"
        if query_upper.startswith(("BEGIN", "COMMIT", "ROLLBACK")):
            return "TRANSACTION"

        return None

    def _validate_query(self, query: str) -> List[str]:
        """Validate SQL query syntax."""
        issues = []
        query_upper = query.upper()

        # Check for missing WHERE in UPDATE/DELETE
        if query_upper.startswith("UPDATE") and "WHERE" not in query_upper:
            issues.append("UPDATE query without WHERE clause may modify all rows")
        if query_upper.startswith("DELETE") and "WHERE" not in query_upper:
            issues.append("DELETE query without WHERE clause may delete all rows")

        # Check for balanced parentheses
        if not self._check_parentheses_balanced(query):
            issues.append("Unbalanced parentheses in query")

        # Check for unclosed string literals
        if not self._check_strings_closed(query):
            issues.append("Unclosed string literal")

        # Check for suspicious patterns
        if re.search(r"'\s+OR\s+'", query_upper):
            issues.append("Potential SQL injection pattern detected")

        return issues

    def _check_parentheses_balanced(self, text: str) -> bool:
        """Check if parentheses are balanced."""
        stack = 0
        in_string = False
        string_char = None

        for char in text:
            if char in ("'", '"') and (not in_string or string_char == char):
                in_string = not in_string
                string_char = char if in_string else None
                continue

            if in_string:
                continue

            if char == "(":
                stack += 1
            elif char == ")":
                stack -= 1
                if stack < 0:
                    return False

        return stack == 0

    def _check_strings_closed(self, text: str) -> bool:
        """Check if all string literals are closed."""
        in_single = False
        in_double = False

        i = 0
        while i < len(text):
            char = text[i]

            if char == "'" and (not in_double):
                if i + 1 < len(text) and text[i + 1] == "'":
                    i += 2
                    continue
                in_single = not in_single
            elif char == '"' and (not in_single):
                if i + 1 < len(text) and text[i + 1] == '"':
                    i += 2
                    continue
                in_double = not in_double

            i += 1

        return not (in_single or in_double)

    def _extract_structure(self, text: str, metadata: Dict) -> None:
        """Extract structural information from SQL."""
        text_upper = text.upper()

        # Find table names in FROM and JOIN clauses
        table_pattern = r"(?:FROM|JOIN)\s+([a-zA-Z0-9_\.]+)"
        tables = re.findall(table_pattern, text_upper)
        if tables:
            metadata["tables_referenced"] = list(set([t.split(".")[-1] for t in tables]))

        # Find column definitions
        column_pattern = r"([a-zA-Z0-9_]+)\s+(INT|VARCHAR|TEXT|BOOLEAN|TIMESTAMP|DECIMAL|UUID|JSONB|DATE)"
        columns = re.findall(column_pattern, text_upper)
        if columns:
            metadata["columns_defined"] = [c[0].lower() for c in columns]

        # Find join types
        join_types = set()
        if "INNER JOIN" in text_upper:
            join_types.add("INNER")
        if "LEFT JOIN" in text_upper or "LEFT OUTER JOIN" in text_upper:
            join_types.add("LEFT")
        if "RIGHT JOIN" in text_upper or "RIGHT OUTER JOIN" in text_upper:
            join_types.add("RIGHT")
        if "FULL JOIN" in text_upper or "FULL OUTER JOIN" in text_upper:
            join_types.add("FULL")
        if "CROSS JOIN" in text_upper:
            join_types.add("CROSS")

        if join_types:
            metadata["join_types"] = list(join_types)

        # Check for aggregates
        aggregates = set()
        for func in ["COUNT", "SUM", "AVG", "MAX", "MIN", "GROUP_CONCAT"]:
            if func in text_upper:
                aggregates.add(func)

        if aggregates:
            metadata["aggregate_functions"] = list(aggregates)

        # Check for subqueries
        if text_upper.count("SELECT") > 1:
            metadata["has_subqueries"] = True

        # Check for CTEs (Common Table Expressions)
        if "WITH" in text_upper and "AS" in text_upper:
            metadata["has_cte"] = True
