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

"""Unit tests for the ERP FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

import app.erp.database as db_module
from app.fast_api_app import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def tmp_db_for_api(tmp_path, monkeypatch):
    """Redirect the database path for Fast API testing to a temporary database."""
    db_file = str(tmp_path / "api_test_erp.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    
    # Patch get_connection inside queries so it also points to tmp_db
    import app.erp.queries as q_module
    monkeypatch.setattr(q_module, "get_connection", db_module.get_connection)
    
    db_module.init_db()


# ---------------------------------------------------------------------------
# API Tests
# ---------------------------------------------------------------------------

def test_api_get_vendors():
    """Verify GET /api/erp/vendors returns 200 and all seeded vendors."""
    client = TestClient(app)
    response = client.get("/api/erp/vendors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 15
    # Check Acme Corp is in the list
    acme = next((v for v in data if v["vendor_name"] == "Acme Corp"), None)
    assert acme is not None
    assert acme["vendor_status"] == "Trusted"
    assert acme["trust_score"] == 95
    assert acme["vendor_id"] == 1


def test_api_get_vendor_by_id():
    """Verify GET /api/erp/vendors/{vendor_id} returns 200 and correct profile."""
    client = TestClient(app)
    response = client.get("/api/erp/vendors/1")
    assert response.status_code == 200
    data = response.json()
    assert data["vendor_name"] == "Acme Corp"
    assert data["vendor_id"] == 1


def test_api_get_vendor_by_id_not_found():
    """Verify GET /api/erp/vendors/{vendor_id} returns 404 for nonexistent vendor."""
    client = TestClient(app)
    response = client.get("/api/erp/vendors/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Vendor not found"


def test_api_get_vendor_history():
    """Verify GET /api/erp/vendors/{vendor_id}/history returns 200 and list of historical invoices."""
    client = TestClient(app)
    response = client.get("/api/erp/vendors/1/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 7
    assert all(h["vendor_id"] == 1 for h in data)


def test_api_get_vendor_purchase_orders():
    """Verify GET /api/erp/vendors/{vendor_id}/purchase-orders returns 200 and PO list."""
    client = TestClient(app)
    response = client.get("/api/erp/vendors/1/purchase-orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert all(po["vendor_id"] == 1 for po in data)


def test_api_get_vendor_goods_receipts():
    """Verify GET /api/erp/vendors/{vendor_id}/goods-receipts returns 200 and receipt list."""
    client = TestClient(app)
    response = client.get("/api/erp/vendors/1/goods-receipts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert all(r["vendor_id"] == 1 for r in data)


def test_api_get_purchase_orders():
    """Verify GET /api/erp/purchase-orders returns 200 and all POs."""
    client = TestClient(app)
    response = client.get("/api/erp/purchase-orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10
    po1 = next((po for po in data if po["purchase_order_number"] == "PO-2026-001"), None)
    assert po1 is not None
    assert po1["vendor_name"] == "Acme Corp"
    assert po1["status"] == "Open"


def test_api_get_purchase_order_by_number():
    """Verify GET /api/erp/purchase-orders/{po_number} returns 200 and correct PO."""
    client = TestClient(app)
    response = client.get("/api/erp/purchase-orders/PO-2026-001")
    assert response.status_code == 200
    data = response.json()
    assert data["purchase_order_number"] == "PO-2026-001"
    assert data["vendor_name"] == "Acme Corp"


def test_api_get_purchase_order_by_number_not_found():
    """Verify GET /api/erp/purchase-orders/{po_number} returns 404 for nonexistent PO."""
    client = TestClient(app)
    response = client.get("/api/erp/purchase-orders/PO-NONEXISTENT-999")
    assert response.status_code == 404


def test_api_get_goods_receipts():
    """Verify GET /api/erp/goods-receipts returns 200 and all receipts."""
    client = TestClient(app)
    response = client.get("/api/erp/goods-receipts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5


def test_api_get_goods_receipt_by_grn():
    """Verify GET /api/erp/goods-receipts/{grn_number} returns 200 and correct receipt."""
    client = TestClient(app)
    response = client.get("/api/erp/goods-receipts/GR-2026-001")
    assert response.status_code == 200
    data = response.json()
    assert data["goods_receipt_number"] == "GR-2026-001"
    assert data["purchase_order_number"] == "PO-2026-001"


def test_api_get_goods_receipt_by_grn_not_found():
    """Verify GET /api/erp/goods-receipts/{grn_number} returns 404 for nonexistent receipt."""
    client = TestClient(app)
    response = client.get("/api/erp/goods-receipts/GR-NONEXISTENT")
    assert response.status_code == 404
