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

"""Typed dataclass models for ERP entities.

Each model maps 1-to-1 to a SQLite table row and provides:
- from_row(row): construct from a sqlite3.Row
- to_dict(): serialize to a plain dict for API/MCP responses
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Vendor:
    """Represents a row in the ``vendors`` table."""

    vendor_id: int
    vendor_name: str
    vendor_status: str          # Trusted | Watchlist | New | Suspended
    trust_score: int            # 0 - 100
    average_invoice_amount: float
    total_previous_invoices: int
    previous_rejections: int
    last_bank_account_change: Optional[str]
    bank_account: Optional[str]
    risk_level: str             # Low | Medium | High

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Vendor":
        return cls(
            vendor_id=row["vendor_id"],
            vendor_name=row["vendor_name"],
            vendor_status=row["vendor_status"],
            trust_score=row["trust_score"],
            average_invoice_amount=row["average_invoice_amount"],
            total_previous_invoices=row["total_previous_invoices"],
            previous_rejections=row["previous_rejections"],
            last_bank_account_change=row["last_bank_account_change"],
            bank_account=row["bank_account"],
            risk_level=row["risk_level"],
        )

    def to_dict(self) -> dict:
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "vendor_status": self.vendor_status,
            "trust_score": self.trust_score,
            "average_invoice_amount": self.average_invoice_amount,
            "total_previous_invoices": self.total_previous_invoices,
            "previous_rejections": self.previous_rejections,
            "last_bank_account_change": self.last_bank_account_change or "N/A",
            "bank_account": self.bank_account or "N/A",
            "risk_level": self.risk_level,
        }


@dataclass
class PurchaseOrder:
    """Represents a row in the ``purchase_orders`` table."""

    purchase_order_number: str
    vendor_id: int
    vendor_name: str
    approved_amount: float
    currency: str
    purchase_date: str
    status: str                 # Open | Cancelled | Closed
    expected_items: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "PurchaseOrder":
        return cls(
            purchase_order_number=row["purchase_order_number"],
            vendor_id=row["vendor_id"],
            vendor_name=row["vendor_name"],
            approved_amount=row["approved_amount"],
            currency=row["currency"],
            purchase_date=row["purchase_date"],
            status=row["status"],
            expected_items=row["expected_items"],
        )

    def to_dict(self) -> dict:
        return {
            "purchase_order_number": self.purchase_order_number,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "approved_amount": self.approved_amount,
            "currency": self.currency,
            "purchase_date": self.purchase_date,
            "status": self.status,
            "expected_items": self.expected_items or "",
        }


@dataclass
class GoodsReceipt:
    """Represents a row in the ``goods_receipts`` table."""

    goods_receipt_number: str
    purchase_order_number: str
    vendor_id: int
    received_date: str
    received_quantity: float    # percentage 0-100
    status: str                 # Complete | Partial | Pending

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "GoodsReceipt":
        return cls(
            goods_receipt_number=row["goods_receipt_number"],
            purchase_order_number=row["purchase_order_number"],
            vendor_id=row["vendor_id"],
            received_date=row["received_date"],
            received_quantity=row["received_quantity"],
            status=row["status"],
        )

    def to_dict(self) -> dict:
        return {
            "goods_receipt_number": self.goods_receipt_number,
            "purchase_order_number": self.purchase_order_number,
            "vendor_id": self.vendor_id,
            "received_date": self.received_date,
            "received_quantity": self.received_quantity,
            "status": self.status,
        }


@dataclass
class InvoiceHistory:
    """Represents a row in the ``invoice_history`` table."""

    id: int
    invoice_number: str
    vendor_id: int
    vendor_name: str
    invoice_amount: float
    invoice_date: str
    status: str                 # Paid | Rejected | Pending

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "InvoiceHistory":
        return cls(
            id=row["id"],
            invoice_number=row["invoice_number"],
            vendor_id=row["vendor_id"],
            vendor_name=row["vendor_name"],
            invoice_amount=row["invoice_amount"],
            invoice_date=row["invoice_date"],
            status=row["status"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "invoice_amount": self.invoice_amount,
            "invoice_date": self.invoice_date,
            "status": self.status,
        }
