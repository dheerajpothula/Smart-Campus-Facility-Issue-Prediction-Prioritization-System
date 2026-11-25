import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Notification } from '../../components/ui/Notification';
import { Building2, ShieldCheck, GraduationCap, Lock, User } from 'lucide-react';

type LoginMode = 'student' | 'admin';

export const LoginPage: React.FC = () => {
  const { login, studentLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [mode, setMode] = useState<LoginMode>('student');

  // Student fields (Name + 8-digit string ID)
  const [studentName, setStudentName] = useState('');
  const [studentId, setStudentId] = useState('');

  // Administrator fields
  const [adminUsername, setAdminUsername] = useState('');
  const [adminPassword, setAdminPassword] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleModeSwitch = (nextMode: LoginMode) => {
    setMode(nextMode);
    setError(null);
  };

  const handleStudentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = studentName.trim().replace(/\s+/g, ' ');
    const trimmedId = studentId.trim();

    if (trimmedName.length < 2 || !/[a-zA-Z]/.test(trimmedName)) {
      setError('Please enter your registered full Student Name (at least 2 alphabetic characters).');
      return;
    }
    if (!/^\d{8}$/.test(trimmedId)) {
      setError('Student ID must consist of exactly eight numeric digits (0-9), preserving any leading zeroes.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      await studentLogin(trimmedName, trimmedId);
      const from = (location.state as any)?.from?.pathname;
      if (from && from.startsWith('/student')) {
        navigate(from, { replace: true });
      } else {
        navigate('/student', { replace: true });
      }
    } catch (err: any) {
      setError(
        err.message ||
          'Student identity could not be verified against active campus enrollment records.',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAdminSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminUsername.trim() || !adminPassword) {
      setError('Please enter both your administrator username and password.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const user = await login(adminUsername.trim(), adminPassword);
      const from = (location.state as any)?.from?.pathname;
      if (from && from.startsWith('/admin') && !user.must_change_password) {
        navigate(from, { replace: true });
      } else {
        navigate('/admin', { replace: true });
      }
    } catch (err: any) {
      setError(err.message || 'Invalid administrator credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-[#F5F7F2]">
      {/* Brand Header */}
      <div className="mb-6 text-center">
        <Link to="/" className="inline-flex items-center gap-2.5 mb-2">
          <div className="w-10 h-10 rounded-xl bg-[#203A32] flex items-center justify-center text-white shadow-xs">
            <Building2 className="w-5 h-5 text-[#DCE5D8]" />
          </div>
          <span className="font-bold text-xl tracking-tight text-[#172D28]">FIPP 2.0</span>
        </Link>
        <p className="text-xs text-[#52605B]">University Campus Facility Operations Gateway</p>
      </div>

      <Card className="w-full max-w-md shadow-md">
        <CardHeader>
          <div>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              {mode === 'student'
                ? 'Verify your registered Student Name and 8-digit Student ID'
                : 'Authenticate with your provisioned administrator account'}
            </CardDescription>
          </div>
          <Lock className="w-5 h-5 text-[#A8B9A3]" />
        </CardHeader>

        <CardContent className="space-y-4 pt-5">
          {/* Role Mode Tabs */}
          <div className="grid grid-cols-2 gap-2 p-1 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8]">
            <button
              type="button"
              onClick={() => handleModeSwitch('student')}
              className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                mode === 'student'
                  ? 'bg-[#203A32] text-white shadow-xs'
                  : 'text-[#52605B] hover:text-[#172D28]'
              }`}
            >
              <GraduationCap className="w-3.5 h-3.5" /> Student Portal
            </button>
            <button
              type="button"
              onClick={() => handleModeSwitch('admin')}
              className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                mode === 'admin'
                  ? 'bg-[#203A32] text-white shadow-xs'
                  : 'text-[#52605B] hover:text-[#172D28]'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" /> Administrator
            </button>
          </div>

          {error && <Notification type="error" message={error} onClose={() => setError(null)} />}

          {mode === 'student' ? (
            <form onSubmit={handleStudentSubmit} className="space-y-4">
              <div className="p-3 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] text-[11px] text-[#52605B] leading-relaxed">
                <strong className="text-[#172D28]">Required Identity Format:</strong> Enter your full registered name
                and your <strong>exact 8-digit numeric Student ID</strong> (including any leading zeroes). Only
                administrator-authorized student records can sign in.
              </div>

              <Input
                label="Student Name"
                name="studentName"
                placeholder="Enter your registered full name"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                leftIcon={<User className="w-4 h-4" />}
                required
                autoFocus
              />

              <Input
                label="Student ID (8 Digits)"
                name="studentId"
                type="text"
                inputMode="numeric"
                maxLength={8}
                placeholder="Enter 8-digit numeric ID"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                helperText="Exact 8 digits (0-9). Leading zeroes are preserved."
                required
              />

              <Button type="submit" variant="primary" className="w-full" isLoading={loading}>
                Verify Student Identity & Continue
              </Button>
            </form>
          ) : (
            <form onSubmit={handleAdminSubmit} className="space-y-4">
              <Input
                label="Administrator Username"
                name="username"
                placeholder="Enter administrator username"
                value={adminUsername}
                onChange={(e) => setAdminUsername(e.target.value)}
                required
                autoFocus
              />

              <Input
                label="Password"
                name="password"
                type="password"
                placeholder="••••••••••••"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                required
              />

              <Button type="submit" variant="primary" className="w-full" isLoading={loading}>
                Authenticate Administrator
              </Button>
            </form>
          )}
        </CardContent>
      </Card>

      <div className="mt-6 text-center">
        <Link to="/" className="text-xs text-[#52605B] hover:text-[#172D28] transition-colors">
          ← Return to Public Homepage
        </Link>
      </div>
    </div>
  );
};
