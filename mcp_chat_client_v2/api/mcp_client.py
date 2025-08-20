import os
from typing import Dict, Any, List, Optional
import requests

LEAVE_MCP_URL = os.getenv("LEAVE_MCP_URL", "http://localhost:8011/mcp").rstrip("/")
TIMESHEET_MCP_URL = os.getenv("TIMESHEET_MCP_URL", "http://localhost:8012/mcp").rstrip("/")

class MCPServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        # Detect if the provided base already includes the /mcp prefix.
        self._base_has_mcp = self.base_url.endswith("/mcp")
        # Persist cookies/headers across calls (needed for streamable-http sessions)
        self._session = requests.Session()
        self._active_base: Optional[str] = None
        # Accept header required by streamable-http
        self._headers: Dict[str, str] = {"Accept": "application/json, text/event-stream"}
        # Simple JSON-RPC id counter
        self._rpc_id = 0
        token = os.getenv("MCP_PROXY_TOKEN")
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def _candidate_bases(self) -> List[str]:
        """
        Return candidate base URLs to try. If the configured base ends with /mcp,
        try it first, then the root (without /mcp). If not, try root first,
        then append /mcp as a fallback. This makes the client compatible with
        both FastMCP streamable-http (which commonly mounts under /mcp) and
        servers that mount at root.
        """
        if self._base_has_mcp:
            return [self.base_url, self.base_url[:-4]]  # drop '/mcp'
        else:
            return [self.base_url, f"{self.base_url}/mcp"]

    def _get(self, path: str, params: Dict[str, Any] | None = None):
        last_exc: Optional[Exception] = None
        for base in ([self._active_base] if self._active_base else []) + self._candidate_bases():
            if not base:
                continue
            url = f"{base}{path}"
            try:
                r = self._session.get(url, params=params, headers=self._headers, timeout=20)
                r.raise_for_status()
                self._active_base = base
                return r.json()
            except requests.HTTPError as e:
                # Retry on 404 by trying the next base; rethrow for others
                if getattr(e.response, "status_code", None) == 404:
                    last_exc = e
                    continue
                raise
        # If all candidates failed with 404, raise the last
        if last_exc:
            raise last_exc
        # Fallback safety
        raise requests.HTTPError("Failed to GET from all base URL candidates")

    def _init_session_for_base(self, base: str) -> None:
        """For streamable-http, POST to the base /mcp root to establish a session (cookie)."""
        try:
            # If base already ends with /mcp, hit it directly; otherwise, hit base + /mcp
            session_url = base if base.endswith("/mcp") else f"{base}/mcp"
            # Empty JSON body is acceptable for session init
            self._session.post(session_url, json={}, headers=self._headers, timeout=10)
        except Exception:
            # Non-fatal: some servers don't require explicit session init
            pass

    def _post(self, path: str, payload: Dict[str, Any] | None = None):
        last_exc: Optional[Exception] = None
        # Try an already active base first for sticky routing
        bases = ([self._active_base] if self._active_base else []) + self._candidate_bases()
        seen = set()
        for base in [b for b in bases if b and (b not in seen and not seen.add(b))]:
            url = f"{base}{path}"
            try:
                # Ensure session before calling (harmless if not needed)
                self._init_session_for_base(base)
                r = self._session.post(url, json=payload or {}, headers=self._headers, timeout=30)
                r.raise_for_status()
                self._active_base = base
                return r.json()
            except requests.HTTPError as e:
                if getattr(e.response, "status_code", None) == 404:
                    # Attempt JSON-RPC fallback to /mcp if specialized endpoint is not present
                    rpc_method, rpc_params = self._map_path_to_rpc(path, payload)
                    if rpc_method:
                        try:
                            data = self._rpc_call(base, rpc_method, rpc_params)
                            self._active_base = base
                            return data
                        except Exception:
                            pass
                    last_exc = e
                    continue
                raise
        if last_exc:
            raise last_exc
        raise requests.HTTPError("Failed to POST to all base URL candidates")

    def _rpc_call(self, base: str, method: str, params: Dict[str, Any] | None) -> Dict[str, Any]:
        # Ensure URL points at /mcp root
        rpc_url = base if base.endswith("/mcp") else f"{base}/mcp"
        self._rpc_id += 1
        body = {"jsonrpc": "2.0", "id": self._rpc_id, "method": method, "params": params or {}}
        # Ensure session exists
        self._init_session_for_base(base)
        r = self._session.post(rpc_url, json=body, headers=self._headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        # Return result portion if present
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data

    @staticmethod
    def _map_path_to_rpc(path: str, payload: Dict[str, Any] | None) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Map specialized endpoint paths to JSON-RPC method names used by streamable-http servers."""
        payload = payload or {}
        if path == "/tools/list":
            return "tools/list", {}
        if path == "/prompts/list":
            return "prompts/list", {}
        if path == "/resources/list":
            return "resources/list", {}
        if path == "/tools/call":
            # Expect payload { name, arguments }
            return "tools/call", payload
        if path == "/prompts/get":
            return "prompts/get", payload
        if path == "/resources/read":
            return "resources/read", payload
        return None, None

    async def list_tools(self) -> List[Dict[str, Any]]:
        # FastMCP streamable-http uses POST for list operations
        data = self._post("/tools/list")
        return data.get("tools", [])

    async def list_prompts(self) -> List[Dict[str, Any]]:
        data = self._post("/prompts/list")
        return data.get("prompts", [])

    async def list_resources(self) -> List[Dict[str, Any]]:
        data = self._post("/resources/list")
        return data.get("resources", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # FastMCP streamable-http: POST /mcp/tools/call with { name, arguments }
        return self._post("/tools/call", payload={"name": name, "arguments": arguments or {}})

    async def get_prompt(self, name: str, arguments: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self._post("/prompts/get", payload={"name": name, "arguments": arguments or {}})

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        return self._post("/resources/read", payload={"uri": uri})


leave_client = MCPServiceClient(LEAVE_MCP_URL)
_timesheet_client = MCPServiceClient(TIMESHEET_MCP_URL)

def get_client(server: str) -> MCPServiceClient:
    return leave_client if server == "leave" else _timesheet_client
