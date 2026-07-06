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

"""
Integration tests that verify structural consistency between the deterministic
engine outputs (Risk Assessment, Fraud Assessment, Vendor Intelligence) and the
generated Executive Investigation Report.

These tests call compile_report_tool directly with controlled structured inputs,
without running the full multi-agent pipeline. They act as a regression guard:
future changes to compile_report_tool cannot introduce contradictions without
breaking these tests.

Design principles:
- All inputs are fully deterministic (no LLM, no MCP, no DB calls).
- The canonical context is cleared before every test so no state bleeds between
  runs.
- Each test targets a single consistency contract.
"""

import pytest
from app.agent import compile_report_tool, _clear_request_context


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures and helpers
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_ctx():
    """Ensure the request-scoped canonical context is empty for every test.
    This forces compile_report_tool to use the dicts passed directly rather
    than any cached value from a prior pipeline run."""
    _clear_request_context()
    yield
    _clear_request_context()


def _invoice(
    number="INV-TEST-001",
    vendor="Acme Corp",
    amount=1_000.0,
    po="PO-001",
    currency="$",
    date="2026-07-01",
    terms="Net 30",
) -> dict:
    return {
        "invoice_number": number,
        "vendor_name": vendor,
        "invoice_date": date,
        "invoice_amount": amount,
        "currency": currency,
        "purchase_order_number": po,
        "due_date": None,
        "payment_terms": terms,
        "order_id": None,
    }


def _vendor(
    name="Acme Corp",
    status="Trusted",
    found=True,
    trust=85,
    avg_amount=900.0,
    invoices=12,
    finding: str | None = None,
) -> dict:
    finding_text = finding if finding is not None else (
        f"Vendor {name} was found in the ERP vendor master and is classified as a {status} vendor."
    )
    return {
        "vendor_id": 1,
        "vendor_name": name,
        "vendor_status": status,
        "trust_score": trust,
        "average_invoice_amount": avg_amount,
        "total_previous_invoices": invoices,
        "previous_rejections": 0,
        "last_bank_account_change": "N/A",
        "vendor_found": found,
        "vendor_finding": finding_text,
    }


def _risk(
    score=25,
    recommendation="APPROVE",
    risk_findings: list | None = None,
    positive_findings: list | None = None,
) -> dict:
    return {
        "risk_score": score,
        "recommendation": recommendation,
        "risk_findings": risk_findings or [],
        "positive_findings": positive_findings or ["All checks passed."],
        "evidence": [],
        "final_reasoning": "Deterministic engine output.",
    }


def _fraud(
    score=0,
    flags: list | None = None,
    investigation_required=False,
    confidence="LOW",
) -> dict:
    return {
        "fraud_score": score,
        "fraud_flags": flags or [],
        "investigation_required": investigation_required,
        "confidence_level": confidence,
        "explanation": "Deterministic engine output.",
    }


def _report(*args, **kwargs) -> str:
    """Thin wrapper: calls compile_report_tool with invoice_text_len=200."""
    return compile_report_tool(*args, **kwargs, invoice_text_len=200)


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Amount anomaly from Risk Assessment appears in the Executive Report
# ─────────────────────────────────────────────────────────────────────────────

def test_amount_anomaly_from_risk_appears_in_report():
    """If risk_engine flags an invoice-amount anomaly the finding must appear
    in the Top Findings section of the Executive Report verbatim (or at least
    a distinguishing substring thereof)."""
    anomaly = (
        "Invoice amount ($5,000.00) is unusually high: "
        "5.6x the historical average for this vendor ($900.00)."
    )
    risk = _risk(score=55, recommendation="INVESTIGATE", risk_findings=[anomaly])
    fraud = _fraud()
    inv = _invoice(amount=5_000.0)
    vend = _vendor()

    report = _report(inv, vend, risk, fraud)

    assert "unusually high" in report.lower() or "5.6x" in report or "5,000.00" in report, (
        "Amount anomaly flagged by the risk engine must appear in the Executive Report.\n"
        f"Report:\n{report}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Confirmed duplicate → REJECT + no "no anomalies" claim
# ─────────────────────────────────────────────────────────────────────────────

def test_confirmed_duplicate_produces_reject_and_suppresses_no_anomaly():
    """A confirmed-duplicate fraud flag must produce Overall Decision = REJECT.
    The report must not state that no anomalies were detected."""
    dup_flag = (
        "CRITICAL: Duplicate Invoice Number detected. "
        "'INV-TEST-001' was already processed in history."
    )
    fraud = _fraud(score=50, flags=[dup_flag], investigation_required=True, confidence="HIGH")
    risk = _risk(score=30, recommendation="REVIEW")
    inv = _invoice()
    vend = _vendor()

    report = _report(inv, vend, risk, fraud)

    assert "REJECT" in report, (
        "A confirmed-duplicate must produce REJECT in the Executive Report.\n"
        f"Report:\n{report}"
    )
    assert "no anomalies" not in report.lower(), (
        "Report must not claim 'no anomalies' when a confirmed duplicate exists.\n"
        f"Report:\n{report}"
    )
    # The duplicate flag itself must appear in findings.
    assert "duplicate" in report.lower() or "Duplicate" in report, (
        "The duplicate fraud flag must appear in the report findings.\n"
        f"Report:\n{report}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Every fraud finding appears in the Executive Report
# ─────────────────────────────────────────────────────────────────────────────

def test_all_fraud_flags_appear_in_report():
    """Every fraud_flag item produced by the fraud engine must be represented
    in the report body. Fraud flags have the highest priority and are the last
    to be truncated by the 5-bullet cap."""
    flags = [
        "HIGH: Vendor bank account changed recently on 2026-06-15 (within 60 days).",
        "LOW: Missing Purchase Order (PO) reference.",
    ]
    fraud = _fraud(score=40, flags=flags, investigation_required=True, confidence="HIGH")
    risk = _risk(score=40, recommendation="INVESTIGATE")
    inv = _invoice(po=None)
    vend = _vendor()

    report = _report(inv, vend, risk, fraud)

    assert "bank account changed recently" in report.lower(), (
        "Bank-account-change fraud flag must appear in the report.\n"
        f"Report:\n{report}"
    )
    assert "purchase order" in report.lower() or "PO" in report, (
        "Missing-PO fraud flag must appear in the report.\n"
        f"Report:\n{report}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Every risk finding appears in the Executive Report
# ─────────────────────────────────────────────────────────────────────────────

def test_all_risk_findings_appear_in_report():
    """Every risk_finding returned by the risk engine must appear in the report.
    Risk findings have second-highest priority after fraud flags."""
    rf1 = "Vendor is NEW/UNVERIFIED in the master database (no prior transaction history)."
    rf2 = "Missing Purchase Order (PO) reference on the invoice."

    risk = _risk(score=45, recommendation="REVIEW", risk_findings=[rf1, rf2])
    fraud = _fraud(score=10)
    inv = _invoice(po=None)
    vend = _vendor(status="New")

    report = _report(inv, vend, risk, fraud)

    assert "NEW/UNVERIFIED" in report or "no prior transaction history" in report.lower(), (
        f"New-vendor risk finding must appear in the report.\nReport:\n{report}"
    )
    assert "Purchase Order" in report or "PO" in report, (
        f"Missing-PO risk finding must appear in the report.\nReport:\n{report}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Clean invoice: "No anomalies detected" once, no phantom findings
# ─────────────────────────────────────────────────────────────────────────────

def test_clean_invoice_no_phantom_findings():
    """A genuinely clean invoice with no upstream findings must show 'no anomalies'
    exactly once and must not include any invented content."""
    risk = _risk(score=10, recommendation="APPROVE", risk_findings=[], positive_findings=[])
    fraud = _fraud(score=0, flags=[], investigation_required=False)
    # Empty vendor_finding so there are truly no upstream findings.
    vend = _vendor(finding="")
    inv = _invoice()

    report = _report(inv, vend, risk, fraud)

    count = report.lower().count("no anomalies")
    assert count == 1, (
        f"'No anomalies' should appear exactly once in a clean report; found {count}.\n"
        f"Report:\n{report}"
    )
    assert "APPROVE" in report, (
        f"Clean invoice should produce APPROVE recommendation.\nReport:\n{report}"
    )
    # The report must not invent extra bullet points beyond the no-anomalies line
    # and the PO note (if PO is present, the PO note is presentational).
    bullets = [line for line in report.splitlines() if line.startswith("•") and "Invoice" not in line
               and "Vendor" not in line and "Amount" not in line and "Date" not in line]
    for b in bullets:
        assert "no anomalies" in b.lower() or "purchase order" in b.lower() or "references" in b.lower(), (
            f"Unexpected invented finding in clean report: {b!r}\nReport:\n{report}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — High fraud score without confirmed duplicate → INVESTIGATE, not REJECT
# ─────────────────────────────────────────────────────────────────────────────

def test_high_fraud_score_without_duplicate_produces_investigate_not_reject():
    """A high fraud score (≥ 50) that does NOT contain a confirmed-duplicate flag
    must produce INVESTIGATE, never REJECT. REJECT is only for confirmed duplicates."""
    flags = [
        "HIGH: Vendor bank account changed recently on 2026-06-15 (within 60 days).",
        "HIGH: Invoice amount ($9,000.00) is significantly larger than historical average "
        "($900.00) by 10.0x (threshold is >3x).",
    ]
    fraud = _fraud(score=60, flags=flags, investigation_required=True, confidence="HIGH")
    risk = _risk(score=60, recommendation="INVESTIGATE")
    inv = _invoice(amount=9_000.0)
    vend = _vendor()

    report = _report(inv, vend, risk, fraud)

    assert "REJECT" not in report, (
        "REJECT must not appear when there is no confirmed duplicate, "
        f"even if fraud_score is high.\nReport:\n{report}"
    )
    assert "INVESTIGATE" in report, (
        "High fraud score without confirmed duplicate should produce INVESTIGATE.\n"
        f"Report:\n{report}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 7a — Contradiction guard: findings exist → "no anomalies" must not appear
# ─────────────────────────────────────────────────────────────────────────────

def test_no_anomalies_absent_when_risk_findings_exist():
    """If risk_findings is non-empty the report must never state 'no anomalies'."""
    risk = _risk(
        score=45,
        recommendation="REVIEW",
        risk_findings=["Missing Purchase Order (PO) reference on the invoice."],
    )
    fraud = _fraud()
    inv = _invoice(po=None)
    vend = _vendor()

    report = _report(inv, vend, risk, fraud)

    assert "no anomalies" not in report.lower(), (
        "Report must not state 'no anomalies' when risk_findings are present.\n"
        f"Report:\n{report}"
    )


def test_no_anomalies_absent_when_fraud_flags_exist():
    """If fraud_flags is non-empty the report must never state 'no anomalies'."""
    fraud = _fraud(
        score=40,
        flags=["HIGH: Vendor bank account changed recently on 2026-06-15 (within 60 days)."],
        investigation_required=True,
    )
    risk = _risk(score=20, recommendation="APPROVE")
    inv = _invoice()
    vend = _vendor()

    report = _report(inv, vend, risk, fraud)

    assert "no anomalies" not in report.lower(), (
        "Report must not state 'no anomalies' when fraud_flags are present.\n"
        f"Report:\n{report}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 7b — investigation_required=True escalates to INVESTIGATE
# ─────────────────────────────────────────────────────────────────────────────

def test_investigation_required_escalates_recommendation():
    """When fraud_assessment.investigation_required is True the pipeline
    recommendation must be at least INVESTIGATE (not APPROVE or REVIEW)."""
    flags = [
        "HIGH: Vendor bank account changed recently on 2026-06-10 (within 60 days)."
    ]
    fraud = _fraud(score=30, flags=flags, investigation_required=True, confidence="HIGH")
    # Risk engine only says REVIEW — fraud engine must escalate to INVESTIGATE.
    risk = _risk(score=25, recommendation="REVIEW")
    inv = _invoice()
    vend = _vendor()

    report = _report(inv, vend, risk, fraud)

    has_high_severity = "INVESTIGATE" in report or "REJECT" in report
    assert has_high_severity, (
        "When investigation_required=True the recommendation must be INVESTIGATE or REJECT, "
        f"not APPROVE or REVIEW.\nReport:\n{report}"
    )
    assert "APPROVE" not in report or "INVESTIGATE" in report or "REJECT" in report, (
        f"APPROVE must not be the final recommendation when investigation_required=True.\nReport:\n{report}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 7c — Every recommendation is consistent with investigation outputs
# ─────────────────────────────────────────────────────────────────────────────

def test_approve_only_when_no_investigation_required_and_low_risk():
    """APPROVE must only appear when both risk score is low and the fraud engine
    does not require investigation."""
    risk = _risk(score=15, recommendation="APPROVE")
    fraud = _fraud(score=0, flags=[], investigation_required=False)
    inv = _invoice()
    vend = _vendor(status="Trusted", trust=90)

    report = _report(inv, vend, risk, fraud)

    assert "APPROVE" in report, (
        f"Low risk, no fraud findings should produce APPROVE.\nReport:\n{report}"
    )
    assert "INVESTIGATE" not in report, (
        f"INVESTIGATE must not appear for a genuinely clean low-risk invoice.\nReport:\n{report}"
    )
    assert "REJECT" not in report, (
        f"REJECT must not appear for a genuinely clean low-risk invoice.\nReport:\n{report}"
    )
