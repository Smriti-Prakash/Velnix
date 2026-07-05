# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from google.adk.tools import McpToolset, FunctionTool
from google.adk.tools.base_toolset import BaseToolset
from mcp import StdioServerParameters

_vendor_toolset = None


def create_vendor_toolset() -> BaseToolset:
    """Factory to create and cache the production McpToolset."""
    global _vendor_toolset
    if _vendor_toolset is None:
        if os.environ.get("VELNIX_USE_MOCK_MCP") == "1":
            _vendor_toolset = MockVendorToolset()
        else:
            _mcp_env = os.environ.copy()
            _mcp_env["PYTHONPATH"] = os.getcwd() + os.pathsep + _mcp_env.get("PYTHONPATH", "")

            _venv_python = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
            if not os.path.exists(_venv_python):
                _venv_python = os.path.join(os.getcwd(), ".venv", "bin", "python")
            if not os.path.exists(_venv_python):
                _venv_python = sys.executable

            _vendor_toolset = McpToolset(
                connection_params=StdioServerParameters(
                    command=_venv_python,
                    args=["app/mcp/server.py"],
                    env=_mcp_env,
                    cwd=os.getcwd(),
                )
            )
    return _vendor_toolset


class MockVendorToolset(BaseToolset):
    """A clean mock toolset that wraps the FastMCP server functions directly.
    
    This bypasses spawning the Stdio subprocess during tests while keeping
    the exact same tool names, signatures, and internal execution paths active.
    """
    def __init__(self, *args, **kwargs):
        super().__init__()

    async def get_tools(self, readonly_context=None):
        from app.mcp.server import (
            get_vendor_profile,
            get_purchase_order,
            get_goods_receipt,
            get_invoice_history,
            find_duplicate_invoice,
            submit_investigation_result,
            list_pending_invoices,
        )
        return [
            FunctionTool(get_vendor_profile),
            FunctionTool(get_purchase_order),
            FunctionTool(get_goods_receipt),
            FunctionTool(get_invoice_history),
            FunctionTool(find_duplicate_invoice),
            FunctionTool(submit_investigation_result),
            FunctionTool(list_pending_invoices),
        ]

    async def close(self) -> None:
        pass
