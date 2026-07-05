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
import { Link as RouterLink } from 'react-router-dom';
import { Eye, Loader2, AlertCircle } from 'lucide-react';
import type { ErpVendor } from '../services/mockData';
import { fetchVendors } from '../services/api';

export const Vendors: React.FC = () => {
  const [vendors, setVendors] = useState<ErpVendor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVendors()
      .then((data) => {
        setVendors(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load vendors');
        setLoading(false);
      });
  }, []);

  const getRiskLevelStyles = (level: string) => {
    switch (level) {
      case 'Low': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Medium': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'High': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'Critical': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Trusted': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'Watchlist': return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'New': return 'bg-slate-100 text-slate-800 border-slate-200';
      case 'Suspended': return 'bg-amber-100 text-amber-800 border-amber-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <Loader2 className="h-8 w-8 text-emerald-500 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading vendor registry...</p>
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
            onClick={() => { setLoading(true); setError(null); fetchVendors().then(setVendors).catch(e => setError(e.message)).finally(() => setLoading(false)); }}
            className="mt-4 px-4 py-2 bg-red-800 text-white rounded text-xs font-semibold hover:bg-red-900 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden animate-fadeIn">
      <div className="p-6 border-b border-slate-200">
        <h2 className="text-lg font-bold text-slate-800">Master Vendor Registry</h2>
        <p className="text-xs text-slate-500 mt-1">Directory of historical vendors and calculated trust scores</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th className="px-6 py-4">Vendor Name</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-center">Trust Score</th>
              <th className="px-6 py-4 text-center">Previous Invoices</th>
              <th className="px-6 py-4 text-right">Average Invoice Amount</th>
              <th className="px-6 py-4 text-center">Risk Level</th>
              <th className="px-6 py-4 text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {vendors.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-slate-400">
                  No vendors found in ERP master records.
                </td>
              </tr>
            ) : (
              vendors.map((vendor) => (
                <tr key={vendor.vendor_id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-semibold text-slate-800">{vendor.vendor_name}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(vendor.vendor_status)}`}>
                      {vendor.vendor_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-bold text-slate-800">{vendor.trust_score}/100</td>
                  <td className="px-6 py-4 text-center text-slate-600">{vendor.total_previous_invoices}</td>
                  <td className="px-6 py-4 text-right font-bold text-slate-800">
                    ${vendor.average_invoice_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-bold border ${getRiskLevelStyles(vendor.risk_level)}`}>
                      {vendor.risk_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <RouterLink 
                      to={`/vendors/${encodeURIComponent(vendor.vendor_name)}`}
                      className="inline-flex items-center space-x-1 bg-slate-100 text-slate-700 text-xs px-2.5 py-1.5 rounded hover:bg-emerald-600 hover:text-white transition-colors"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      <span>View Profile</span>
                    </RouterLink>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
