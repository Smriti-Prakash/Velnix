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

from typing import List
from pydantic import BaseModel
from app.tools.invoice_tools import InvoiceData
from app.tools.vendor_intelligence import VendorProfile


class RiskAssessment(BaseModel):
    risk_score: int
    recommendation: str
    positive_findings: List[str]
    risk_findings: List[str]
    evidence: List[str]
    final_reasoning: str


def calculate_risk(invoice: InvoiceData, vendor: VendorProfile) -> RiskAssessment:
    """Calculates risk score and makes trust recommendations deterministically.

    Args:
        invoice: The extracted invoice fields.
        vendor: The vendor historical profile.

    Returns:
        A RiskAssessment Pydantic model.
    """
    positive = []
    risks = []
    evidence_items = []
    score = 0

    # Gather baseline evidence
    curr = invoice.currency or ""
    inv_amount_str = f"{curr}{invoice.invoice_amount:,.2f}" if invoice.invoice_amount is not None else "None"
    avg_amount_str = f"{curr}{vendor.average_invoice_amount:,.2f}"
    
    evidence_items.append(f"Vendor Name: {vendor.vendor_name}")
    evidence_items.append(f"Vendor Status: {vendor.vendor_status}")
    evidence_items.append(f"Vendor Trust Score: {vendor.trust_score}/100")
    evidence_items.append(f"Total Previous Invoices: {vendor.total_previous_invoices}")
    evidence_items.append(f"Average Invoice Amount: {avg_amount_str}")
    evidence_items.append(f"Current Invoice Amount: {inv_amount_str}")
    evidence_items.append(f"Purchase Order (PO): {invoice.purchase_order_number or 'None'}")
    evidence_items.append(f"Payment Terms: {invoice.payment_terms or 'None'}")
    evidence_items.append(f"Last Bank Account Change: {vendor.last_bank_account_change}")

    # 1. Vendor Status Check
    if vendor.vendor_status == "Watchlist":
        score += 40
        risks.append(f"Vendor is on corporate WATCHLIST (Trust Score: {vendor.trust_score}/100).")
    elif vendor.vendor_status == "New":
        score += 20
        risks.append("Vendor is NEW/UNVERIFIED in the master database (no prior transaction history).")
    elif vendor.vendor_status == "Trusted":
        positive.append(f"Vendor status is verified and TRUSTED (Trust Score: {vendor.trust_score}/100).")

    # 2. Vendor Trust Score Penalty Check
    if vendor.trust_score < 70:
        penalty = max(0, 70 - vendor.trust_score)
        score += penalty
        risks.append(f"Vendor trust score is low: {vendor.trust_score}/100 (penalty of +{penalty} risk points).")
    elif vendor.trust_score >= 90:
        positive.append(f"High vendor trust score: {vendor.trust_score}/100.")

    # 3. Invoice Amount vs Historical Average check
    if invoice.invoice_amount is not None and vendor.total_previous_invoices > 0:
        if invoice.invoice_amount > 1.5 * vendor.average_invoice_amount:
            score += 25
            ratio = invoice.invoice_amount / vendor.average_invoice_amount
            risks.append(
                f"Invoice amount ({inv_amount_str}) is unusually high: "
                f"{ratio:.1f}x the historical average for this vendor ({avg_amount_str})."
            )
        else:
            positive.append(
                f"Invoice amount ({inv_amount_str}) is within normal "
                f"historical billing average ({avg_amount_str})."
            )

    # 4. Purchase Order Check
    if not invoice.purchase_order_number:
        score += 15
        risks.append("Missing Purchase Order (PO) reference on the invoice.")
    else:
        positive.append(f"Purchase Order ({invoice.purchase_order_number}) matches invoice documentation.")

    # 5. Payment Terms Check
    if not invoice.payment_terms:
        score += 10
        risks.append("Missing payment terms details.")
    else:
        positive.append(f"Payment terms are specified: '{invoice.payment_terms}'.")

    # Bound risk score between 0 and 100
    final_score = min(100, max(0, score))

    # Determine recommendation and reasoning
    if final_score < 30:
        recommendation = "APPROVE"
        reasoning = (
            f"The invoice has a low risk profile (Risk Score: {final_score}/100) and is from "
            f"a trusted vendor with standard matching documents. Recommended for payment approval."
        )
    elif final_score < 60:
        recommendation = "REVIEW"
        reasoning = (
            f"The invoice has a moderate risk profile (Risk Score: {final_score}/100). "
            f"There are missing fields (e.g. PO or payment terms) or the vendor has a brief history. "
            f"Requires review by an AP analyst before approval."
        )
    else:
        recommendation = "INVESTIGATE"
        reasoning = (
            f"The invoice has a high risk profile (Risk Score: {final_score}/100) due to significant "
            f"anomalies such as watchlist status, a low trust score, or an unusually high transaction amount. "
            f"Requires formal investigation and holds on disbursement."
        )

    return RiskAssessment(
        risk_score=final_score,
        recommendation=recommendation,
        positive_findings=positive,
        risk_findings=risks,
        evidence=evidence_items,
        final_reasoning=reasoning
    )
