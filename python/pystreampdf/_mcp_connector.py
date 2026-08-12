"""MCP Connector for PyStreamPDF - PDF Document Processing"""

import json
import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from statguardian._mcp_connector import BaseMCPConnector
except ImportError:
    class BaseMCPConnector(ABC):
        def __init__(
            self,
            project_name: str,
            port: int = 8765,
            host: str = "127.0.0.1",
            allow_remote: bool = False,
            cors_origins: Optional[list] = None,
        ):
            self.project_name = project_name
            self.port = port
            # Secure-by-default: bind to loopback only. Binding to all interfaces
            # (e.g. "0.0.0.0") requires an explicit opt-in via `allow_remote=True`,
            # since this connector has no authentication of its own.
            if host in ("0.0.0.0", "::") and not allow_remote:
                raise ValueError(
                    "Binding the MCP/DAB connector to all interfaces "
                    f"(host={host!r}) requires allow_remote=True. By default the "
                    "connector only binds to 127.0.0.1."
                )
            self.host = host
            self.allow_remote = allow_remote
            # CORS defaults to no cross-origin access; wildcard origins must be
            # requested explicitly and only take effect when allow_remote=True.
            if cors_origins is None:
                cors_origins = [] if not allow_remote else ["*"]
            self.cors_origins = cors_origins
            self.dab_process: Optional[subprocess.Popen] = None
            self._ready = False

        @abstractmethod
        def get_mcp_tools(self) -> Dict[str, Any]:
            pass

        @abstractmethod
        def get_tool_handlers(self) -> Any:
            pass

        def start_mcp_connector(self) -> str:
            logger.info(f"Starting {self.project_name} MCP...")
            try:
                tools = self.get_mcp_tools()
                self.handler = self.get_tool_handlers()
                config = self._generate_dab_config(tools)
                config_path = self._write_temp_config(config)
                self._start_dab_subprocess(config_path)
                self._ready = True
                return f"http://localhost:{self.port}/mcp"
            except Exception as e:
                logger.error(f"Failed: {e}")
                raise

        def stop_mcp_connector(self):
            if self.dab_process:
                try:
                    self.dab_process.terminate()
                    self.dab_process.wait(timeout=5)
                except (subprocess.TimeoutExpired, OSError):
                    pass
                self._ready = False

        def _generate_dab_config(self, tools: Dict[str, Any]) -> Dict:
            # Secure defaults: loopback-only host, no cross-origin access, and
            # permissions scoped to a "local" role rather than wildcard "*"/"*".
            # Callers that genuinely need remote access or wildcard permissions
            # must opt in explicitly via allow_remote=True / cors_origins=[...].
            permissions_role = "*" if self.allow_remote else "local"
            permissions_actions = ["*"] if self.allow_remote else ["read"]
            return {
                "runtime": {
                    "host": self.host,
                    "port": self.port,
                    "cors": {"origins": self.cors_origins},
                },
                "entities": {
                    k: {
                        "source": k,
                        "permissions": [
                            {"actions": permissions_actions, "roles": [permissions_role]}
                        ],
                    }
                    for k in tools.keys()
                },
                "rest": {"enabled": True, "path": "/api"},
                "graphql": {"enabled": True, "path": "/graphql"},
                "mcp": {"enabled": True, "path": "/mcp"},
            }

        def _write_temp_config(self, config: Dict) -> str:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config, f)
                return f.name

        def _start_dab_subprocess(self, config_path: str):
            self.dab_process = subprocess.Popen(
                ["dab", "start", "--config", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        def is_ready(self) -> bool:
            return self._ready


class PDFProcessor:
    """PDF document processing with extraction and OCR"""

    def __init__(self):
        self.mcp_connector: Optional[Any] = None

    def start_mcp_connector(
        self,
        port: int = 8780,
        host: str = "127.0.0.1",
        allow_remote: bool = False,
        cors_origins: Optional[list] = None,
    ) -> str:
        """Start the local MCP/DAB connector.

        Binds to 127.0.0.1 with no cross-origin access by default. Pass
        ``allow_remote=True`` (and optionally an explicit ``host`` /
        ``cors_origins``) to expose the connector beyond localhost — this
        connector has no authentication of its own, so widening exposure is
        an explicit, deliberate choice for the caller.
        """
        from pystreampdf._mcp_tools import PyStreamPDFMCPHandler, PyStreamPDFMCPTools
        self.mcp_connector = _MCPPDFConnector(
            pdf=self,
            port=port,
            host=host,
            allow_remote=allow_remote,
            cors_origins=cors_origins,
        )
        return self.mcp_connector.start_mcp_connector()

    def stop_mcp_connector(self):
        if self.mcp_connector:
            self.mcp_connector.stop_mcp_connector()


class _MCPPDFConnector(BaseMCPConnector):
    def __init__(
        self,
        pdf: PDFProcessor,
        port: int = 8780,
        host: str = "127.0.0.1",
        allow_remote: bool = False,
        cors_origins: Optional[list] = None,
    ):
        super().__init__(
            "PyStreamPDF",
            port=port,
            host=host,
            allow_remote=allow_remote,
            cors_origins=cors_origins,
        )
        self.pdf = pdf

    def get_mcp_tools(self) -> Dict[str, Any]:
        from pystreampdf._mcp_tools import PyStreamPDFMCPTools
        return PyStreamPDFMCPTools.get_tools()

    def get_tool_handlers(self) -> Any:
        from pystreampdf._mcp_tools import PyStreamPDFMCPHandler
        return PyStreamPDFMCPHandler(self.pdf)
