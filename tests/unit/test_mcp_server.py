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

"""Unit tests for the Velnix MCP server tools.

Each test calls the tool via ``mcp_server.call_tool()``, which exercises
the full RBAC + query path without spawning a subprocess.

The ERP database is redirected to a temporary in-memory path via the
``tmp_erp_db`` fixture so tests do not depend on or modify the production
erp.db file.
"""

import json
import pytest
import app.erp.database as db_module
from app.mcp.server import mcp_server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def tmp_erp_db(tmp_path, monkeypatch):
    """Redirect the ERP database to a fresh temp file for each test."""
    db_file = str(tmp_path / "test_erp.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    # Patch get_connection inside queries so it uses the temp path too
    import app.erp.queries as q_module
    monkeypatch.setattr(q_module, "get_connection", db_module.get_connection)
    db_module.init_db()


# ---------------------------------------------------------------------------
# get_vendor_profile
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_get_vendor_profile():
    """get_vendor_profile should return SQLite data for known vendors."""
    res = await mcp_server.call_tool("get_vendor_profile", {"vendor_name": "Acme Corp"})
    parsed = json.loads(res[0].text)
    assert parsed["vendor_name"] == "Acme Corp"
    assert parsed["vendor_status"] == "Trusted"
    assert parsed["trust_score"] == 95
    assert parsed["last_bank_account_change"] == "2025-12-01"
    assert parsed["vendor_id"] == 1
    assert parsed["previous_rejections"] == 1


@pytest.mark.asyncio
async def test_mcp_get_vendor_profile_unknown_returns_default():
    """get_vendor_profile should return a New/50 fallback for unknown vendors."""
    res = await mcp_server.call_tool("get_vendor_profile", {"vendor_name": "Ghost Vendor XYZ"})
    parsed = json.loads(res[0].text)
    assert parsed["vendor_status"] == "New"
    assert parsed["trust_score"] == 50
    assert parsed["total_previous_invoices"] == 0
    assert parsed["vendor_id"] is None


# ---------------------------------------------------------------------------
# get_purchase_order
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_get_purchase_order_found():
    """get_purchase_order should return the correct PO record."""
    res = await mcp_server.call_tool("get_purchase_order", {"purchase_order_number": "PO-2026-001"})
    parsed = json.loads(res[0].text)
    assert parsed["purchase_order_number"] == "PO-2026-001"
    assert parsed["vendor_id"] == 1
    assert parsed["vendor_name"] == "Acme Corp"
    assert parsed["status"] == "Open"
    assert parsed["approved_amount"] == 10000.00


@pytest.mark.asyncio
async def test_mcp_get_purchase_order_cancelled():
    """get_purchase_order should correctly report cancelled POs."""
    res = await mcp_server.call_tool("get_purchase_order", {"purchase_order_number": "PO-2026-011"})
    parsed = json.loads(res[0].text)
    assert parsed["status"] == "Cancelled"
    assert parsed["vendor_id"] == 9   # RiskCo LLC


@pytest.mark.asyncio
async def test_mcp_get_purchase_order_not_found():
    """get_purchase_order should return found=False for unknown PO numbers."""
    res = await mcp_server.call_tool("get_purchase_order", {"purchase_order_number": "PO-DOES-NOT-EXIST"})
    parsed = json.loads(res[0].text)
    assert parsed["found"] is False


# ---------------------------------------------------------------------------
# get_goods_receipt
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_get_goods_receipt_found():
    """get_goods_receipt should return receipts for a known PO."""
    res = await mcp_server.call_tool("get_goods_receipt", {"purchase_order_number": "PO-2026-001"})
    # FastMCP serializes list items as individual TextContent objects
    result = [json.loads(item.text) for item in res]
    assert len(result) >= 1
    assert result[0]["purchase_order_number"] == "PO-2026-001"
    assert result[0]["vendor_id"] == 1
    assert result[0]["status"] == "Complete"


@pytest.mark.asyncio
async def test_mcp_get_goods_receipt_empty():
    """get_goods_receipt should return an empty list for POs with no receipts."""
    res = await mcp_server.call_tool("get_goods_receipt", {"purchase_order_number": "PO-NO-RECEIPT"})
    result = [json.loads(item.text) for item in res]
    assert result == []


# ---------------------------------------------------------------------------
# get_invoice_history
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_get_invoice_history_found():
    """get_invoice_history should return historical invoices for Acme Corp."""
    res = await mcp_server.call_tool("get_invoice_history", {"vendor_name": "Acme Corp"})
    result = [json.loads(item.text) for item in res]
    assert len(result) >= 7
    assert all(r["vendor_id"] == 1 for r in result)


@pytest.mark.asyncio
async def test_mcp_get_invoice_history_includes_rejected():
    """get_invoice_history should include Rejected invoices for RiskCo LLC."""
    res = await mcp_server.call_tool("get_invoice_history", {"vendor_name": "RiskCo LLC"})
    result = [json.loads(item.text) for item in res]
    statuses = {r["status"] for r in result}
    assert "Rejected" in statuses


@pytest.mark.asyncio
async def test_mcp_get_invoice_history_empty_new_vendor():
    """get_invoice_history should return an empty list for new vendors."""
    res = await mcp_server.call_tool("get_invoice_history", {"vendor_name": "NewTech Solutions"})
    result = [json.loads(item.text) for item in res]
    assert result == []


# ---------------------------------------------------------------------------
# find_duplicate_invoice (now SQLite-backed)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_find_duplicate_invoice():
    """find_duplicate_invoice should detect known duplicates in invoice_history."""
    res_1 = await mcp_server.call_tool("find_duplicate_invoice", {"invoice_number": "INV-2026-001"})
    assert res_1[1]["result"] is True

    res_2 = await mcp_server.call_tool("find_duplicate_invoice", {"invoice_number": "INV-NEW-UNIQUE-999"})
    assert res_2[1]["result"] is False


# ---------------------------------------------------------------------------
# submit_investigation_result
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_submit_investigation_result():
    """submit_investigation_result should return a success dict with Finance Manager role."""
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
    parsed = json.loads(res[0].text)
    assert parsed["invoice_number"] == "INV-2026-001"
    assert parsed["recommendation"] == "REVIEW"
    assert parsed["submitted"] is True


# ---------------------------------------------------------------------------
# list_pending_invoices
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_list_pending_invoices():
    """list_pending_invoices should return at least 2 pending invoices for Administrator."""
    res = await mcp_server.call_tool("list_pending_invoices", {"role": "Administrator"})
    pending_list = res[1]["result"]
    assert isinstance(pending_list, list)
    assert len(pending_list) >= 2
    assert pending_list[0]["invoice_number"] == "INV-NEW-001"
    assert pending_list[0]["status"] == "Pending"
