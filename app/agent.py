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
from dotenv import load_dotenv

load_dotenv()


# =====================================================================
# NATIVE MCP TOOLSET CONNECTION
# =====================================================================

erp_mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "python", "app/mcp/server.py"],
    )
)


# =====================================================================
# DETERMINISTIC AGENT TOOLS
# =====================================================================

def parse_invoice_tool(invoice_text: str) -> dict:
    """Deterministic tool to parse raw invoice text and extract structured fields.

    Args:
        invoice_text: The raw invoice text.

    Returns:
        A dictionary containing parsed invoice fields (invoice_number, vendor_name, etc.).
    """
    from app.tools.invoice_tools import parse_invoice
    parsed = parse_invoice(invoice_text)
    return parsed.model_dump()


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
    inv = InvoiceData(**invoice_data)
    vend = VendorProfile(**vendor_profile)
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
    inv = InvoiceData(**invoice_data)
    vend = VendorProfile(**vendor_profile)
    assessment = calculate_fraud(inv, vend, invoice_text, is_duplicate)
    return assessment.model_dump()


def compile_report_tool(
    invoice_data: dict,
    vendor_profile: dict,
    risk_assessment: dict,
    fraud_assessment: dict,
    invoice_text_len: int
) -> str:
    """Formats and compiles all assessments into the branded VELNIX INITIAL INVESTIGATION REPORT.

    Args:
        invoice_data: The dictionary of parsed invoice fields.
        vendor_profile: The dictionary of vendor profile fields.
        risk_assessment: The dictionary of risk assessment fields.
        fraud_assessment: The dictionary of fraud assessment fields.
        invoice_text_len: The length of the raw invoice text.

    Returns:
        Formatted string containing the branded investigation report.
    """
    # 1. Format parsed fields block
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
        invoice_data.get("invoice_number"),
        invoice_data.get("vendor_name"),
        invoice_data.get("invoice_date"),
        invoice_data.get("due_date"),
        invoice_data.get("purchase_order_number"),
        invoice_data.get("currency"),
        invoice_data.get("invoice_amount"),
        invoice_data.get("payment_terms"),
    )

    # 2. Format Vendor Intelligence block
    alerts = []
    status = vendor_profile.get("vendor_status")
    trust_score = vendor_profile.get("trust_score", 0)
    avg_amt = vendor_profile.get("average_invoice_amount", 0.0)
    total_inv = vendor_profile.get("total_previous_invoices", 0)
    inv_amt = invoice_data.get("invoice_amount")
    curr = invoice_data.get("currency") or ""
    
    if status == "New":
        alerts.append("- NOTICE: Vendor is New/Unverified. No prior invoice history.")
    elif status == "Watchlist":
        alerts.append(f"- WARNING: Vendor is on the Watchlist! Trust score is {trust_score}/100.")

    if inv_amt is not None and total_inv > 0:
        if inv_amt > 1.5 * avg_amt:
            ratio = inv_amt / avg_amt
            alerts.append(
                f"- WARNING: Current invoice amount ({curr}{inv_amt:,.2f}) "
                f"is unusually high ({ratio:.1f}x the historical average of "
                f"{curr}{avg_amt:,.2f})."
            )

    alerts_text = "\n    ".join(alerts) if alerts else "- No critical alerts found."

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
        vendor_profile.get("vendor_name"),
        status,
        trust_score,
        total_inv,
        avg_amt,
        vendor_profile.get("previous_rejections", 0),
        vendor_profile.get("last_bank_account_change"),
        alerts_text,
    )

    # 3. Format Evidence Summary block
    pos_findings = risk_assessment.get("positive_findings", [])
    risk_findings = risk_assessment.get("risk_findings", [])
    evidence = risk_assessment.get("evidence", [])
    
    pos_findings_lines = "\n  ".join(f"- {f}" for f in pos_findings) if pos_findings else "  - None"
    risk_findings_lines = "\n  ".join(f"- {f}" for f in risk_findings) if risk_findings else "  - None"
    evidence_lines = "\n  ".join(f"- {f}" for f in evidence)

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
        risk_assessment.get("risk_score"),
        risk_assessment.get("recommendation"),
        risk_assessment.get("final_reasoning")
    )

    # 4. Format Fraud Intelligence block
    fraud_flags = fraud_assessment.get("fraud_flags", [])
    fraud_flags_lines = "\n  ".join(f"- {f}" for f in fraud_flags) if fraud_flags else "  - None"

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
        fraud_assessment.get("fraud_score"),
        fraud_assessment.get("confidence_level"),
        "YES" if fraud_assessment.get("investigation_required") else "NO",
        fraud_flags_lines.replace("\n", "\n    "),
        fraud_assessment.get("explanation").replace("\n", "\n    ")
    )

    # 5. Format final report
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
        invoice_text_len,
        risk_assessment.get("recommendation"),
        risk_assessment.get("risk_score"),
        fraud_assessment.get("fraud_score"),
    )

    return report


# =====================================================================
# SPECIALIZED AGENT INSTANCES
# =====================================================================

invoice_analysis_agent = Agent(
    name="invoice_analysis_agent",
    description="Extracts structured invoice fields (invoice number, vendor name, amount, PO, payment terms, dates, currency) from raw text.",
    model=Gemini(
        model="gemini-flash-latest",
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
    description="Retrieves the historical vendor profile and trust metrics for a given vendor name using the local ERP MCP server.",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Vendor Intelligence Agent.
Your sole responsibility is to load the historical profile for the specified vendor name.
You must invoke the `get_vendor_profile` tool on the connected MCP server to fetch the data.
Return the resulting profile dictionary.
Do not parse invoices or calculate risk or fraud.""",
    tools=[erp_mcp_toolset],
)

risk_assessment_agent = Agent(
    name="risk_assessment_agent",
    description="Evaluates the risk score, recommendation, and positive/risk findings of an invoice against the vendor profile.",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Risk Assessment Agent.
Your sole responsibility is to calculate the risk score and make an AP recommendation.
You must use the calculate_risk_tool, passing the extracted invoice fields and vendor profile.
Return the resulting risk assessment dictionary.
Do not parse invoices or run fraud checks.""",
    tools=[calculate_risk_tool],
)

fraud_intelligence_agent = Agent(
    name="fraud_intelligence_agent",
    description="Evaluates an invoice for potential fraud flags (duplicates, recent bank changes, urgent requests, extreme deviations) using the local ERP MCP server.",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Fraud Intelligence Agent.
Your sole responsibility is to run the fraud detection engine.
You must first invoke the `find_duplicate_invoice` tool on the connected MCP server to verify if the invoice number is a duplicate.
Then call `calculate_fraud_tool` passing the duplicate check result, along with the invoice data, vendor profile, and raw text.
Return the resulting fraud assessment dictionary.
If needed, you can submit results using the MCP tool `submit_investigation_result` or view pending items using `list_pending_invoices`.""",
    tools=[erp_mcp_toolset, calculate_fraud_tool],
)

final_decision_agent = Agent(
    name="final_decision_agent",
    description="Compiles and formats all analysis inputs into the final branded executive investigation report.",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the Final Decision Agent.
Your sole responsibility is to synthesize all findings into the final branded VELNIX INITIAL INVESTIGATION REPORT.
You must use the compile_report_tool to format the inputs (parsed invoice, vendor intelligence, risk assessment, fraud assessment) and raw text length into the branded report.
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
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are Velnix, an AI Finance Intelligence Platform for enterprise Accounts Payable teams.
Your primary objective is to investigate vendor invoices to determine whether they should be trusted.

When a user submits an invoice or asks to analyze an invoice, you MUST coordinate the workflow step-by-step using your sub-agents:
1. Transfer to `invoice_analysis_agent` with the raw invoice text to extract structured invoice data.
2. Transfer to `vendor_intelligence_agent` with the extracted vendor name to load the vendor profile from the MCP server.
3. Transfer to `risk_assessment_agent` with the invoice data and vendor profile to evaluate the risk score.
4. Transfer to `fraud_intelligence_agent` with the invoice data, vendor profile, and raw invoice text to check for fraud indicators (leveraging the MCP server for duplicate verification).
5. Transfer to `final_decision_agent` to compile all four structures (invoice data, vendor profile, risk assessment, and fraud assessment) plus the length of the raw invoice text into the final branded report.
6. Return the resulting branded VELNIX INITIAL INVESTIGATION REPORT verbatim to the user.

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
