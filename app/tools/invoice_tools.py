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

import re
import threading
from typing import Optional, List
from pydantic import BaseModel


# Optional thread-local profiler hook (set by upload handler, None otherwise)
_profiler_ctx: threading.local = threading.local()


def _get_profiler():
    return getattr(_profiler_ctx, "profiler", None)


class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    purchase_order_number: Optional[str] = None
    currency: Optional[str] = None
    invoice_amount: Optional[float] = None
    payment_terms: Optional[str] = None
    order_id: Optional[str] = None


def parse_invoice_with_gemini(invoice_text: str) -> InvoiceData:
    """Primary document extraction method using Gemini's structured output.
    
    Falls back to regex-based extraction if API calls fail or credentials are missing.
    """
    import os
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            prompt = (
                "Analyze the following raw invoice text and extract the structured fields. "
                "Ensure that order_id is extracted if present (e.g. Order ID: ES-2013-VD21670139-41293) "
                "and purchase_order_number is extracted separately. Do not map Order ID into purchase_order_number.\n\n"
                f"Raw invoice text:\n{invoice_text}"
            )

            # --- Profiler instrumentation ---
            _prof = _get_profiler()
            _gcall = _prof.record_gemini_call(
                caller="parse_invoice_with_gemini",
                prompt_chars=len(prompt),
                model="gemini-2.5-flash",
            ) if _prof else None
            # --------------------------------

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=InvoiceData,
                ),
            )

            if _gcall:
                _gcall.finish()

            import json
            parsed_json = json.loads(response.text)
            return InvoiceData(**parsed_json)
    except Exception:
        # Fall back to regex parsing if Gemini is unavailable or errors.
        pass

    return parse_invoice(invoice_text)


def parse_invoice(invoice_text: str) -> InvoiceData:
    """Parses invoice text using regular expressions to extract structured information.

    Args:
        invoice_text: The raw text of the invoice.

    Returns:
        An InvoiceData Pydantic model containing the extracted fields.
    """
    data = {}

    # 1. Invoice Number
    inv_num_match = re.search(
        r'(?:invoice\s*(?:id|number|no|#)?|inv\s*(?:#|no|number)?)\s*[:#-]?\s*([a-zA-Z0-9-]+)',
        invoice_text,
        re.IGNORECASE,
    )
    data["invoice_number"] = inv_num_match.group(1).strip() if inv_num_match else None

    # 2. Vendor Name
    vendor_match = re.search(
        r'(?:vendor\s*(?:name)?|billed\s*by|from)\s*:\s*([^\n]+)',
        invoice_text,
        re.IGNORECASE,
    )
    data["vendor_name"] = vendor_match.group(1).strip() if vendor_match else None

    # 3. Invoice Date
    inv_date_match = re.search(
        r'invoice\s+date\s*:\s*([^\n]+)', invoice_text, re.IGNORECASE
    )
    if inv_date_match:
        data["invoice_date"] = inv_date_match.group(1).strip()
    else:
        date_match = re.search(
            r'(?<!due\s)(?<!due\sdate\s)\bdate\s*:\s*([^\n]+)',
            invoice_text,
            re.IGNORECASE,
        )
        data["invoice_date"] = date_match.group(1).strip() if date_match else None

    # 4. Due Date
    due_date_match = re.search(
        r'(?:due\s+date|due|pay\s+by)\s*:\s*([^\n]+)', invoice_text, re.IGNORECASE
    )
    data["due_date"] = due_date_match.group(1).strip() if due_date_match else None

    # 5. Purchase Order Number (do not map Order ID here)
    po_match = re.search(
        r'(?:purchase\s+order(?:\s+number)?|po\s*(?:#|number|no)?)\s*[:#-]?\s*([a-zA-Z0-9-]+)',
        invoice_text,
        re.IGNORECASE,
    )
    data["purchase_order_number"] = po_match.group(1).strip() if po_match else None

    # 5.5 Order ID (separated from PO Reference)
    order_id_match = re.search(
        r'(?:order\s*(?:id|#|number))\s*[:#-]?\s*([a-zA-Z0-9-]+)',
        invoice_text,
        re.IGNORECASE,
    )
    data["order_id"] = order_id_match.group(1).strip() if order_id_match else None

    # 6. Currency & Invoice Amount
    amount_match = re.search(
        r'(?:total\s+amount|amount(?:\s+due)?|total(?:\s+due)?|grand\s+total)\s*:\s*([^\n]+)',
        invoice_text,
        re.IGNORECASE,
    )
    if amount_match:
        amount_raw = amount_match.group(1).strip()
        # Parse currency
        currency_match = re.search(
            r'(\$|€|£|¥|USD|EUR|GBP|JPY)', amount_raw, re.IGNORECASE
        )
        if currency_match:
            data["currency"] = currency_match.group(1).strip()
        else:
            text_currency_match = re.search(
                r'\b(USD|EUR|GBP|JPY)\b', invoice_text, re.IGNORECASE
            )
            data["currency"] = (
                text_currency_match.group(1).strip() if text_currency_match else None
            )

        # Clean amount string to extract float
        amount_clean = re.sub(r'[^\d.]', '', amount_raw)
        try:
            data["invoice_amount"] = float(amount_clean) if amount_clean else None
        except ValueError:
            data["invoice_amount"] = None
    else:
        data["currency"] = None
        data["invoice_amount"] = None

    # 7. Payment Terms
    terms_match = re.search(
        r'(?:payment\s+terms|terms)\s*:\s*([^\n]+)', invoice_text, re.IGNORECASE
    )
    data["payment_terms"] = terms_match.group(1).strip() if terms_match else None

    return InvoiceData(**data)


def validate_invoice(invoice: InvoiceData) -> None:
    """Validates required invoice fields to prevent malformed or fraudulent processing.

    Args:
        invoice: The extracted InvoiceData model.

    Raises:
        ValueError: If any validation rule fails.
    """
    if not invoice.invoice_number or not invoice.invoice_number.strip():
        raise ValueError("Missing Invoice Number.")
    if not invoice.vendor_name or not invoice.vendor_name.strip():
        raise ValueError("Missing Vendor Name.")
    if invoice.invoice_amount is None or invoice.invoice_amount <= 0:
        raise ValueError("Invalid or missing Invoice Amount.")
    if not invoice.invoice_date:
        raise ValueError("Missing Invoice Date.")
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", invoice.invoice_date.strip()):
        raise ValueError("Invalid Invoice Date format (must be YYYY-MM-DD).")


def analyze_invoice(invoice_text: str, session_id: str = "N/A", role: str = "Finance Analyst") -> str:
    """Analyzes the text of an invoice, parses it, and returns a branded investigation report.

    Args:
        invoice_text: The full text content of the invoice to analyze.
        session_id: Optional session identifier for security auditing.
        role: Optional user role for access control auditing.

    Returns:
        A formatted string containing the branded VELNIX INITIAL INVESTIGATION or REJECTION report.
    """
    print("[DEBUG LOG] analyze_invoice tool has been invoked by the agent!")

    # 1. First call the parse_invoice helper
    parsed_data = parse_invoice(invoice_text)

    # 2. Perform enterprise input validation
    from app.security import log_audit_event
    try:
        validate_invoice(parsed_data)
    except ValueError as val_err:
        rejection_reason = str(val_err)
        log_audit_event(
            parsed_data.invoice_number or "N/A",
            "Invoice Analysis Agent",
            session_id,
            role,
            "REJECTED",
            "NONE",
            rejection_reason
        )
        rejection_report = (
            "==================================================\n"
            "         VELNIX INVOICE REJECTION REPORT          \n"
            "==================================================\n"
            "REJECTION REASON: {}\n"
            "--------------------------------------------------\n"
            "STATUS: REJECTED & BLOCKED FROM PROCESSING\n"
            "PHASE: Validation & Security\n"
            "=================================================="
        ).format(rejection_reason)
        return rejection_report

    # 3. Load the vendor profile
    from app.tools.vendor_intelligence import get_vendor_profile
    vendor_profile = get_vendor_profile(parsed_data.vendor_name)

    # 3. Perform historical comparisons and check alerts
    alerts = []
    if vendor_profile.vendor_status == "New":
        alerts.append("- NOTICE: Vendor is New/Unverified. No prior invoice history.")
    elif vendor_profile.vendor_status == "Watchlist":
        alerts.append(f"- WARNING: Vendor is on the Watchlist! Trust score is {vendor_profile.trust_score}/100.")

    if parsed_data.invoice_amount is not None and vendor_profile.total_previous_invoices > 0:
        if parsed_data.invoice_amount > 1.5 * vendor_profile.average_invoice_amount:
            ratio = parsed_data.invoice_amount / vendor_profile.average_invoice_amount
            curr = parsed_data.currency or ""
            alerts.append(
                f"- WARNING: Current invoice amount ({curr}{parsed_data.invoice_amount:,.2f}) "
                f"is unusually high ({ratio:.1f}x the historical average of "
                f"{curr}{vendor_profile.average_invoice_amount:,.2f})."
            )

    alerts_text = "\n".join(alerts) if alerts else "- No critical alerts found."

    # 4. Perform deterministic risk assessment
    from app.tools.risk_engine import calculate_risk
    risk_assessment = calculate_risk(parsed_data, vendor_profile)

    # 5. Perform deterministic fraud assessment
    from app.tools.fraud_engine import calculate_fraud
    fraud_assessment = calculate_fraud(parsed_data, vendor_profile, invoice_text)

    # 6. Format the parsed fields block
    parsed_fields_block = (
        "--------------------------------------------------\n"
        "PARSED INVOICE FIELDS:\n"
        "  - Invoice Number: {}\n"
        "  - Vendor Name: {}\n"
        "  - Invoice Date: {}\n"
        "  - Due Date: {}\n"
        "  - Purchase Order Number: {}\n"
        "  - Currency: {}\n"
        "  - Invoice Amount: {}\n"
        "  - Payment Terms: {}\n"
        "--------------------------------------------------"
    ).format(
        parsed_data.invoice_number,
        parsed_data.vendor_name,
        parsed_data.invoice_date,
        parsed_data.due_date,
        parsed_data.purchase_order_number,
        parsed_data.currency,
        parsed_data.invoice_amount,
        parsed_data.payment_terms,
    )

    # 7. Format the Vendor Intelligence block
    vendor_intel_block = (
        "--------------------------------------------------\n"
        "VENDOR INTELLIGENCE:\n"
        "  - Vendor Name: {}\n"
        "  - Status: {}\n"
        "  - Trust Score: {}/100\n"
        "  - Total Previous Invoices: {}\n"
        "  - Avg Invoice Amount: {}\n"
        "  - Previous Rejections: {}\n"
        "  - Last Bank Account Change: {}\n"
        "  - Alerts/Notes:\n"
        "    {}\n"
        "--------------------------------------------------"
    ).format(
        vendor_profile.vendor_name,
        vendor_profile.vendor_status,
        vendor_profile.trust_score,
        vendor_profile.total_previous_invoices,
        vendor_profile.average_invoice_amount,
        vendor_profile.previous_rejections,
        vendor_profile.last_bank_account_change,
        alerts_text.replace("\n", "\n    "),
    )

    # 8. Format the Evidence Summary block
    pos_findings_lines = "\n  ".join(f"- {f}" for f in risk_assessment.positive_findings) if risk_assessment.positive_findings else "  - None"
    risk_findings_lines = "\n  ".join(f"- {f}" for f in risk_assessment.risk_findings) if risk_assessment.risk_findings else "  - None"
    evidence_lines = "\n  ".join(f"- {f}" for f in risk_assessment.evidence)

    evidence_block = (
        "--------------------------------------------------\n"
        "EVIDENCE SUMMARY:\n"
        "Positive Findings:\n"
        "  {}\n"
        "Risk Findings:\n"
        "  {}\n"
        "Evidence:\n"
        "  {}\n"
        "Risk Score: {}/100\n"
        "Recommendation: {}\n"
        "Final Reasoning:\n"
        "  {}\n"
        "--------------------------------------------------"
    ).format(
        pos_findings_lines,
        risk_findings_lines,
        evidence_lines,
        risk_assessment.risk_score,
        risk_assessment.recommendation,
        risk_assessment.final_reasoning
    )

    # 9. Format the Fraud Intelligence block
    fraud_flags_lines = "\n  ".join(f"- {f}" for f in fraud_assessment.fraud_flags) if fraud_assessment.fraud_flags else "  - None"

    fraud_block = (
        "--------------------------------------------------\n"
        "FRAUD INTELLIGENCE:\n"
        "  - Fraud Score: {}/100\n"
        "  - Confidence Level: {}\n"
        "  - Investigation Required: {}\n"
        "  - Fraud Flags:\n"
        "    {}\n"
        "  - Explanation:\n"
        "    {}\n"
        "--------------------------------------------------"
    ).format(
        fraud_assessment.fraud_score,
        fraud_assessment.confidence_level,
        "YES" if fraud_assessment.investigation_required else "NO",
        fraud_flags_lines.replace("\n", "\n    "),
        fraud_assessment.explanation.replace("\n", "\n    ")
    )

    # 10. Format the final branded report
    report = (
        "==================================================\n"
        "         VELNIX INITIAL INVESTIGATION REPORT       \n"
        "==================================================\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "{}\n"
        "STATUS: RECEIVED & QUEUED FOR INVESTIGATION\n"
        "PHASE: 5 (Fraud Intelligence)\n"
        "CHARACTER COUNT: {}\n"
        "SUMMARY:\n"
        "Invoice content has been successfully parsed, historical risk evidence calculated, and fraud flags evaluated.\n"
        "A final trust recommendation of {} has been issued with a risk score of {}/100 and a fraud score of {}/100.\n"
        "=================================================="
    ).format(
        parsed_fields_block,
        vendor_intel_block,
        evidence_block,
        fraud_block,
        len(invoice_text),
        risk_assessment.recommendation,
        risk_assessment.risk_score,
        fraud_assessment.fraud_score,
    )

    log_audit_event(
        parsed_data.invoice_number,
        "Velnix Platform",
        session_id,
        role,
        "SUCCESS",
        risk_assessment.recommendation,
        risk_assessment.final_reasoning
    )

    return report
