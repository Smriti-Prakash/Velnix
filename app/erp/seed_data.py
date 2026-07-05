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

"""Seed data for the Velnix ERP SQLite database.

Data is inserted only if the relevant tables are empty (idempotent).
vendor_id is the primary relationship key across all tables.
"""

# ---------------------------------------------------------------------------
# Vendors  (18 records: 8 Trusted, 4 Watchlist, 4 New, 2 Suspended)
# Column order: vendor_id, vendor_name, vendor_status, trust_score,
#               average_invoice_amount, total_previous_invoices,
#               previous_rejections, last_bank_account_change,
#               bank_account, risk_level
# ---------------------------------------------------------------------------
VENDORS = [
    # --- Trusted ---
    (1,  "Acme Corp",               "Trusted",   95, 5000.00,  150, 1,  "2025-12-01", "ACC-0001-UK", "Low"),
    (2,  "Global Supplies Inc",     "Trusted",   98, 12000.00,  45, 0,  "2026-01-10", "ACC-0002-US", "Low"),
    (3,  "TechPro Systems",         "Trusted",   92, 8500.00,   80, 2,  "2025-08-15", "ACC-0003-US", "Low"),
    (4,  "Office Direct Ltd",       "Trusted",   88, 3200.00,   30, 0,  "2025-06-01", "ACC-0004-UK", "Low"),
    (5,  "Premier Logistics",       "Trusted",   90, 15000.00,  60, 1,  "2026-02-20", "ACC-0005-EU", "Low"),
    (6,  "DataCore Solutions",      "Trusted",   85, 22000.00,  25, 3,  "2025-09-10", "ACC-0006-US", "Medium"),
    (7,  "BuildRight Contractors",  "Trusted",   94, 45000.00, 120, 0,  "2025-11-05", "ACC-0007-UK", "Low"),
    (8,  "CloudStack Inc",          "Trusted",   91, 9800.00,   55, 2,  "2026-03-01", "ACC-0008-US", "Low"),
    # --- Watchlist ---
    (9,  "RiskCo LLC",              "Watchlist", 35, 8500.00,   12, 5,  "2026-06-01", "ACC-0009-OF", "High"),
    (10, "ShadowVend Corp",         "Watchlist", 28, 18000.00,   8, 6,  "2026-05-15", "ACC-0010-OF", "High"),
    (11, "QuickBill Services",      "Watchlist", 42, 4200.00,   18, 4,  "2026-04-22", "ACC-0011-OF", "High"),
    (12, "DoubleCharge Inc",        "Watchlist", 22, 11500.00,   5, 7,  "2026-06-25", "ACC-0012-OF", "High"),
    # --- New ---
    (13, "NewTech Solutions",       "New",       70, 0.0,        0, 0,  None,          None,          "Low"),
    (14, "SuperStore",              "New",       70, 0.0,        0, 0,  None,          None,          "Low"),
    (15, "FreshStart Ltd",          "New",       65, 0.0,        0, 0,  None,          None,          "Low"),
    (16, "StartupDesk Co",          "New",       60, 0.0,        0, 0,  None,          None,          "Low"),
    # --- Suspended ---
    (17, "FraudCo International",   "Suspended", 10, 28000.00,   3, 8,  "2026-06-28", "ACC-0017-SU", "High"),
    (18, "BogusSupply Ltd",         "Suspended",  5, 15000.00,   2, 9,  "2026-06-30", "ACC-0018-SU", "High"),
]

# ---------------------------------------------------------------------------
# Purchase Orders  (20 records: Open / Cancelled / Closed mix)
# Column order: purchase_order_number, vendor_id, vendor_name,
#               approved_amount, currency, purchase_date, status,
#               expected_items
# ---------------------------------------------------------------------------
PURCHASE_ORDERS = [
    # Exact-amount matches (will be used in future PO validation)
    ("PO-2026-001", 1,  "Acme Corp",              10000.00, "USD", "2026-05-01", "Open",      "Office Supplies, Packaging"),
    ("PO-2026-002", 2,  "Global Supplies Inc",     50000.00, "USD", "2026-04-15", "Open",      "IT Hardware, Networking Gear"),
    ("PO-2026-003", 3,  "TechPro Systems",          8500.00, "USD", "2026-04-20", "Open",      "Software Licenses"),
    ("PO-2026-004", 4,  "Office Direct Ltd",        3200.00, "USD", "2026-05-10", "Closed",    "Stationery"),
    ("PO-2026-005", 5,  "Premier Logistics",       15000.00, "USD", "2026-05-20", "Open",      "Freight Services"),
    ("PO-2026-006", 6,  "DataCore Solutions",      22000.00, "USD", "2026-03-01", "Open",      "Cloud Storage Subscription"),
    ("PO-2026-007", 7,  "BuildRight Contractors",  45000.00, "USD", "2026-02-15", "Closed",    "Office Renovation Phase 1"),
    ("PO-2026-008", 8,  "CloudStack Inc",           9800.00, "USD", "2026-05-25", "Open",      "DevOps Platform Tools"),
    ("PO-2026-009", 1,  "Acme Corp",               12500.00, "USD", "2026-06-01", "Open",      "Manufacturing Parts"),
    ("PO-2026-010", 2,  "Global Supplies Inc",     75000.00, "USD", "2026-06-10", "Open",      "Server Equipment"),
    # Amount mismatches (intentional for future validation testing)
    ("PO-2026-011", 9,  "RiskCo LLC",               9000.00, "USD", "2026-04-01", "Cancelled", "Consulting Services"),
    ("PO-2026-012", 3,  "TechPro Systems",          18000.00, "USD", "2026-05-05", "Open",      "Security Software Suite"),
    ("PO-2026-013", 5,  "Premier Logistics",        20000.00, "USD", "2026-06-15", "Open",      "Warehousing Q3"),
    ("PO-2026-014", 7,  "BuildRight Contractors",   55000.00, "USD", "2026-06-20", "Open",      "Parking Structure"),
    ("PO-2026-015", 4,  "Office Direct Ltd",         4800.00, "USD", "2026-06-25", "Open",      "Ergonomic Equipment"),
    ("PO-2026-016", 8,  "CloudStack Inc",           14000.00, "USD", "2026-06-28", "Open",      "AI Platform License"),
    # Closed POs
    ("PO-2026-017", 6,  "DataCore Solutions",       30000.00, "USD", "2026-05-15", "Closed",    "Backup Systems"),
    ("PO-2026-018", 1,  "Acme Corp",                5500.00, "USD", "2026-06-30", "Open",      "Packaging Materials"),
    # New vendor PO
    ("PO-2026-019", 13, "NewTech Solutions",         2500.00, "USD", "2026-07-01", "Open",      "Prototype Testing Kit"),
    # Cancelled watchlist PO
    ("PO-2026-020", 11, "QuickBill Services",        4000.00, "USD", "2026-04-10", "Cancelled", "Marketing Campaign"),
]

# ---------------------------------------------------------------------------
# Goods Receipts  (15 records: Complete / Partial / Pending mix)
# Column order: goods_receipt_number, purchase_order_number, vendor_id,
#               received_date, received_quantity (pct 0-100), status
# ---------------------------------------------------------------------------
GOODS_RECEIPTS = [
    ("GR-2026-001", "PO-2026-001", 1,  "2026-05-15", 100.0, "Complete"),
    ("GR-2026-002", "PO-2026-002", 2,  "2026-05-01",  80.0, "Partial"),
    ("GR-2026-003", "PO-2026-003", 3,  "2026-05-10", 100.0, "Complete"),
    ("GR-2026-004", "PO-2026-004", 4,  "2026-05-20", 100.0, "Complete"),
    ("GR-2026-005", "PO-2026-005", 5,  "2026-06-01", 100.0, "Complete"),
    ("GR-2026-006", "PO-2026-006", 6,  "2026-04-01",  60.0, "Partial"),
    ("GR-2026-007", "PO-2026-007", 7,  "2026-03-15", 100.0, "Complete"),
    ("GR-2026-008", "PO-2026-008", 8,  "2026-06-05", 100.0, "Complete"),
    ("GR-2026-009", "PO-2026-009", 1,  "2026-06-20",  50.0, "Partial"),
    ("GR-2026-010", "PO-2026-010", 2,  "2026-06-25",   0.0, "Pending"),
    ("GR-2026-011", "PO-2026-012", 3,  "2026-05-25", 100.0, "Complete"),
    ("GR-2026-012", "PO-2026-013", 5,  "2026-07-01",  75.0, "Partial"),
    ("GR-2026-013", "PO-2026-014", 7,  "2026-07-02",   0.0, "Pending"),
    ("GR-2026-014", "PO-2026-015", 4,  "2026-07-03", 100.0, "Complete"),
    ("GR-2026-015", "PO-2026-016", 8,  "2026-07-05",  30.0, "Partial"),
]

# ---------------------------------------------------------------------------
# Invoice History  (54 records across all vendors with vendor_id FK)
# Column order: invoice_number, vendor_id, vendor_name,
#               invoice_amount, invoice_date, status
# ---------------------------------------------------------------------------
INVOICE_HISTORY = [
    # --- Acme Corp (vendor_id=1) — 8 invoices, 1 rejected ---
    ("INV-2026-001",     1, "Acme Corp",  5000.00, "2026-05-15", "Paid"),
    ("INV-2026-002",     1, "Acme Corp",  4800.00, "2026-04-20", "Paid"),
    ("INV-2026-003",     1, "Acme Corp",  5200.00, "2026-03-18", "Paid"),
    ("INV-2026-004",     1, "Acme Corp",  4950.00, "2026-02-14", "Paid"),
    ("INV-2026-005",     1, "Acme Corp",  5100.00, "2026-01-10", "Paid"),
    ("INV-2026-006",     1, "Acme Corp",  4800.00, "2025-12-12", "Paid"),
    ("INV-2026-007",     1, "Acme Corp",  5400.00, "2025-11-08", "Paid"),
    ("INV-2026-REJ-001", 1, "Acme Corp",  5000.00, "2025-10-05", "Rejected"),

    # --- Global Supplies Inc (vendor_id=2) — 6 invoices ---
    ("INV-GS-001",       2, "Global Supplies Inc", 12000.00, "2026-05-20", "Paid"),
    ("INV-GS-002",       2, "Global Supplies Inc", 11500.00, "2026-04-15", "Paid"),
    ("INV-GS-003",       2, "Global Supplies Inc", 12500.00, "2026-03-10", "Paid"),
    ("INV-GS-004",       2, "Global Supplies Inc", 11800.00, "2026-02-05", "Paid"),
    ("INV-GS-005",       2, "Global Supplies Inc", 12200.00, "2026-01-08", "Paid"),
    ("INV-2026-999",     2, "Global Supplies Inc", 15250.50, "2026-06-30", "Paid"),

    # --- TechPro Systems (vendor_id=3) — 5 invoices, 1 rejected ---
    ("INV-TP-001",       3, "TechPro Systems",  8500.00, "2026-05-25", "Paid"),
    ("INV-TP-002",       3, "TechPro Systems",  8200.00, "2026-04-10", "Paid"),
    ("INV-TP-003",       3, "TechPro Systems",  9000.00, "2026-03-05", "Paid"),
    ("INV-TP-004",       3, "TechPro Systems",  8700.00, "2026-02-01", "Paid"),
    ("INV-TP-REJ-001",   3, "TechPro Systems",  8500.00, "2025-12-20", "Rejected"),

    # --- Office Direct Ltd (vendor_id=4) — 3 invoices ---
    ("INV-OD-001",       4, "Office Direct Ltd", 3200.00, "2026-05-10", "Paid"),
    ("INV-OD-002",       4, "Office Direct Ltd", 3100.00, "2026-04-08", "Paid"),
    ("INV-OD-003",       4, "Office Direct Ltd", 3300.00, "2026-02-15", "Paid"),

    # --- Premier Logistics (vendor_id=5) — 4 invoices, 1 rejected ---
    ("INV-PL-001",       5, "Premier Logistics", 15000.00, "2026-06-01", "Paid"),
    ("INV-PL-002",       5, "Premier Logistics", 14500.00, "2026-04-20", "Paid"),
    ("INV-PL-003",       5, "Premier Logistics", 15500.00, "2026-03-15", "Paid"),
    ("INV-PL-REJ-001",   5, "Premier Logistics", 15000.00, "2025-11-10", "Rejected"),

    # --- DataCore Solutions (vendor_id=6) — 3 invoices, 1 rejected ---
    ("INV-DC-001",       6, "DataCore Solutions", 22000.00, "2026-04-01", "Paid"),
    ("INV-DC-002",       6, "DataCore Solutions", 21500.00, "2026-02-10", "Paid"),
    ("INV-DC-REJ-001",   6, "DataCore Solutions", 22000.00, "2025-10-20", "Rejected"),

    # --- BuildRight Contractors (vendor_id=7) — 8 invoices ---
    ("INV-BR-001",       7, "BuildRight Contractors", 45000.00, "2026-05-20", "Paid"),
    ("INV-BR-002",       7, "BuildRight Contractors", 44000.00, "2026-04-15", "Paid"),
    ("INV-BR-003",       7, "BuildRight Contractors", 46000.00, "2026-03-10", "Paid"),
    ("INV-BR-004",       7, "BuildRight Contractors", 45500.00, "2026-02-05", "Paid"),
    ("INV-BR-005",       7, "BuildRight Contractors", 44800.00, "2026-01-15", "Paid"),
    ("INV-BR-006",       7, "BuildRight Contractors", 45200.00, "2025-12-10", "Paid"),
    ("INV-BR-007",       7, "BuildRight Contractors", 44500.00, "2025-11-05", "Paid"),
    ("INV-BR-008",       7, "BuildRight Contractors", 45800.00, "2025-10-01", "Paid"),

    # --- CloudStack Inc (vendor_id=8) — 4 invoices, 1 rejected ---
    ("INV-CS-001",       8, "CloudStack Inc",  9800.00, "2026-05-25", "Paid"),
    ("INV-CS-002",       8, "CloudStack Inc",  9500.00, "2026-04-10", "Paid"),
    ("INV-CS-003",       8, "CloudStack Inc", 10100.00, "2026-02-28", "Paid"),
    ("INV-CS-REJ-001",   8, "CloudStack Inc",  9800.00, "2025-12-15", "Rejected"),

    # --- RiskCo LLC (vendor_id=9) — 3 invoices, all rejected ---
    ("INV-RC-001",       9, "RiskCo LLC",  8500.00, "2026-04-10", "Rejected"),
    ("INV-RC-002",       9, "RiskCo LLC",  9000.00, "2026-02-05", "Rejected"),
    ("INV-DUP-123",      9, "RiskCo LLC",  8500.00, "2025-12-01", "Rejected"),

    # --- ShadowVend Corp (vendor_id=10) — 2 invoices, all rejected ---
    ("INV-SV-001",      10, "ShadowVend Corp", 18000.00, "2026-03-20", "Rejected"),
    ("INV-SV-002",      10, "ShadowVend Corp", 18500.00, "2025-11-15", "Rejected"),

    # --- QuickBill Services (vendor_id=11) — 3 invoices, 2 rejected ---
    ("INV-QB-001",      11, "QuickBill Services", 4200.00, "2026-03-01", "Paid"),
    ("INV-QB-002",      11, "QuickBill Services", 4500.00, "2026-01-10", "Rejected"),
    ("INV-QB-003",      11, "QuickBill Services", 4000.00, "2025-10-05", "Rejected"),

    # --- DoubleCharge Inc (vendor_id=12) — 2 identical invoices (duplicate scenario) ---
    ("INV-DCI-001",     12, "DoubleCharge Inc", 11500.00, "2026-02-15", "Rejected"),
    ("INV-DCI-002",     12, "DoubleCharge Inc", 11500.00, "2026-02-15", "Rejected"),

    # --- FraudCo International (vendor_id=17) — 2 identical invoices ---
    ("INV-FC-001",      17, "FraudCo International", 28000.00, "2026-01-10", "Rejected"),
    ("INV-FC-002",      17, "FraudCo International", 28000.00, "2026-01-10", "Rejected"),

    # --- BogusSupply Ltd (vendor_id=18) — 1 invoice ---
    ("INV-BS-001",      18, "BogusSupply Ltd", 15000.00, "2026-03-05", "Rejected"),
]
