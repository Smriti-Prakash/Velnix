import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, UserCheck, Inbox, ShieldAlert, Award, FileText } from 'lucide-react';
import { MOCK_VENDORS, MOCK_INVOICES } from '../services/mockData';

export const VendorDetails: React.FC = () => {
  const { name } = useParams<{ name: string }>();
  const vendorName = decodeURIComponent(name || '');
  const vendor = MOCK_VENDORS.find(v => v.name === vendorName);

  if (!vendor) {
    return (
      <div className="text-center py-12">
        <p className="text-lg text-slate-500">Vendor not found.</p>
        <Link to="/vendors" className="text-emerald-600 hover:underline mt-4 inline-block">Back to Vendors</Link>
      </div>
    );
  }

  // Filter invoices for this vendor
  const vendorInvoices = MOCK_INVOICES.filter(i => i.vendorName === vendor.name);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Trusted': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'Watchlist': return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'New': return 'bg-slate-100 text-slate-800 border-slate-200';
      default: return 'bg-slate-50 text-slate-700';
    }
  };

  const getRiskColor = (score: number) => {
    if (score <= 30) return 'emerald';
    if (score <= 60) return 'amber';
    if (score <= 85) return 'orange';
    return 'rose';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Back button */}
      <div>
        <Link to="/vendors" className="flex items-center space-x-2 text-sm text-slate-500 hover:text-slate-800 transition-colors">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Vendors</span>
        </Link>
      </div>

      {/* Vendor Profile Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-slate-900 text-emerald-500 rounded-xl">
            <UserCheck className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-800">{vendor.name}</h2>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(vendor.status)}`}>
                {vendor.status}
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-slate-500 text-xs font-semibold">Master DB Registry</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          <div className="text-center md:text-right">
            <p className="text-xs font-semibold text-slate-400 uppercase">Trust Score</p>
            <p className="text-3xl font-extrabold text-slate-800 mt-1">{vendor.trustScore}/100</p>
          </div>
        </div>
      </div>

      {/* Detail statistics cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase">Previous Invoices</p>
          <p className="text-2xl font-bold text-slate-800 mt-2">{vendor.previousInvoicesCount}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase">Average Billing</p>
          <p className="text-2xl font-bold text-slate-800 mt-2">${vendor.averageInvoiceAmount.toLocaleString()}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase">Previous Rejections</p>
          <p className="text-2xl font-bold text-slate-800 mt-2 text-rose-700">{vendor.previousRejections}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm col-span-2 md:col-span-1">
          <p className="text-xs font-semibold text-slate-400 uppercase">Bank Changes</p>
          <p className="text-sm font-semibold text-slate-700 mt-3 truncate">{vendor.lastBankAccountChange}</p>
        </div>
      </div>

      {/* Invoice Billing History Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <h3 className="text-md font-bold text-slate-800">Invoice History</h3>
          <p className="text-xs text-slate-500 mt-1">Transaction entries matching this vendor</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-4">Invoice ID</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-right">Amount</th>
                <th className="px-6 py-4 text-center">Risk Score</th>
                <th className="px-6 py-4 text-center">Fraud Score</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {vendorInvoices.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400">
                    No transactions matching this vendor found.
                  </td>
                </tr>
              ) : (
                vendorInvoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-800">
                      <Link to={`/invoices/${invoice.id}`} className="hover:underline hover:text-emerald-600">
                        {invoice.id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-slate-500">{invoice.invoiceDate}</td>
                    <td className="px-6 py-4 text-right font-bold text-slate-800">
                      {invoice.currency}{invoice.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-bold border bg-${getRiskColor(invoice.riskScore)}-50 text-${getRiskColor(invoice.riskScore)}-700 border-${getRiskColor(invoice.riskScore)}-200`}>
                        {invoice.riskScore}/100
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-bold border bg-${getRiskColor(invoice.fraudScore)}-50 text-${getRiskColor(invoice.fraudScore)}-700 border-${getRiskColor(invoice.fraudScore)}-200`}>
                        {invoice.fraudScore}/100
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded-full border ${
                        invoice.status === 'Approved' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                        invoice.status === 'Pending' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                        'bg-slate-50 text-slate-700 border-slate-200'
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
    </div>
  );
};
