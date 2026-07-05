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

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Package, Loader2, AlertCircle, ShoppingCart } from 'lucide-react';
import type { GoodsReceipt, PurchaseOrder, ErpVendor } from '../services/mockData';
import { fetchGoodsReceipt, fetchPurchaseOrder, fetchVendors } from '../services/api';

export const GRDetails: React.FC = () => {
  const { grnNumber } = useParams<{ grnNumber: string }>();
  const decodedGrnNumber = decodeURIComponent(grnNumber || '');

  const [receipt, setReceipt] = useState<GoodsReceipt | null>(null);
  const [po, setPO] = useState<PurchaseOrder | null>(null);
  const [vendor, setVendor] = useState<ErpVendor | null>(null);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchGoodsReceipt(decodedGrnNumber)
      .then((grData) => {
        setReceipt(grData);
        // Fetch related purchase order and all vendors to map details
        return Promise.all([
          fetchPurchaseOrder(grData.purchase_order_number),
          fetchVendors()
        ]);
      })
      .then(([poData, vendorList]) => {
        setPO(poData);
        if (receipt) {
          const v = vendorList.find(x => x.vendor_id === receipt.vendor_id);
          if (v) setVendor(v);
        } else {
          // If state batching hasn't updated yet, search using poData
          const v = vendorList.find(x => x.vendor_id === poData.vendor_id);
          if (v) setVendor(v);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load goods receipt details');
        setLoading(false);
      });
  }, [decodedGrnNumber]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Complete': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Partial': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Pending': return 'bg-slate-50 text-slate-700 border-slate-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  const getPoStatusBadge = (status: string) => {
    switch (status) {
      case 'Open': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Closed': return 'bg-slate-50 text-slate-700 border-slate-200';
      case 'Cancelled': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading Goods Receipt details...</p>
      </div>
    );
  }

  if (error || !receipt) {
    return (
      <div className="max-w-xl mx-auto py-12 text-center space-y-4">
        <div className="inline-flex p-3 bg-red-50 text-red-500 rounded-full">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">Goods Receipt Not Found</h3>
        <p className="text-sm text-slate-500">{error || `GRN "${decodedGrnNumber}" could not be retrieved.`}</p>
        <Link to="/goods-receipts" className="inline-block mt-4 text-emerald-600 font-semibold hover:underline">
          Back to Goods Receipts
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Back button */}
      <div>
        <Link to="/goods-receipts" className="flex items-center space-x-2 text-sm text-slate-500 hover:text-slate-800 transition-colors">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Goods Receipts</span>
        </Link>
      </div>

      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-slate-900 text-emerald-500 rounded-xl">
            <Package className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-800">{receipt.goods_receipt_number}</h2>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(receipt.status)}`}>
                {receipt.status}
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-slate-500 text-xs font-semibold">ERP Goods Receipt Registry</span>
            </div>
          </div>
        </div>

        <div className="text-right">
          <p className="text-xs font-semibold text-slate-400 uppercase">Received Quantity</p>
          <p className="text-3xl font-extrabold text-slate-800 mt-1">{receipt.received_quantity}%</p>
        </div>
      </div>

      {/* Receipt Details Information Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-md font-bold text-slate-800 border-b border-slate-100 pb-3">Receipt Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4 mt-4 text-sm">
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">GRN Number</span>
            <span className="text-slate-800 font-semibold font-mono">{receipt.goods_receipt_number}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Purchase Order</span>
            <Link to={`/purchase-orders/${receipt.purchase_order_number}`} className="text-emerald-600 font-semibold hover:underline font-mono">
              {receipt.purchase_order_number}
            </Link>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Vendor</span>
            <span className="text-slate-800 font-semibold">
              {vendor ? (
                <Link to={`/vendors/${encodeURIComponent(vendor.vendor_name)}`} className="text-emerald-600 font-semibold hover:underline">
                  {vendor.vendor_name}
                </Link>
              ) : (
                `Vendor ID ${receipt.vendor_id}`
              )}
            </span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Received Date</span>
            <span className="text-slate-800 font-semibold">{receipt.received_date}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50 col-span-2">
            <span className="text-slate-400 font-medium">Status</span>
            <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getStatusBadge(receipt.status)}`}>
              {receipt.status}
            </span>
          </div>
        </div>
      </div>

      {/* Related Purchase Order Card */}
      {po && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-md font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center space-x-2">
            <ShoppingCart className="h-4 w-4 text-slate-500" />
            <span>Related Purchase Order</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4 mt-4 text-sm">
            <div className="flex justify-between py-2 border-b border-slate-50">
              <span className="text-slate-400 font-medium">PO Number</span>
              <Link to={`/purchase-orders/${po.purchase_order_number}`} className="text-emerald-600 font-semibold hover:underline font-mono">
                {po.purchase_order_number}
              </Link>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-50">
              <span className="text-slate-400 font-medium">Vendor</span>
              <span className="text-slate-800 font-semibold">{po.vendor_name}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400 font-medium">PO Status</span>
              <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getPoStatusBadge(po.status)}`}>
                {po.status}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400 font-medium">Approved Amount</span>
              <span className="text-slate-800 font-semibold">
                {po.currency} {po.approved_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Linked Invoice Placeholder */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 className="text-md font-bold text-slate-800 border-b border-slate-100 pb-3">Linked Invoice</h3>
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-center">
          <p className="text-sm text-slate-500 font-medium">
            No linked invoice. Will be implemented in Phase 4 Step 3.
          </p>
        </div>
      </div>
    </div>
  );
};
