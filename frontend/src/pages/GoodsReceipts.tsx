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
import { Search, Loader2, AlertCircle, Package } from 'lucide-react';
import type { GoodsReceipt } from '../services/mockData';
import { fetchGoodsReceipts, fetchVendors } from '../services/api';

type FilterType = 'All' | 'Complete' | 'Partial' | 'Pending';
type SortField = 'date' | 'status' | 'vendor';

interface EnrichedGoodsReceipt extends GoodsReceipt {
  vendor_name: string;
}

export const GoodsReceipts: React.FC = () => {
  const navigate = useNavigate();

  const [receipts, setReceipts] = useState<EnrichedGoodsReceipt[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<FilterType>('All');
  const [sortBy, setSortBy] = useState<SortField>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    Promise.all([
      fetchGoodsReceipts(),
      fetchVendors()
    ])
      .then(([grData, vendorList]) => {
        // Map vendor_id to vendor_name for each receipt
        const enriched = grData.map((gr) => {
          const v = vendorList.find(x => x.vendor_id === gr.vendor_id);
          return {
            ...gr,
            vendor_name: v ? v.vendor_name : `Vendor ID ${gr.vendor_id}`
          };
        });
        setReceipts(enriched);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load goods receipts');
        setLoading(false);
      });
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Complete': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Partial': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Pending': return 'bg-slate-50 text-slate-700 border-slate-200';
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
  const filteredReceipts = receipts.filter((gr) => {
    const query = searchQuery.toLowerCase();
    const matchesSearch = 
      gr.goods_receipt_number.toLowerCase().includes(query) ||
      gr.purchase_order_number.toLowerCase().includes(query) ||
      gr.vendor_name.toLowerCase().includes(query);
    
    const matchesStatus = statusFilter === 'All' || gr.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Sorting
  const sortedReceipts = [...filteredReceipts].sort((a, b) => {
    let comp = 0;
    if (sortBy === 'date') {
      comp = a.received_date.localeCompare(b.received_date);
    } else if (sortBy === 'status') {
      comp = a.status.localeCompare(b.status);
    } else if (sortBy === 'vendor') {
      comp = a.vendor_name.localeCompare(b.vendor_name);
    }

    return sortOrder === 'asc' ? comp : -comp;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading Goods Receipts...</p>
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
            onClick={() => { setLoading(true); setError(null); fetchGoodsReceipts().then(() => window.location.reload()).catch(e => setError(e.message)).finally(() => setLoading(false)); }}
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
          <Package className="h-6 w-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800">Goods Receipts</h2>
          <p className="text-xs text-slate-500 mt-1">Browse and search warehouse goods receipt notes (GRN)</p>
        </div>
      </div>

      {/* Filters and search */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {(['All', 'Complete', 'Partial', 'Pending'] as FilterType[]).map((filter) => (
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
            placeholder="Search GRN, PO or Vendor..."
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
                <th className="px-6 py-4">GR Number</th>
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('vendor')}>
                  Vendor {sortBy === 'vendor' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="px-6 py-4">Purchase Order</th>
                <th className="px-6 py-4 text-center">Received Quantity</th>
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('date')}>
                  Received Date {sortBy === 'date' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100" onClick={() => handleSort('status')}>
                  Status {sortBy === 'status' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {sortedReceipts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-400">
                    No Goods Receipts found.
                  </td>
                </tr>
              ) : (
                sortedReceipts.map((gr) => (
                  <tr 
                    key={gr.goods_receipt_number} 
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/goods-receipts/${gr.goods_receipt_number}`)}
                  >
                    <td className="px-6 py-4 font-mono font-medium text-slate-800 hover:text-emerald-600 hover:underline">
                      {gr.goods_receipt_number}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{gr.vendor_name}</td>
                    <td className="px-6 py-4 font-mono text-slate-500">{gr.purchase_order_number}</td>
                    <td className="px-6 py-4 text-center font-semibold text-slate-855">{gr.received_quantity}%</td>
                    <td className="px-6 py-4 text-slate-500">{gr.received_date}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(gr.status)}`}>
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
    </div>
  );
};
