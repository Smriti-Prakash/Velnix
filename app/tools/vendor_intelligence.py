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
    vendor_found: bool = True
    vendor_finding: str = ""



def get_vendor_profile(vendor_name: str) -> VendorProfile:
    """Retrieves the vendor profile from the SQLite ERP database.

    If the vendor is not in the database, returns a default 'New' profile with vendor_found=False.

    Args:
        vendor_name: The name of the vendor to search for.

    Returns:
        A VendorProfile Pydantic model.
    """
    normalized_target = vendor_name.strip() if vendor_name else ""

    if normalized_target:
        try:
            from app.erp.queries import fetch_vendor_by_name, fetch_invoice_history_by_vendor_name
            vendor = fetch_vendor_by_name(normalized_target)
            if vendor:
                # Find last invoice date from history
                history = fetch_invoice_history_by_vendor_name(normalized_target)
                last_invoice_date = "N/A"
                if history:
                    # History is ordered newest-first
                    last_invoice_date = history[0].invoice_date
                
                vendor_finding = f"Vendor {vendor.vendor_name} was found in the ERP vendor master and is classified as a {vendor.vendor_status} vendor."
                
                return VendorProfile(
                    vendor_name=vendor.vendor_name,
                    total_previous_invoices=vendor.total_previous_invoices,
                    average_invoice_amount=vendor.average_invoice_amount,
                    last_invoice_date=last_invoice_date,
                    previous_rejections=vendor.previous_rejections,
                    vendor_status=vendor.vendor_status,
                    trust_score=vendor.trust_score,
                    last_bank_account_change=vendor.last_bank_account_change or "N/A",
                    vendor_found=True,
                    vendor_finding=vendor_finding,
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
        vendor_found=False,
        vendor_finding="Vendor was not found in the ERP vendor master. Vendor verification could not be completed.",
    )

