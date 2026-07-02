import React from 'react';
import { Link } from 'react-router-dom';
import { Eye, CheckCircle2, ShieldAlert } from 'lucide-react';
import { MOCK_INVOICES, Invoice } from '../services/mockData';

export const ApprovalQueue: React.FC = () => {
  // Filters for invoices requiring action (Pending, Review, Investigate)
  const queueInvoices = MOCK_INVOICES.filter(
    invoice => invoice.status === 'Pending' || invoice.status === 'Review' || invoice.status === 'Investigate'
  );

  // Priority ranking for sorting: High (3), Medium (2), Low (1)
  const getPriorityWeight = (priority: string) => {
    switch (priority) {
      case 'High': return 3;
      case 'Medium': return 2;
      case 'Low': return 1;
      default: return 0;
    }
  };

  // Sort by priority weight descending
  const sortedInvoices = [...queueInvoices].sort(
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
      <div className="p-6 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-800">Action Required Queue</h2>
          <p className="text-xs text-slate-500 mt-1">Invoices awaiting analysis review or analyst action, ordered by priority</p>
        </div>
        <span className="bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full border border-amber-200">
          {sortedInvoices.length} Items Awaiting Review
        </span>
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
