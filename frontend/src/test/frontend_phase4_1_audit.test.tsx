// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AdminOverviewPage } from '../pages/admin/AdminOverviewPage';
import { AdminAllRequestsPage } from '../pages/admin/AdminAllRequestsPage';
import { AdminUnassignedPage } from '../pages/admin/AdminUnassignedPage';
import { AdminInProgressPage } from '../pages/admin/AdminInProgressPage';
import { AdminResolvedPage } from '../pages/admin/AdminResolvedPage';
import { AdminReportsPage } from '../pages/admin/AdminReportsPage';
import { ComplaintDetailsDrawer } from '../components/admin/ComplaintDetailsDrawer';
import { TokenManager } from '../services/apiClient';
import { complaintService } from '../services/complaintService';

const { mockKPIs, mockTickets, mockReportNoTurnaround } = vi.hoisted(() => {
  const kpis = {
    total: 10,
    new: 2,
    in_progress: 4,
    resolved: 3,
    withdrawn: 1,
    resolution_rate_percent: 33.3,
    average_turnaround_days: null,
  };

  const tickets = [
    {
      complaint_id: 'CMP-2026-201',
      student_id: '00123456',
      student_name: 'Student',
      contact_number: '9876543210',
      category: 'Electricity',
      sub_category: 'Fan Problem',
      specific_categories: ['General Problem / Not Working'],
      facility_type: 'Electricity',
      building: 'BH-1 Boys Hostel',
      room_number: '204',
      location: 'BH-1 Boys Hostel - Room 204',
      date_reported: '2026-11-24 10:00',
      status: 'Submitted' as const,
      priority_tier: 'High' as const,
      priority_score: 72.5,
      score_breakdown: {
        'Severity Contribution': 26.3,
        'Location Criticality Contribution': 15.0,
        'Recurrence Risk Contribution': 16.2,
        'Impact Population Contribution': 15.0,
      },
      description: 'Ceiling fan sparking.',
      photo_stored_filename: 'CMP-PHOTO_abc123.png',
      remarks_history: [],
      is_reopened: false,
      has_photo: true,
    },
    {
      complaint_id: 'CMP-2026-202',
      student_id: '00123456',
      student_name: 'Rahul Sharma',
      category: 'Plumbing',
      facility_type: 'Plumbing',
      building: 'Hostel Block B',
      location: 'Hostel Block B - 2nd Floor',
      date_reported: '2026-11-23 09:00',
      status: 'In Progress' as const,
      priority_tier: 'Critical' as const,
      priority_score: 88.2,
      allotted_person: 'Ramesh Kumar',
      department: 'Plumbing Squad',
      description: 'Main pipe burst.',
      specific_categories: [],
      remarks_history: [],
      is_reopened: false,
      has_photo: false,
    },
    {
      complaint_id: 'CMP-2026-203',
      student_id: '00123457',
      student_name: 'Priya Patel',
      category: 'Carpentry',
      facility_type: 'Carpentry',
      building: 'GH-1 Girls Hostel',
      location: 'GH-1 Girls Hostel - Room 302',
      date_reported: '2026-11-20 08:00',
      status: 'Resolved' as const,
      priority_tier: 'Medium' as const,
      priority_score: 45.0,
      resolved_at: '2026-11-22 10:00:00',
      resolved_by: 'fipp.admin',
      closing_remarks: 'Door hinge replaced.',
      is_reopened: true,
      reopened_at: '2026-11-23 11:00:00',
      original_resolved_at: '2026-11-22 10:00:00',
      original_resolved_by: 'fipp.admin',
      previous_closing_remarks: 'Door hinge replaced.',
      description: 'Door hinge broken.',
      specific_categories: [],
      remarks_history: [],
      has_photo: false,
    },
  ];

  const report = {
    kpis,
    trends: [{ period: '2026-11-24', reported_count: 3, resolved_count: 1 }],
    category_distribution: [{ category: 'Electricity', count: 5, percentage: 50.0 }],
    location_distribution: [{ building: 'BH-1 Boys Hostel', count: 5, percentage: 50.0 }],
    priority_distribution: { Critical: 1, High: 3, Medium: 4, Low: 2 },
    aging_brackets: { '<24h': 2, '1–3d': 2, '3–7d': 0, '>7d': 0 },
  };

  return { mockKPIs: kpis, mockTickets: tickets, mockReportNoTurnaround: report };
});

vi.mock('../services/taxonomyService', () => ({
  taxonomyService: {
    getHierarchy: vi.fn().mockResolvedValue({
      maintenance_categories: ['Electricity', 'Plumbing', 'Carpentry'],
      campus_blocks: ['BH-1 Boys Hostel', 'Hostel Block B', 'GH-1 Girls Hostel'],
    }),
  },
}));

vi.mock('../services/complaintService', () => ({
  complaintService: {
    getAdminKPIs: vi.fn().mockResolvedValue(mockKPIs),
    getAllAdminComplaints: vi.fn().mockResolvedValue({
      total_count: mockTickets.length,
      limit: 15,
      offset: 0,
      records: mockTickets,
    }),
    getUnassignedComplaints: vi.fn().mockResolvedValue({
      total_count: 1,
      limit: 50,
      offset: 0,
      records: [mockTickets[0]],
    }),
    getInProgressComplaints: vi.fn().mockResolvedValue({
      total_count: 1,
      limit: 50,
      offset: 0,
      records: [mockTickets[1]],
    }),
    getResolvedComplaints: vi.fn().mockResolvedValue({
      total_count: 1,
      limit: 50,
      offset: 0,
      records: [mockTickets[2]],
    }),
    getAnalyticsReport: vi.fn().mockResolvedValue(mockReportNoTurnaround),
    updateComplaintStatus: vi.fn().mockImplementation((_id, payload) =>
      Promise.resolve({
        ...mockTickets[0],
        status: payload.status,
        allotted_person: payload.allotted_person || null,
        department: payload.squad_assigned || null,
      })
    ),
    reopenComplaint: vi.fn(),
  },
}));

describe('FIPP 2.0 Phase 4.1 — Verification Audit Regression Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    TokenManager.setSession('mock-admin-jwt', 'mock-refresh', {
      id: 'fipp.admin',
      role: 'admin',
      name: 'Administrator',
    });
  });

  it('1. renders Reports Unavailable turnaround (no fake 1.8 Days), sends Daily/Weekly/Monthly, and passes filters to CSV export', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('complaint_id\nCMP-2026-201\n', {
        status: 200,
        headers: { 'content-type': 'text/csv' },
      })
    );
    window.URL.createObjectURL = vi.fn(() => 'blob:mock');
    window.URL.revokeObjectURL = vi.fn();

    render(
      <BrowserRouter>
        <AdminReportsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Unavailable')).toBeDefined();
      expect(screen.queryByText('1.8 Days')).toBeNull();
      expect(screen.queryByText(/DPDP Act 2023/i)).toBeNull();
      expect(
        screen.getByText(/room\/location details and technician names remain in operational exports/i)
      ).toBeDefined();
    });

    // Change trend grouping to Weekly and verify backend param is 'Weekly'
    const trendSelect = screen.getByLabelText(/Trend Grouping/i);
    fireEvent.change(trendSelect, { target: { value: 'Weekly' } });

    await waitFor(() => {
      expect(complaintService.getAnalyticsReport).toHaveBeenCalledWith(
        expect.objectContaining({ trend_agg: 'Weekly' })
      );
    });

    // Set category filter and click Export CSV
    const catSelect = screen.getByLabelText(/Category/i);
    fireEvent.change(catSelect, { target: { value: 'Electricity' } });

    const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
    fireEvent.click(exportBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/reports/export?redact_pii=true&category=Electricity'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer mock-admin-jwt' },
        })
      );
    });

    fetchSpy.mockRestore();
  });

  it('2. transitions ComplaintDetailsDrawer open/closed without hook errors, shows MCPI pts, resolution history, and authenticated photo fetch', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(new Blob(['png'], { type: 'image/png' }), { status: 200 })
    );
    window.URL.createObjectURL = vi.fn(() => 'blob:mock-img');
    window.URL.revokeObjectURL = vi.fn();
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);

    const { rerender } = render(
      <ComplaintDetailsDrawer
        isOpen={false}
        ticket={null}
        onClose={vi.fn()}
        onTicketUpdated={vi.fn()}
      />
    );

    rerender(
      <ComplaintDetailsDrawer
        isOpen={true}
        ticket={mockTickets[0]}
        onClose={vi.fn()}
        onTicketUpdated={vi.fn()}
      />
    );

    // Verify backend MCPI points displayed as pts (not 2630%)
    expect(screen.getByText('26.3 pts')).toBeDefined();
    expect(screen.queryByText(/2630%/)).toBeNull();

    // Verify authenticated attachment retrieval hits /api/uploads/{filename} with Bearer token
    const viewBtn = screen.getByRole('button', { name: /View/i });
    fireEvent.click(viewBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        '/api/uploads/CMP-PHOTO_abc123.png',
        expect.objectContaining({
          headers: { Authorization: 'Bearer mock-admin-jwt' },
        })
      );
    });

    // Switch to reopened resolved ticket and verify resolution record + prior remarks
    rerender(
      <ComplaintDetailsDrawer
        isOpen={true}
        ticket={mockTickets[2]}
        onClose={vi.fn()}
        onTicketUpdated={vi.fn()}
      />
    );

    expect(screen.getByText('Resolution Record')).toBeDefined();
    expect(screen.getByText('Door hinge replaced.')).toBeDefined();
    expect(screen.getByText(/Prior remarks: "Door hinge replaced."/)).toBeDefined();

    fetchSpy.mockRestore();
    openSpy.mockRestore();
  });

  it('3. preserves parent table and filters in AdminAllRequestsPage during drawer update', async () => {
    render(
      <BrowserRouter>
        <AdminAllRequestsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('CMP-2026-201')).toBeDefined();
    });

    // Apply status filter
    fireEvent.change(screen.getByDisplayValue('All Statuses'), {
      target: { value: 'Submitted' },
    });

    await waitFor(() => {
      expect(complaintService.getAllAdminComplaints).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'Submitted' })
      );
    });

    // Open drawer and update status
    const inspectBtns = screen.getAllByRole('button', { name: /Inspect/i });
    fireEvent.click(inspectBtns[0]);
    fireEvent.change(screen.getByLabelText(/Transition Status/i), {
      target: { value: 'Assigned' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Update Status & Work Order/i }));

    // Parent table remains mounted (both table cell and drawer header show CMP-2026-201) and filter remains 'Submitted'
    await waitFor(() => {
      expect(screen.getAllByText('CMP-2026-201').length).toBeGreaterThanOrEqual(2);
      expect(screen.getByDisplayValue('Submitted')).toBeDefined();
    });

    // Close drawer and confirm table & filter remain intact
    fireEvent.click(screen.getByTitle(/Close Drawer/i));
    await waitFor(() => {
      expect(screen.getByText('CMP-2026-201')).toBeDefined();
      expect(screen.getByDisplayValue('Submitted')).toBeDefined();
    });
  });

  it('4. verifies drawer opens cleanly across Overview, Unassigned, In Progress, and Resolved views', async () => {
    const views = [
      { component: <AdminOverviewPage />, buttonText: /Inspect/i, expectedToken: 'CMP-2026-201' },
      { component: <AdminUnassignedPage />, buttonText: /Triage & Assign/i, expectedToken: 'CMP-2026-201' },
      { component: <AdminInProgressPage />, buttonText: /Inspect & Manage/i, expectedToken: 'CMP-2026-202' },
      { component: <AdminResolvedPage />, buttonText: /Audit \/ Reopen/i, expectedToken: 'CMP-2026-203' },
    ];

    for (const view of views) {
      const { unmount } = render(<BrowserRouter>{view.component}</BrowserRouter>);
      await waitFor(() => {
        expect(screen.getByText(view.expectedToken)).toBeDefined();
      });
      const btns = screen.getAllByRole('button', { name: view.buttonText });
      fireEvent.click(btns[0]);
      await waitFor(() => {
        expect(screen.getByText('Official Complaint Lifecycle')).toBeDefined();
      });
      unmount();
    }
  });

  it('5. displays aligned Overview Active & Under Review KPI label and In Progress status definition', async () => {
    const { unmount } = render(
      <BrowserRouter>
        <AdminOverviewPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('Active & Under Review')).toBeDefined();
      expect(screen.getByText('Under Review, Assigned & In Progress')).toBeDefined();
    });
    unmount();

    render(
      <BrowserRouter>
        <AdminInProgressPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(
        screen.getByText(/Dispatched work orders with status .Assigned. or .In Progress./i)
      ).toBeDefined();
    });
  });
});
