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
from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.tools.invoice_tools import InvoiceData
from app.tools.vendor_intelligence import VendorProfile


class FraudAssessment(BaseModel):
    fraud_score: int
    fraud_flags: List[str]
    investigation_required: bool
    confidence_level: str  # "LOW", "MEDIUM", "HIGH"
    explanation: str


# Construct the history CSV path relative to the file location to ensure robust imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_CSV_PATH = os.path.join(current_dir, "data", "invoice_history.csv")


def calculate_fraud(
    invoice: InvoiceData,
    vendor: VendorProfile,
    invoice_text: str,
    is_duplicate: bool = None
) -> FraudAssessment:
    """Calculates a deterministic fraud score and assessment based on transaction evidence.

    Args:
        invoice: The extracted invoice fields.
        vendor: The vendor historical profile.
        invoice_text: The raw text of the invoice.
        is_duplicate: Optional override. If provided, skips the CSV lookup.

    Returns:
        A FraudAssessment Pydantic model.
    """
    score = 0
    flags = []
    has_high_severity = False
    has_medium_severity = False
    has_low_severity = False

    # 1. Duplicate Invoice Number Check
    if is_duplicate is None:
        is_duplicate = False
        if invoice.invoice_number and os.path.exists(HISTORY_CSV_PATH):
            try:
                with open(HISTORY_CSV_PATH, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        hist_inv = row.get("Invoice Number", "").strip().lower()
                        if hist_inv == invoice.invoice_number.strip().lower():
                            is_duplicate = True
                            break
            except Exception:
                pass

    if is_duplicate:
        score += 50
        flags.append(
            f"CRITICAL: Duplicate Invoice Number detected. '{invoice.invoice_number}' was already processed in history."
        )
        has_high_severity = True

    # 2. Bank Account Recently Changed Check
    recent_bank_change = False
    if vendor.last_bank_account_change and vendor.last_bank_account_change != "N/A":
        try:
            change_date = datetime.strptime(
                vendor.last_bank_account_change.strip(), "%Y-%m-%d"
            )
            mock_today = datetime(2026, 6, 30)
            delta = mock_today - change_date
            if 0 <= delta.days <= 60:
                recent_bank_change = True
        except ValueError:
            pass

    if recent_bank_change:
        score += 30
        flags.append(
            f"HIGH: Vendor bank account changed recently on {vendor.last_bank_account_change} (within 60 days)."
        )
        has_high_severity = True

    # 3. Invoice Amount Significantly Larger than Average Check (>3x)
    if invoice.invoice_amount is not None and vendor.total_previous_invoices > 0:
        if invoice.invoice_amount > 3.0 * vendor.average_invoice_amount:
            score += 30
            ratio = invoice.invoice_amount / vendor.average_invoice_amount
            curr = invoice.currency or ""
            flags.append(
                f"HIGH: Invoice amount ({curr}{invoice.invoice_amount:,.2f}) is significantly larger than historical average "
                f"({curr}{vendor.average_invoice_amount:,.2f}) by {ratio:.1f}x (threshold is >3x)."
            )
            has_high_severity = True

    # 4. Watchlisted Vendor Check
    if vendor.vendor_status == "Watchlist":
        score += 30
        flags.append(
            f"HIGH: Vendor '{vendor.vendor_name}' is currently on the Watchlist."
        )
        has_high_severity = True

    # 5. New Vendor Requesting Urgent Payment Check
    is_urgent_new = False
    if getattr(vendor, "vendor_found", False) and vendor.vendor_status == "New":
        urgency_keywords = [
            "urgent",
            "immediate",
            "asap",
            "due now",
            "pay now",
            "immediately",
            "critical payment",
        ]
        has_urgency = any(
            keyword in invoice_text.lower() for keyword in urgency_keywords
        )
        if has_urgency:
            is_urgent_new = True


    if is_urgent_new:
        score += 25
        flags.append("MEDIUM-HIGH: New vendor requesting urgent payment terms.")
        has_medium_severity = True

    # 6. Missing Purchase Order Check
    if not invoice.purchase_order_number:
        score += 10
        flags.append("LOW: Missing Purchase Order (PO) reference.")
        has_low_severity = True

    # Bound fraud score between 0 and 100
    final_score = min(100, max(0, score))

    # Determine investigation required
    investigation_required = (final_score >= 40) or has_high_severity

    # Derive confidence level deterministically
    num_flags = len(flags)
    if num_flags == 0:
        confidence_level = "LOW"
    elif num_flags == 1:
        if has_high_severity:
            confidence_level = "HIGH"
        else:
            confidence_level = "MEDIUM"
    else:
        confidence_level = "HIGH"

    # Construct explanation summary
    if num_flags == 0:
        explanation = "No fraud indicators were identified. The invoice appears consistent with baseline transaction rules."
    else:
        findings_summary = ", ".join(f.split(":")[0].strip() for f in flags)
        explanation = (
            f"The fraud intelligence check identified {num_flags} active indicator(s): [{findings_summary}]. "
            f"With a calculated Fraud Score of {final_score}/100 and a {confidence_level} confidence classification, "
            f"this transaction {'requires formal investigation' if investigation_required else 'does not require immediate AP escalation, but flags should be checked'}."
        )

    return FraudAssessment(
        fraud_score=final_score,
        fraud_flags=flags,
        investigation_required=investigation_required,
        confidence_level=confidence_level,
        explanation=explanation,
    )
