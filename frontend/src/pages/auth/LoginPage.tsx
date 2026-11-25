import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Notification } from '../../components/ui/Notification';
import { Building2, ShieldCheck, GraduationCap, Lock, KeyRound } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please provide both your identification ID and password.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const user = await login(username.trim(), password);
      const from = (location.state as any)?.from?.pathname;
      if (from) {
        navigate(from, { replace: true });
      } else if (user.role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/student', { replace: true });
      }
    } catch (err: any) {
      setError(err.message || 'Invalid credentials. Please verify your ID and password.');
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setError(null);
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
            <CardDescription>Enter your university credentials to access your portal</CardDescription>
          </div>
          <Lock className="w-5 h-5 text-[#A8B9A3]" />
        </CardHeader>

        <CardContent className="space-y-4 pt-5">
          {error && <Notification type="error" message={error} onClose={() => setError(null)} />}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Identification ID"
              placeholder="e.g. STU-2026-001 or ADM-2026-001"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button type="submit" variant="primary" className="w-full" isLoading={loading}>
              Authenticate & Continue
            </Button>
          </form>

          {/* Quick Demo Fillers (Strictly disabled in pilot/production builds unless explicitly enabled) */}
          {((import.meta.env.DEV && import.meta.env.VITE_ENABLE_DEMO_LOGIN !== 'false') ||
            import.meta.env.VITE_ENABLE_DEMO_LOGIN === 'true') && (
            <div className="pt-4 border-t border-[#DCE5D8] space-y-2">
              <p className="text-[11px] font-semibold text-[#52605B] uppercase tracking-wider flex items-center gap-1">
                <KeyRound className="w-3.5 h-3.5 text-[#203A32]" /> Demo Credentials:
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => fillCredentials('STU-2026-001', 'student123')}
                  className="p-2 text-left rounded-lg border border-[#DCE5D8] bg-[#F5F7F2] hover:bg-white hover:border-[#203A32] transition-all text-xs"
                >
                  <div className="flex items-center gap-1 font-semibold text-[#172D28]">
                    <GraduationCap className="w-3.5 h-3.5 text-[#203A32]" /> Student
                  </div>
                  <div className="text-[10px] text-[#52605B] mt-0.5 font-mono">STU-2026-001</div>
                </button>

                <button
                  type="button"
                  onClick={() => fillCredentials('ADM-2026-001', 'Admin@001')}
                  className="p-2 text-left rounded-lg border border-[#DCE5D8] bg-[#F5F7F2] hover:bg-white hover:border-[#203A32] transition-all text-xs"
                >
                  <div className="flex items-center gap-1 font-semibold text-[#172D28]">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#203A32]" /> Admin Lead
                  </div>
                  <div className="text-[10px] text-[#52605B] mt-0.5 font-mono">ADM-2026-001</div>
                </button>
              </div>
            </div>
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
