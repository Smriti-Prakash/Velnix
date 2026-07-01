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
from app.tools.fraud_engine import calculate_fraud


def test_calculate_fraud_no_flags():
    """Test scenario with no fraud flags raised."""
    invoice = InvoiceData(
        invoice_number="INV-NEW-UNIQUE-999",
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
        last_bank_account_change="2025-12-01", # >60 days
    )

    assessment = calculate_fraud(invoice, vendor, "Regular invoice details.")
    assert assessment.fraud_score == 0
    assert len(assessment.fraud_flags) == 0
    assert assessment.investigation_required is False
    assert assessment.confidence_level == "LOW"


def test_calculate_fraud_duplicate():
    """Test that a duplicate invoice number triggers critical flag."""
    invoice = InvoiceData(
        invoice_number="INV-2026-001", # Existing in history CSV
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

    assessment = calculate_fraud(invoice, vendor, "Regular invoice text.")
    assert assessment.fraud_score >= 50
    assert any("Duplicate Invoice Number" in f for f in assessment.fraud_flags)
    assert assessment.investigation_required is True
    assert assessment.confidence_level == "HIGH"


def test_calculate_fraud_recent_bank():
    """Test that recent bank account change is flagged."""
    invoice = InvoiceData(
        invoice_number="INV-UNIQUE-1",
        vendor_name="RiskCo LLC",
        invoice_amount=4000.0,
        currency="$",
        purchase_order_number="PO-100",
        payment_terms="Net 30",
    )
    vendor = VendorProfile(
        vendor_name="RiskCo LLC",
        total_previous_invoices=100,
        average_invoice_amount=5000.0,
        last_invoice_date="2026-06-01",
        previous_rejections=0,
        vendor_status="Trusted",
        trust_score=95,
        last_bank_account_change="2026-06-01", # Changed within 60 days
    )

    assessment = calculate_fraud(invoice, vendor, "Regular invoice text.")
    assert assessment.fraud_score >= 30
    assert any("bank account changed recently" in f for f in assessment.fraud_flags)
    assert assessment.investigation_required is True
    assert assessment.confidence_level == "HIGH"


def test_calculate_fraud_high_deviation():
    """Test that invoice amount >3x average is flagged."""
    invoice = InvoiceData(
        invoice_number="INV-UNIQUE-2",
        vendor_name="Acme Corp",
        invoice_amount=20000.0, # Average is 5000 (4x)
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

    assessment = calculate_fraud(invoice, vendor, "Regular invoice text.")
    assert assessment.fraud_score >= 30
    assert any("significantly larger than historical average" in f for f in assessment.fraud_flags)
    assert assessment.investigation_required is True


def test_calculate_fraud_urgent_new():
    """Test new vendor requesting urgent payment flags correctly."""
    invoice = InvoiceData(
        invoice_number="INV-UNIQUE-3",
        vendor_name="NewTech Solutions",
        invoice_amount=2000.0,
        currency="$",
        purchase_order_number="PO-100",
        payment_terms="Immediate",
    )
    vendor = VendorProfile(
        vendor_name="NewTech Solutions",
        total_previous_invoices=0,
        average_invoice_amount=0.0,
        last_invoice_date="N/A",
        previous_rejections=0,
        vendor_status="New",
        trust_score=70,
        last_bank_account_change="N/A",
    )

    # Contains "urgent" in text
    assessment = calculate_fraud(invoice, vendor, "Invoice is URGENT. Please pay now.")
    assert assessment.fraud_score >= 25
    assert any("urgent payment terms" in f for f in assessment.fraud_flags)
    assert assessment.confidence_level == "MEDIUM"
