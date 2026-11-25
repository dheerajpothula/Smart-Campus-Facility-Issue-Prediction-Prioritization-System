import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Notification } from '../../components/ui/Notification';
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
  KeyRound,
} from 'lucide-react';

export const AdminPortalLayout: React.FC = () => {
  const { user, logout, changePassword } = useAuth();
  const navigate = useNavigate();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const [currPwd, setCurrPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [pwdErr, setPwdErr] = useState<string | null>(null);
  const [pwdSaving, setPwdSaving] = useState(false);

  const handleForcedPasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdErr(null);
    if (newPwd !== confirmPwd) {
      setPwdErr('New password and confirmation do not match.');
      return;
    }
    if (newPwd.length < 12) {
      setPwdErr('New password must be at least 12 characters with uppercase, lowercase, digit, and special character.');
      return;
    }
    setPwdSaving(true);
    try {
      await changePassword(currPwd, newPwd);
      setCurrPwd('');
      setNewPwd('');
      setConfirmPwd('');
    } catch (err: any) {
      setPwdErr(err.message || 'Unable to update password.');
    } finally {
      setPwdSaving(false);
    }
  };

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
          {user?.must_change_password ? (
            <div className="max-w-md mx-auto py-8">
              <Card>
                <CardHeader>
                  <div>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <KeyRound className="w-4 h-4 text-[#203A32]" /> First-Login Password Update Required
                    </CardTitle>
                    <CardDescription>
                      Replace your temporary bootstrap password before accessing Control Centre operations.
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <form onSubmit={handleForcedPasswordChange} className="space-y-4">
                    {pwdErr && <Notification type="error" message={pwdErr} onClose={() => setPwdErr(null)} />}
                    <Input
                      label="Current Temporary Password"
                      type="password"
                      value={currPwd}
                      onChange={(e) => setCurrPwd(e.target.value)}
                      required
                    />
                    <Input
                      label="New Strong Password"
                      type="password"
                      value={newPwd}
                      onChange={(e) => setNewPwd(e.target.value)}
                      helperText="Minimum 12 characters with upper, lower, number & symbol."
                      required
                    />
                    <Input
                      label="Confirm New Password"
                      type="password"
                      value={confirmPwd}
                      onChange={(e) => setConfirmPwd(e.target.value)}
                      required
                    />
                    <Button type="submit" variant="primary" className="w-full" isLoading={pwdSaving}>
                      Update Password & Unlock Control Centre
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Outlet />
          )}
        </main>
      </div>
    </div>
  );
};
