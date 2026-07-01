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

import os
import csv
import pytest
from app.tools.invoice_tools import InvoiceData, validate_invoice
from app.security.rbac import verify_permission, AuthorizationError
from app.security.audit_logger import log_audit_event, AUDIT_LOG_CSV


def test_validate_invoice_success():
    """Verify validate_invoice passes on fully compliant invoice data."""
    invoice = InvoiceData(
        invoice_number="INV-2026-888",
        vendor_name="Acme Corp",
        invoice_amount=5000.0,
        currency="$",
        invoice_date="2026-06-30"
    )
    # Should not raise exception
    validate_invoice(invoice)


def test_validate_invoice_missing_number():
    """Verify validate_invoice rejects missing invoice number."""
    invoice = InvoiceData(
        invoice_number="",
        vendor_name="Acme Corp",
        invoice_amount=5000.0,
        invoice_date="2026-06-30"
    )
    with pytest.raises(ValueError, match="Missing Invoice Number"):
        validate_invoice(invoice)


def test_validate_invoice_missing_vendor():
    """Verify validate_invoice rejects missing vendor name."""
    invoice = InvoiceData(
        invoice_number="INV-2026-888",
        vendor_name=None,
        invoice_amount=5000.0,
        invoice_date="2026-06-30"
    )
    with pytest.raises(ValueError, match="Missing Vendor Name"):
        validate_invoice(invoice)


def test_validate_invoice_invalid_amount():
    """Verify validate_invoice rejects non-positive invoice amounts."""
    # Negative amount
    invoice_neg = InvoiceData(
        invoice_number="INV-2026-888",
        vendor_name="Acme Corp",
        invoice_amount=-100.0,
        invoice_date="2026-06-30"
    )
    with pytest.raises(ValueError, match="Invalid or missing Invoice Amount"):
        validate_invoice(invoice_neg)

    # Zero amount
    invoice_zero = InvoiceData(
        invoice_number="INV-2026-888",
        vendor_name="Acme Corp",
        invoice_amount=0,
        invoice_date="2026-06-30"
    )
    with pytest.raises(ValueError, match="Invalid or missing Invoice Amount"):
        validate_invoice(invoice_zero)


def test_validate_invoice_invalid_date():
    """Verify validate_invoice rejects missing or malformed dates."""
    # Missing date
    invoice_missing_date = InvoiceData(
        invoice_number="INV-2026-888",
        vendor_name="Acme Corp",
        invoice_amount=5000.0,
        invoice_date=None
    )
    with pytest.raises(ValueError, match="Missing Invoice Date"):
        validate_invoice(invoice_missing_date)

    # Malformed date format
    invoice_bad_date = InvoiceData(
        invoice_number="INV-2026-888",
        vendor_name="Acme Corp",
        invoice_amount=5000.0,
        invoice_date="30/06/2026"
    )
    with pytest.raises(ValueError, match="Invalid Invoice Date format"):
        validate_invoice(invoice_bad_date)


def test_rbac_analyst_permissions():
    """Verify that Finance Analyst permissions are correctly verified and restricted."""
    # Analyst can view profile, find duplicates, and analyze invoices
    verify_permission("Finance Analyst", "view_profile")
    verify_permission("Finance Analyst", "find_duplicate")
    verify_permission("Finance Analyst", "analyze_invoice")

    # Analyst cannot submit results or list pending invoices
    with pytest.raises(AuthorizationError):
        verify_permission("Finance Analyst", "submit_investigation_result")


def test_rbac_manager_permissions():
    """Verify that Finance Manager permissions are verified and restricted."""
    verify_permission("Finance Manager", "view_profile")
    verify_permission("Finance Manager", "submit_investigation_result")

    # Manager cannot list pending invoices
    with pytest.raises(AuthorizationError):
        verify_permission("Finance Manager", "list_pending_invoices")


def test_rbac_admin_permissions():
    """Verify Administrator possesses full permissions."""
    verify_permission("Administrator", "view_profile")
    verify_permission("Administrator", "submit_investigation_result")
    verify_permission("Administrator", "list_pending_invoices")
    verify_permission("Administrator", "view_audit_logs")


def test_rbac_unknown_role():
    """Verify unknown roles are rejected with AuthorizationError."""
    with pytest.raises(AuthorizationError, match="Unknown role"):
        verify_permission("Guest Analyst", "view_profile")


def test_audit_logger():
    """Verify that audit logger writes files and logs expected values."""
    # Remove existing log if present
    if os.path.exists(AUDIT_LOG_CSV):
        try:
            os.remove(AUDIT_LOG_CSV)
        except Exception:
            pass

    log_audit_event(
        invoice_number="INV-AUDIT-99",
        agent="Analyst Agent",
        session_id="session-xyz",
        role="Finance Analyst",
        decision="SUCCESS",
        recommendation="APPROVE",
        reason="Looks good"
    )

    assert os.path.exists(AUDIT_LOG_CSV)

    with open(AUDIT_LOG_CSV, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        # Headers should exist
        assert rows[0] == ["Timestamp", "Invoice Number", "Agent", "Session ID", "User Role", "Decision", "Recommendation", "Reason"]
        # Entry should exist
        last_row = rows[-1]
        assert last_row[1] == "INV-AUDIT-99"
        assert last_row[2] == "Analyst Agent"
        assert last_row[3] == "session-xyz"
        assert last_row[4] == "Finance Analyst"
        assert last_row[5] == "SUCCESS"
        assert last_row[6] == "APPROVE"
        assert last_row[7] == "Looks good"


def test_secrets_safety():
    """Verify secure handling of secrets: .env is ignored and .env.example exists."""
    # Verify .env.example exists
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    assert os.path.exists(os.path.join(project_root, ".env.example"))

    # Verify .env is present in gitignore rules
    gitignore_path = os.path.join(project_root, ".gitignore")
    assert os.path.exists(gitignore_path)
    with open(gitignore_path, mode="r", encoding="utf-8") as f:
        content = f.read()
        assert ".env" in content
