"""Verify PyStreamPDF actually uses StatGuardian's canonical MCP base.

PyStreamPDF keeps a local fallback for older installs, but when StatGuardian
is importable the shared base must be the implementation in use.
"""

import pytest

from pystreampdf._mcp_connector import PDFProcessor, _MCPPDFConnector


def test_shared_base_is_used_when_statguardian_is_installed():
    shared = pytest.importorskip("statguardian._mcp_connector")

    from pystreampdf import _mcp_connector as pystreampdf_connector

    assert pystreampdf_connector.BaseMCPConnector is shared.BaseMCPConnector


def test_connector_generates_secure_shared_config():
    shared = pytest.importorskip("statguardian._mcp_connector")

    connector = _MCPPDFConnector(PDFProcessor(), port=9124)

    assert isinstance(connector, shared.BaseMCPConnector)
    assert connector.host == "127.0.0.1"
    assert connector.cors_origins == []

    config = connector._generate_dab_config({"tool_a": {}})
    assert config["runtime"] == {
        "host": "127.0.0.1",
        "port": 9124,
        "cors": {"origins": []},
    }
    assert config["entities"]["tool_a"]["permissions"] == [
        {"actions": ["read"], "roles": ["local"]}
    ]


def test_connector_rejects_remote_bind_without_opt_in():
    pytest.importorskip("statguardian._mcp_connector")

    with pytest.raises(ValueError, match="allow_remote=True"):
        _MCPPDFConnector(PDFProcessor(), port=9124, host="0.0.0.0")
