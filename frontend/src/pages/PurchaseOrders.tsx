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
import { useNavigate } from 'react-router-dom';
import { Search, Loader2, AlertCircle, ShoppingCart } from 'lucide-react';
import type { PurchaseOrder } from '../services/mockData';
import { fetchPurchaseOrders } from '../services/api';

type FilterType = 'All' | 'Open' | 'Closed' | 'Cancelled';
type SortField = 'date' | 'amount' | 'status';

export const PurchaseOrders: React.FC = () => {
  const navigate = useNavigate();

  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<FilterType>('All');
  const [sortBy, setSortBy] = useState<SortField>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchPurchaseOrders()
      .then((data) => {
        setPurchaseOrders(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load purchase orders');
        setLoading(false);
      });
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Open': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Closed': return 'bg-slate-50 text-slate-700 border-slate-200';
      case 'Cancelled': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  // Filter and search
  const filteredPO = purchaseOrders.filter((po) => {
    const matchesSearch = 
      po.purchase_order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      po.vendor_name.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'All' || po.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Sorting logic
  const sortedPO = [...filteredPO].sort((a, b) => {
    let comp = 0;
    if (sortBy === 'date') {
      comp = a.purchase_date.localeCompare(b.purchase_date);
    } else if (sortBy === 'amount') {
      comp = a.approved_amount - b.approved_amount;
    } else if (sortBy === 'status') {
      comp = a.status.localeCompare(b.status);
    }

    return sortOrder === 'asc' ? comp : -comp;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading Purchase Orders...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-start space-x-3 max-w-2xl mx-auto my-12">
        <AlertCircle className="h-6 w-6 text-red-500 shrink-0" />
        <div>
          <h3 className="text-sm font-bold text-red-800">Connection Error</h3>
          <p className="text-sm text-red-700 mt-1">{error}</p>
          <button 
            onClick={() => { setLoading(true); setError(null); fetchPurchaseOrders().then(setPurchaseOrders).catch(e => setError(e.message)).finally(() => setLoading(false)); }}
            className="mt-4 px-4 py-2 bg-red-800 text-white rounded text-xs font-semibold hover:bg-red-900 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Title */}
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-slate-900 text-emerald-500 rounded-lg">
          <ShoppingCart className="h-6 w-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800">Purchase Orders</h2>
          <p className="text-xs text-slate-500 mt-1">Browse and search active Purchase Orders from the SQLite ERP registry</p>
        </div>
      </div>

      {/* Filters and search */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {(['All', 'Open', 'Closed', 'Cancelled'] as FilterType[]).map((filter) => (
            <button
              key={filter}
              onClick={() => setStatusFilter(filter)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                statusFilter === filter
                  ? 'bg-emerald-600 border-emerald-600 text-white shadow-sm'
                  : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

        <div className="relative max-w-xs w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search PO # or Vendor..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider select-none">
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('date')}>
                  PO Number {sortBy === 'date' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="px-6 py-4">Vendor</th>
                <th className="px-6 py-4">Order ID</th>
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('date')}>
                  Issue Date {sortBy === 'date' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="px-6 py-4 text-right cursor-pointer hover:bg-slate-100" onClick={() => handleSort('amount')}>
                  Amount {sortBy === 'amount' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('status')}>
                  Status {sortBy === 'status' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {sortedPO.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-400">
                    No Purchase Orders found matching the criteria.
                  </td>
                </tr>
              ) : (
                sortedPO.map((po) => (
                  <tr 
                    key={po.purchase_order_number} 
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/purchase-orders/${po.purchase_order_number}`)}
                  >
                    <td className="px-6 py-4 font-mono font-medium text-slate-800 hover:text-emerald-600 hover:underline">
                      {po.purchase_order_number}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{po.vendor_name}</td>
                    <td className="px-6 py-4 text-slate-500 font-mono">—</td>
                    <td className="px-6 py-4 text-slate-500">{po.purchase_date}</td>
                    <td className="px-6 py-4 text-right font-bold text-slate-800">
                      {po.currency} {po.approved_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(po.status)}`}>
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
    </div>
  );
};
