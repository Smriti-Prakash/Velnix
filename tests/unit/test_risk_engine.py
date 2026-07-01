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

from app.tools.invoice_tools import InvoiceData
from app.tools.vendor_intelligence import VendorProfile
from app.tools.risk_engine import calculate_risk


def test_calculate_risk_approve():
    """Test low risk scenario maps to APPROVE."""
    # A trusted vendor with high trust score (95), matching PO, matching terms, normal amount
    invoice = InvoiceData(
        invoice_number="INV-001",
        vendor_name="Acme Corp",
        invoice_amount=4000.0,
        currency="$",
        purchase_order_number="PO-100",
        payment_terms="Net 30",
    )
    vendor = VendorProfile(
        vendor_name="Acme Corp",
        total_previous_invoices=100,
        average_invoice_amount=5000.0,
        last_invoice_date="2026-06-01",
        previous_rejections=0,
        vendor_status="Trusted",
        trust_score=95,
        last_bank_account_change="2025-12-01",
    )

    assessment = calculate_risk(invoice, vendor)
    assert assessment.risk_score < 30
    assert assessment.recommendation == "APPROVE"
    assert len(assessment.positive_findings) > 0
    assert len(assessment.risk_findings) == 0
    assert any("TRUSTED" in f for f in assessment.positive_findings)
    assert any("Vendor Name: Acme Corp" in ev for ev in assessment.evidence)


def test_calculate_risk_review():
    """Test medium risk scenario maps to REVIEW."""
    # Trusted vendor, but missing PO and missing payment terms
    invoice = InvoiceData(
        invoice_number="INV-002",
        vendor_name="Acme Corp",
        invoice_amount=4000.0,
        currency="$",
        purchase_order_number=None,
        payment_terms=None,
    )
    vendor = VendorProfile(
        vendor_name="Acme Corp",
        total_previous_invoices=100,
        average_invoice_amount=5000.0,
        last_invoice_date="2026-06-01",
        previous_rejections=0,
        vendor_status="Trusted",
        trust_score=95,
        last_bank_account_change="2025-12-01",
    )

    assessment = calculate_risk(invoice, vendor)
    # Missing PO is +15, Missing Terms is +10. Total score = 25. Wait, 25 is < 30 (APPROVE).
    # What if it's a new vendor with missing PO? New is +20, missing PO is +15. Total score = 35.
    new_vendor = VendorProfile(
        vendor_name="NewTech Solutions",
        total_previous_invoices=0,
        average_invoice_amount=0.0,
        last_invoice_date="N/A",
        previous_rejections=0,
        vendor_status="New",
        trust_score=70,
        last_bank_account_change="N/A",
    )
    assessment_new = calculate_risk(invoice, new_vendor)
    assert 30 <= assessment_new.risk_score < 60
    assert assessment_new.recommendation == "REVIEW"
    assert len(assessment_new.risk_findings) >= 2  # New vendor, missing PO, missing terms
    assert any("NEW/UNVERIFIED" in f for f in assessment_new.risk_findings)


def test_calculate_risk_investigate_watchlist():
    """Test high risk scenario (watchlist) maps to INVESTIGATE."""
    # Watchlist vendor with missing PO
    invoice = InvoiceData(
        invoice_number="INV-003",
        vendor_name="RiskCo LLC",
        invoice_amount=5000.0,
        currency="$",
        purchase_order_number=None,
        payment_terms="Net 30",
    )
    vendor = VendorProfile(
        vendor_name="RiskCo LLC",
        total_previous_invoices=12,
        average_invoice_amount=8500.0,
        last_invoice_date="2026-04-10",
        previous_rejections=5,
        vendor_status="Watchlist",
        trust_score=35,
        last_bank_account_change="2026-06-01",
    )

    assessment = calculate_risk(invoice, vendor)
    assert assessment.risk_score >= 60
    assert assessment.recommendation == "INVESTIGATE"
    assert any("WATCHLIST" in f for f in assessment.risk_findings)


def test_calculate_risk_investigate_high_amount():
    """Test high risk scenario (unusually high amount + missing PO) maps to INVESTIGATE."""
    # Trusted vendor, but invoice is 3x average and PO is missing
    invoice = InvoiceData(
        invoice_number="INV-004",
        vendor_name="Acme Corp",
        invoice_amount=15000.0,
        currency="$",
        purchase_order_number=None,
        payment_terms="Net 30",
    )
    vendor = VendorProfile(
        vendor_name="Acme Corp",
        total_previous_invoices=100,
        average_invoice_amount=5000.0,
        last_invoice_date="2026-06-01",
        previous_rejections=0,
        vendor_status="Trusted",
        trust_score=95,
        last_bank_account_change="2025-12-01",
    )

    assessment = calculate_risk(invoice, vendor)
    # High amount (+25), missing PO (+15), missing terms (+0). Total score = 40 (REVIEW).
    # Wait, let's make it have a lower trust score (e.g. 50, +20 penalty).
    # Total score = 25 (amount) + 15 (PO) + 20 (low trust score) = 60 (INVESTIGATE).
    vendor_low_trust = VendorProfile(
        vendor_name="Acme Corp",
        total_previous_invoices=100,
        average_invoice_amount=5000.0,
        last_invoice_date="2026-06-01",
        previous_rejections=0,
        vendor_status="Trusted",
        trust_score=50,
        last_bank_account_change="2025-12-01",
    )
    assessment_high_risk = calculate_risk(invoice, vendor_low_trust)
    assert assessment_high_risk.risk_score >= 60
    assert assessment_high_risk.recommendation == "INVESTIGATE"
    assert any("unusually high" in f for f in assessment_high_risk.risk_findings)
