// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import type { ErpVendor, PurchaseOrder, GoodsReceipt, InvoiceHistoryRecord } from './mockData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, options);
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const fetchVendors = (): Promise<ErpVendor[]> => {
  return request<ErpVendor[]>('/api/erp/vendors');
};

export const fetchVendor = (vendorId: number): Promise<ErpVendor> => {
  return request<ErpVendor>(`/api/erp/vendors/${vendorId}`);
};

export const fetchVendorHistory = (vendorId: number): Promise<InvoiceHistoryRecord[]> => {
  return request<InvoiceHistoryRecord[]>(`/api/erp/vendors/${vendorId}/history`);
};

export const fetchVendorPurchaseOrders = (vendorId: number): Promise<PurchaseOrder[]> => {
  return request<PurchaseOrder[]>(`/api/erp/vendors/${vendorId}/purchase-orders`);
};

export const fetchVendorGoodsReceipts = (vendorId: number): Promise<GoodsReceipt[]> => {
  return request<GoodsReceipt[]>(`/api/erp/vendors/${vendorId}/goods-receipts`);
};

export const fetchPurchaseOrders = (): Promise<PurchaseOrder[]> => {
  return request<PurchaseOrder[]>('/api/erp/purchase-orders');
};

export const fetchPurchaseOrder = (poNumber: string): Promise<PurchaseOrder> => {
  return request<PurchaseOrder>(`/api/erp/purchase-orders/${encodeURIComponent(poNumber)}`);
};

export const fetchGoodsReceipts = (): Promise<GoodsReceipt[]> => {
  return request<GoodsReceipt[]>('/api/erp/goods-receipts');
};

export const fetchGoodsReceipt = (grnNumber: string): Promise<GoodsReceipt> => {
  return request<GoodsReceipt>(`/api/erp/goods-receipts/${encodeURIComponent(grnNumber)}`);
};
