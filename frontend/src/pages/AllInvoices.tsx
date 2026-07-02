import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, ArrowUpDown, Eye } from 'lucide-react';
import { MOCK_INVOICES, type Invoice } from '../services/mockData';

export const AllInvoices: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [sortField, setSortField] = useState<keyof Invoice>('date');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (field: keyof Invoice) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const filteredInvoices = MOCK_INVOICES.filter((invoice) => {
    const matchesSearch = 
      invoice.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.vendorName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (invoice.purchaseOrderNumber && invoice.purchaseOrderNumber.toLowerCase().includes(searchTerm.toLowerCase()));
      
    const matchesFilter = statusFilter === 'All' || invoice.status === statusFilter;
    
    return matchesSearch && matchesFilter;
  });

  const sortedInvoices = [...filteredInvoices].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];

    if (aVal === undefined) return 1;
    if (bVal === undefined) return -1;

    if (typeof aVal === 'string') {
      return sortAsc 
        ? (aVal as string).localeCompare(bVal as string) 
        : (bVal as string).localeCompare(aVal as string);
    } else {
      return sortAsc 
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    }
  });

  const getStatusBadgeStyles = (status: string) => {
    switch (status) {
      case 'Approved':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Pending':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Review':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'Investigate':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'Rejected':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const getRiskBadgeStyles = (score: number) => {
    if (score <= 30) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (score <= 60) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (score <= 85) return 'bg-orange-50 text-orange-700 border-orange-200';
    return 'bg-rose-50 text-rose-700 border-rose-200';
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Search and Filters Controls */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Invoice ID, Vendor, or PO..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-slate-50"
          />
        </div>

        {/* Filter */}
        <div className="flex items-center space-x-3">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-200 rounded-lg text-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
          >
            <option value="All">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Approved">Approved</option>
            <option value="Rejected">Rejected</option>
            <option value="Review">Review</option>
            <option value="Investigate">Investigate</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider select-none">
                <th className="px-6 py-4 cursor-pointer" onClick={() => handleSort('id')}>
                  <div className="flex items-center space-x-1">
                    <span>Invoice ID</span>
                    <ArrowUpDown className="h-3.5 w-3.5" />
                  </div>
                </th>
                <th className="px-6 py-4 cursor-pointer" onClick={() => handleSort('vendorName')}>
                  <div className="flex items-center space-x-1">
                    <span>Vendor</span>
                    <ArrowUpDown className="h-3.5 w-3.5" />
                  </div>
                </th>
                <th className="px-6 py-4 cursor-pointer" onClick={() => handleSort('date')}>
                  <div className="flex items-center space-x-1">
                    <span>Invoice Date</span>
                    <ArrowUpDown className="h-3.5 w-3.5" />
                  </div>
                </th>
                <th className="px-6 py-4 text-right cursor-pointer" onClick={() => handleSort('amount')}>
                  <div className="flex items-center justify-end space-x-1">
                    <span>Amount</span>
                    <ArrowUpDown className="h-3.5 w-3.5" />
                  </div>
                </th>
                <th className="px-6 py-4 text-center cursor-pointer" onClick={() => handleSort('riskScore')}>
                  <div className="flex items-center justify-center space-x-1">
                    <span>Risk Score</span>
                    <ArrowUpDown className="h-3.5 w-3.5" />
                  </div>
                </th>
                <th className="px-6 py-4 text-center cursor-pointer" onClick={() => handleSort('fraudScore')}>
                  <div className="flex items-center justify-center space-x-1">
                    <span>Fraud Score</span>
                    <ArrowUpDown className="h-3.5 w-3.5" />
                  </div>
                </th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {sortedInvoices.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-slate-400">
                    No matching invoices found.
                  </td>
                </tr>
              ) : (
                sortedInvoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-800">
                      <Link to={`/invoices/${invoice.id}`} className="hover:underline hover:text-emerald-600">
                        {invoice.id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{invoice.vendorName}</td>
                    <td className="px-6 py-4 text-slate-500">{invoice.invoiceDate}</td>
                    <td className="px-6 py-4 text-right font-bold text-slate-800">
                      {invoice.currency}{invoice.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-bold border ${getRiskBadgeStyles(invoice.riskScore)}`}>
                        {invoice.riskScore}/100
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-bold border ${getRiskBadgeStyles(invoice.fraudScore)}`}>
                        {invoice.fraudScore}/100
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeStyles(invoice.status)}`}>
                        {invoice.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Link 
                        to={`/invoices/${invoice.id}`}
                        className="inline-flex items-center space-x-1 bg-slate-100 text-slate-700 text-xs px-2.5 py-1.5 rounded hover:bg-emerald-600 hover:text-white transition-colors"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>View</span>
                      </Link>
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
