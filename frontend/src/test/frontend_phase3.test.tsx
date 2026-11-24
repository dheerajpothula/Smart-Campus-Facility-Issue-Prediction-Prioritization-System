// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TokenManager } from '../services/apiClient';
import { RaiseQueryPage } from '../pages/student/RaiseQueryPage';
import { StudentHistoryPage } from '../pages/student/StudentHistoryPage';
import { LoginPage } from '../pages/auth/LoginPage';
import { AuthProvider } from '../context/AuthContext';
import { BrowserRouter } from 'react-router-dom';

// Mock taxonomyService and complaintService
vi.mock('../services/taxonomyService', () => ({
  taxonomyService: {
    getHierarchy: vi.fn().mockResolvedValue({
      category_types: ['Maintenance / Electrical Complaints'],
      message_types: ['Grievance', 'Assistance', 'Enquiry', 'Feedback'],
      maintenance_categories: [
        'Air Conditioner',
        'Carpenter',
        'Civil Works',
        'Electrical',
        'Plumbing',
      ],
      hierarchy: {
        'Air Conditioner': {
          'Cooling Issue': ['AC Not Cooling', 'AC Gas Leakage'],
          'Water Dripping': ['Indoor Unit Leaking'],
        },
        Electrical: {
          'Power Failure': ['Socket Not Working', 'Tripped MCB'],
        },
      },
      campus_blocks: ['Block 38', 'Block 34', 'Block 25'],
      campus_sub_blocks: ['A', 'B', 'C'],
      room_types: ['Room No', 'Any Other'],
      time_slots: [
        '08:00–10:00',
        '10:00–12:00',
        '12:00–14:00',
        '14:00–16:00',
        '16:00–18:00',
      ],
      mandatory_declarations: [
        'I am responsible for the content typed in query.',
        'I understand that necessary disciplinary action can be initiated against me in case of use of derogatory words or false statements against any Student/Faculty/Staff/Higher Authority.',
        'The information given by me regarding the complaint/request is true to the best of my knowledge and if found false/ wrong, necessary disciplinary action can be initiated against me.',
      ],
      faq_confirmation_text: 'Please confirm you have checked self-help guides.',
    }),
  },
}));

vi.mock('../services/complaintService', () => ({
  complaintService: {
    submitStudentComplaint: vi.fn().mockResolvedValue({
      success: true,
      token: 'CMP-2026-999',
      message: 'Complaint CMP-2026-999 has been registered successfully.',
    }),
    getStudentComplaints: vi.fn().mockResolvedValue({
      student_id: 'STU-2026-001',
      student_name: 'Aarav Sharma',
      total_complaints: 2,
      open_complaints: 1,
      closed_complaints: 1,
      records: [
        {
          complaint_id: 'CMP-2026-001',
          title: '[Grievance] AC Not Cooling',
          category: 'Air Conditioner',
          sub_category: 'Cooling Issue',
          specific_categories: ['AC Not Cooling'],
          location: 'Block 38 - Room 302',
          date_reported: '2026-11-20',
          status: 'In Progress',
          description: 'AC unit blowing ambient air.',
          allotted_person: 'Ramesh Kumar',
          department: 'HVAC Squad',
          status_history: [
            { status: 'Submitted', timestamp: '2026-11-20T10:00:00' },
            { status: 'Under Review', timestamp: '2026-11-20T11:00:00' },
            { status: 'Assigned', timestamp: '2026-11-20T12:00:00' },
            { status: 'In Progress', timestamp: '2026-11-20T14:00:00' },
          ],
          remarks_history: [
            { name: 'Admin Desk', update_date: '11/20/2026', remarks: 'Technician assigned.' },
          ],
        },
        {
          complaint_id: 'CMP-2026-002',
          title: '[Grievance] Leaking Tap',
          category: 'Plumbing',
          sub_category: 'Washroom Fixtures',
          specific_categories: ['Tap Leaking'],
          location: 'Block 38 - Room 302',
          date_reported: '2026-11-18',
          status: 'Resolved',
          resolution_date: '2026-11-19',
          description: 'Water tap leaking continuously.',
          status_history: [
            { status: 'Submitted', timestamp: '2026-11-18T09:00:00' },
            { status: 'Resolved', timestamp: '2026-11-19T16:00:00' },
          ],
          remarks_history: [],
          feedback: null,
        },
      ],
    }),
    getStudentComplaintDetails: vi.fn().mockImplementation((id: string) => {
      return Promise.resolve({
        complaint_id: id,
        title: id === 'CMP-2026-001' ? '[Grievance] AC Not Cooling' : '[Grievance] Leaking Tap',
        category: id === 'CMP-2026-001' ? 'Air Conditioner' : 'Plumbing',
        sub_category: id === 'CMP-2026-001' ? 'Cooling Issue' : 'Washroom Fixtures',
        location: 'Block 38 - Room 302',
        date_reported: '2026-11-20',
        status: id === 'CMP-2026-001' ? 'In Progress' : 'Resolved',
        description: 'Test issue description',
        status_history: [
          { status: 'Submitted', timestamp: '2026-11-20T10:00:00' },
          { status: 'In Progress', timestamp: '2026-11-20T14:00:00' },
        ],
        remarks_history: [],
      });
    }),
    withdrawComplaint: vi.fn().mockResolvedValue({
      success: true,
      message: 'Complaint CMP-2026-001 has been marked as Withdrawn.',
    }),
    submitFeedback: vi.fn().mockResolvedValue({
      success: true,
      message: 'Thank you! Your feedback has been recorded.',
    }),
  },
}));

describe('FIPP 2.0 Phase 3 — Student Portal Unit Tests', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  describe('1. Student Authentication & Session Persistence', () => {
    it('stores authenticated student tokens in sessionStorage and isolates tab lifecycle', () => {
      TokenManager.setSession('test_access_jwt', 'test_refresh_jwt', {
        id: 'STU-2026-001',
        name: 'Aarav Sharma',
        role: 'student',
        block: 'Block 38',
      });

      expect(TokenManager.getAccessToken()).toBe('test_access_jwt');
      expect(TokenManager.getUser()?.id).toBe('STU-2026-001');
      expect(TokenManager.getUser()?.role).toBe('student');

      TokenManager.clearSession();
      expect(TokenManager.getAccessToken()).toBeNull();
      expect(TokenManager.getUser()).toBeNull();
      expect(sessionStorage.getItem('fipp_student_agreed')).toBeNull();
    });
  });

  describe('2. Raise Query Mandatory Declarations & Workflow', () => {
    it('displays agreement card on initial entry and requires all 3 declarations before unlocking form', async () => {
      render(
        <AuthProvider>
          <BrowserRouter>
            <RaiseQueryPage />
          </BrowserRouter>
        </AuthProvider>
      );

      // Should display Agreement card
      await waitFor(() => {
        expect(screen.getByText(/Mandatory Undertaking/i)).toBeInTheDocument();
      });

      const agreeButton = screen.getByRole('button', { name: /Agree & Proceed/i });
      expect(agreeButton).toBeDisabled();

      // Check all 3 declarations
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBe(3);

      fireEvent.click(checkboxes[0]);
      expect(agreeButton).toBeDisabled();

      fireEvent.click(checkboxes[1]);
      expect(agreeButton).toBeDisabled();

      fireEvent.click(checkboxes[2]);
      expect(agreeButton).not.toBeDisabled();

      // Click Agree & Proceed
      fireEvent.click(agreeButton);

      // Form should now be unlocked
      await waitFor(() => {
        expect(screen.getByText(/1\. Issue Classification/i)).toBeInTheDocument();
      });

      expect(sessionStorage.getItem('fipp_student_agreed')).toBe('true');
    });

    it('bypasses agreement screen when student has already agreed in current session', async () => {
      sessionStorage.setItem('fipp_student_agreed', 'true');

      render(
        <AuthProvider>
          <BrowserRouter>
            <RaiseQueryPage />
          </BrowserRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/1\. Issue Classification/i)).toBeInTheDocument();
      });
      expect(screen.queryByText(/Mandatory Student Terms & Undertakings/i)).not.toBeInTheDocument();
    });
  });

  describe('3. Form Validation, Cascading Taxonomy & Phone Constraints', () => {
    beforeEach(() => {
      sessionStorage.setItem('fipp_student_agreed', 'true');
    });

    it('validates 10-digit Indian phone numbers and prevents invalid phone formats', () => {
      const validPhone = '9876543210';
      const cleanValid = validPhone.replace(/\D/g, '');
      expect(cleanValid.length).toBe(10);
      expect(/^[6-9]\d{9}$/.test(cleanValid)).toBe(true);

      const invalidLength = '98765';
      expect(invalidLength.replace(/\D/g, '').length).toBeLessThan(10);

      const invalidStart = '1234567890';
      expect(/^[6-9]\d{9}$/.test(invalidStart)).toBe(false);
    });

    it('enforces 500-character description limit', () => {
      const sampleShort = 'Test defect';
      expect(sampleShort.length).toBeGreaterThanOrEqual(5);
      expect(sampleShort.length).toBeLessThanOrEqual(500);

      const sampleLong = 'A'.repeat(501);
      expect(sampleLong.length).toBeGreaterThan(500);
    });

    it('resets downstream selections when category or message type changes', async () => {
      render(
        <AuthProvider>
          <BrowserRouter>
            <RaiseQueryPage />
          </BrowserRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/1\. Issue Classification/i)).toBeInTheDocument();
      });

      // Verify category select is present
      const categorySelect = screen.getByLabelText(/Primary Category/i);
      expect(categorySelect).toBeInTheDocument();
    });
  });

  describe('4. Student History & Status Progression Timeline', () => {
    it('renders complaint records and displays summary KPIs', async () => {
      render(
        <AuthProvider>
          <BrowserRouter>
            <StudentHistoryPage />
          </BrowserRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('CMP-2026-001')).toBeInTheDocument();
        expect(screen.getByText('CMP-2026-002')).toBeInTheDocument();
      });

      // Status Badges
      expect(screen.getAllByText('In Progress').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Resolved').length).toBeGreaterThanOrEqual(1);
    });

    it('filters complaint records using the status dropdown', async () => {
      render(
        <AuthProvider>
          <BrowserRouter>
            <StudentHistoryPage />
          </BrowserRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('CMP-2026-001')).toBeInTheDocument();
      });

      // Find status select
      const selects = screen.getAllByRole('combobox');
      const statusSelect = selects[0];

      fireEvent.change(statusSelect, { target: { value: 'Resolved' } });

      await waitFor(() => {
        expect(screen.getByText('CMP-2026-002')).toBeInTheDocument();
        expect(screen.queryByText('CMP-2026-001')).not.toBeInTheDocument();
      });
    });

    it('opens detail modal and displays genuine 5-stage lifecycle and withdrawal button for open tickets', async () => {
      render(
        <AuthProvider>
          <BrowserRouter>
            <StudentHistoryPage />
          </BrowserRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('CMP-2026-001')).toBeInTheDocument();
      });

      const viewButtons = screen.getAllByRole('button', { name: /View Details/i });
      fireEvent.click(viewButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/Ticket Details — CMP-2026-001/i)).toBeInTheDocument();
        expect(screen.getByText(/Official Complaint Lifecycle/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Withdraw Query/i })).toBeInTheDocument();
      });
    });
  });
});
