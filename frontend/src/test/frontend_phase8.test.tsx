import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { Footer } from '../components/layout/Footer';
import { LoginPage } from '../pages/auth/LoginPage';
import { AdminPortalLayout } from '../pages/admin/AdminPortalLayout';
import { RaiseQueryPage } from '../pages/student/RaiseQueryPage';
import { StudentHistoryPage } from '../pages/student/StudentHistoryPage';
import { authService } from '../services/authService';
import { uploadService } from '../services/uploadService';
import { complaintService } from '../services/complaintService';
import { taxonomyService } from '../services/taxonomyService';
import { api, TokenManager } from '../services/apiClient';
import type { ComplaintDetail } from '../types';

describe('FIPP 2.0 Phase 8 & Phase 9 QA Frontend Regressions', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('1. Footer omits unverified compliance and institution naming claims', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>,
    );

    const text = document.body.textContent || '';
    expect(text).not.toContain('ISO 27001');
    expect(text).not.toContain('DPDP Act 2023');
    expect(text).not.toMatch(/\bLPU\b/i);
    expect(text).toContain('Role-Based Access Control');
    expect(text).toContain('PBKDF2 & JWT Session Security');
  });

  it('2. LoginPage removes all demo credentials and enforces self-registration 8-digit Student ID + Name validation', async () => {
    const studentLoginSpy = vi.spyOn(authService, 'studentLogin').mockResolvedValue({
      success: true,
      access_token: 'stu-jwt',
      token_type: 'bearer',
      expires_in_seconds: 3600,
      user: { id: '00123456', name: 'Aarav Sharma', role: 'student' },
      message: 'ok',
      is_new_registration: true,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    // Zero demo autofill UI anywhere and honest self-declared disclosure
    expect(screen.queryByText(/Demo Credentials/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Student Demo/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Admin Demo/i })).not.toBeInTheDocument();
    expect(screen.getByText(/Self-Declared Student Identity/i)).toBeInTheDocument();

    // Reject invalid alphanumeric or non-8-digit ID client-side
    fireEvent.change(screen.getByPlaceholderText(/Enter your full name/i), {
      target: { value: 'Aarav Sharma' },
    });
    fireEvent.change(screen.getByPlaceholderText(/Enter 8-digit numeric ID/i), {
      target: { value: '1234ABCD' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Continue to Student Portal/i }));

    await waitFor(() => {
      expect(screen.getByText(/exactly eight numeric digits/i)).toBeInTheDocument();
    });
    expect(studentLoginSpy).not.toHaveBeenCalled();

    // Accept valid leading-zero 8-digit ID cleanly preserving leading zeroes
    fireEvent.change(screen.getByPlaceholderText(/Enter 8-digit numeric ID/i), {
      target: { value: '00123456' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Continue to Student Portal/i }));

    await waitFor(() => {
      expect(studentLoginSpy).toHaveBeenCalledWith('Aarav Sharma', '00123456');
    });
  });

  it('3. AdminPortalLayout enforces mandatory first-login password change gate before exposing admin portal', async () => {
    TokenManager.setSession('adm-temp-jwt', 'adm-refresh', {
      id: 'fipp.admin',
      name: 'FIPP System Administrator',
      role: 'admin',
      must_change_password: true,
    });
    vi.spyOn(authService, 'getCurrentUser').mockResolvedValue({
      id: 'fipp.admin',
      name: 'FIPP System Administrator',
      role: 'admin',
      must_change_password: true,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPortalLayout />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/First-Login Password Update Required/i)).toBeInTheDocument();
    });
  });

  it('4. RaiseQueryPage resets floor and room on block change and handles unknown floor counts without fabrication', async () => {
    sessionStorage.setItem('fipp_student_agreed', 'true');
    TokenManager.setSession('stu-jwt', 'stu-ref', {
      id: '00123456',
      name: 'Aarav Sharma',
      role: 'student',
    });

    vi.spyOn(taxonomyService, 'getHierarchy').mockResolvedValue({
      category_types: ['Maintenance / Electrical Complaints'],
      message_types: ['Grievance'],
      maintenance_categories: ['Electricity'],
      hierarchy: { Electricity: { 'Power Supply': ['Socket'] } },
      campus_blocks: ['Block 57', 'Block 3'],
      blocks_reference: [
        {
          block_id: 'BLK-57',
          display_name: 'Block 57',
          block_category: 'Academic',
          floor_count: 8,
          floor_status: 'external_reference_8_floors',
          verification_status: 'unverified_external_reference',
          floors: [
            { floor_id: 'BLK-57-F0', block_id: 'BLK-57', floor_label: 'Ground Floor', sort_order: 0, verification_status: 'unverified_external_reference' },
            { floor_id: 'BLK-57-F1', block_id: 'BLK-57', floor_label: 'First Floor', sort_order: 1, verification_status: 'unverified_external_reference' },
          ],
        },
        {
          block_id: 'BLK-3',
          display_name: 'Block 3',
          block_category: 'Academic',
          floor_count: null,
          floor_status: 'unknown',
          verification_status: 'unverified_external_reference',
          floors: [],
        },
      ],
      campus_sub_blocks: [],
      room_types: ['Room No', 'Any Other'],
      time_slots: ['08:00–10:00'],
      mandatory_declarations: ['d1', 'd2', 'd3'],
      faq_confirmation_text: 'Confirm FAQ',
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <RaiseQueryPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Raise a Facility Query/i)).toBeInTheDocument();
    });

    const selects = screen.getAllByRole('combobox');
    const blockSelect = selects.find((s) =>
      Array.from((s as HTMLSelectElement).options).some((o) => o.value === 'Block 57'),
    ) as HTMLSelectElement;
    expect(blockSelect).toBeTruthy();

    // Switch from Block 57 (2 floors) -> Block 3 (unknown floors)
    fireEvent.change(blockSelect, { target: { value: 'Block 3' } });

    await waitFor(() => {
      expect(screen.getByText(/Floor count unverified/i)).toBeInTheDocument();
    });
  });

  it('5. authService.logout transmits refresh_token and uploadService rejects WebP', async () => {
    TokenManager.setSession('access-123', 'refresh-xyz', {
      id: '00123456',
      name: 'Aarav Sharma',
      role: 'student',
    });

    const postSpy = vi.spyOn(api, 'post').mockResolvedValue({ success: true });
    await authService.logout();
    expect(postSpy).toHaveBeenCalledWith('/api/auth/logout', { refresh_token: 'refresh-xyz' });

    const webpFile = new File(['dummy'], 'photo.webp', { type: 'image/webp' });
    await expect(uploadService.uploadPhoto(webpFile)).rejects.toThrow(/Only JPEG and PNG/i);
  });

  it('6. StudentHistoryPage fetches photo attachment via Bearer token and displays resolved_at date', async () => {
    TokenManager.setSession('student-jwt-token', 'refresh-token', {
      id: '00123456',
      name: 'Aarav Sharma',
      role: 'student',
    });

    const mockTicket: ComplaintDetail = {
      complaint_id: 'CMP-2026-099',
      student_id: '00123456',
      student_name: 'Aarav Sharma',
      category_type: 'Maintenance / Electrical Complaints',
      message_type: 'Grievance',
      category: 'Electricity',
      sub_category: 'Lighting / Fixtures / Wiring',
      specific_categories: ['Tube light flickering'],
      facility_type: 'Electricity',
      building: 'Block 57',
      block_id: 'BLK-57',
      floor_id: 'BLK-57-F2',
      floor_label: 'Second Floor',
      room_type: 'Room No',
      room_number: '204',
      location: 'Block 57 - Second Floor, Room 204',
      contact_number: '9876543210',
      time_slot: '10:00–12:00',
      title: 'Tube light flickering continuously',
      description: 'Fixture flickers and trips MCB.',
      status: 'Resolved',
      priority_tier: 'High',
      priority_score: 62.5,
      allotted_person: 'Electrical Maintenance',
      date_reported: '2026-04-01T09:00:00Z',
      resolved_at: '2026-04-02T14:30:00Z',
      is_reopened: false,
      has_photo: true,
      photo_name: 'evidence.png',
      photo_stored_filename: 'CMP_2026_099_evidence.png',
      remarks_history: [
        {
          remarks: 'Replaced starter.',
          update_date: '2026-04-02T14:30:00Z',
          name: 'fipp.admin',
          previous_status: 'In Progress',
          new_status: 'Resolved',
        },
      ],
    };

    vi.spyOn(complaintService, 'getStudentComplaints').mockResolvedValue({
      student_id: '00123456',
      student_name: 'Aarav Sharma',
      total_complaints: 1,
      open_complaints: 0,
      closed_complaints: 1,
      records: [mockTicket],
    });

    const blob = new Blob(['png-bytes'], { type: 'image/png' });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(blob),
    });
    vi.stubGlobal('fetch', fetchMock);
    const createUrlSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-photo-url');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);

    render(
      <MemoryRouter>
        <StudentHistoryPage />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole('button', { name: /View Details/i }));
    await waitFor(() => expect(screen.getByText(/Resolved on:/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /View Attachment/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/uploads/CMP_2026_099_evidence.png',
        expect.objectContaining({ headers: { Authorization: 'Bearer student-jwt-token' } }),
      );
      expect(createUrlSpy).toHaveBeenCalledWith(blob);
      expect(openSpy).toHaveBeenCalledWith('blob:mock-photo-url', '_blank', 'noopener,noreferrer');
    });
  });
});
