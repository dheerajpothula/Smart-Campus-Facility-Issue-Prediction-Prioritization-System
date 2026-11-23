import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/Button';
import { Building2, ShieldCheck, GraduationCap, Menu, X, LogOut } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#DCE5D8] transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-[#203A32] flex items-center justify-center text-white shadow-xs group-hover:bg-[#172D28] transition-colors">
              <Building2 className="w-5 h-5 text-[#DCE5D8]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-[#172D28]">FIPP 2.0</span>
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded-sm bg-[#DCE5D8] text-[#203A32]">
                  Campus
                </span>
              </div>
              <p className="text-[11px] text-[#52605B] hidden sm:block">
                Facility Issue Prediction & Prioritisation Platform
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              to="/"
              className="text-sm font-medium text-[#172D28] hover:text-[#203A32] transition-colors"
            >
              Overview
            </Link>
            <Link
              to="/student"
              className="text-sm font-medium text-[#52605B] hover:text-[#172D28] flex items-center gap-1.5 transition-colors"
            >
              <GraduationCap className="w-4 h-4 text-[#A8B9A3]" />
              Student Portal
            </Link>
            <Link
              to="/admin"
              className="text-sm font-medium text-[#52605B] hover:text-[#172D28] flex items-center gap-1.5 transition-colors"
            >
              <ShieldCheck className="w-4 h-4 text-[#A8B9A3]" />
              Admin Portal
            </Link>
          </nav>

          {/* User Controls */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated && user ? (
              <div className="flex items-center gap-3 pl-4 border-l border-[#DCE5D8]">
                <div className="text-right">
                  <p className="text-xs font-semibold text-[#172D28]">{user.name}</p>
                  <p className="text-[10px] text-[#52605B] capitalize">{user.role}</p>
                </div>
                <Link to={user.role === 'admin' ? '/admin' : '/student'}>
                  <Button variant="secondary" size="sm">
                    Workspace
                  </Button>
                </Link>
                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="p-1.5 text-[#52605B] hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2.5">
                <Link to="/login">
                  <Button variant="outline" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link to="/student">
                  <Button variant="primary" size="sm">
                    Raise a Query
                  </Button>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu trigger */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-[#172D28] hover:bg-[#F5F7F2]"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#DCE5D8] bg-white px-4 pt-2 pb-5 space-y-3">
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block py-2 text-sm font-medium text-[#172D28]"
          >
            Overview
          </Link>
          <Link
            to="/student"
            onClick={() => setMobileMenuOpen(false)}
            className="block py-2 text-sm font-medium text-[#52605B]"
          >
            Student Portal
          </Link>
          <Link
            to="/admin"
            onClick={() => setMobileMenuOpen(false)}
            className="block py-2 text-sm font-medium text-[#52605B]"
          >
            Admin Portal
          </Link>
          <div className="pt-3 border-t border-[#DCE5D8] flex flex-col gap-2">
            {isAuthenticated && user ? (
              <>
                <div className="py-1">
                  <p className="text-xs font-semibold text-[#172D28]">{user.name}</p>
                  <p className="text-[10px] text-[#52605B] capitalize">{user.role} ({user.id})</p>
                </div>
                <Button variant="outline" size="sm" onClick={handleLogout} className="w-full">
                  Sign Out
                </Button>
              </>
            ) : (
              <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="primary" size="sm" className="w-full">
                  Sign In
                </Button>
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
