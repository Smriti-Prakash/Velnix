import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { 
  Home, 
  Inbox, 
  FileText, 
  Users, 
  BarChart3, 
  Scroll, 
  Settings, 
  Upload,
  ShieldCheck,
  ToggleLeft,
  ToggleRight,
  ShoppingCart,
  Package
} from 'lucide-react';
import { useDevMode } from '../../context/DevModeContext';

export const Layout: React.FC = () => {
  const location = useLocation();
  const { isMockMode, setIsMockMode } = useDevMode();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Approval Queue', href: '/queue', icon: Inbox },
    { name: 'All Invoices', href: '/invoices', icon: FileText },
    { name: 'Upload Invoice', href: '/upload', icon: Upload },
    { name: 'Vendors', href: '/vendors', icon: Users },
    { name: 'Purchase Orders', href: '/purchase-orders', icon: ShoppingCart },
    { name: 'Goods Receipts', href: '/goods-receipts', icon: Package },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Audit Logs', href: '/audit', icon: Scroll },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];


  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      {/* Persistent Left Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col justify-between border-r border-slate-800">
        <div>
          {/* Logo Brand area */}
          <div className="h-16 flex items-center px-6 bg-slate-950 border-b border-slate-800 space-x-2">
            <ShieldCheck className="h-7 w-7 text-emerald-500" />
            <span className="text-xl font-bold text-white tracking-wider">VELNIX</span>
          </div>

          {/* Navigation Links */}
          <nav className="mt-6 px-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                              (item.href !== '/' && location.pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    isActive 
                      ? 'bg-emerald-600 text-white shadow-md' 
                      : 'hover:bg-slate-800 hover:text-white text-slate-400'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Identity Info at Bottom */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 uppercase font-semibold">User Role</p>
            <p className="text-sm font-medium text-white">Finance Analyst</p>
          </div>
          <div className="h-8 w-8 rounded-full bg-emerald-500 flex items-center justify-center text-slate-950 font-bold text-xs">
            FA
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Global Top Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shadow-sm z-10">
          <div>
            <h1 className="text-lg font-semibold text-slate-800">
              {navigation.find(n => location.pathname === n.href || (n.href !== '/' && location.pathname.startsWith(n.href)))?.name || 'Velnix Platform'}
            </h1>
          </div>

          {/* Developer Mode Switcher */}
          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Developer Mode:
            </span>
            <button 
              onClick={() => setIsMockMode(!isMockMode)}
              className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded-md py-1 px-2"
            >
              {isMockMode ? (
                <div className="flex items-center space-x-2 bg-amber-50 border border-amber-200 text-amber-800 px-3 py-1 rounded-full text-xs font-medium">
                  <span>Mock Data</span>
                  <ToggleRight className="h-5 w-5 text-amber-600" />
                </div>
              ) : (
                <div className="flex items-center space-x-2 bg-emerald-50 border border-emerald-200 text-emerald-800 px-3 py-1 rounded-full text-xs font-medium">
                  <span>Live Backend</span>
                  <ToggleLeft className="h-5 w-5 text-emerald-600" />
                </div>
              )}
            </button>
          </div>
        </header>

        {/* Content Outlet */}
        <main className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
