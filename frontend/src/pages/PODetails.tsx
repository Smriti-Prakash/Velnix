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
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShoppingCart, Loader2, AlertCircle, ShieldCheck } from 'lucide-react';
import type { PurchaseOrder, GoodsReceipt } from '../services/mockData';
import { fetchPurchaseOrder, fetchGoodsReceipts } from '../services/api';

export const PODetails: React.FC = () => {
  const { poNumber } = useParams<{ poNumber: string }>();
  const decodedPoNumber = decodeURIComponent(poNumber || '');
  const navigate = useNavigate();

  const [po, setPO] = useState<PurchaseOrder | null>(null);
  const [receipts, setReceipts] = useState<GoodsReceipt[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      fetchPurchaseOrder(decodedPoNumber),
      fetchGoodsReceipts()
    ])
      .then(([poData, allReceipts]) => {
        setPO(poData);
        // Filter goods receipts linked to this purchase order
        const relatedReceipts = allReceipts.filter(
          r => r.purchase_order_number.toUpperCase() === decodedPoNumber.toUpperCase()
        );
        setReceipts(relatedReceipts);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load purchase order details');
        setLoading(false);
      });
  }, [decodedPoNumber]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Open': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Closed': return 'bg-slate-50 text-slate-700 border-slate-200';
      case 'Cancelled': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  const getGrStatusBadge = (status: string) => {
    switch (status) {
      case 'Complete': return 'bg-emerald-100 text-emerald-855 border-emerald-200';
      case 'Partial': return 'bg-amber-100 text-amber-855 border-amber-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading Purchase Order details...</p>
      </div>
    );
  }

  if (error || !po) {
    return (
      <div className="max-w-xl mx-auto py-12 text-center space-y-4">
        <div className="inline-flex p-3 bg-red-50 text-red-500 rounded-full">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">Purchase Order Not Found</h3>
        <p className="text-sm text-slate-500">{error || `PO "${decodedPoNumber}" could not be retrieved.`}</p>
        <Link to="/purchase-orders" className="inline-block mt-4 text-emerald-600 font-semibold hover:underline">
          Back to Purchase Orders
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Back button */}
      <div>
        <Link to="/purchase-orders" className="flex items-center space-x-2 text-sm text-slate-500 hover:text-slate-800 transition-colors">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Purchase Orders</span>
        </Link>
      </div>

      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-slate-900 text-emerald-500 rounded-xl">
            <ShoppingCart className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-800">{po.purchase_order_number}</h2>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(po.status)}`}>
                {po.status}
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-slate-500 text-xs font-semibold">ERP Purchase Order Registry</span>
            </div>
          </div>
        </div>

        <div className="text-right">
          <p className="text-xs font-semibold text-slate-400 uppercase">Approved Amount</p>
          <p className="text-3xl font-extrabold text-slate-800 mt-1">
            {po.currency} {po.approved_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      {/* General Information Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-md font-bold text-slate-800 border-b border-slate-100 pb-3">General Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4 mt-4 text-sm">
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">PO Number</span>
            <span className="text-slate-800 font-semibold font-mono">{po.purchase_order_number}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Order ID</span>
            <span className="text-slate-800 font-semibold font-mono">—</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Vendor</span>
            <Link to={`/vendors/${encodeURIComponent(po.vendor_name)}`} className="text-emerald-600 font-semibold hover:underline">
              {po.vendor_name}
            </Link>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Created Date</span>
            <span className="text-slate-800 font-semibold">{po.purchase_date}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Status</span>
            <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getStatusBadge(po.status)}`}>
              {po.status}
            </span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-50">
            <span className="text-slate-400 font-medium">Currency</span>
            <span className="text-slate-800 font-semibold">{po.currency}</span>
          </div>
          <div className="flex justify-between py-2 md:col-span-2">
            <span className="text-slate-400 font-medium">Expected Items / Scope</span>
            <span className="text-slate-800 font-semibold">{po.expected_items || 'No scope details available'}</span>
          </div>
        </div>
      </div>

      {/* Related Goods Receipts */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <h3 className="text-md font-bold text-slate-800">Related Goods Receipts</h3>
          <p className="text-xs text-slate-500 mt-1">Goods receipts matched to this PO in ERP records</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-4">GR Number</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-center">Received Quantity</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {receipts.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-8 text-slate-400">
                    No goods receipts associated with this Purchase Order.
                  </td>
                </tr>
              ) : (
                receipts.map((gr) => (
                  <tr 
                    key={gr.goods_receipt_number} 
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/goods-receipts/${gr.goods_receipt_number}`)}
                  >
                    <td className="px-6 py-4 font-mono font-medium text-slate-800 hover:text-emerald-600 hover:underline">
                      {gr.goods_receipt_number}
                    </td>
                    <td className="px-6 py-4 text-slate-500">{gr.received_date}</td>
                    <td className="px-6 py-4 text-center font-semibold text-slate-800">{gr.received_quantity}%</td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getGrStatusBadge(gr.status)}`}>
                        {gr.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Related Invoices Placeholder */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 className="text-md font-bold text-slate-800 border-b border-slate-100 pb-3">Related Invoices</h3>
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-center">
          <p className="text-sm text-slate-500 font-medium">
            Invoice relationships will be available in the next implementation phase after Purchase Order references are added to invoice history.
          </p>
        </div>
      </div>

      {/* Future Placeholder for Three-Way Match */}
      <div className="bg-emerald-50 border border-emerald-200 border-dashed rounded-xl p-8 text-center">
        <ShieldCheck className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
        <h4 className="text-md font-bold text-emerald-800">Three-Way Match & Enterprise Validation</h4>
        <p className="text-xs text-emerald-600 mt-1 max-w-lg mx-auto">
          Automated line-item validation comparing Invoices, Purchase Orders, and Goods Receipts is coming in Phase 4 Step 3.
        </p>
      </div>
    </div>
  );
};
