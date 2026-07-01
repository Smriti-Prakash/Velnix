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

import json
import pytest
from app.mcp.server import mcp_server


@pytest.mark.asyncio
async def test_mcp_get_vendor_profile():
    """Verify that get_vendor_profile tool behaves correctly on the MCP server."""
    res = await mcp_server.call_tool("get_vendor_profile", {"vendor_name": "Acme Corp"})
    # Returns a list of TextContent
    parsed = json.loads(res[0].text)
    assert parsed["vendor_name"] == "Acme Corp"
    assert parsed["vendor_status"] == "Trusted"
    assert parsed["trust_score"] == 95
    assert parsed["last_bank_account_change"] == "2025-12-01"


@pytest.mark.asyncio
async def test_mcp_find_duplicate_invoice():
    """Verify that find_duplicate_invoice tool correctly flags duplicates from CSV history."""
    res_1 = await mcp_server.call_tool("find_duplicate_invoice", {"invoice_number": "INV-2026-001"})
    # Returns a tuple of (content_list, output_dict) where output_dict contains 'result'
    assert res_1[1]["result"] is True

    res_2 = await mcp_server.call_tool("find_duplicate_invoice", {"invoice_number": "INV-NEW-UNIQUE-999"})
    assert res_2[1]["result"] is False


@pytest.mark.asyncio
async def test_mcp_submit_investigation_result():
    """Verify that submit_investigation_result returns success dictionary when called with authorized role."""
    res = await mcp_server.call_tool(
        "submit_investigation_result",
        {
            "invoice_number": "INV-2026-001",
            "recommendation": "REVIEW",
            "risk_score": 50,
            "fraud_score": 60,
            "role": "Finance Manager",
        }
    )
    # Returns a list of TextContent
    parsed = json.loads(res[0].text)
    assert parsed["invoice_number"] == "INV-2026-001"
    assert parsed["recommendation"] == "REVIEW"
    assert parsed["submitted"] is True


@pytest.mark.asyncio
async def test_mcp_list_pending_invoices():
    """Verify that list_pending_invoices returns a list of mock pending invoices when called with admin role."""
    res = await mcp_server.call_tool("list_pending_invoices", {"role": "Administrator"})
    # Returns a tuple of (content_list, output_dict)
    pending_list = res[1]["result"]
    assert isinstance(pending_list, list)
    assert len(pending_list) >= 2
    assert pending_list[0]["invoice_number"] == "INV-NEW-001"
    assert pending_list[0]["status"] == "Pending"
