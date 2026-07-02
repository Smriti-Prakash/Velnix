import React from 'react';
import { Settings as SettingsIcon, ShieldCheck, Bell, Users, Building } from 'lucide-react';

export const Settings: React.FC = () => {
  const sections = [
    { title: "Organization Settings", desc: "Manage corporate entities, master databases, and general ledger routing rules.", icon: Building },
    { title: "Risk Thresholds", desc: "Define threshold metrics for auto-approval limits, duplicate warnings, and risk score weights.", icon: ShieldCheck },
    { title: "Notification Preferences", desc: "Configure Slack alerts, email digests, and critical fraud indicators alerts.", icon: Bell },
    { title: "User Roles & Permissions", desc: "Manage role-based access controls (RBAC) and security analyst roles.", icon: Users },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fadeIn">
      {sections.map((sec) => {
        const Icon = sec.icon;
        return (
          <div key={sec.title} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-start space-x-4">
            <div className="p-3 bg-slate-100 rounded-lg text-slate-600 mt-1">
              <Icon className="h-6 w-6" />
            </div>
            <div className="flex-1 space-y-1">
              <h3 className="text-md font-bold text-slate-800">{sec.title}</h3>
              <p className="text-sm text-slate-500">{sec.desc}</p>
              <div className="pt-3">
                <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
                  Configuration Placeholder
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
