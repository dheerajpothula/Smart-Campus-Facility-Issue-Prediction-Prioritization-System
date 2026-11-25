import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { Footer } from '../components/layout/Footer';
import { LoginPage } from '../pages/auth/LoginPage';
import { StudentHistoryPage } from '../pages/student/StudentHistoryPage';
import { authService } from '../services/authService';
import { uploadService } from '../services/uploadService';
import { complaintService } from '../services/complaintService';
import { api, TokenManager } from '../services/apiClient';
import type { ComplaintDetail } from '../types';

describe('FIPP 2.0 Phase 8 QA Frontend Regressions', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('1. Footer omits unverified ISO 27001 and DPDP Act 2023 compliance claims', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>,
    );

    const text = document.body.textContent || '';
    expect(text).not.toContain('ISO 27001');
    expect(text).not.toContain('DPDP Act 2023');
    expect(text).toContain('Role-Based Access Control');
    expect(text).toContain('PBKDF2 & JWT Session Security');
  });

  it('2. LoginPage hides Demo Credentials autofill buttons when VITE_ENABLE_DEMO_LOGIN=false', () => {
    vi.stubEnv('VITE_ENABLE_DEMO_LOGIN', 'false');

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.queryByText(/Demo Credentials/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Student Demo/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Admin Demo/i })).not.toBeInTheDocument();
  });

  it('3. authService.logout transmits refresh_token payload for server-side revocation', async () => {
    TokenManager.setSession('access-123', 'refresh-xyz', {
      id: 'STU-2026-001',
      name: 'Aarav Sharma',
      role: 'student',
    });

    const postSpy = vi.spyOn(api, 'post').mockResolvedValue({ success: true });
    await authService.logout();

    expect(postSpy).toHaveBeenCalledWith('/api/auth/logout', { refresh_token: 'refresh-xyz' });
    expect(TokenManager.getAccessToken()).toBeNull();
    expect(TokenManager.getRefreshToken()).toBeNull();
  });

  it('4. uploadService rejects WebP images client-side to match strict backend PNG/JPEG policy', async () => {
    const uploadSpy = vi.spyOn(api, 'upload');
    const webpFile = new File(['dummy'], 'photo.webp', { type: 'image/webp' });

    await expect(uploadService.uploadPhoto(webpFile)).rejects.toThrow(/Only JPEG and PNG/i);
    expect(uploadSpy).not.toHaveBeenCalled();

    uploadSpy.mockResolvedValue({
      success: true,
      original_filename: 'ok.png',
      stored_filename: 'ok_123.png',
      sha256: 'abc',
      size_bytes: 5,
      mime_type: 'image/png',
    });
    const pngFile = new File(['dummy'], 'ok.png', { type: 'image/png' });
    const res = await uploadService.uploadPhoto(pngFile);
    expect(res.stored_filename).toBe('ok_123.png');
    expect(uploadSpy).toHaveBeenCalledTimes(1);
  });

  it('5. StudentHistoryPage fetches photo attachment via Bearer token and displays resolved_at date', async () => {
    TokenManager.setSession('student-jwt-token', 'refresh-token', {
      id: 'STU-2026-001',
      name: 'Aarav Sharma',
      role: 'student',
    });

    const mockTicket: ComplaintDetail = {
      complaint_id: 'CMP-2026-099',
      student_id: 'STU-2026-001',
      student_name: 'Aarav Sharma',
      category_type: 'Maintenance / Electrical Complaints',
      message_type: 'Grievance',
      category: 'Electrical',
      sub_category: 'Lighting / Fixtures / Wiring',
      specific_categories: ['Tube light flickering'],
      facility_type: 'Electrical',
      building: 'BH-1',
      sub_block: 'Block A',
      room_type: 'Room No',
      room_number: '204',
      location: 'BH-1 - Block A - Room 204',
      contact_number: '9876543210',
      time_slot: '10:00 AM - 12:00 PM',
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
          name: 'ADM-2026-001',
          previous_status: 'In Progress',
          new_status: 'Resolved',
        },
      ],
    };

    vi.spyOn(complaintService, 'getStudentComplaints').mockResolvedValue({
      student_id: 'STU-2026-001',
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
    const revokeUrlSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);

    render(
      <MemoryRouter>
        <StudentHistoryPage />
      </MemoryRouter>,
    );

    const viewDetailsBtn = await screen.findByRole('button', { name: /View Details/i });
    fireEvent.click(viewDetailsBtn);

    await waitFor(() => {
      expect(screen.getByText(/Resolved on:/i)).toBeInTheDocument();
    });

    const viewAttachmentBtn = screen.getByRole('button', { name: /View Attachment/i });
    fireEvent.click(viewAttachmentBtn);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/uploads/CMP_2026_099_evidence.png',
        expect.objectContaining({
          headers: { Authorization: 'Bearer student-jwt-token' },
        }),
      );
      expect(createUrlSpy).toHaveBeenCalledWith(blob);
      expect(openSpy).toHaveBeenCalledWith('blob:mock-photo-url', '_blank', 'noopener,noreferrer');
    });
    expect(revokeUrlSpy).not.toThrow();
  });
});
