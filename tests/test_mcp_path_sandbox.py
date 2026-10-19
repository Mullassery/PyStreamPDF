"""PyStreamPDF MCP handler path sandbox.

The connector has no authentication of its own; ``allowed_root`` is the
enforceable boundary for MCP tool paths. This tests the boundary directly.
"""

from __future__ import annotations

import pytest

from pystreampdf._mcp_connector import PDFProcessor, _MCPPDFConnector
from pystreampdf._mcp_tools import PyStreamPDFMCPHandler


def test_allowed_root_allows_inside(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    pdf = root / "a.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    handler = PyStreamPDFMCPHandler(allowed_root=root)
    assert handler._check_path(str(pdf)) == pdf.resolve()


def test_allowed_root_rejects_outside(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "b.pdf"
    outside.write_bytes(b"%PDF-1.4\n")

    handler = PyStreamPDFMCPHandler(allowed_root=root)
    with pytest.raises(ValueError, match="outside allowed_root"):
        handler._check_path(str(outside))
    with pytest.raises(ValueError, match="outside allowed_root"):
        handler._open(str(outside))


def test_connector_propagates_allowed_root(tmp_path):
    connector = _MCPPDFConnector(PDFProcessor(), allowed_root=str(tmp_path))
    handler = connector.get_tool_handlers()
    assert handler.allowed_root == tmp_path.resolve()


def test_no_allowed_root_is_backwards_compatible(tmp_path):
    handler = PyStreamPDFMCPHandler()
    assert handler.allowed_root is None
    # Without a configured root, paths are not restricted (legacy behavior).
    assert handler._check_path(str(tmp_path / "x.pdf")).is_absolute()
