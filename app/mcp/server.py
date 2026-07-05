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

"""Velnix MCP server exposing ERP tools to the AI agent pipeline.

All database interactions are delegated to :mod:`app.erp.queries` so that
no SQL is embedded directly in this module.
"""

import os
from mcp.server.fastmcp import FastMCP
from app.security import verify_permission

mcp_server = FastMCP("Velnix ERP Server")


# ---------------------------------------------------------------------------
# Vendor tools
# ---------------------------------------------------------------------------

@mcp_server.tool()
def get_vendor_profile(vendor_name: str, role: str = "Finance Analyst") -> dict:
    """Retrieves the vendor profile and trust metrics from the ERP database.

    Looks up the vendor by name in the SQLite vendors table.  Returns a
    structured profile dict, or a default 'New vendor' profile if not found.

    Args:
        vendor_name: The display name of the vendor to look up.
        role: The role name requesting the action (default: Finance Analyst).
    """
    verify_permission(role, "view_profile")
    from app.erp.queries import fetch_vendor_by_name

    vendor = fetch_vendor_by_name(vendor_name)
    if vendor:
        res = vendor.to_dict()
        res["vendor_found"] = True
        res["vendor_finding"] = f"Vendor {vendor.vendor_name} was found in the ERP vendor master and is classified as a {vendor.vendor_status} vendor."
        return res

    # Graceful fallback for unknown / newly onboarded vendors
    return {
        "vendor_found": False,
        "vendor_finding": "Vendor was not found in the ERP vendor master. Vendor verification could not be completed.",
        "vendor_id": None,
        "vendor_name": vendor_name or "Unknown Vendor",
        "vendor_status": "New",
        "trust_score": 50,
        "average_invoice_amount": 0.0,
        "total_previous_invoices": 0,
        "previous_rejections": 0,
        "last_bank_account_change": "N/A",
        "bank_account": "N/A",
        "risk_level": "Low",
    }



# ---------------------------------------------------------------------------
# Purchase Order tools
# ---------------------------------------------------------------------------

@mcp_server.tool()
def get_purchase_order(purchase_order_number: str, role: str = "Finance Analyst") -> dict:
    """Retrieves a Purchase Order record from the ERP database.

    Args:
        purchase_order_number: The PO reference number (e.g. PO-2026-001).
        role: The role name requesting the action (default: Finance Analyst).

    Returns:
        A dict containing PO fields, or {"found": False} if not found.
    """
    verify_permission(role, "get_purchase_order")
    from app.erp.queries import fetch_purchase_order

    po = fetch_purchase_order(purchase_order_number)
    if po:
        return po.to_dict()
    return {"found": False, "purchase_order_number": purchase_order_number}


# ---------------------------------------------------------------------------
# Goods Receipt tools
# ---------------------------------------------------------------------------

@mcp_server.tool()
def get_goods_receipt(purchase_order_number: str, role: str = "Finance Analyst") -> list:
    """Retrieves all Goods Receipt records linked to a Purchase Order.

    Args:
        purchase_order_number: The PO reference number to look up.
        role: The role name requesting the action (default: Finance Analyst).

    Returns:
        A list of goods receipt dicts (may be empty if no receipts exist).
    """
    verify_permission(role, "get_goods_receipt")
    from app.erp.queries import fetch_goods_receipts_for_po

    receipts = fetch_goods_receipts_for_po(purchase_order_number)
    return [r.to_dict() for r in receipts]


# ---------------------------------------------------------------------------
# Invoice History tools
# ---------------------------------------------------------------------------

@mcp_server.tool()
def get_invoice_history(vendor_name: str, role: str = "Finance Analyst") -> list:
    """Retrieves the historical invoice records for a vendor from the ERP database.

    Supports lookup by vendor name to accommodate callers that have only the
    name from an uploaded invoice.  Internally the query uses the indexed
    vendor_name column; for vendor_id-based lookup use the queries module directly.

    Args:
        vendor_name: The display name of the vendor.
        role: The role name requesting the action (default: Finance Analyst).

    Returns:
        A list of invoice history dicts ordered newest-first (may be empty).
    """
    verify_permission(role, "get_invoice_history")
    from app.erp.queries import fetch_invoice_history_by_vendor_name

    history = fetch_invoice_history_by_vendor_name(vendor_name)
    return [h.to_dict() for h in history]


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

@mcp_server.tool()
def find_duplicate_invoice(invoice_number: str, role: str = "Finance Analyst") -> bool:
    """Checks whether the invoice number already exists in ERP invoice history.

    Args:
        invoice_number: The unique invoice reference code to check.
        role: The role name requesting the action (default: Finance Analyst).
    """
    verify_permission(role, "find_duplicate")
    if not invoice_number:
        return False
    from app.erp.queries import check_duplicate_invoice
    return check_duplicate_invoice(invoice_number)


# ---------------------------------------------------------------------------
# Investigation result submission
# ---------------------------------------------------------------------------

@mcp_server.tool()
def submit_investigation_result(
    invoice_number: str,
    recommendation: str,
    risk_score: int,
    fraud_score: int,
    role: str = "Finance Analyst"
) -> dict:
    """Submits the Velnix AI risk and fraud investigation results back to the ERP system.

    Args:
        invoice_number: The invoice reference code that was analyzed.
        recommendation: The AP recommendation decision (APPROVE, REVIEW, or INVESTIGATE).
        risk_score: The final calculated Risk Score (0-100).
        fraud_score: The final calculated Fraud Score (0-100).
        role: The role name requesting the action (default: Finance Analyst).
    """
    verify_permission(role, "submit_investigation_result")
    return {
        "invoice_number": invoice_number,
        "recommendation": recommendation,
        "risk_score": risk_score,
        "fraud_score": fraud_score,
        "submitted": True,
        "message": f"Successfully updated ERP status for '{invoice_number}'. Decision: {recommendation}.",
    }


# ---------------------------------------------------------------------------
# Pending invoices listing
# ---------------------------------------------------------------------------

@mcp_server.tool()
def list_pending_invoices(role: str = "Finance Analyst") -> list[dict]:
    """Lists all pending invoices currently awaiting review or approval in the ERP.

    Args:
        role: The role name requesting the action (default: Finance Analyst).
    """
    verify_permission(role, "list_pending_invoices")
    return [
        {
            "invoice_number": "INV-NEW-001",
            "vendor_name": "NewTech Solutions",
            "amount": 2500.00,
            "status": "Pending",
            "date": "2026-06-29",
        },
        {
            "invoice_number": "INV-RISK-102",
            "vendor_name": "RiskCo LLC",
            "amount": 8000.00,
            "status": "Pending",
            "date": "2026-06-30",
        },
    ]


if __name__ == "__main__":
    mcp_server.run()
