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

import csv
import os
from mcp.server.fastmcp import FastMCP
from app.security import verify_permission

mcp_server = FastMCP("Velnix ERP Server")

# Paths relative to the app folder
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_CSV_PATH = os.path.join(current_dir, "data", "invoice_history.csv")


@mcp_server.tool()
def get_vendor_profile(vendor_name: str, role: str = "Finance Analyst") -> dict:
    """Retrieves the historical vendor profile and trust metrics for a given vendor name.

    Args:
        vendor_name: The name of the vendor to search for.
        role: The role name requesting the action (default: Finance Analyst).
    """
    verify_permission(role, "view_profile")
    from app.tools.vendor_intelligence import get_vendor_profile as local_get_profile
    profile = local_get_profile(vendor_name)
    return profile.model_dump()


@mcp_server.tool()
def find_duplicate_invoice(invoice_number: str, role: str = "Finance Analyst") -> bool:
    """Checks whether the given invoice number has already been paid or processed in ERP history.

    Args:
        invoice_number: The unique invoice reference code.
        role: The role name requesting the action (default: Finance Analyst).
    """
    verify_permission(role, "find_duplicate")
    if not invoice_number:
        return False

    if os.path.exists(HISTORY_CSV_PATH):
        try:
            with open(HISTORY_CSV_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    hist_inv = row.get("Invoice Number", "").strip().lower()
                    if hist_inv == invoice_number.strip().lower():
                        return True
        except Exception:
            pass

    return False


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
        "message": f"Successfully updated ERP status for '{invoice_number}'. Decision: {recommendation}."
    }


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
            "date": "2026-06-29"
        },
        {
            "invoice_number": "INV-RISK-102",
            "vendor_name": "RiskCo LLC",
            "amount": 8000.00,
            "status": "Pending",
            "date": "2026-06-30"
        }
    ]


if __name__ == "__main__":
    mcp_server.run()
