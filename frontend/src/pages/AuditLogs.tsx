import React, { useState } from 'react';
import { Search, Scroll } from 'lucide-react';
import { MOCK_AUDIT_LOGS } from '../services/mockData';

export const AuditLogs: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredLogs = MOCK_AUDIT_LOGS.filter((log) => {
    return (
      log.invoiceNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.userRole.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.recommendation.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.reason.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Search Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800 flex items-center space-x-2">
            <Scroll className="h-5 w-5 text-slate-500" />
            <span>Audit Trail Ledger</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">Read-only immutable record of all invoice investigation decisions</p>
        </div>
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by ID, role, recommendation, or reason..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-slate-50"
          />
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Invoice ID</th>
                <th className="px-6 py-4">Audited Agent</th>
                <th className="px-6 py-4">User Role</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Recommendation</th>
                <th className="px-6 py-4">Reason / Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs font-mono text-slate-700">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-400">
                    No matching audit trail logs found.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 text-slate-500">{log.timestamp}</td>
                    <td className="px-6 py-4 font-bold text-slate-800">{log.invoiceNumber}</td>
                    <td className="px-6 py-4">{log.agent}</td>
                    <td className="px-6 py-4 font-semibold">{log.userRole}</td>
                    <td className="px-6 py-4">
                      <span className="bg-emerald-50 text-emerald-800 border border-emerald-100 px-2 py-0.5 rounded font-bold uppercase text-[10px]">
                        {log.decision}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-bold text-slate-800">{log.recommendation}</td>
                    <td className="px-6 py-4 text-slate-600 font-sans max-w-xs truncate" title={log.reason}>
                      {log.reason}
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
