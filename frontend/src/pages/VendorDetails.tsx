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
import { 
  ArrowLeft, 
  UserCheck, 
  Loader2, 
  AlertCircle, 
  FileText, 
  ShoppingCart, 
  Package, 
  Clock 
} from 'lucide-react';
import type { ErpVendor, PurchaseOrder, GoodsReceipt, InvoiceHistoryRecord } from '../services/mockData';
import { 
  fetchVendors, 
  fetchVendorHistory, 
  fetchVendorPurchaseOrders, 
  fetchVendorGoodsReceipts 
} from '../services/api';

type TabType = 'profile' | 'invoices' | 'pos' | 'receipts';

export const VendorDetails: React.FC = () => {
  const { name } = useParams<{ name: string }>();
  const vendorName = decodeURIComponent(name || '');
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [vendor, setVendor] = useState<ErpVendor | null>(null);
  const [invoices, setInvoices] = useState<InvoiceHistoryRecord[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [goodsReceipts, setGoodsReceipts] = useState<GoodsReceipt[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    
    // Resolve vendor_id by fetching list of vendors
    fetchVendors()
      .then((vendorList) => {
        const found = vendorList.find(
          v => v.vendor_name.toLowerCase().trim() === vendorName.toLowerCase().trim()
        );
        
        if (!found) {
          throw new Error(`Vendor "${vendorName}" not found in ERP records.`);
        }
        
        setVendor(found);
        
        // Fetch all related details in parallel using the vendor_id
        return Promise.all([
          fetchVendorHistory(found.vendor_id),
          fetchVendorPurchaseOrders(found.vendor_id),
          fetchVendorGoodsReceipts(found.vendor_id)
        ]);
      })
      .then(([historyData, posData, receiptsData]) => {
        setInvoices(historyData as InvoiceHistoryRecord[]);
        setPurchaseOrders(posData as PurchaseOrder[]);
        setGoodsReceipts(receiptsData as GoodsReceipt[]);
        setLoading(false);
      })

      .catch((err) => {
        setError(err.message || 'Failed to load vendor details');
        setLoading(false);
      });
  }, [vendorName]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Trusted': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'Watchlist': return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'New': return 'bg-slate-100 text-slate-800 border-slate-200';
      case 'Suspended': return 'bg-amber-100 text-amber-800 border-amber-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'emerald';
      case 'Medium': return 'amber';
      case 'High': return 'rose';
      default: return 'slate';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading vendor records...</p>
      </div>
    );
  }

  if (error || !vendor) {
    return (
      <div className="max-w-xl mx-auto py-12 text-center space-y-4">
        <div className="inline-flex p-3 bg-red-50 text-red-500 rounded-full">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-800">Vendor Lookup Failed</h3>
        <p className="text-sm text-slate-500">{error || 'Vendor not found.'}</p>
        <Link to="/vendors" className="inline-block mt-4 text-emerald-600 font-semibold hover:underline">
          Back to Vendor Registry
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Back link */}
      <div>
        <Link to="/vendors" className="flex items-center space-x-2 text-sm text-slate-500 hover:text-slate-800 transition-colors">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Vendors</span>
        </Link>
      </div>

      {/* Profile Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-slate-900 text-emerald-500 rounded-xl">
            <UserCheck className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-800">{vendor.vendor_name}</h2>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(vendor.vendor_status)}`}>
                {vendor.vendor_status}
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-slate-500 text-xs font-semibold">ERP Database Registry</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          <div className="text-center md:text-right">
            <p className="text-xs font-semibold text-slate-400 uppercase">Trust Score</p>
            <p className="text-3xl font-extrabold text-slate-800 mt-1">{vendor.trust_score}/100</p>
          </div>
        </div>
      </div>

      {/* Tabs list */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8" aria-label="Tabs">
          {(['profile', 'invoices', 'pos', 'receipts'] as TabType[]).map((tab) => {
            const labelMap: Record<TabType, string> = {
              profile: 'Profile',
              invoices: `Invoice History (${invoices.length})`,
              pos: `Purchase Orders (${purchaseOrders.length})`,
              receipts: `Goods Receipts (${goodsReceipts.length})`
            };
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  isActive
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                {labelMap[tab]}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Contents */}
      {activeTab === 'profile' && (
        <div className="space-y-6">
          {/* Key Statistics cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Previous Invoices</p>
              <p className="text-2xl font-bold text-slate-800 mt-2">{vendor.total_previous_invoices}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Average Billing</p>
              <p className="text-2xl font-bold text-slate-800 mt-2">
                ${vendor.average_invoice_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Previous Rejections</p>
              <p className="text-2xl font-bold text-rose-700 mt-2">{vendor.previous_rejections}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm col-span-2 md:col-span-1">
              <p className="text-xs font-semibold text-slate-400 uppercase">Bank Changes</p>
              <p className="text-sm font-semibold text-slate-700 mt-3 truncate">
                {vendor.last_bank_account_change || 'No Changes'}
              </p>
            </div>
          </div>

          {/* Relationship Metrics & Quick info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-5 flex items-center space-x-4">
              <div className="p-3 bg-emerald-500/10 text-emerald-600 rounded-lg">
                <ShoppingCart className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-500 font-medium">Purchase Orders</p>
                <p className="text-xl font-bold text-slate-800">{purchaseOrders.length} records</p>
              </div>
            </div>
            
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-5 flex items-center space-x-4">
              <div className="p-3 bg-blue-500/10 text-blue-600 rounded-lg">
                <Package className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-500 font-medium">Goods Receipts</p>
                <p className="text-xl font-bold text-slate-800">{goodsReceipts.length} entries</p>
              </div>
            </div>

            <div className="bg-purple-50 border border-purple-100 rounded-xl p-5 flex items-center space-x-4">
              <div className="p-3 bg-purple-500/10 text-purple-600 rounded-lg">
                <FileText className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-500 font-medium">Historical Invoices</p>
                <p className="text-xl font-bold text-slate-800">{invoices.length} transactions</p>
              </div>
            </div>
          </div>

          {/* Vendor Summary Panel */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-md font-bold text-slate-800 border-b border-slate-100 pb-3">Vendor Summary</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4 mt-4 text-sm">
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Vendor ID</span>
                <span className="text-slate-800 font-semibold">{vendor.vendor_id}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Vendor Status</span>
                <span className="text-slate-800 font-semibold">{vendor.vendor_status}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Risk Level</span>
                <span className={`px-2 py-0.5 rounded text-xs font-bold border bg-${getRiskColor(vendor.risk_level)}-50 text-${getRiskColor(vendor.risk_level)}-700 border-${getRiskColor(vendor.risk_level)}-200`}>
                  {vendor.risk_level}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Trust Score</span>
                <span className="text-slate-800 font-semibold">{vendor.trust_score}/100</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Total Previous Invoices</span>
                <span className="text-slate-800 font-semibold">{vendor.total_previous_invoices}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Average Invoice Amount</span>
                <span className="text-slate-800 font-semibold">
                  ${vendor.average_invoice_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Previous Rejections</span>
                <span className="text-slate-800 font-semibold">{vendor.previous_rejections}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-50">
                <span className="text-slate-400 font-medium">Last Bank Account Change</span>
                <span className="text-slate-800 font-semibold">{vendor.last_bank_account_change || 'Not Available'}</span>
              </div>
              <div className="flex justify-between py-2 md:col-span-2">
                <span className="text-slate-400 font-medium">Masked Bank Account</span>
                <span className="text-slate-800 font-semibold font-mono">
                  {vendor.bank_account ? `****${vendor.bank_account.slice(-4)}` : 'Not Available'}
                </span>
              </div>
            </div>
          </div>

          {/* Coming Soon Placeholder */}
          <div className="bg-slate-50 border border-slate-200 border-dashed rounded-xl p-8 text-center">
            <Clock className="h-6 w-6 text-slate-400 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-slate-700">🔮 Risk Timeline</h4>
            <p className="text-xs text-slate-500 mt-1">Unified analytics showing vendor audit events will be available soon.</p>
          </div>
        </div>
      )}

      {activeTab === 'invoices' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-md font-bold text-slate-800">Invoice History</h3>
            <p className="text-xs text-slate-500 mt-1">Transaction entries matching this vendor in ERP records</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="px-6 py-4">Invoice Number</th>
                  <th className="px-6 py-4">Invoice Date</th>
                  <th className="px-6 py-4 text-right">Invoice Amount</th>
                  <th className="px-6 py-4 text-center">Risk Score</th>
                  <th className="px-6 py-4 text-center">Fraud Score</th>
                  <th className="px-6 py-4">Decision Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-400">
                      No invoices found in ERP history.
                    </td>
                  </tr>
                ) : (
                  invoices.map((invoice) => (
                    <tr key={invoice.invoice_number} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-mono font-medium text-slate-800">
                        {invoice.invoice_number}
                      </td>
                      <td className="px-6 py-4 text-slate-500">{invoice.invoice_date}</td>
                      <td className="px-6 py-4 text-right font-bold text-slate-800">
                        ${invoice.invoice_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4 text-center text-slate-400">—</td>
                      <td className="px-6 py-4 text-center text-slate-400">—</td>
                      <td className="px-6 py-4">
                        <span className={`inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
                          invoice.status === 'Paid' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          invoice.status === 'Pending' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          'bg-rose-50 text-rose-700 border-rose-200'
                        }`}>
                          {invoice.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'pos' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-md font-bold text-slate-800">Purchase Orders</h3>
            <p className="text-xs text-slate-500 mt-1">Authorized Purchase Orders issued to this vendor</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="px-6 py-4">PO Number</th>
                  <th className="px-6 py-4">Order ID</th>
                  <th className="px-6 py-4">Issue Date</th>
                  <th className="px-6 py-4 text-right">Total Amount</th>
                  <th className="px-6 py-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {purchaseOrders.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-slate-400">
                      No Purchase Orders found.
                    </td>
                  </tr>
                ) : (
                  purchaseOrders.map((po) => (
                    <tr 
                      key={po.purchase_order_number} 
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/purchase-orders/${po.purchase_order_number}`)}
                    >
                      <td className="px-6 py-4 font-mono font-medium text-slate-800 hover:text-emerald-600 hover:underline">
                        {po.purchase_order_number}
                      </td>
                      <td className="px-6 py-4 text-slate-500 font-mono">—</td>
                      <td className="px-6 py-4 text-slate-500">{po.purchase_date}</td>
                      <td className="px-6 py-4 text-right font-bold text-slate-800">
                        {po.currency} {po.approved_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
                          po.status === 'Open' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          po.status === 'Closed' ? 'bg-slate-50 text-slate-700 border-slate-200' :
                          'bg-rose-50 text-rose-700 border-rose-200'
                        }`}>
                          {po.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'receipts' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-md font-bold text-slate-800">Goods Receipts</h3>
            <p className="text-xs text-slate-500 mt-1">Receipt confirmations of goods or services matching this vendor</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="px-6 py-4">GRN Number</th>
                  <th className="px-6 py-4">Purchase Order</th>
                  <th className="px-6 py-4 text-center">Received Quantity</th>
                  <th className="px-6 py-4">Received Date</th>
                  <th className="px-6 py-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {goodsReceipts.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-slate-400">
                      No Goods Receipts found.
                    </td>
                  </tr>
                ) : (
                  goodsReceipts.map((gr) => (
                    <tr 
                      key={gr.goods_receipt_number} 
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/goods-receipts/${gr.goods_receipt_number}`)}
                    >
                      <td className="px-6 py-4 font-mono font-medium text-slate-800 hover:text-emerald-600 hover:underline">
                        {gr.goods_receipt_number}
                      </td>
                      <td className="px-6 py-4 font-mono text-slate-500 hover:underline" onClick={(e) => { e.stopPropagation(); navigate(`/purchase-orders/${gr.purchase_order_number}`); }}>
                        {gr.purchase_order_number}
                      </td>
                      <td className="px-6 py-4 text-center font-semibold text-slate-800">{gr.received_quantity}%</td>
                      <td className="px-6 py-4 text-slate-500">{gr.received_date}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
                          gr.status === 'Complete' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          gr.status === 'Partial' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          'bg-slate-50 text-slate-700 border-slate-200'
                        }`}>
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
      )}
    </div>
  );
};
