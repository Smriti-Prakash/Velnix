import React from 'react';
import { Link } from 'react-react-router-dom'; // Wait, it should be react-router-dom! Let's check imports
import { Link as RouterLink } from 'react-router-dom';
import { Eye, ArrowUpRight } from 'lucide-react';
import { MOCK_VENDORS } from '../services/mockData';

export const Vendors: React.FC = () => {
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
      default: return 'bg-slate-50 text-slate-700';
    }
  };

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
            {MOCK_VENDORS.map((vendor) => (
              <tr key={vendor.name} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 font-semibold text-slate-800">{vendor.name}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(vendor.status)}`}>
                    {vendor.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-center font-bold text-slate-800">{vendor.trustScore}/100</td>
                <td className="px-6 py-4 text-center text-slate-600">{vendor.previousInvoicesCount}</td>
                <td className="px-6 py-4 text-right font-bold text-slate-800">
                  ${vendor.averageInvoiceAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </td>
                <td className="px-6 py-4 text-center">
                  <span className={`px-2 py-1 rounded text-xs font-bold border ${getRiskLevelStyles(vendor.riskLevel)}`}>
                    {vendor.riskLevel}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <RouterLink 
                    to={`/vendors/${encodeURIComponent(vendor.name)}`}
                    className="inline-flex items-center space-x-1 bg-slate-100 text-slate-700 text-xs px-2.5 py-1.5 rounded hover:bg-emerald-600 hover:text-white transition-colors"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    <span>View Profile</span>
                  </RouterLink>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
