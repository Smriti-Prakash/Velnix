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


# ---------------------------------------------------------------------------
# Request-scoped canonical data store.
#
# Stores the authoritative vendor profile and invoice data for the current
# pipeline run so that downstream Python tools (calculate_risk_tool,
# calculate_fraud_tool, compile_report_tool) can retrieve the ERP-verified
# objects directly, rather than relying on LLM-reconstructed dicts passed
# through natural-language agent messages.
#
# Thread-local is appropriate here because the 13-second rate-limit enforcer
# serialises requests, and we already use the same pattern for the profiler.
# ---------------------------------------------------------------------------
_request_ctx: threading.local = threading.local()


def _set_canonical_vendor_profile(profile: dict) -> None:
    """Store the ERP-authoritative vendor profile for this request."""
    _request_ctx.vendor_profile = profile


def _get_canonical_vendor_profile() -> dict | None:
    """Return the ERP-authoritative vendor profile, or None if not yet set."""
    return getattr(_request_ctx, "vendor_profile", None)


def _set_canonical_invoice_data(data: dict) -> None:
    """Store the authoritative parsed invoice data for this request."""
    _request_ctx.invoice_data = data


def _get_canonical_invoice_data() -> dict | None:
    """Return the authoritative parsed invoice data, or None if not yet set."""
    return getattr(_request_ctx, "invoice_data", None)


def _set_canonical_risk_assessment(assessment: dict) -> None:
    """Store the canonical risk assessment for this request."""
    _request_ctx.risk_assessment = assessment


def _get_canonical_risk_assessment() -> dict | None:
    """Return the canonical risk assessment, or None if not yet set."""
    return getattr(_request_ctx, "risk_assessment", None)


def _set_canonical_fraud_assessment(assessment: dict) -> None:
    """Store the canonical fraud assessment for this request."""
    _request_ctx.fraud_assessment = assessment


def _get_canonical_fraud_assessment() -> dict | None:
    """Return the canonical fraud assessment, or None if not yet set."""
    return getattr(_request_ctx, "fraud_assessment", None)


def _clear_request_context() -> None:
    """Reset all canonical stores at the start of a new pipeline run."""
    _request_ctx.vendor_profile = None
    _request_ctx.invoice_data = None
    _request_ctx.risk_assessment = None
    _request_ctx.fraud_assessment = None

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
    from app.tools.invoice_tools import parse_invoice_with_gemini
    parsed = parse_invoice_with_gemini(invoice_text)
    result = parsed.model_dump()
    # Store as the authoritative invoice data for this request so downstream
    # tools can retrieve it directly without depending on LLM reconstruction.
    _set_canonical_invoice_data(result)
    return result


def get_vendor_profile_tool(vendor_name: str) -> dict:
    """Retrieves the ERP vendor profile and stores it as the authoritative record.

    This is a pure Python tool that calls the ERP database directly (no MCP
    subprocess round-trip). The result is stored in the request-scoped canonical
    store so that calculate_risk_tool, calculate_fraud_tool, and
    compile_report_tool can read the verified ERP data without relying on LLM
    reconstruction of the vendor profile dict.

    Args:
        vendor_name: The vendor name extracted from the invoice.

    Returns:
        A dictionary containing vendor profile fields identical in structure to
        the MCP get_vendor_profile tool response.
    """
    from app.erp.queries import fetch_vendor_by_name, fetch_invoice_history_by_vendor_name

    normalized = vendor_name.strip() if vendor_name else ""
    if normalized:
        try:
            vendor = fetch_vendor_by_name(normalized)
            if vendor:
                history = fetch_invoice_history_by_vendor_name(normalized)
                last_invoice_date = history[0].invoice_date if history else "N/A"
                profile = {
                    "vendor_id": vendor.vendor_id,
                    "vendor_name": vendor.vendor_name,
                    "vendor_status": vendor.vendor_status,
                    "trust_score": vendor.trust_score,
                    "average_invoice_amount": vendor.average_invoice_amount,
                    "total_previous_invoices": vendor.total_previous_invoices,
                    "previous_rejections": vendor.previous_rejections,
                    "last_bank_account_change": vendor.last_bank_account_change or "N/A",
                    "bank_account": vendor.bank_account or "N/A",
                    "risk_level": vendor.risk_level,
                    "last_invoice_date": last_invoice_date,
                    "vendor_found": True,
                    "vendor_finding": (
                        f"Vendor {vendor.vendor_name} was found in the ERP vendor master "
                        f"and is classified as a {vendor.vendor_status} vendor."
                    ),
                }
                _set_canonical_vendor_profile(profile)
                return profile
        except Exception:
            pass

    # Graceful fallback — vendor not in ERP master.
    profile = {
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
        "last_invoice_date": "N/A",
        "vendor_found": False,
        "vendor_finding": (
            "Vendor was not found in the ERP vendor master. "
            "Vendor verification could not be completed."
        ),
    }
    _set_canonical_vendor_profile(profile)
    return profile


def calculate_risk_tool(invoice_data: dict, vendor_profile: dict) -> dict:
    """Deterministic tool to assess risk comparing invoice to vendor profile history.

    Uses the ERP-authoritative vendor profile from the request context (set by
    get_vendor_profile_tool) so that LLM reconstruction of the vendor_profile
    dict argument cannot cause field loss.

    Args:
        invoice_data: Dictionary of parsed invoice fields (used as LLM hint;
            the canonical version from parse_invoice_tool is preferred).
        vendor_profile: Dictionary of vendor profile (used as LLM hint;
            the canonical version from get_vendor_profile_tool is preferred).

    Returns:
        A dictionary containing RiskAssessment fields.
    """
    from app.tools.invoice_tools import InvoiceData
    from app.tools.vendor_intelligence import VendorProfile
    from app.tools.risk_engine import calculate_risk

    # Prefer ERP-authoritative data over LLM-reconstructed dicts.
    canonical_inv = _get_canonical_invoice_data()
    if canonical_inv:
        invoice_data = canonical_inv

    canonical_vend = _get_canonical_vendor_profile()
    if canonical_vend:
        vendor_profile = canonical_vend

    normalized_inv = normalize_invoice_data(invoice_data)
    normalized_vend = normalize_vendor_profile(vendor_profile, normalized_inv)

    inv = InvoiceData(**normalized_inv)
    vend = VendorProfile(**normalized_vend)
    assessment = calculate_risk(inv, vend)
    res = assessment.model_dump()
    _set_canonical_risk_assessment(res)
    return res


def calculate_fraud_tool(invoice_data: dict, vendor_profile: dict, invoice_text: str, is_duplicate: bool = None) -> dict:
    """Deterministic tool to assess transaction fraud flags.

    Uses the ERP-authoritative vendor profile from the request context (set by
    get_vendor_profile_tool) so that LLM reconstruction cannot cause field loss.

    Args:
        invoice_data: Dictionary of parsed invoice fields (LLM hint; canonical preferred).
        vendor_profile: Dictionary of vendor profile (LLM hint; canonical preferred).
        invoice_text: Raw invoice text.
        is_duplicate: Optional override. If provided, skips the DB duplicate lookup.

    Returns:
        A dictionary containing FraudAssessment fields.
    """
    from app.tools.invoice_tools import InvoiceData
    from app.tools.vendor_intelligence import VendorProfile
    from app.tools.fraud_engine import calculate_fraud

    # Prefer ERP-authoritative data over LLM-reconstructed dicts.
    canonical_inv = _get_canonical_invoice_data()
    if canonical_inv:
        invoice_data = canonical_inv

    canonical_vend = _get_canonical_vendor_profile()
    if canonical_vend:
        vendor_profile = canonical_vend

    normalized_inv = normalize_invoice_data(invoice_data)
    normalized_vend = normalize_vendor_profile(vendor_profile, normalized_inv)

    inv = InvoiceData(**normalized_inv)
    vend = VendorProfile(**normalized_vend)
    assessment = calculate_fraud(inv, vend, invoice_text, is_duplicate)
    res = assessment.model_dump()
    _set_canonical_fraud_assessment(res)
    return res


def compile_report_tool(
    invoice_data: dict,
    vendor_profile: dict,
    risk_assessment: dict,
    fraud_assessment: dict,
    invoice_text_len: int,
) -> str:
    """Formats and compiles all assessments into the branded VELNIX INVESTIGATION REPORT.

    This function is a PURE PRESENTATION LAYER. It must not introduce, suppress,
    or contradict any finding produced by upstream agents. Every bullet in the
    Top Findings section originates exclusively from the structured outputs of
    the Risk Assessment, Fraud Assessment, and Vendor Intelligence agents, or
    from deterministic ERP validation results.

    Recommendation displayed is the highest-severity value produced by the
    investigation pipeline (APPROVE < REVIEW < INVESTIGATE < REJECT). REJECT
    fires only when a confirmed duplicate is present in fraud_flags — never from
    a score threshold alone.

    Retrieves ERP-authoritative invoice_data and vendor_profile from the request
    context (populated by parse_invoice_tool and get_vendor_profile_tool) so that
    LLM reconstruction of the dict arguments cannot cause field loss.
    """
    # Override LLM-passed dicts with ERP-authoritative canonical versions.
    canonical_inv = _get_canonical_invoice_data()
    if canonical_inv:
        invoice_data = canonical_inv

    canonical_vend = _get_canonical_vendor_profile()
    if canonical_vend:
        vendor_profile = canonical_vend

    canonical_risk = _get_canonical_risk_assessment()
    if canonical_risk:
        risk_assessment = canonical_risk

    canonical_fraud = _get_canonical_fraud_assessment()
    if canonical_fraud:
        fraud_assessment = canonical_fraud

    # ── Invoice summary fields ────────────────────────────────────────────────
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

    # ── Structured outputs from upstream agents ───────────────────────────────
    risk_score = risk_assessment.get("risk_score") or 0
    fraud_score = fraud_assessment.get("fraud_score") or 0
    fraud_flags = fraud_assessment.get("fraud_flags") or []
    risk_findings = risk_assessment.get("risk_findings") or []
    vendor_finding = vendor_profile.get("vendor_finding") or ""
    vendor_status = vendor_profile.get("vendor_status") or "New"
    vendor_found = vendor_profile.get("vendor_found", False)
    po = invoice_data.get("purchase_order_number")

    # ── 1. Determine final recommendation ────────────────────────────────────
    # Severity ladder: APPROVE(0) < REVIEW(1) < INVESTIGATE(2) < REJECT(3)
    # The compiler never independently escalates or downgrade; it selects the
    # highest-severity value already produced by the pipeline.
    _SEVERITY = {"APPROVE": 0, "REVIEW": 1, "INVESTIGATE": 2, "REJECT": 3}

    # REJECT fires only on a confirmed duplicate (deterministic fraud condition).
    is_confirmed_duplicate = any(
        "duplicate" in flag.lower() for flag in fraud_flags
    )

    risk_rec = risk_assessment.get("recommendation") or "REVIEW"
    # Fraud engine conveys its severity through investigation_required.
    fraud_rec = "INVESTIGATE" if fraud_assessment.get("investigation_required") else "APPROVE"

    if is_confirmed_duplicate:
        pipeline_recommendation = "REJECT"
    else:
        pipeline_recommendation = (
            risk_rec
            if _SEVERITY.get(risk_rec, 1) >= _SEVERITY.get(fraud_rec, 1)
            else fraud_rec
        )

    # ── 2. Build Top Findings — zero invented content ─────────────────────────
    # Priority order (highest to lowest):
    #   1. Fraud flags        — always first; never suppressed
    #   2. Risk findings      — deterministic engine output
    #   3. Vendor finding     — authoritative ERP record
    #   4. ERP/PO note        — deterministic validation
    #
    # "No anomalies detected" is ONLY inserted when ALL three upstream agents
    # return empty findings. It is NEVER used as a padding bullet.
    raw_findings: list[str] = []

    for ff in fraud_flags:
        raw_findings.append(ff.strip())

    for rf in risk_findings:
        raw_findings.append(rf.strip())

    if vendor_finding:
        raw_findings.append(vendor_finding.strip())

    if not po:
        raw_findings.append(
            "No Purchase Order reference was provided in the uploaded invoice. "
            "Purchase Order validation could not be performed."
        )
    else:
        raw_findings.append(f"The invoice references Purchase Order {po}.")

    # Deduplicate while preserving priority order.
    seen: set = set()
    unique_findings: list[str] = []
    for f in raw_findings:
        key = f.strip().lower()
        if key not in seen:
            seen.add(key)
            unique_findings.append(f.strip())

    # Insert "no anomalies" only when there are genuinely no upstream findings.
    has_upstream_findings = bool(fraud_flags or risk_findings or vendor_finding)
    if not has_upstream_findings:
        unique_findings.insert(
            0,
            "No anomalies or billing deviations were detected for this transaction.",
        )

    # Cap at 5. Fraud flags are added first so they are the last to be truncated.
    findings = unique_findings[:5]

    # ── 3. Recommended Action — derived from pipeline outputs only ────────────
    if pipeline_recommendation == "REJECT":
        recommended_action = (
            "Reject the invoice immediately to prevent double payment; "
            "contact the vendor to resolve."
        )
    elif pipeline_recommendation == "INVESTIGATE":
        if not vendor_found:
            recommended_action = (
                "This vendor was not found in the ERP vendor master. "
                "Payment should remain on hold until vendor verification is complete."
            )
        elif vendor_status == "Watchlist":
            recommended_action = (
                "Perform enhanced due diligence and obtain senior AP management "
                "approval before proceeding."
            )
        elif any("bank" in flag.lower() for flag in fraud_flags):
            recommended_action = (
                "Verify bank details directly with a known contact at the vendor "
                "via a secondary channel before authorizing payment."
            )
        else:
            recommended_action = (
                "Place this invoice on hold pending a formal AP investigation. "
                "Do not disburse until all anomalies are fully resolved."
            )
    elif pipeline_recommendation == "REVIEW":
        if vendor_status == "New":
            if not po:
                recommended_action = (
                    "This invoice was submitted by a newly onboarded vendor. "
                    "No Purchase Order reference was provided; payment should remain "
                    "on hold until Procurement verifies the transaction."
                )
            else:
                recommended_action = (
                    "Verify new vendor bank details against the provided Purchase "
                    "Order reference before authorizing."
                )
        else:
            recommended_action = (
                "Review the invoice against department budget and verify deliverables "
                "before disbursement."
            )
    else:  # APPROVE
        recommended_action = "Proceed with standard payment approval queue."

    # ── 4. Format report ──────────────────────────────────────────────────────
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
        pipeline_recommendation,
        risk_score,
        fraud_score,
        findings_bullets,
        recommended_action,
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
    description="Retrieves the ERP vendor profile and trust metrics for a given vendor name using the Python ERP tool.",
    model=Gemini(
        model="gemini-3.1-flash-lite",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Vendor Intelligence Agent.
Your sole responsibility is to load the ERP vendor profile for the specified vendor name.
You MUST call the `get_vendor_profile_tool` with the exact vendor name string extracted from the invoice.
Do not paraphrase, translate, or modify the vendor name before passing it to the tool.
The ERP database is the absolute authoritative source of truth. Return the exact profile dictionary retrieved by the tool verbatim.
Do not parse invoices, calculate risk or fraud, or make any assumptions or inferences about the vendor status or trust score.""",
    tools=[get_vendor_profile_tool],
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
Return the resulting fraud assessment dictionary.""",
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
