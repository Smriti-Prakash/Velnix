import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, CheckCircle2, ShieldAlert, Search, RotateCcw } from 'lucide-react';
import { MOCK_INVOICES } from '../services/mockData';

export const ApprovalQueue: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('All');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [riskFilter, setRiskFilter] = useState<string>('All');
  const [timePeriod, setTimePeriod] = useState<string>('All');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');

  // Priority ranking for sorting: High (3), Medium (2), Low (1)
  const getPriorityWeight = (priority: string) => {
    switch (priority) {
      case 'High': return 3;
      case 'Medium': return 2;
      case 'Low': return 1;
      default: return 0;
    }
  };

  const matchesStatus = (status: string, rec: string, filter: string) => {
    if (filter === 'All') return true;
    if (filter === 'Pending Approval') return status === 'Pending';
    if (filter === 'Needs Review') return status === 'Review' || status === 'Investigate' || rec === 'REVIEW';
    if (filter === 'Approved') return status === 'Approved';
    if (filter === 'Rejected') return status === 'Rejected';
    return true;
  };

  const matchesRisk = (score: number, filter: string) => {
    if (filter === 'All') return true;
    if (filter === 'Low') return score <= 30;
    if (filter === 'Medium') return score > 30 && score <= 60;
    if (filter === 'High') return score > 60 && score <= 85;
    if (filter === 'Critical') return score > 85;
    return true;
  };

  const isWithinPeriod = (dateStr: string, period: string, from: string, to: string): boolean => {
    if (period === 'All') return true;
    
    const invDate = new Date(dateStr);
    const today = new Date('2026-07-02'); // Fixed mock context date
    
    if (isNaN(invDate.getTime())) return false;
    
    const diffTime = today.getTime() - invDate.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    switch (period) {
      case 'Today':
        return dateStr === '2026-07-02';
      case 'Last 7 Days':
        return diffDays >= 0 && diffDays <= 7;
      case 'Last 30 Days':
        return diffDays >= 0 && diffDays <= 30;
      case 'Last 90 Days':
        return diffDays >= 0 && diffDays <= 90;
      case 'This Month':
        return invDate.getFullYear() === 2026 && invDate.getMonth() === 6; // July (6)
      case 'Last Month':
        return invDate.getFullYear() === 2026 && invDate.getMonth() === 5; // June (5)
      case 'This Year':
        return invDate.getFullYear() === 2026;
      case 'Custom Range':
        const fromD = from ? new Date(from) : null;
        const toD = to ? new Date(to) : null;
        if (fromD && invDate < fromD) return false;
        if (toD && invDate > toD) return false;
        return true;
      default:
        return true;
    }
  };

  // Reset all filters
  const resetFilters = () => {
    setSearchTerm('');
    setPriorityFilter('All');
    setStatusFilter('All');
    setRiskFilter('All');
    setTimePeriod('All');
    setFromDate('');
    setToDate('');
  };

  // Filter list of all invoices based on user's selected filters
  const filteredInvoices = MOCK_INVOICES.filter((invoice) => {
    const matchesSearch = 
      invoice.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.vendor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (invoice.purchase_order_number && invoice.purchase_order_number.toLowerCase().includes(searchTerm.toLowerCase()));
      
    const matchesPrio = priorityFilter === 'All' || invoice.priority === priorityFilter;
    const matchesStat = matchesStatus(invoice.status, invoice.recommendation, statusFilter);
    const matchesRsk = matchesRisk(invoice.risk_score, riskFilter);
    const matchesTime = isWithinPeriod(invoice.invoice_date, timePeriod, fromDate, toDate);

    return matchesSearch && matchesPrio && matchesStat && matchesRsk && matchesTime;
  });

  // Sort by priority weight descending
  const sortedInvoices = [...filteredInvoices].sort(
    (a, b) => getPriorityWeight(b.priority) - getPriorityWeight(a.priority)
  );

  const getRiskBadgeStyles = (score: number) => {
    if (score <= 30) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (score <= 60) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (score <= 85) return 'bg-orange-50 text-orange-700 border-orange-200';
    return 'bg-rose-50 text-rose-700 border-rose-200';
  };

  const getPriorityBadgeStyles = (priority: string) => {
    switch (priority) {
      case 'High': return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'Medium': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'Low': return 'bg-slate-100 text-slate-800 border-slate-200';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  const handleApprove = (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    alert(`Invoice ${id} approved successfully!`);
  };

  const handleInvestigate = (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    alert(`Invoice ${id} sent for formal investigation.`);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden animate-fadeIn">
      {/* Title Header Card */}
      <div className="p-6 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Action Required Queue</h2>
          <p className="text-xs text-slate-500 mt-1">Invoices awaiting review, filterable by priority, risk level, status and date periods</p>
        </div>
        <span className="bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full border border-amber-200">
          {MOCK_INVOICES.filter(i => i.status === 'Pending' || i.status === 'Review' || i.status === 'Investigate').length} Items Total Queue
        </span>
      </div>

      {/* Dynamic Filter Controls Bar */}
      <div className="bg-slate-50 p-6 border-b border-slate-200 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
          
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search ID, Vendor, PO..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 border border-slate-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500 bg-white text-slate-700 font-medium placeholder-slate-400"
            />
          </div>

          {/* Priority Select */}
          <div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full border border-slate-200 rounded px-2.5 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500 text-xs text-slate-700 font-medium"
            >
              <option value="All">All Priorities</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          {/* Status Select */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full border border-slate-200 rounded px-2.5 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500 text-xs text-slate-700 font-medium"
            >
              <option value="All">All Statuses</option>
              <option value="Pending Approval">Pending Approval</option>
              <option value="Needs Review">Needs Review</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
            </select>
          </div>

          {/* Risk Level Select */}
          <div>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="w-full border border-slate-200 rounded px-2.5 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500 text-xs text-slate-700 font-medium"
            >
              <option value="All">All Risk Levels</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>

          {/* Time Period Select */}
          <div>
            <select
              value={timePeriod}
              onChange={(e) => setTimePeriod(e.target.value)}
              className="w-full border border-slate-200 rounded px-2.5 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500 text-xs text-slate-700 font-medium"
            >
              <option value="All">All Time Periods</option>
              <option value="Today">Today</option>
              <option value="Last 7 Days">Last 7 Days</option>
              <option value="Last 30 Days">Last 30 Days</option>
              <option value="Last 90 Days">Last 90 Days</option>
              <option value="This Month">This Month</option>
              <option value="Last Month">Last Month</option>
              <option value="This Year">This Year</option>
              <option value="Custom Range">Custom Range...</option>
            </select>
          </div>

        </div>

        {/* Custom Range Date Pickers (Conditional) */}
        {timePeriod === 'Custom Range' && (
          <div className="flex items-center space-x-4 p-3 bg-white rounded border border-slate-200 animate-slideDown">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500 font-semibold">From:</span>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="border border-slate-200 rounded px-2.5 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500 text-xs font-semibold text-slate-700"
              />
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500 font-semibold">To:</span>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="border border-slate-200 rounded px-2.5 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500 text-xs font-semibold text-slate-700"
              />
            </div>
          </div>
        )}

        {/* Reset Filters & Count summary */}
        <div className="flex items-center justify-between border-t border-slate-200/60 pt-3">
          <span className="text-xs text-slate-400">
            Showing {sortedInvoices.length} of {MOCK_INVOICES.length} total entries
          </span>
          <button
            onClick={resetFilters}
            className="flex items-center space-x-1.5 text-xs text-rose-600 hover:text-rose-800 transition-colors font-semibold"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset Filters</span>
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th className="px-6 py-4">Priority</th>
              <th className="px-6 py-4">Invoice ID</th>
              <th className="px-6 py-4">Vendor</th>
              <th className="px-6 py-4">Date</th>
              <th className="px-6 py-4 text-right">Amount</th>
              <th className="px-6 py-4 text-center">Risk Score</th>
              <th className="px-6 py-4 text-center">Fraud Score</th>
              <th className="px-6 py-4">AP Recommendation</th>
              <th className="px-6 py-4 text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {sortedInvoices.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-8 text-slate-400">
                  No invoices pending approval in the queue.
                </td>
              </tr>
            ) : (
              sortedInvoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${getPriorityBadgeStyles(invoice.priority)}`}>
                      {invoice.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono font-medium text-slate-800">
                    <Link to={`/invoices/${invoice.id}`} className="hover:underline hover:text-emerald-600">
                      {invoice.id}
                    </Link>
                  </td>
                  <td className="px-6 py-4 font-semibold text-slate-800">{invoice.vendor_name}</td>
                  <td className="px-6 py-4 text-slate-500">{invoice.invoice_date}</td>
                  <td className="px-6 py-4 text-right font-bold text-slate-800">
                    {invoice.currency}{(invoice.invoice_amount ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-bold border ${getRiskBadgeStyles(invoice.risk_score)}`}>
                      {invoice.risk_score}/100
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-bold border ${getRiskBadgeStyles(invoice.fraud_score)}`}>
                      {invoice.fraud_score}/100
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                      invoice.recommendation === 'APPROVE' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                      invoice.recommendation === 'REVIEW' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                      'bg-rose-100 text-rose-800 border border-rose-200'
                    }`}>
                      {invoice.recommendation}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center space-x-2">
                      <Link 
                        to={`/invoices/${invoice.id}`}
                        title="View Details"
                        className="p-1.5 hover:bg-slate-100 rounded text-slate-500 hover:text-slate-800 transition-colors"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                      <button 
                        onClick={(e) => handleApprove(invoice.id, e)}
                        title="Approve"
                        className="p-1.5 hover:bg-emerald-50 rounded text-slate-500 hover:text-emerald-700 transition-colors"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                      </button>
                      <button 
                        onClick={(e) => handleInvestigate(invoice.id, e)}
                        title="Investigate"
                        className="p-1.5 hover:bg-rose-50 rounded text-slate-500 hover:text-rose-700 transition-colors"
                      >
                        <ShieldAlert className="h-4 w-4" />
                      </button>
                    </div>
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
