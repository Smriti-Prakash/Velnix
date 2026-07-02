import React from 'react';
import { MOCK_INVOICES, MOCK_VENDORS } from '../services/mockData';

export const Analytics: React.FC = () => {
  const totalInvoices = MOCK_INVOICES.length;
  const approvedInvoices = MOCK_INVOICES.filter(i => i.status === 'Approved').length;
  const approvalRate = totalInvoices > 0 ? Math.round((approvedInvoices / totalInvoices) * 100) : 0;
  
  const alertsCount = MOCK_INVOICES.filter(i => i.recommendation === 'INVESTIGATE').length;
  const detectionRate = totalInvoices > 0 ? Math.round((alertsCount / totalInvoices) * 100) : 0;

  // Group risk scores: 0-30 (Low), 31-60 (Med), 61-85 (High), 86-100 (Critical)
  const lowRiskCount = MOCK_INVOICES.filter(i => i.riskScore <= 30).length;
  const medRiskCount = MOCK_INVOICES.filter(i => i.riskScore > 30 && i.riskScore <= 60).length;
  const highRiskCount = MOCK_INVOICES.filter(i => i.riskScore > 60 && i.riskScore <= 85).length;
  const critRiskCount = MOCK_INVOICES.filter(i => i.riskScore > 85).length;

  const riskDistribution = [
    { label: 'Low Risk (0-30)', count: lowRiskCount, color: 'bg-emerald-500' },
    { label: 'Medium Risk (31-60)', count: medRiskCount, color: 'bg-amber-500' },
    { label: 'High Risk (61-85)', count: highRiskCount, color: 'bg-orange-500' },
    { label: 'Critical Risk (86-100)', count: critRiskCount, color: 'bg-rose-500' },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase">Total Invoice Volume</p>
          <p className="text-3xl font-extrabold text-slate-800 mt-2">{totalInvoices}</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase">Auto-Approval Rate</p>
          <p className="text-3xl font-extrabold text-slate-800 mt-2">{approvalRate}%</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase">Fraud Detection Rate</p>
          <p className="text-3xl font-extrabold text-slate-800 mt-2 text-rose-600">{detectionRate}%</p>
        </div>
      </div>

      {/* Visual Analytics Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Risk Distribution Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <h3 className="text-md font-bold text-slate-800">Risk Score Distribution</h3>
          <div className="space-y-4">
            {riskDistribution.map((item) => {
              const percentage = totalInvoices > 0 ? Math.round((item.count / totalInvoices) * 100) : 0;
              return (
                <div key={item.label} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600">
                    <span>{item.label}</span>
                    <span>{item.count} ({percentage}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                    <div 
                      className={`${item.color} h-full transition-all`} 
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Risk Vendors */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <h3 className="text-md font-bold text-slate-800">Top High Risk Vendors</h3>
          <div className="divide-y divide-slate-100">
            {MOCK_VENDORS.filter(v => v.trustScore < 80).map((vendor) => (
              <div key={vendor.name} className="py-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">{vendor.name}</p>
                  <p className="text-xs text-slate-400">{vendor.previousInvoicesCount} invoices billing history</p>
                </div>
                <span className="bg-rose-50 text-rose-700 text-xs font-bold px-2.5 py-1 rounded border border-rose-200">
                  Trust Score: {vendor.trustScore}/100
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
