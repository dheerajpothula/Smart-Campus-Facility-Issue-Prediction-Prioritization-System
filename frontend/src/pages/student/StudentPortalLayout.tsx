import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Building2, PlusCircle, History, LogOut, User, MapPin } from 'lucide-react';

export const StudentPortalLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F7F2]">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-white border-b border-[#DCE5D8]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            {/* Branding */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#203A32] flex items-center justify-center text-white">
                <Building2 className="w-4 h-4 text-[#DCE5D8]" />
              </div>
              <div>
                <span className="font-bold text-sm tracking-tight text-[#172D28]">FIPP 2.0</span>
                <span className="text-xs text-[#52605B] block sm:inline sm:ml-2 sm:pl-2 sm:border-l sm:border-[#DCE5D8]">
                  Student Grievance Portal
                </span>
              </div>
            </div>

            {/* Student Identity Badge & Logout */}
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2.5 text-right">
                <div className="w-8 h-8 rounded-full bg-[#DCE5D8] text-[#203A32] flex items-center justify-center font-semibold text-xs">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#172D28]">{user?.name || 'Student'}</p>
                  <p className="text-[10px] text-[#52605B] font-mono">
                    {user?.id} {user?.block && `• ${user.block}`}
                  </p>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#DCE5D8] text-xs font-medium text-[#52605B] hover:text-red-700 hover:border-red-200 hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          </div>

          {/* Primary Navigation Tabs */}
          <div className="flex items-center gap-2 pt-1 border-t border-[#DCE5D8]/60">
            <NavLink
              to="/student"
              end
              className={({ isActive }) =>
                `inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                  isActive
                    ? 'border-[#203A32] text-[#203A32] bg-[#F5F7F2]/60 rounded-t-md'
                    : 'border-transparent text-[#52605B] hover:text-[#172D28] hover:border-[#DCE5D8]'
                }`
              }
            >
              <PlusCircle className="w-4 h-4" />
              Raise a Query
            </NavLink>

            <NavLink
              to="/student/history"
              className={({ isActive }) =>
                `inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                  isActive
                    ? 'border-[#203A32] text-[#203A32] bg-[#F5F7F2]/60 rounded-t-md'
                    : 'border-transparent text-[#52605B] hover:text-[#172D28] hover:border-[#DCE5D8]'
                }`
              }
            >
              <History className="w-4 h-4" />
              History & Tracking
            </NavLink>
          </div>
        </div>
      </header>

      {/* Main Content Workspace */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>

      {/* Compact Student Footer */}
      <footer className="border-t border-[#DCE5D8] bg-white py-4 text-center text-xs text-[#52605B]">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Campus Facilities Directorate • Student Support Desk</span>
          <span>Emergency Support: Ext. 4400 / 4401</span>
        </div>
      </footer>
    </div>
  );
};
