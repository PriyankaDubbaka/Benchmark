import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Key, Brain, FileText, Play, BarChart3, Menu } from 'lucide-react';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [expanded, setExpanded] = useState(true);

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/api-keys', icon: Key, label: 'API Keys' },
    { to: '/models', icon: Brain, label: 'Models' },
    { to: '/documents', icon: FileText, label: 'Documents' },
    { to: '/benchmark', icon: Play, label: 'Run Benchmark' },
    { to: '/results', icon: BarChart3, label: 'Results' },
  ];

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className={`bg-slate-900 text-slate-300 transition-all duration-300 ${expanded ? 'w-64' : 'w-16'} flex flex-col`}>
        <div className="h-16 flex items-center justify-between px-4 bg-slate-950">
          {expanded && <span className="font-bold text-white text-lg whitespace-nowrap overflow-hidden">BAM Bench</span>}
          <button onClick={() => setExpanded(!expanded)} className="p-1 hover:bg-slate-800 rounded">
            <Menu size={20} />
          </button>
        </div>
        <nav className="flex-1 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 hover:bg-slate-800 hover:text-white transition-colors ${
                  isActive ? 'bg-blue-600 text-white hover:bg-blue-700' : ''
                }`
              }
            >
              <item.icon size={20} className="flex-shrink-0" />
              {expanded && <span className="ml-4 font-medium whitespace-nowrap">{item.label}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 justify-between shrink-0">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-slate-800">BAM VLM Benchmark</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              PW2
            </span>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
