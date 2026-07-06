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

import pytest
from app.fast_api_app import parse_csv_invoice


def test_parse_csv_invoice_key_value_success():
    csv_content = b"""Invoice Number,INV-2026-CSV
Vendor Name,SuperStore
Invoice Amount,910.50
Invoice Date,2026-07-01
Due Date,2026-07-31
Purchase Order Number,PO-404
Currency,USD
Payment Terms,Net 30"""

    res = parse_csv_invoice(csv_content)
    assert res["invoice_number"] == "INV-2026-CSV"
    assert res["vendor_name"] == "SuperStore"
    assert res["amount"] == 910.50
    assert res["invoice_date"] == "2026-07-01"
    assert res["currency"] == "USD"
    assert "Invoice ID: INV-2026-CSV" in res["text"]
    assert "Vendor Name: SuperStore" in res["text"]
    assert "Total Amount: USD910.50" in res["text"]
    assert "Purchase Order Number: PO-404" in res["text"]
    assert "Payment Terms: Net 30" in res["text"]


def test_parse_csv_invoice_header_row_success():
    csv_content = b"""invoice_number,vendor_name,invoice_amount,invoice_date,currency,purchase_order_number
INV-HEADER-123,Acme Corp,$5000.00,2026-06-30,$,PO-100"""

    res = parse_csv_invoice(csv_content)
    assert res["invoice_number"] == "INV-HEADER-123"
    assert res["vendor_name"] == "Acme Corp"
    assert res["amount"] == 5000.0
    assert res["invoice_date"] == "2026-06-30"
    assert res["currency"] == "$"
    assert "Invoice ID: INV-HEADER-123" in res["text"]
    assert "Vendor Name: Acme Corp" in res["text"]


def test_parse_csv_invoice_missing_number():
    csv_content = b"""Vendor Name,SuperStore
Invoice Amount,910.50
Invoice Date,2026-07-01"""
    with pytest.raises(ValueError, match="Missing required field: Invoice Number."):
        parse_csv_invoice(csv_content)


def test_parse_csv_invoice_invalid_amount():
    csv_content = b"""Invoice Number,INV-2026-CSV
Vendor Name,SuperStore
Invoice Amount,-120.00
Invoice Date,2026-07-01"""
    with pytest.raises(ValueError, match="Invalid or missing Invoice Amount. Must be a positive number."):
        parse_csv_invoice(csv_content)


def test_parse_csv_invoice_invalid_date_format():
    # "01-Jul-26" is not in the supported normalisation formats; the parser
    # should reject it with the canonical error message.
    csv_content = b"""Invoice Number,INV-2026-CSV
Vendor Name,SuperStore
Invoice Amount,500.00
Invoice Date,01-Jul-26"""
    with pytest.raises(ValueError, match="Invalid Invoice Date format \\(must be YYYY-MM-DD\\)."):
        parse_csv_invoice(csv_content)
