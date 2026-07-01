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

import csv
import os
from typing import Optional
from pydantic import BaseModel


class VendorProfile(BaseModel):
    vendor_name: str
    total_previous_invoices: int
    average_invoice_amount: float
    last_invoice_date: str
    previous_rejections: int
    vendor_status: str
    trust_score: int
    last_bank_account_change: str


# Construct the CSV path relative to the file location to ensure robust imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(current_dir, "data", "vendors.csv")


def get_vendor_profile(vendor_name: str) -> VendorProfile:
    """Retrieves the vendor profile from the CSV database.

    If the vendor is not in the database, returns a default 'New' profile.

    Args:
        vendor_name: The name of the vendor to search for.

    Returns:
        A VendorProfile Pydantic model.
    """
    normalized_target = vendor_name.lower().strip() if vendor_name else ""

    if normalized_target and os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_vendor = row.get("Vendor Name", "").lower().strip()
                    if row_vendor == normalized_target:
                        return VendorProfile(
                            vendor_name=row.get("Vendor Name", "").strip(),
                            total_previous_invoices=int(
                                row.get("Total Previous Invoices", 0)
                            ),
                            average_invoice_amount=float(
                                row.get("Average Invoice Amount", 0.0)
                            ),
                            last_invoice_date=row.get(
                                "Last Invoice Date", "N/A"
                            ).strip(),
                            previous_rejections=int(row.get("Previous Rejections", 0)),
                            vendor_status=row.get("Vendor Status", "New").strip(),
                            trust_score=int(row.get("Trust Score", 50)),
                            last_bank_account_change=row.get(
                                "Last Bank Account Change", "N/A"
                            ).strip(),
                        )
        except Exception:
            pass

    # Default profile for unknown/new vendors
    return VendorProfile(
        vendor_name=vendor_name or "Unknown Vendor",
        total_previous_invoices=0,
        average_invoice_amount=0.0,
        last_invoice_date="N/A",
        previous_rejections=0,
        vendor_status="New",
        trust_score=50,
        last_bank_account_change="N/A",
    )
