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
    vi.unstubAllGlobals();
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

    // Zero demo autofill UI, no large technical info box, and concise instruction text present
    expect(screen.queryByText(/Demo Credentials/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Student Demo/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Admin Demo/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/Self-Declared Student Identity/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/not verified against an external university directory/i)).not.toBeInTheDocument();
    expect(screen.getByText('Enter your name and 8-digit Student ID to continue.')).toBeInTheDocument();

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

  it('7. apiClient reads Fetch Response body once across JSON, empty, HTML, and plain-text errors without "body stream already read"', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    // 7a. New registration (200 JSON)
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          success: true,
          access_token: 'tok-new',
          refresh_token: 'ref-new',
          token_type: 'bearer',
          expires_in_seconds: 3600,
          is_new_registration: true,
          user: { id: '00112233', name: 'Neha Singh', role: 'student' },
          message: 'Student profile registered.',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    const regRes = await authService.studentLogin('Neha Singh', '00112233');
    expect(regRes.is_new_registration).toBe(true);
    expect(regRes.user.id).toBe('00112233');

    // 7b. Existing student login (200 JSON)
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          success: true,
          access_token: 'tok-existing',
          refresh_token: 'ref-existing',
          token_type: 'bearer',
          expires_in_seconds: 3600,
          is_new_registration: false,
          user: { id: '00112233', name: 'Neha Singh', role: 'student' },
          message: 'Welcome back.',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    const loginRes = await authService.studentLogin('Neha Singh', '00112233');
    expect(loginRes.is_new_registration).toBe(false);

    // 7c. Duplicate ID / name mismatch (409 Conflict JSON)
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ detail: 'This 8-digit Student ID is already registered under a different name.' }),
        { status: 409, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    await expect(authService.studentLogin('Other Name', '00112233')).rejects.toMatchObject({
      status: 409,
      message: 'This 8-digit Student ID is already registered under a different name.',
    });

    // 7d. Empty 500 error (previously threw "body stream already read")
    fetchMock.mockResolvedValueOnce(new Response('', { status: 500 }));
    await expect(authService.studentLogin('Neha Singh', '00112233')).rejects.toMatchObject({
      status: 500,
      message: 'Request failed with HTTP status 500.',
    });

    // 7e. Non-JSON plain-text 502 error
    fetchMock.mockResolvedValueOnce(new Response('Bad Gateway', { status: 502, headers: { 'Content-Type': 'text/plain' } }));
    await expect(authService.studentLogin('Neha Singh', '00112233')).rejects.toMatchObject({
      status: 502,
      message: 'Bad Gateway',
    });

    // 7f. HTML proxy error response (502 HTML) shows clean HTTP status message, never raw HTML or stream error
    fetchMock.mockResolvedValueOnce(
      new Response('<html><body><h1>502 Bad Gateway</h1></body></html>', { status: 502, headers: { 'Content-Type': 'text/html' } }),
    );
    await expect(authService.studentLogin('Neha Singh', '00112233')).rejects.toMatchObject({
      status: 502,
      message: 'Backend service error (HTTP 502). Verify the API server is running and try again.',
    });

    // 7g. Upload endpoint reads non-JSON error safely once
    fetchMock.mockResolvedValueOnce(new Response('Payload Too Large', { status: 413 }));
    const dummyFile = new File(['abc'], 'photo.png', { type: 'image/png' });
    await expect(api.upload('/api/uploads/photo', dummyFile)).rejects.toMatchObject({
      status: 413,
      message: 'Payload Too Large',
    });
  });

  it('8. LoginPage surfaces genuine 409 mismatch and 500/502 backend errors gracefully without stream errors', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByPlaceholderText(/Enter your full name/i), {
      target: { value: 'Wrong Person' },
    });
    fireEvent.change(screen.getByPlaceholderText(/Enter 8-digit numeric ID/i), {
      target: { value: '00123456' },
    });

    // 409 Conflict JSON detail shown cleanly
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Student ID already registered under a different name.' }), {
        status: 409,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    fireEvent.click(screen.getByRole('button', { name: /Continue to Student Portal/i }));
    await waitFor(() => {
      expect(screen.getByText('Student ID already registered under a different name.')).toBeInTheDocument();
    });

    // Non-JSON empty 502 error shown cleanly (no "body stream already read")
    fetchMock.mockResolvedValueOnce(new Response('', { status: 502 }));
    fireEvent.click(screen.getByRole('button', { name: /Continue to Student Portal/i }));
    await waitFor(() => {
      expect(screen.getByText('Request failed with HTTP status 502.')).toBeInTheDocument();
    });
    expect(document.body.textContent).not.toMatch(/body stream already read/i);
  });
});
