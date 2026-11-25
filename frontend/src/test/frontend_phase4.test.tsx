// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { AdminPortalLayout } from '../pages/admin/AdminPortalLayout';
import { AdminOverviewPage } from '../pages/admin/AdminOverviewPage';
import { AdminAllRequestsPage } from '../pages/admin/AdminAllRequestsPage';
import { AdminUnassignedPage } from '../pages/admin/AdminUnassignedPage';
import { AdminInProgressPage } from '../pages/admin/AdminInProgressPage';
import { AdminResolvedPage } from '../pages/admin/AdminResolvedPage';
import { AdminReportsPage } from '../pages/admin/AdminReportsPage';
import { ComplaintDetailsDrawer } from '../components/admin/ComplaintDetailsDrawer';
import { AuthProvider } from '../context/AuthContext';
import { TokenManager } from '../services/apiClient';

const { mockKPIs, mockTickets, mockAnalyticsReport } = vi.hoisted(() => {
  const kpis = {
    total: 42,
    new: 7,
    in_progress: 15,
    resolved: 20,
    withdrawn: 0,
    resolution_rate_percent: 47.6,
    average_turnaround_days: 1.8,
  };

  const tickets = [
    {
      complaint_id: 'CMP-2026-101',
      student_id: '00123456',
      student_name: 'Aarav Sharma',
      contact_number: '+91 98765 43210',
      category: 'Air Conditioner',
      sub_category: 'Cooling Issue',
      specific_categories: ['AC Not Cooling'],
      facility_type: 'Hostel',
      building: 'Block 38',
      room_number: '302',
      location: 'Block 38 - Room 302',
      date_reported: '2026-11-20',
      status: 'In Progress',
      priority_tier: 'High',
      priority_score: 78.5,
      score_breakdown: {
        severity: 0.8,
        location_criticality: 0.7,
        recurrence_probability: 0.8,
        impact_population: 0.75,
      },
      description: 'AC unit blowing ambient air.',
      allotted_person: 'Ramesh Kumar',
      department: 'Campus HVAC Squad',
      status_history: [
        { status: 'Submitted', timestamp: '2026-11-20T10:00:00' },
        { status: 'Assigned', timestamp: '2026-11-20T12:00:00' },
        { status: 'In Progress', timestamp: '2026-11-20T14:00:00' },
      ],
      remarks_history: [
        { name: 'Admin Desk', update_date: '11/20/2026', remarks: 'Work order dispatched.' },
      ],
    },
    {
      complaint_id: 'CMP-2026-102',
      student_id: '00123457',
      student_name: 'Priya Patel',
      category: 'Electrical',
      sub_category: 'Power Failure',
      specific_categories: ['Tripped MCB'],
      facility_type: 'Academic',
      building: 'Block 34',
      location: 'Block 34 - Lab 101',
      date_reported: '2026-11-21',
      status: 'Submitted',
      priority_tier: 'Critical',
      priority_score: 92.0,
      score_breakdown: {
        severity: 0.95,
        location_criticality: 0.9,
        recurrence_probability: 0.85,
        impact_population: 0.95,
      },
      description: 'Complete power loss in computer lab.',
      department: 'Electrical Squad',
      status_history: [{ status: 'Submitted', timestamp: '2026-11-21T09:00:00' }],
      remarks_history: [],
    },
    {
      complaint_id: 'CMP-2026-103',
      student_id: '00123458',
      student_name: 'Rahul Verma',
      category: 'Plumbing',
      sub_category: 'Washroom Fixtures',
      specific_categories: ['Water Leakage'],
      facility_type: 'Hostel',
      building: 'Block 25',
      location: 'Block 25 - Room 104',
      date_reported: '2026-11-18',
      status: 'Resolved',
      priority_tier: 'Medium',
      priority_score: 54.0,
      description: 'Water tap leaking continuously.',
      allotted_person: 'Suresh Singh',
      department: 'Plumbing Squad',
      resolved_at: '2026-11-19',
      closing_remarks: 'Washroom fixture valve replaced.',
      feedback: {
        rating: 5,
        comments: 'Very quick resolution! Thank you.',
        created_at: '2026-11-19T18:00:00',
      },
      status_history: [
        { status: 'Submitted', timestamp: '2026-11-18T10:00:00' },
        { status: 'Resolved', timestamp: '2026-11-19T15:00:00' },
      ],
      remarks_history: [
        { name: 'Suresh Singh', update_date: '11/19/2026', remarks: 'Replaced worn gasket valve.' },
      ],
    },
  ];

  const report = {
    kpis,
    trends: [
      { period: '2026-11-18', reported_count: 5, resolved_count: 4 },
      { period: '2026-11-19', reported_count: 8, resolved_count: 6 },
      { period: '2026-11-20', reported_count: 12, resolved_count: 7 },
    ],
    category_distribution: [
      { category: 'Air Conditioner', count: 18, percentage: 42.8 },
      { category: 'Electrical', count: 14, percentage: 33.3 },
      { category: 'Plumbing', count: 10, percentage: 23.9 },
    ],
    location_distribution: [
      { location: 'Block 38', count: 20, percentage: 47.6 },
      { location: 'Block 34', count: 12, percentage: 28.5 },
      { location: 'Block 25', count: 10, percentage: 23.9 },
    ],
    priority_distribution: {
      Critical: 6,
      High: 14,
      Medium: 16,
      Low: 6,
    },
    aging_brackets: {
      '< 24 Hours': 8,
      '1 - 3 Days': 12,
      '3 - 7 Days': 4,
      '> 7 Days': 1,
    },
  };

  return { mockKPIs: kpis, mockTickets: tickets, mockAnalyticsReport: report };
});

// Mock services
vi.mock('../services/taxonomyService', () => ({
  taxonomyService: {
    getHierarchy: vi.fn().mockResolvedValue({
      maintenance_categories: ['Air Conditioner', 'Electrical', 'Plumbing', 'Civil Works'],
      campus_blocks: ['Block 38', 'Block 34', 'Block 25'],
    }),
  },
}));

vi.mock('../services/complaintService', () => ({
  complaintService: {
    getAdminKPIs: vi.fn().mockResolvedValue(mockKPIs),
    getAllAdminComplaints: vi.fn().mockResolvedValue({
      total_count: mockTickets.length,
      records: mockTickets,
    }),
    getUnassignedComplaints: vi.fn().mockResolvedValue({
      total_count: 1,
      records: [mockTickets[1]],
    }),
    getInProgressComplaints: vi.fn().mockResolvedValue({
      total_count: 1,
      records: [mockTickets[0]],
    }),
    getResolvedComplaints: vi.fn().mockResolvedValue({
      total_count: 1,
      records: [mockTickets[2]],
    }),
    getAnalyticsReport: vi.fn().mockResolvedValue(mockAnalyticsReport),
    updateComplaintStatus: vi.fn().mockImplementation((_id, payload) =>
      Promise.resolve({
        ...mockTickets[0],
        status: payload.status,
        allotted_person: payload.allotted_person || mockTickets[0].allotted_person,
        department: payload.squad_assigned || mockTickets[0].department,
      })
    ),
    reopenComplaint: vi.fn().mockImplementation((_id, remarks) =>
      Promise.resolve({
        ...mockTickets[2],
        status: 'Under Review',
        remarks_history: [
          ...mockTickets[2].remarks_history,
          { name: 'Admin Staff', update_date: '11/25/2026', remarks: `Reopened: ${remarks}` },
        ],
      })
    ),
  },
}));

describe('FIPP 2.0 Phase 4 — Administrator Control Centre Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    TokenManager.setSession('mock-admin-token', 'mock-refresh-token', {
      user_id: 'fipp.admin',
      role: 'admin',
      name: 'Operations Director',
    });
  });

  it('1. verifies exactly 6 primary administrator navigation sections in AdminPortalLayout', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <AdminPortalLayout />
        </AuthProvider>
      </MemoryRouter>
    );

    // Verify all 6 approved sections
    expect(screen.getByText('Overview')).toBeDefined();
    expect(screen.getByText('All Requests')).toBeDefined();
    expect(screen.getByText('New / Unassigned')).toBeDefined();
    expect(screen.getByText('In Progress')).toBeDefined();
    expect(screen.getByText('Resolved')).toBeDefined();
    expect(screen.getByText('Reports')).toBeDefined();
  });

  it('2. renders AdminOverviewPage with live KPIs and opens ComplaintDetailsDrawer on inspect', async () => {
    render(
      <BrowserRouter>
        <AdminOverviewPage />
      </BrowserRouter>
    );

    // Wait for KPI cards
    await waitFor(() => {
      expect(screen.getByText('Executive Operations Overview')).toBeDefined();
      expect(screen.getByText('42')).toBeDefined(); // Total Ledger
      expect(screen.getByText('7')).toBeDefined();  // New / Unassigned
      expect(screen.getByText('15')).toBeDefined(); // In Progress
      expect(screen.getByText('20')).toBeDefined(); // Resolved
    });

    // Verify recent requests table rendered
    expect(screen.getByText('CMP-2026-101')).toBeDefined();
    expect(screen.getByText('CMP-2026-102')).toBeDefined();

    // Click "Inspect" button on first row
    const inspectButtons = screen.getAllByRole('button', { name: /Inspect/i });
    fireEvent.click(inspectButtons[0]);

    // Verify ComplaintDetailsDrawer opened
    await waitFor(() => {
      expect(screen.getByText('Official Complaint Lifecycle')).toBeDefined();
      expect(screen.getByText('AC unit blowing ambient air.')).toBeDefined();
      expect(screen.getByText('Multi-Criteria Priority (MCPI)')).toBeDefined();
    });
  });

  it('3. renders AdminAllRequestsPage with filter toolbar, table and handles drawer interaction', async () => {
    render(
      <BrowserRouter>
        <AdminAllRequestsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('All Requests Ledger')).toBeDefined();
      expect(screen.getByText('CMP-2026-101')).toBeDefined();
      expect(screen.getByText('CMP-2026-102')).toBeDefined();
    });

    // Verify filter dropdowns present
    expect(screen.getByDisplayValue('All Statuses')).toBeDefined();
    expect(screen.getByDisplayValue('All Categories')).toBeDefined();
    expect(screen.getByDisplayValue('All Locations')).toBeDefined();
    expect(screen.getByDisplayValue('All Priorities')).toBeDefined();

    // Click inspect
    const inspectButtons = screen.getAllByRole('button', { name: /Inspect/i });
    fireEvent.click(inspectButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Official Complaint Lifecycle')).toBeDefined();
    });
  });

  it('4. renders AdminUnassignedPage and opens triage drawer', async () => {
    render(
      <BrowserRouter>
        <AdminUnassignedPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New / Unassigned Requests')).toBeDefined();
      expect(screen.getByText('CMP-2026-102')).toBeDefined();
    });

    // Click "Triage & Assign"
    const triageBtn = screen.getByRole('button', { name: /Triage & Assign/i });
    fireEvent.click(triageBtn);

    // Verify drawer opened with ticket details
    await waitFor(() => {
      expect(screen.getByText('Complete power loss in computer lab.')).toBeDefined();
      expect(screen.getByText('Control Actions')).toBeDefined();
    });
  });

  it('5. renders AdminInProgressPage with active work orders and inspection drawer', async () => {
    render(
      <BrowserRouter>
        <AdminInProgressPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('In Progress Work Orders')).toBeDefined();
      expect(screen.getByText('CMP-2026-101')).toBeDefined();
      expect(screen.getByText('Ramesh Kumar')).toBeDefined();
    });

    const manageBtn = screen.getByRole('button', { name: /Inspect & Manage/i });
    fireEvent.click(manageBtn);

    await waitFor(() => {
      expect(screen.getByText('Official Complaint Lifecycle')).toBeDefined();
      expect(screen.getByText('Update Status & Work Order')).toBeDefined();
    });
  });

  it('6. renders AdminResolvedPage with student ratings and allows reopening ticket', async () => {
    render(
      <BrowserRouter>
        <AdminResolvedPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Resolved Complaint Archive')).toBeDefined();
      expect(screen.getByText('CMP-2026-103')).toBeDefined();
      expect(screen.getByText('5 / 5')).toBeDefined(); // Student rating
    });

    const auditBtn = screen.getByRole('button', { name: /Audit \/ Reopen/i });
    fireEvent.click(auditBtn);

    // Drawer should show student satisfaction feedback and "Reopen Ticket" button
    await waitFor(() => {
      expect(screen.getByText('Student Satisfaction Feedback')).toBeDefined();
      expect(screen.getByText('"Very quick resolution! Thank you."')).toBeDefined();
      expect(screen.getByRole('button', { name: /Reopen Ticket/i })).toBeDefined();
    });

    // Click Reopen Ticket
    const reopenBtn = screen.getByRole('button', { name: /Reopen Ticket/i });
    fireEvent.click(reopenBtn);

    // Reopening reason input should appear
    expect(screen.getByPlaceholderText(/e\.g\. Student reported issue recurred/i)).toBeDefined();
  });

  it('7. renders AdminReportsPage with trends, Pareto distribution and CSV export button', async () => {
    render(
      <BrowserRouter>
        <AdminReportsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Reports & Analytics')).toBeDefined();
      expect(screen.getByText('Category Pareto Distribution')).toBeDefined();
      expect(screen.getByText('Campus Location & Infrastructure Hotspots')).toBeDefined();
      expect(screen.getByText('Priority Hazard Index Breakdown')).toBeDefined();
      expect(screen.getByText('Work Order Aging Brackets')).toBeDefined();
      expect(screen.getByText(/Export CSV \(PII Redacted\)/i)).toBeDefined();
    });

    // Check Pareto items
    expect(screen.getAllByText('Air Conditioner').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('18 tickets (42.8%)')).toBeDefined();

    // Check aging brackets
    expect(screen.getByText('< 24 Hours')).toBeDefined();
    expect(screen.getByText('8 active')).toBeDefined();
  });

  it('8. enforces mandatory closing remarks when transitioning status to Resolved in ComplaintDetailsDrawer', async () => {
    const handleUpdated = vi.fn();
    const handleClose = vi.fn();

    render(
      <ComplaintDetailsDrawer
        isOpen={true}
        ticket={mockTickets[0]}
        onClose={handleClose}
        onTicketUpdated={handleUpdated}
      />
    );

    expect(screen.getByText('CMP-2026-101')).toBeDefined();

    // Change status select to Resolved
    const statusSelect = screen.getByLabelText(/Transition Status/i);
    fireEvent.change(statusSelect, { target: { value: 'Resolved' } });

    // Submit without closing remarks
    const submitBtn = screen.getByRole('button', { name: /Update Status & Work Order/i });
    fireEvent.click(submitBtn);

    // Validation notification should appear
    await waitFor(() => {
      expect(
        screen.getByText(/Mandatory closing remarks detailing the resolution are required/i)
      ).toBeDefined();
    });
    expect(handleUpdated).not.toHaveBeenCalled();
  });
});
