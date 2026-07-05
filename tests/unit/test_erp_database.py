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

"""Unit tests for the ERP SQLite database layer.

Each test function operates on an in-memory (or temp-file) database so that
tests are fully isolated and do not modify the production erp.db.
"""

import os
import sqlite3
import tempfile
import pytest

import app.erp.database as db_module
from app.erp.database import _create_tables, _seed_if_empty, get_connection
from app.erp.queries import (
    check_duplicate_invoice,
    fetch_goods_receipts_for_po,
    fetch_invoice_history_by_vendor_id,
    fetch_invoice_history_by_vendor_name,
    fetch_purchase_order,
    fetch_vendor_by_id,
    fetch_vendor_by_name,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Redirect DB_PATH to a fresh temp file for each test."""
    db_file = str(tmp_path / "test_erp.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    # Also patch the module-level DB_PATH inside queries so get_connection
    # inside queries uses the same temp path.
    import app.erp.queries as q_module
    monkeypatch.setattr(q_module, "get_connection", db_module.get_connection)
    db_module.init_db()
    return db_file


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

def test_db_init_creates_vendors_table(tmp_db):
    """vendors table must exist after init_db()."""
    conn = sqlite3.connect(tmp_db)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vendors'"
    ).fetchone()
    conn.close()
    assert row is not None, "vendors table not found"


def test_db_init_creates_purchase_orders_table(tmp_db):
    """purchase_orders table must exist after init_db()."""
    conn = sqlite3.connect(tmp_db)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='purchase_orders'"
    ).fetchone()
    conn.close()
    assert row is not None, "purchase_orders table not found"


def test_db_init_creates_goods_receipts_table(tmp_db):
    """goods_receipts table must exist after init_db()."""
    conn = sqlite3.connect(tmp_db)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='goods_receipts'"
    ).fetchone()
    conn.close()
    assert row is not None, "goods_receipts table not found"


def test_db_init_creates_invoice_history_table(tmp_db):
    """invoice_history table must exist after init_db()."""
    conn = sqlite3.connect(tmp_db)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_history'"
    ).fetchone()
    conn.close()
    assert row is not None, "invoice_history table not found"


# ---------------------------------------------------------------------------
# Seed data row-count tests
# ---------------------------------------------------------------------------

def test_vendors_seeded_minimum_15(tmp_db):
    """At least 15 vendor rows must be present after seeding."""
    conn = sqlite3.connect(tmp_db)
    count = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
    conn.close()
    assert count >= 15, f"Expected >= 15 vendors, got {count}"


def test_purchase_orders_seeded_minimum_10(tmp_db):
    """At least 10 purchase order rows must be present after seeding."""
    conn = sqlite3.connect(tmp_db)
    count = conn.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()[0]
    conn.close()
    assert count >= 10, f"Expected >= 10 POs, got {count}"


def test_goods_receipts_seeded_minimum_5(tmp_db):
    """At least 5 goods receipt rows must be present after seeding."""
    conn = sqlite3.connect(tmp_db)
    count = conn.execute("SELECT COUNT(*) FROM goods_receipts").fetchone()[0]
    conn.close()
    assert count >= 5, f"Expected >= 5 receipts, got {count}"


def test_invoice_history_seeded_minimum_20(tmp_db):
    """At least 20 invoice history rows must be present after seeding."""
    conn = sqlite3.connect(tmp_db)
    count = conn.execute("SELECT COUNT(*) FROM invoice_history").fetchone()[0]
    conn.close()
    assert count >= 20, f"Expected >= 20 invoice history rows, got {count}"


# ---------------------------------------------------------------------------
# Idempotency test
# ---------------------------------------------------------------------------

def test_init_db_is_idempotent(tmp_db):
    """Calling init_db() a second time must not duplicate any rows."""
    conn = sqlite3.connect(tmp_db)
    count_before = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
    conn.close()

    db_module.init_db()  # second call

    conn = sqlite3.connect(tmp_db)
    count_after = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
    conn.close()
    assert count_before == count_after, (
        f"Row count changed after second init_db(): {count_before} -> {count_after}"
    )


# ---------------------------------------------------------------------------
# Query function tests
# ---------------------------------------------------------------------------

def test_fetch_vendor_by_name_found(tmp_db):
    vendor = fetch_vendor_by_name("Acme Corp")
    assert vendor is not None
    assert vendor.vendor_name == "Acme Corp"
    assert vendor.vendor_status == "Trusted"
    assert vendor.trust_score == 95
    assert vendor.vendor_id == 1


def test_fetch_vendor_by_name_case_insensitive(tmp_db):
    vendor = fetch_vendor_by_name("acme corp")
    assert vendor is not None
    assert vendor.vendor_name == "Acme Corp"


def test_fetch_vendor_by_name_not_found(tmp_db):
    vendor = fetch_vendor_by_name("Completely Unknown Vendor XYZ")
    assert vendor is None


def test_fetch_vendor_by_id(tmp_db):
    vendor = fetch_vendor_by_id(2)
    assert vendor is not None
    assert vendor.vendor_name == "Global Supplies Inc"
    assert vendor.trust_score == 98


def test_vendor_to_dict_contains_all_fields(tmp_db):
    vendor = fetch_vendor_by_name("RiskCo LLC")
    assert vendor is not None
    d = vendor.to_dict()
    expected_keys = {
        "vendor_id", "vendor_name", "vendor_status", "trust_score",
        "average_invoice_amount", "total_previous_invoices",
        "previous_rejections", "last_bank_account_change",
        "bank_account", "risk_level",
    }
    assert expected_keys.issubset(d.keys())
    assert d["vendor_status"] == "Watchlist"
    assert d["previous_rejections"] == 5


def test_fetch_purchase_order_found(tmp_db):
    po = fetch_purchase_order("PO-2026-001")
    assert po is not None
    assert po.purchase_order_number == "PO-2026-001"
    assert po.vendor_id == 1
    assert po.vendor_name == "Acme Corp"
    assert po.status == "Open"


def test_fetch_purchase_order_case_insensitive(tmp_db):
    po = fetch_purchase_order("po-2026-001")
    assert po is not None
    assert po.purchase_order_number == "PO-2026-001"


def test_fetch_purchase_order_not_found(tmp_db):
    po = fetch_purchase_order("PO-DOES-NOT-EXIST")
    assert po is None


def test_fetch_purchase_order_cancelled(tmp_db):
    po = fetch_purchase_order("PO-2026-011")
    assert po is not None
    assert po.status == "Cancelled"
    assert po.vendor_id == 9   # RiskCo LLC


def test_fetch_goods_receipts_for_po(tmp_db):
    receipts = fetch_goods_receipts_for_po("PO-2026-001")
    assert len(receipts) >= 1
    gr = receipts[0]
    assert gr.purchase_order_number == "PO-2026-001"
    assert gr.vendor_id == 1
    assert gr.status == "Complete"


def test_fetch_goods_receipts_for_nonexistent_po(tmp_db):
    receipts = fetch_goods_receipts_for_po("PO-NO-RECEIPT")
    assert receipts == []


def test_fetch_invoice_history_by_vendor_name(tmp_db):
    history = fetch_invoice_history_by_vendor_name("Acme Corp")
    assert len(history) >= 7
    # All entries belong to Acme Corp (vendor_id=1)
    assert all(h.vendor_id == 1 for h in history)
    # Ordered newest first
    dates = [h.invoice_date for h in history]
    assert dates == sorted(dates, reverse=True)


def test_fetch_invoice_history_by_vendor_id(tmp_db):
    history = fetch_invoice_history_by_vendor_id(2)  # Global Supplies Inc
    assert len(history) >= 5
    assert all(h.vendor_id == 2 for h in history)


def test_fetch_invoice_history_includes_rejected(tmp_db):
    history = fetch_invoice_history_by_vendor_name("RiskCo LLC")
    statuses = {h.status for h in history}
    assert "Rejected" in statuses


def test_fetch_invoice_history_empty_for_new_vendor(tmp_db):
    history = fetch_invoice_history_by_vendor_name("NewTech Solutions")
    assert history == []


def test_check_duplicate_invoice_found(tmp_db):
    assert check_duplicate_invoice("INV-2026-001") is True


def test_check_duplicate_invoice_not_found(tmp_db):
    assert check_duplicate_invoice("INV-COMPLETELY-NEW-9999") is False


def test_check_duplicate_invoice_case_insensitive(tmp_db):
    assert check_duplicate_invoice("inv-2026-001") is True
