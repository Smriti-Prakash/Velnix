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

"""Database connection and initialisation for the Velnix ERP SQLite store.

Usage
-----
Call :func:`init_db` once at application startup to create the schema and
seed sample data if the database is empty::

    from app.erp.database import init_db
    init_db()

For all subsequent queries use :func:`get_connection` which returns a
``sqlite3.Connection`` with ``row_factory = sqlite3.Row`` already set.
"""

from __future__ import annotations

import os
import sqlite3

# ---------------------------------------------------------------------------
# DB path: app/data/erp.db (relative to project root)
# ---------------------------------------------------------------------------
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))   # app/erp/
_APP_DIR = os.path.dirname(_PACKAGE_DIR)                     # app/
DB_PATH = os.path.join(_APP_DIR, "data", "erp.db")


# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Return a new sqlite3 connection to the ERP database.

    The connection has:
    - ``row_factory = sqlite3.Row`` so columns are accessible by name.
    - ``PRAGMA foreign_keys = ON`` to enforce referential integrity.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

_CREATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id                INTEGER PRIMARY KEY,
    vendor_name              TEXT    NOT NULL UNIQUE,
    vendor_status            TEXT    NOT NULL CHECK(vendor_status IN ('Trusted','Watchlist','New','Suspended')),
    trust_score              INTEGER NOT NULL CHECK(trust_score BETWEEN 0 AND 100),
    average_invoice_amount   REAL    NOT NULL DEFAULT 0.0,
    total_previous_invoices  INTEGER NOT NULL DEFAULT 0,
    previous_rejections      INTEGER NOT NULL DEFAULT 0,
    last_bank_account_change TEXT,
    bank_account             TEXT,
    risk_level               TEXT    NOT NULL DEFAULT 'Low' CHECK(risk_level IN ('Low','Medium','High'))
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    purchase_order_number TEXT    PRIMARY KEY,
    vendor_id             INTEGER NOT NULL REFERENCES vendors(vendor_id),
    vendor_name           TEXT    NOT NULL,
    approved_amount       REAL    NOT NULL,
    currency              TEXT    NOT NULL DEFAULT 'USD',
    purchase_date         TEXT    NOT NULL,
    status                TEXT    NOT NULL CHECK(status IN ('Open','Cancelled','Closed')),
    expected_items        TEXT
);

CREATE TABLE IF NOT EXISTS goods_receipts (
    goods_receipt_number  TEXT    PRIMARY KEY,
    purchase_order_number TEXT    NOT NULL REFERENCES purchase_orders(purchase_order_number),
    vendor_id             INTEGER NOT NULL REFERENCES vendors(vendor_id),
    received_date         TEXT    NOT NULL,
    received_quantity     REAL    NOT NULL DEFAULT 0.0,
    status                TEXT    NOT NULL CHECK(status IN ('Complete','Partial','Pending'))
);

CREATE TABLE IF NOT EXISTS invoice_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT    NOT NULL UNIQUE,
    vendor_id      INTEGER NOT NULL REFERENCES vendors(vendor_id),
    vendor_name    TEXT    NOT NULL,
    invoice_amount REAL    NOT NULL,
    invoice_date   TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'Paid' CHECK(status IN ('Paid','Rejected','Pending'))
);
"""


def _create_tables(conn: sqlite3.Connection) -> None:
    """Execute DDL to create all ERP tables if they do not yet exist."""
    conn.executescript(_CREATE_SCHEMA)


# ---------------------------------------------------------------------------
# Seeding (idempotent — only inserts if table is empty)
# ---------------------------------------------------------------------------

def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Insert sample data into each table if it contains no rows."""
    from app.erp.seed_data import (
        GOODS_RECEIPTS,
        INVOICE_HISTORY,
        PURCHASE_ORDERS,
        VENDORS,
    )

    # vendors
    if conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO vendors VALUES (?,?,?,?,?,?,?,?,?,?)", VENDORS
        )

    # purchase_orders (depends on vendors)
    if conn.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO purchase_orders VALUES (?,?,?,?,?,?,?,?)", PURCHASE_ORDERS
        )

    # goods_receipts (depends on purchase_orders)
    if conn.execute("SELECT COUNT(*) FROM goods_receipts").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO goods_receipts VALUES (?,?,?,?,?,?)", GOODS_RECEIPTS
        )

    # invoice_history (depends on vendors)
    if conn.execute("SELECT COUNT(*) FROM invoice_history").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO invoice_history (invoice_number, vendor_id, vendor_name, "
            "invoice_amount, invoice_date, status) VALUES (?,?,?,?,?,?)",
            INVOICE_HISTORY,
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create schema and seed data.  Safe to call multiple times (idempotent).

    Call once during application startup::

        from app.erp.database import init_db
        init_db()
    """
    conn = get_connection()
    try:
        _create_tables(conn)
        _seed_if_empty(conn)
        conn.commit()
    finally:
        conn.close()
