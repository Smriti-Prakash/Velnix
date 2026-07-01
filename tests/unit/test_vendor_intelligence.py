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

from app.tools.vendor_intelligence import get_vendor_profile
from app.tools.invoice_tools import parse_invoice, analyze_invoice


def test_get_vendor_profile_existing():
    """Test retrieving existing vendor profiles from the CSV."""
    # Test Trusted Vendor
    profile_acme = get_vendor_profile("Acme Corp")
    assert profile_acme.vendor_name == "Acme Corp"
    assert profile_acme.vendor_status == "Trusted"
    assert profile_acme.trust_score == 95
    assert profile_acme.average_invoice_amount == 5000.0
    assert profile_acme.last_bank_account_change == "2025-12-01"

    # Test Watchlist Vendor
    profile_risk = get_vendor_profile("RiskCo LLC")
    assert profile_risk.vendor_name == "RiskCo LLC"
    assert profile_risk.vendor_status == "Watchlist"
    assert profile_risk.trust_score == 35
    assert profile_risk.previous_rejections == 5
    assert profile_risk.last_bank_account_change == "2026-06-01"


def test_get_vendor_profile_case_insensitivity():
    """Test that vendor profile retrieval is case and space insensitive."""
    profile_acme = get_vendor_profile("  acme corp  ")
    assert profile_acme.vendor_name == "Acme Corp"
    assert profile_acme.vendor_status == "Trusted"


def test_get_vendor_profile_unknown():
    """Test retrieving profile for unknown/new vendor defaults to a standard New profile."""
    profile_unknown = get_vendor_profile("Mystery Enterprises Inc")
    assert profile_unknown.vendor_name == "Mystery Enterprises Inc"
    assert profile_unknown.vendor_status == "New"
    assert profile_unknown.trust_score == 50
    assert profile_unknown.total_previous_invoices == 0
    assert profile_unknown.average_invoice_amount == 0.0
    assert profile_unknown.last_bank_account_change == "N/A"


def test_analyze_invoice_trusted_high_amount():
    """Test alerts generated for a trusted vendor with an unusually high invoice amount."""
    invoice_text = """
    Invoice ID: INV-001
    Vendor: Acme Corp
    Amount: $10,000
    Date: 2026-06-30
    """
    report = analyze_invoice(invoice_text)
    assert "VENDOR INTELLIGENCE:" in report
    assert "Status: Trusted" in report
    # Should flag 10k since it is > 1.5x average (5k)
    assert "WARNING: Current invoice amount ($10,000.00) is unusually high" in report


def test_analyze_invoice_watchlist_vendor():
    """Test alerts generated for a watchlisted vendor."""
    invoice_text = """
    Invoice ID: INV-002
    Vendor: RiskCo LLC
    Amount: $5,000
    Date: 2026-06-30
    """
    report = analyze_invoice(invoice_text)
    assert "VENDOR INTELLIGENCE:" in report
    assert "Status: Watchlist" in report
    # Should flag watchlist warning
    assert "WARNING: Vendor is on the Watchlist!" in report
    # Should not flag unusually high amount since 5k is <= 1.5x average (8.5k)
    assert "is unusually high" not in report


def test_analyze_invoice_new_vendor():
    """Test alerts generated for a new vendor."""
    invoice_text = """
    Invoice ID: INV-003
    Vendor: NewTech Solutions
    Amount: $1,200
    Date: 2026-06-30
    """
    report = analyze_invoice(invoice_text)
    assert "VENDOR INTELLIGENCE:" in report
    assert "Status: New" in report
    assert "NOTICE: Vendor is New/Unverified. No prior invoice history." in report
