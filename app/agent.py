# ruff: noqa
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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import McpToolset
from google.genai import types
from mcp import StdioServerParameters

import os
import sys
import asyncio
import threading
import time
from google.genai.models import AsyncModels
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Optional thread-local profiler hook — shared with the upload handler.
# ---------------------------------------------------------------------------
_profiler_ctx: threading.local = threading.local()


def _get_agent_profiler():
    return getattr(_profiler_ctx, "profiler", None)

# Monkey-patch AsyncModels to enforce rate limit (at least 13 seconds between calls)
# to avoid exceeding the 5 requests-per-minute limit of the gemini-2.5-flash model on the free tier.
_original_generate_content = AsyncModels.generate_content
_original_generate_content_stream = AsyncModels.generate_content_stream
_last_request_time = 0.0

async def _patched_generate_content(self, *args, **kwargs):
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    delay = 13.0 - elapsed
    if delay > 0:
        await asyncio.sleep(delay)

    # --- Profiler instrumentation ---
    _prof = _get_agent_profiler()
    _gcall = None
    if _prof:
        # Estimate prompt size from first positional arg (contents)
        try:
            _contents = kwargs.get("contents") or (args[0] if args else "")
            _prompt_chars = len(str(_contents))
        except Exception:
            _prompt_chars = 0
        _gcall = _prof.record_gemini_call(
            caller="agent_generate_content",
            prompt_chars=_prompt_chars,
            model="gemini-3.1-flash-lite",
            call_type="generate_content",
        )
    # --------------------------------

    res = await _original_generate_content(self, *args, **kwargs)
    _last_request_time = time.time()
    if _gcall:
        _gcall.finish()
    return res


async def _patched_generate_content_stream(self, *args, **kwargs):
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    delay = 13.0 - elapsed
    if delay > 0:
        await asyncio.sleep(delay)

    # --- Profiler instrumentation ---
    _prof = _get_agent_profiler()
    _gcall = None
    if _prof:
        try:
            _contents = kwargs.get("contents") or (args[0] if args else "")
            _prompt_chars = len(str(_contents))
        except Exception:
            _prompt_chars = 0
        _gcall = _prof.record_gemini_call(
            caller="agent_generate_content_stream",
            prompt_chars=_prompt_chars,
            model="gemini-3.1-flash-lite",
            call_type="generate_content_stream",
        )
    # --------------------------------

    res = await _original_generate_content_stream(self, *args, **kwargs)
    _last_request_time = time.time()
    if _gcall:
        _gcall.finish()
    return res

AsyncModels.generate_content = _patched_generate_content
AsyncModels.generate_content_stream = _patched_generate_content_stream



# =====================================================================
# NATIVE MCP TOOLSET CONNECTION
# =====================================================================

from app.mcp.tool_factory import create_vendor_toolset
erp_mcp_toolset = create_vendor_toolset()


# =====================================================================
# DETERMINISTIC AGENT TOOLS
# =====================================================================

def normalize_invoice_data(d: dict) -> dict:
    if not isinstance(d, dict):
        d = {}
    import re
    invoice_number = d.get("invoice_number") or d.get("invoice_id") or d.get("id") or d.get("number")
    vendor_name = d.get("vendor_name") or d.get("vendor") or d.get("name")
    invoice_date = d.get("invoice_date") or d.get("date")
    due_date = d.get("due_date")
    purchase_order_number = d.get("purchase_order_number") or d.get("purchase_order") or d.get("po_number") or d.get("po")
    order_id = d.get("order_id")
    currency = d.get("currency")
    
    amount_val = d.get("invoice_amount") or d.get("amount")
    invoice_amount = None
    if amount_val is not None:
        try:
            if isinstance(amount_val, str):
                cleaned = re.sub(r'[^\d.]', '', amount_val)
                invoice_amount = float(cleaned)
            else:
                invoice_amount = float(amount_val)
        except Exception:
            pass
            
    payment_terms = d.get("payment_terms") or d.get("terms")
    
    return {
        "invoice_number": str(invoice_number) if invoice_number is not None else None,
        "vendor_name": str(vendor_name) if vendor_name is not None else None,
        "invoice_date": str(invoice_date) if invoice_date is not None else None,
        "due_date": str(due_date) if due_date is not None else None,
        "purchase_order_number": str(purchase_order_number) if purchase_order_number is not None else None,
        "order_id": str(order_id) if order_id is not None else None,
        "currency": str(currency) if currency is not None else None,
        "invoice_amount": invoice_amount,
        "payment_terms": str(payment_terms) if payment_terms is not None else None,
    }


def normalize_vendor_profile(d: dict, inv: dict = None) -> dict:
    if not isinstance(d, dict):
        d = {}
    
    name = d.get("vendor_name") or d.get("name")
    if not name and inv:
        name = inv.get("vendor_name") or inv.get("vendor")
    if not name:
        name = "Unknown Vendor"
        
    status = d.get("vendor_status") or d.get("status") or "New"
    
    try:
        trust_score = int(d.get("trust_score") or d.get("score") or 100)
    except Exception:
        trust_score = 100
        
    try:
        total_inv = int(d.get("total_previous_invoices") or d.get("total_invoices") or d.get("previous_invoices") or d.get("total_previous") or 0)
    except Exception:
        total_inv = 0
        
    try:
        avg_amt = float(d.get("average_invoice_amount") or d.get("average_amount") or d.get("avg_amount") or d.get("average_invoice") or 0.0)
    except Exception:
        avg_amt = 0.0
        
    last_date = d.get("last_invoice_date") or d.get("last_date") or d.get("last_invoice") or "N/A"
    
    try:
        rejections = int(d.get("previous_rejections") or d.get("rejections") or d.get("rejections_count") or 0)
    except Exception:
        rejections = 0
        
    bank_change = d.get("last_bank_account_change") or d.get("bank_account_change") or d.get("last_bank_change") or "N/A"
    
    vendor_found = d.get("vendor_found")
    if vendor_found is None:
        vendor_found = d.get("vendor_id") is not None
        
    vendor_finding = d.get("vendor_finding") or ""
    if not vendor_finding:
        if vendor_found:
            vendor_finding = f"Vendor {name} was found in the ERP vendor master and is classified as a {status} vendor."
        else:
            vendor_finding = "Vendor was not found in the ERP vendor master. Vendor verification could not be completed."

    return {
        "vendor_name": str(name),
        "total_previous_invoices": total_inv,
        "average_invoice_amount": avg_amt,
        "last_invoice_date": str(last_date),
        "previous_rejections": rejections,
        "vendor_status": str(status),
        "trust_score": trust_score,
        "last_bank_account_change": str(bank_change),
        "vendor_found": bool(vendor_found),
        "vendor_finding": str(vendor_finding),
    }



def parse_invoice_tool(invoice_text: str) -> dict:
    """Deterministic tool to parse raw invoice text and extract structured fields.

    Args:
        invoice_text: The raw invoice text.

    Returns:
        A dictionary containing parsed invoice fields (invoice_number, vendor_name, etc.).
    """
    import logging
    _diag = logging.getLogger("velnix.diag")
    from app.tools.invoice_tools import parse_invoice_with_gemini
    parsed = parse_invoice_with_gemini(invoice_text)
    result = parsed.model_dump()
    _diag.info(
        "[VENDOR_DIAG] Stage 2 (parse_invoice_tool output): vendor_name = %r  "
        "Full dict keys with non-None values: %s",
        result.get("vendor_name"),
        {k: v for k, v in result.items() if v is not None},
    )
    return result


def calculate_risk_tool(invoice_data: dict, vendor_profile: dict) -> dict:
    """Deterministic tool to assess risk comparing invoice to vendor profile history.

    Args:
        invoice_data: Dictionary of parsed invoice fields.
        vendor_profile: Dictionary of vendor profile.

    Returns:
        A dictionary containing RiskAssessment fields.
    """
    from app.tools.invoice_tools import InvoiceData
    from app.tools.vendor_intelligence import VendorProfile
    from app.tools.risk_engine import calculate_risk
    
    normalized_inv = normalize_invoice_data(invoice_data)
    normalized_vend = normalize_vendor_profile(vendor_profile, normalized_inv)
    
    inv = InvoiceData(**normalized_inv)
    vend = VendorProfile(**normalized_vend)
    assessment = calculate_risk(inv, vend)
    return assessment.model_dump()


def calculate_fraud_tool(invoice_data: dict, vendor_profile: dict, invoice_text: str, is_duplicate: bool = None) -> dict:
    """Deterministic tool to assess transaction fraud flags.

    Args:
        invoice_data: Dictionary of parsed invoice fields.
        vendor_profile: Dictionary of vendor profile.
        invoice_text: Raw invoice text.
        is_duplicate: Optional override. If provided, skips the CSV lookup.

    Returns:
        A dictionary containing FraudAssessment fields.
    """
    from app.tools.invoice_tools import InvoiceData
    from app.tools.vendor_intelligence import VendorProfile
    from app.tools.fraud_engine import calculate_fraud
    
    normalized_inv = normalize_invoice_data(invoice_data)
    normalized_vend = normalize_vendor_profile(vendor_profile, normalized_inv)
    
    inv = InvoiceData(**normalized_inv)
    vend = VendorProfile(**normalized_vend)
    assessment = calculate_fraud(inv, vend, invoice_text, is_duplicate)
    return assessment.model_dump()


def compile_report_tool(
    invoice_data: dict,
    vendor_profile: dict,
    risk_assessment: dict,
    fraud_assessment: dict,
    invoice_text_len: int
) -> str:
    """Formats and compiles all assessments into the branded VELNIX INVESTIGATION REPORT.

    This function acts strictly as a presentation layer, formatting structured findings
    already produced by the Vendor Intelligence, Risk, and Fraud agents.
    """
    invoice_number = invoice_data.get("invoice_number") or "None"
    vendor_name = invoice_data.get("vendor_name") or "Unknown"
    invoice_date = invoice_data.get("invoice_date") or "None"
    curr = invoice_data.get("currency") or "$"
    amount_val = invoice_data.get("invoice_amount")
    
    if amount_val is not None:
        try:
            amount_str = f"{curr}{float(amount_val):,.2f}"
        except Exception:
            amount_str = f"{curr}{amount_val}"
    else:
        amount_str = "$0.00"

    risk_score = risk_assessment.get("risk_score") or 0
    fraud_score = fraud_assessment.get("fraud_score") or 0
    recommendation = risk_assessment.get("recommendation") or "REVIEW"
    
    # 1. Collect findings from agents/tools
    findings = []
    
    # Vendor Intelligence Finding (authoritative from vendor_profile)
    vendor_finding = vendor_profile.get("vendor_finding")
    if vendor_finding:
        findings.append(vendor_finding)
        
    # Risk Assessment Findings
    risk_findings = risk_assessment.get("risk_findings") or []
    for rf in risk_findings:
        findings.append(rf)
        
    # Fraud Assessment Flags
    fraud_flags = fraud_assessment.get("fraud_flags") or []
    for ff in fraud_flags:
        findings.append(ff)
        
    # PO finding (purely presentation/formatting)
    po = invoice_data.get("purchase_order_number")
    if not po:
        findings.append("No Purchase Order reference was provided in the uploaded invoice. Purchase Order validation could not be performed.")
    else:
        findings.append(f"The invoice references Purchase Order {po}.")
        
    # Select top 3-5 findings, filtering duplicates case-insensitively
    seen = set()
    unique_findings = []
    for f in findings:
        f_norm = f.strip().lower()
        if f_norm not in seen:
            seen.add(f_norm)
            unique_findings.append(f.strip())
            
    findings = unique_findings[:5]
    while len(findings) < 3:
        findings.append("No anomalies or billing deviations were detected for this transaction.")

    # 2. Recommended Action (Presentation mapping of recommendation)
    # The recommendation is decided by the Risk/Fraud engines.
    is_duplicate = any("duplicate" in flag.lower() for flag in fraud_flags) or fraud_assessment.get("fraud_score", 0) >= 50
    recent_bank_change = any("bank account changed recently" in flag.lower() or "bank" in flag.lower() for flag in fraud_flags)
    vendor_status = vendor_profile.get("vendor_status") or "New"
    vendor_found = vendor_profile.get("vendor_found", False)

    if is_duplicate:
        recommended_action = "Reject the invoice immediately to prevent double payment; contact the vendor to resolve."
    elif not vendor_found:
        recommended_action = "This vendor was not found in the ERP vendor master. Payment should remain on hold until vendor verification is complete."
    elif vendor_status == "New":
        if not po:
            recommended_action = "This invoice was submitted by a newly onboarded vendor. No Purchase Order reference was provided in the uploaded invoice, therefore payment should remain on hold until Procurement verifies the transaction."
        else:
            recommended_action = "Verify new vendor bank details against the provided Purchase Order reference before authorizing."
    elif vendor_status == "Watchlist":
        recommended_action = "Perform enhanced due diligence and obtain senior AP management approval before proceeding."
    elif recent_bank_change:
        recommended_action = "Verify bank details directly with a known contact at the vendor via a secondary channel."
    elif recommendation == "APPROVE":
        recommended_action = "Proceed with standard payment approval queue."
    elif recommendation == "REJECT":
        recommended_action = "Reject the invoice immediately due to validation or security policies."
    else:
        recommended_action = "Review the invoice against department budget and verify deliverables before disbursement."

    findings_bullets = "\n".join(f"• {f}" for f in findings)
    
    report = (
        "VELNIX INVESTIGATION REPORT\n\n"
        "Invoice Summary\n"
        "• Invoice Number: {}\n"
        "• Vendor: {}\n"
        "• Amount: {}\n"
        "• Date: {}\n\n"
        "Overall Decision\n"
        "{}\n\n"
        "Risk Score\n"
        "{}/100\n\n"
        "Fraud Score\n"
        "{}/100\n\n"
        "Top Findings (3-5 bullets)\n"
        "{}\n\n"
        "Recommended Action\n"
        "{}\n\n"
        "Generated by VELNIX"
    ).format(
        invoice_number,
        vendor_name,
        amount_str,
        invoice_date,
        recommendation,
        risk_score,
        fraud_score,
        findings_bullets,
        recommended_action
    )
    
    return report


# =====================================================================
# SPECIALIZED AGENT INSTANCES
# =====================================================================


invoice_analysis_agent = Agent(
    name="invoice_analysis_agent",
    mode="single_turn",
    description="Extracts structured invoice fields (invoice number, vendor name, amount, PO, payment terms, dates, currency) from raw text.",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Invoice Analysis Agent.
Your sole responsibility is to extract structured invoice data from the raw text provided.
You must use the parse_invoice_tool to parse the text and return the resulting dictionary.
Do not calculate risk or fraud, and do not look up vendor profiles.""",
    tools=[parse_invoice_tool],
)

vendor_intelligence_agent = Agent(
    name="vendor_intelligence_agent",
    mode="single_turn",
    description="Retrieves the historical vendor profile and trust metrics for a given vendor name using the local ERP MCP server.",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Vendor Intelligence Agent.
Your sole responsibility is to load the historical profile for the specified vendor name.
You must invoke the `get_vendor_profile` tool on the connected MCP server to fetch the data.
The ERP database is the authoritative source of truth for vendor information. You must return the exact profile dictionary retrieved by the tool.
Do not parse invoices, calculate risk or fraud, or make any assumptions or inferences about the vendor status.""",
    tools=[erp_mcp_toolset],
)

risk_assessment_agent = Agent(
    name="risk_assessment_agent",
    mode="single_turn",
    description="Evaluates the risk score, recommendation, and positive/risk findings of an invoice against the vendor profile.",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Risk Assessment Agent.
Your sole responsibility is to calculate the risk score and make an AP recommendation.
You must read the input request and history to locate the exact output dictionary of the `parse_invoice_tool` call.
You MUST pass this dictionary as the `invoice_data` parameter to the `calculate_risk_tool` verbatim, without modifying, omitting, or defaulting any of its keys or values. Every key (such as `invoice_number`, `vendor_name`, `invoice_amount`, `invoice_date`, `due_date`, `purchase_order_number`, `currency`, `payment_terms`, `order_id`) MUST be preserved exactly as returned by the tool.
Also locate the actual vendor profile details retrieved by the vendor_intelligence_agent in the history, and pass it to `calculate_risk_tool`.
Do not infer, redefine, or contradict vendor attributes (such as vendor status, trust score, or count of previous invoices). Treat the Vendor Intelligence Agent's findings as authoritative.
Return the resulting risk assessment dictionary.
Do not parse invoices or run fraud checks.""",
    tools=[calculate_risk_tool],
)

fraud_intelligence_agent = Agent(
    name="fraud_intelligence_agent",
    mode="single_turn",
    description="Evaluates an invoice for potential fraud flags (duplicates, recent bank changes, urgent requests, extreme deviations) using the local ERP MCP server.",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Fraud Intelligence Agent.
Your sole responsibility is to run the fraud detection engine.
You must first invoke the `find_duplicate_invoice` tool on the connected MCP server to verify if the invoice number is a duplicate.
You must read the input request and history to locate the exact output dictionary of the `parse_invoice_tool` call.
You MUST pass this dictionary as the `invoice_data` parameter to the `calculate_fraud_tool` verbatim, without modifying, omitting, or defaulting any of its keys or values. Every key (such as `invoice_number`, `vendor_name`, `invoice_amount`, `invoice_date`, `due_date`, `purchase_order_number`, `currency`, `payment_terms`, `order_id`) MUST be preserved exactly as returned by the tool.
Also locate the actual vendor profile details retrieved by the vendor_intelligence_agent in the history, and pass it to `calculate_fraud_tool` along with the raw text and the duplicate check result.
Do not infer, redefine, or contradict vendor attributes (such as vendor status, trust score, or count of previous invoices). Treat the Vendor Intelligence Agent's findings as authoritative.
Return the resulting fraud assessment dictionary.
If needed, you can submit results using the MCP tool `submit_investigation_result` or view pending items using `list_pending_invoices`.""",
    tools=[erp_mcp_toolset, calculate_fraud_tool],
)

final_decision_agent = Agent(
    name="final_decision_agent",
    mode="single_turn",
    description="Compiles and formats all analysis inputs into the final branded executive investigation report.",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Final Decision Agent.
Your sole responsibility is to synthesize all findings into the final branded VELNIX INVESTIGATION REPORT.
You must read the history to locate the exact output dictionary of the `parse_invoice_tool` call.
You MUST pass this dictionary as the `invoice_data` parameter to the `compile_report_tool` verbatim, without modifying, omitting, or defaulting any of its keys or values. Every key (such as `invoice_number`, `vendor_name`, `invoice_amount`, `invoice_date`, `due_date`, `purchase_order_number`, `currency`, `payment_terms`, `order_id`) MUST be preserved exactly as returned by the tool.
Also locate the retrieved vendor profile, the risk assessment, and the fraud assessment, and pass them to `compile_report_tool`.
You must summarize the structured outputs from previous agents. Do not introduce any new vendor-related conclusions that do not appear in the Vendor Intelligence findings.
Return the complete formatted text of the report.
Do not perform any scoring or parsing calculations yourself.""",
    tools=[compile_report_tool],
)


# =====================================================================
# ROOT ORCHESTRATOR AGENT
# =====================================================================

root_agent = Agent(
    name="velnix_root_agent",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are Velnix, an AI Finance Intelligence Platform for enterprise Accounts Payable teams.
Your primary objective is to investigate vendor invoices to determine whether they should be trusted.
The ERP database is the absolute, authoritative source of truth.

When a user submits an invoice or asks to analyze an invoice, you MUST coordinate the workflow step-by-step:
1. Call `invoice_analysis_agent` with the raw invoice text to extract structured invoice data.
2. Call `vendor_intelligence_agent` with the extracted vendor name to load the vendor profile from the MCP server.
3. Call `risk_assessment_agent` passing BOTH the extracted invoice data and the actual retrieved vendor profile details (vendor_name, status, trust score, average amount, rejections, total invoices, last bank account change, vendor_found, and vendor_finding) to evaluate the risk score.
4. Call `fraud_intelligence_agent` passing BOTH the extracted invoice data and the actual retrieved vendor profile details, along with the raw invoice text, to check for fraud indicators (leveraging the MCP server for duplicate verification).
5. Call `final_decision_agent` to compile all four structures (invoice data, vendor profile, risk assessment, and fraud assessment) plus the length of the raw invoice text into the final branded report.
6. Return the resulting branded VELNIX INVESTIGATION REPORT verbatim to the user.

If a user asks a general question (like 'Why is the sky blue?'), answer it directly. Only invoke the invoice workflow when requested to investigate or analyze an invoice.""",
    sub_agents=[
        invoice_analysis_agent,
        vendor_intelligence_agent,
        risk_assessment_agent,
        fraud_intelligence_agent,
        final_decision_agent,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
