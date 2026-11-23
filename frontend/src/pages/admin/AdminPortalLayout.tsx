import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  ListFilter,
  Inbox,
  Clock,
  CheckCircle2,
  BarChart3,
  LogOut,
  Building2,
  Shield,
  Menu,
  X,
  User,
} from 'lucide-react';

export const AdminPortalLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navItems = [
    { name: 'Overview', to: '/admin', icon: LayoutDashboard, end: true },
    { name: 'All Requests', to: '/admin/all-requests', icon: ListFilter },
    { name: 'New / Unassigned', to: '/admin/unassigned', icon: Inbox },
    { name: 'In Progress', to: '/admin/in-progress', icon: Clock },
    { name: 'Resolved', to: '/admin/resolved', icon: CheckCircle2 },
    { name: 'Reports', to: '/admin/reports', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen flex bg-[#F5F7F2]">
      {/* Deep Forest Sidebar - Desktop */}
      <aside className="hidden lg:flex flex-col w-64 bg-[#172D28] text-white border-r border-[#203A32] shrink-0">
        {/* Brand Crest */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-[#203A32]">
          <div className="w-8 h-8 rounded-lg bg-[#203A32] border border-[#A8B9A3]/30 flex items-center justify-center">
            <Building2 className="w-4 h-4 text-[#DCE5D8]" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-white">FIPP 2.0</h1>
            <p className="text-[10px] text-[#A8B9A3] tracking-wide uppercase font-medium">Control Centre</p>
          </div>
        </div>

        {/* Navigation Sections */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-[#203A32] text-white font-semibold shadow-xs'
                      : 'text-[#A8B9A3] hover:text-white hover:bg-[#203A32]/50'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Administrator Profile Card */}
        <div className="p-4 border-t border-[#203A32] bg-[#101F1C]">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-[#203A32] text-[#DCE5D8] flex items-center justify-center text-xs font-bold border border-[#A8B9A3]/30">
              <Shield className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.name || 'Administrator'}</p>
              <p className="text-[10px] text-[#A8B9A3] truncate">{user?.title || 'Operations Lead'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium text-[#A8B9A3] hover:text-red-400 hover:bg-red-950/30 transition-colors border border-transparent hover:border-red-900/50"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="lg:hidden h-16 bg-[#172D28] text-white flex items-center justify-between px-4 border-b border-[#203A32]">
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
              className="p-1.5 rounded-md text-[#A8B9A3] hover:text-white"
            >
              {mobileSidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <span className="font-bold text-sm tracking-tight">FIPP Control Centre</span>
          </div>

          <button
            onClick={handleLogout}
            className="p-2 text-[#A8B9A3] hover:text-white"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </header>

        {/* Mobile Drawer */}
        {mobileSidebarOpen && (
          <div className="lg:hidden bg-[#172D28] text-white border-b border-[#203A32] px-4 py-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.to}
                  end={item.end}
                  onClick={() => setMobileSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium ${
                      isActive ? 'bg-[#203A32] text-white' : 'text-[#A8B9A3]'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </div>
        )}

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
