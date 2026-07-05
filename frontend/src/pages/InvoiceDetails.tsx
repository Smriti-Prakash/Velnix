import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle,
  UserCheck
} from 'lucide-react';
import { MOCK_INVOICES, MOCK_VENDORS } from '../services/mockData';

export const InvoiceDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const invoice = MOCK_INVOICES.find(i => i.id === id);

  if (!invoice) {
    return (
      <div className="text-center py-12">
        <p className="text-lg text-slate-500">Invoice not found.</p>
        <Link to="/invoices" className="text-emerald-600 hover:underline mt-4 inline-block">Back to Invoices</Link>
      </div>
    );
  }

  const vendor = MOCK_VENDORS.find(v => v.name === invoice.vendor_name);

  // States to control collapsible sections
  const [openSections, setOpenSections] = useState({
    invoiceInfo: true,
    vendorIntel: true,
    riskAssess: true,
    fraudIntel: true,
    finalRec: true,
  });

  const toggleSection = (section: keyof typeof openSections) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const getRiskColor = (score: number) => {
    if (score <= 30) return 'emerald';
    if (score <= 60) return 'amber';
    if (score <= 85) return 'orange';
    return 'rose';
  };

  const handleAction = (action: string) => {
    alert(`Action '${action}' triggered for Invoice ${invoice.invoice_number}`);
  };

  const getRiskBadgeStyles = (score: number) => {
    if (score <= 30) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (score <= 60) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (score <= 85) return 'bg-orange-50 text-orange-700 border-orange-200';
    return 'bg-rose-50 text-rose-700 border-rose-200';
  };

  const sectionHeader = (title: string, isOpen: boolean, onToggle: () => void, icon: React.ReactNode) => (
    <button 
      onClick={onToggle}
      className="w-full flex items-center justify-between px-6 py-4 bg-slate-50 hover:bg-slate-100 transition-colors border-b border-slate-200 select-none cursor-pointer"
    >
      <div className="flex items-center space-x-3">
        {icon}
        <span className="font-bold text-slate-700 text-sm tracking-wide uppercase">{title}</span>
      </div>
      {isOpen ? <ChevronUp className="h-5 w-5 text-slate-400" /> : <ChevronDown className="h-5 w-5 text-slate-400" />}
    </button>
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header card with quick actions */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <Link to="/invoices" className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-emerald-600 transition-colors">
            <ArrowLeft className="h-3 w-3 mr-1" />
            Back to Invoices
          </Link>
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-bold text-slate-800">Invoice {invoice.invoice_number}</h2>
            <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getRiskBadgeStyles(invoice.risk_score)}`}>
              Risk Score: {invoice.risk_score}/100
            </span>
          </div>
          <p className="text-xs text-slate-400">Assessed by Velnix AI Orchestrator</p>
        </div>

        <div className="flex space-x-3">
          <button 
            onClick={() => handleAction('investigate')}
            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-semibold hover:bg-slate-200 transition-colors border border-slate-200"
          >
            Send to Investigation
          </button>
          <button 
            onClick={() => handleAction('reject')}
            className="px-4 py-2 bg-rose-50 text-rose-700 rounded-lg text-sm font-semibold hover:bg-rose-100 transition-colors border border-rose-200"
          >
            Reject
          </button>
          <button 
            onClick={() => handleAction('approve')}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700 transition-colors shadow-md"
          >
            Approve Payment
          </button>
        </div>
      </div>

      {/* Main Collapsible Sections Wrapper */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-200">
        
        {/* SECTION 1: Invoice Information */}
        <div>
          {sectionHeader("1. Invoice Information", openSections.invoiceInfo, () => toggleSection('invoiceInfo'), <FileText className="h-5 w-5 text-slate-500" />)}
          {openSections.invoiceInfo && (
            <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Invoice ID</p>
                <p className="font-mono mt-1 text-slate-800 font-semibold">{invoice.invoice_number}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Vendor</p>
                <p className="mt-1 text-slate-800 font-semibold">{invoice.vendor_name}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Amount</p>
                <p className="mt-1 font-bold text-slate-800">
                  {invoice.currency}{invoice.invoice_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">PO Reference</p>
                <p className="mt-1 text-slate-800 font-semibold">{invoice.purchase_order_number || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Order ID</p>
                <p className="mt-1 text-slate-800 font-semibold">{invoice.order_id || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Invoice Date</p>
                <p className="mt-1 text-slate-800">{invoice.invoice_date}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Due Date</p>
                <p className="mt-1 text-slate-800">{invoice.due_date || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Payment Terms</p>
                <p className="mt-1 text-slate-800">{invoice.payment_terms || 'N/A'}</p>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 2: Vendor Intelligence */}
        <div>
          {sectionHeader("2. Vendor Intelligence", openSections.vendorIntel, () => toggleSection('vendorIntel'), <UserCheck className="h-5 w-5 text-slate-500" />)}
          {openSections.vendorIntel && vendor && (
            <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Vendor Status</p>
                <span className={`inline-block mt-1 text-xs font-bold px-2 py-0.5 rounded border ${
                  vendor.status === 'Trusted' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                  vendor.status === 'Watchlist' ? 'bg-rose-50 text-rose-700 border-rose-200' :
                  'bg-slate-50 text-slate-700 border-slate-200'
                }`}>
                  {vendor.status}
                </span>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Trust Score</p>
                <p className="mt-1 text-slate-800 font-bold text-lg">{vendor.trustScore}/100</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Previous Invoices</p>
                <p className="mt-1 text-slate-800 font-semibold">{vendor.previousInvoicesCount}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Average Amount</p>
                <p className="mt-1 text-slate-800 font-semibold">
                  {invoice.currency}{vendor.averageInvoiceAmount.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Previous Rejections</p>
                <p className="mt-1 text-slate-800">{vendor.previousRejections}</p>
              </div>
              <div className="col-span-2">
                <p className="text-xs font-semibold text-slate-400 uppercase">Last Bank Details Change</p>
                <p className="mt-1 text-slate-800">{vendor.lastBankAccountChange}</p>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 3: Risk Assessment */}
        <div>
          {sectionHeader("3. Risk Assessment", openSections.riskAssess, () => toggleSection('riskAssess'), <AlertTriangle className="h-5 w-5 text-slate-500" />)}
          {openSections.riskAssess && (
            <div className="p-6 space-y-6 text-sm">
              <div className="flex items-center space-x-6">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase">Calculated Risk Score</p>
                  <span className={`inline-block mt-2 text-xl font-extrabold px-3 py-1 rounded border bg-${getRiskColor(invoice.risk_score)}-50 text-${getRiskColor(invoice.risk_score)}-700 border-${getRiskColor(invoice.risk_score)}-200`}>
                    {invoice.risk_score}/100
                  </span>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase">Risk Evaluation</p>
                  <p className="text-sm font-semibold text-slate-800 mt-2">
                    {invoice.risk_score <= 35 ? 'Low Risk: Regular trusted transaction' :
                     invoice.risk_score <= 70 ? 'Moderate Risk: Review details/exceptions' :
                     'High Risk: Significant deviations detected'}
                  </p>
                </div>
              </div>
              <div className="border-t border-slate-100 pt-4">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide">Key Findings:</h4>
                <ul className="mt-2 space-y-1.5 list-disc list-inside text-slate-700">
                  {invoice.risk_findings && invoice.risk_findings.length > 0 ? (
                    invoice.risk_findings.map((finding, idx) => (
                      <li key={idx} className="text-rose-700">{finding}</li>
                    ))
                  ) : (
                    <li className="text-emerald-700">No anomalies detected. Invoice falls within the typical billing range.</li>
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 4: Fraud Intelligence */}
        <div>
          {sectionHeader("4. Fraud Intelligence", openSections.fraudIntel, () => toggleSection('fraudIntel'), <ShieldAlert className="h-5 w-5 text-slate-500" />)}
          {openSections.fraudIntel && (
            <div className="p-6 space-y-6 text-sm">
              <div className="flex items-center space-x-6">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase">Calculated Fraud Score</p>
                  <span className={`inline-block mt-2 text-xl font-extrabold px-3 py-1 rounded border bg-${getRiskColor(invoice.fraud_score)}-50 text-${getRiskColor(invoice.fraud_score)}-700 border-${getRiskColor(invoice.fraud_score)}-200`}>
                    {invoice.fraud_score}/100
                  </span>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase">Fraud Indicators</p>
                  <p className="text-sm font-semibold text-slate-800 mt-2">
                    {invoice.fraud_score > 50 ? 'WARNING: High indicators of duplicate billing or layout mismatch' : 'No fraud alerts detected'}
                  </p>
                </div>
              </div>
              {invoice.fraud_findings && invoice.fraud_findings.length > 0 && (
                <div className="border-t border-slate-100 pt-4">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide">Fraud Flags:</h4>
                  <ul className="mt-2 space-y-1.5 list-disc list-inside text-slate-700">
                    {invoice.fraud_findings.map((flag, idx) => (
                      <li key={idx} className="text-rose-700">{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* SECTION 5: Final Recommendation */}
        <div>
          {sectionHeader("5. Final Recommendation", openSections.finalRec, () => toggleSection('finalRec'), <CheckCircle2 className="h-5 w-5 text-slate-500" />)}
          {openSections.finalRec && (
            <div className="p-6 space-y-4 text-sm bg-slate-50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase">Platform Recommendation</p>
                  <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-bold ${
                    invoice.recommendation === 'APPROVE' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                    invoice.recommendation === 'REVIEW' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                    'bg-rose-100 text-rose-800 border border-rose-200'
                  }`}>
                    {invoice.recommendation}
                  </span>
                </div>
              </div>
              <p className="text-slate-700 leading-relaxed bg-white p-4 rounded-lg border border-slate-200 font-medium">
                {invoice.final_reasoning || (invoice.recommendation === 'APPROVE' 
                  ? "Based on automated analysis, this invoice matches all transaction metadata, aligns with historical vendor averages, and contains zero duplicate or fraud indicators. Approved for immediate disbursement."
                  : "Caution recommended: The invoice deviates significantly from historical limits and contains exceptions. We recommend manual manager review before final AP approval.")}
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
