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

"""SQL query functions for the Velnix ERP database.

All SQL statements live here; MCP tools and application code call these
functions instead of embedding SQL directly.  Each function opens its
own connection, executes a single logical query, and closes the connection.
"""

from __future__ import annotations

from typing import Optional

from app.erp.database import get_connection
from app.erp.models import GoodsReceipt, InvoiceHistory, PurchaseOrder, Vendor


# ---------------------------------------------------------------------------
# Vendor queries
# ---------------------------------------------------------------------------

def fetch_vendor_by_name(vendor_name: str) -> Optional[Vendor]:
    """Return the Vendor record matching *vendor_name* (case-insensitive).

    Args:
        vendor_name: Display name of the vendor to look up.

    Returns:
        A :class:`Vendor` instance or ``None`` if not found.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM vendors WHERE LOWER(vendor_name) = LOWER(?)",
            (vendor_name.strip(),),
        ).fetchone()
        return Vendor.from_row(row) if row else None
    finally:
        conn.close()


def fetch_vendor_by_id(vendor_id: int) -> Optional[Vendor]:
    """Return the Vendor record for the given *vendor_id*.

    Args:
        vendor_id: The integer primary key of the vendor.

    Returns:
        A :class:`Vendor` instance or ``None`` if not found.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM vendors WHERE vendor_id = ?",
            (vendor_id,),
        ).fetchone()
        return Vendor.from_row(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Purchase Order queries
# ---------------------------------------------------------------------------

def fetch_purchase_order(purchase_order_number: str) -> Optional[PurchaseOrder]:
    """Return the PurchaseOrder record matching *purchase_order_number*.

    Lookup is case-insensitive on the PO number.

    Args:
        purchase_order_number: The alphanumeric PO reference (e.g. PO-2026-001).

    Returns:
        A :class:`PurchaseOrder` instance or ``None`` if not found.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM purchase_orders WHERE UPPER(purchase_order_number) = UPPER(?)",
            (purchase_order_number.strip(),),
        ).fetchone()
        return PurchaseOrder.from_row(row) if row else None
    finally:
        conn.close()


def fetch_purchase_orders_by_vendor_id(vendor_id: int) -> list[PurchaseOrder]:
    """Return all PurchaseOrders associated with *vendor_id*.

    Args:
        vendor_id: The integer primary key of the vendor.

    Returns:
        List of :class:`PurchaseOrder` instances (may be empty).
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM purchase_orders WHERE vendor_id = ? ORDER BY purchase_date DESC",
            (vendor_id,),
        ).fetchall()
        return [PurchaseOrder.from_row(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Goods Receipt queries
# ---------------------------------------------------------------------------

def fetch_goods_receipts_for_po(purchase_order_number: str) -> list[GoodsReceipt]:
    """Return all GoodsReceipts linked to *purchase_order_number*.

    Args:
        purchase_order_number: The PO reference to look up (case-insensitive).

    Returns:
        List of :class:`GoodsReceipt` instances (may be empty).
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM goods_receipts "
            "WHERE UPPER(purchase_order_number) = UPPER(?)",
            (purchase_order_number.strip(),),
        ).fetchall()
        return [GoodsReceipt.from_row(r) for r in rows]
    finally:
        conn.close()


def fetch_goods_receipts_by_vendor_id(vendor_id: int) -> list[GoodsReceipt]:
    """Return all GoodsReceipts associated with *vendor_id*.

    Args:
        vendor_id: The integer primary key of the vendor.

    Returns:
        List of :class:`GoodsReceipt` instances (may be empty).
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM goods_receipts WHERE vendor_id = ? ORDER BY received_date DESC",
            (vendor_id,),
        ).fetchall()
        return [GoodsReceipt.from_row(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Invoice History queries
# ---------------------------------------------------------------------------

def fetch_invoice_history_by_vendor_name(vendor_name: str) -> list[InvoiceHistory]:
    """Return all historical invoices for *vendor_name* (case-insensitive).

    This lookup by name supports the case where the caller has a vendor name
    from an uploaded invoice but not a vendor_id.

    Args:
        vendor_name: Display name of the vendor.

    Returns:
        List of :class:`InvoiceHistory` instances ordered newest-first.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM invoice_history "
            "WHERE LOWER(vendor_name) = LOWER(?) "
            "ORDER BY invoice_date DESC",
            (vendor_name.strip(),),
        ).fetchall()
        return [InvoiceHistory.from_row(r) for r in rows]
    finally:
        conn.close()


def fetch_invoice_history_by_vendor_id(vendor_id: int) -> list[InvoiceHistory]:
    """Return all historical invoices for *vendor_id*.

    Preferred over name-based lookup when the vendor_id is known, because
    it uses the indexed FK column directly.

    Args:
        vendor_id: The integer primary key of the vendor.

    Returns:
        List of :class:`InvoiceHistory` instances ordered newest-first.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM invoice_history "
            "WHERE vendor_id = ? "
            "ORDER BY invoice_date DESC",
            (vendor_id,),
        ).fetchall()
        return [InvoiceHistory.from_row(r) for r in rows]
    finally:
        conn.close()


def check_duplicate_invoice(invoice_number: str) -> bool:
    """Return ``True`` if *invoice_number* already exists in invoice_history.

    Args:
        invoice_number: The invoice reference string to check (case-insensitive).

    Returns:
        Boolean indicating whether the invoice is a known duplicate.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM invoice_history WHERE UPPER(invoice_number) = UPPER(?)",
            (invoice_number.strip(),),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
