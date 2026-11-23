import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/layout/ProtectedRoute';

// Pages
import { LandingPage } from './pages/landing/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';

// Student Pages
import { StudentPortalLayout } from './pages/student/StudentPortalLayout';
import { RaiseQueryPage } from './pages/student/RaiseQueryPage';
import { StudentHistoryPage } from './pages/student/StudentHistoryPage';

// Admin Pages
import { AdminPortalLayout } from './pages/admin/AdminPortalLayout';
import { AdminOverviewPage } from './pages/admin/AdminOverviewPage';
import { AdminAllRequestsPage } from './pages/admin/AdminAllRequestsPage';
import { AdminUnassignedPage } from './pages/admin/AdminUnassignedPage';
import { AdminInProgressPage } from './pages/admin/AdminInProgressPage';
import { AdminResolvedPage } from './pages/admin/AdminResolvedPage';
import { AdminReportsPage } from './pages/admin/AdminReportsPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Landing */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Student Portal (Protected) */}
          <Route
            path="/student"
            element={
              <ProtectedRoute allowedRole="student">
                <StudentPortalLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<RaiseQueryPage />} />
            <Route path="history" element={<StudentHistoryPage />} />
          </Route>

          {/* Administrator Portal (Protected) */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRole="admin">
                <AdminPortalLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<AdminOverviewPage />} />
            <Route path="all-requests" element={<AdminAllRequestsPage />} />
            <Route path="unassigned" element={<AdminUnassignedPage />} />
            <Route path="in-progress" element={<AdminInProgressPage />} />
            <Route path="resolved" element={<AdminResolvedPage />} />
            <Route path="reports" element={<AdminReportsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
