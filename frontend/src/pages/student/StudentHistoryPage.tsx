import React, { useEffect, useState, useMemo } from 'react';
import { complaintService } from '../../services/complaintService';
import { uploadService } from '../../services/uploadService';
import { TokenManager } from '../../services/apiClient';
import { Card } from '../../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Modal } from '../../components/ui/Modal';
import { EmptyState } from '../../components/ui/EmptyState';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Notification } from '../../components/ui/Notification';
import { formatDate } from '../../utils/formatters';
import type { ComplaintDetail, StudentComplaintListResponse } from '../../types';
import {
  Search,
  Eye,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  User,
  Star,
  MapPin,
  Image as ImageIcon,
  RotateCcw,
  Ban,
  Calendar,
} from 'lucide-react';

const LIFECYCLE_STAGES = [
  'Submitted',
  'Under Review',
  'Assigned',
  'In Progress',
  'Resolved',
];

const STAGE_ORDER: Record<string, number> = {
  Submitted: 1,
  'Under Review': 2,
  Assigned: 3,
  'In Progress': 4,
  Resolved: 5,
};

export const StudentHistoryPage: React.FC = () => {
  const [data, setData] = useState<StudentComplaintListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('All Statuses');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Details Modal
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);
  const [detailsModalOpen, setDetailsModalOpen] = useState<boolean>(false);

  // Withdrawal dialog state
  const [withdrawModalOpen, setWithdrawModalOpen] = useState<boolean>(false);
  const [withdrawReason, setWithdrawReason] = useState<string>('');
  const [withdrawing, setWithdrawing] = useState<boolean>(false);

  // Feedback form state
  const [feedbackRating, setFeedbackRating] = useState<number>(5);
  const [feedbackComments, setFeedbackComments] = useState<string>('');
  const [submittingFeedback, setSubmittingFeedback] = useState<boolean>(false);
  const [loadingPhoto, setLoadingPhoto] = useState<boolean>(false);

  const fetchHistory = async (keyword?: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getStudentComplaints(keyword);
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to retrieve complaint history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchHistory(search);
  };

  // Filter records by status locally (in addition to backend keyword search)
  const filteredRecords = useMemo(() => {
    if (!data?.records) return [];
    if (statusFilter === 'All Statuses') return data.records;
    return data.records.filter((r) => r.status.toLowerCase() === statusFilter.toLowerCase());
  }, [data?.records, statusFilter]);

  const openDetails = async (ticket: ComplaintDetail) => {
    setSelectedTicket(ticket);
    setDetailsModalOpen(true);
    // Refresh single ticket details from backend
    try {
      const fresh = await complaintService.getStudentComplaintDetails(ticket.complaint_id);
      setSelectedTicket(fresh);
    } catch {
      // Retain existing record if single fetch fails
    }
  };

  // Authenticated Attachment Retrieval
  const handleViewAttachment = async (storedFilename: string) => {
    setLoadingPhoto(true);
    setErrorMsg(null);
    try {
      const token = TokenManager.getAccessToken();
      const res = await fetch(uploadService.getPhotoUrl(storedFilename), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        throw new Error(`Unable to retrieve attachment (${res.status}).`);
      }
      const blob = await res.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      window.open(objectUrl, '_blank', 'noopener,noreferrer');
      setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to load attachment.');
    } finally {
      setLoadingPhoto(false);
    }
  };

  // Withdraw Query Handler
  const handleWithdraw = async () => {
    if (!selectedTicket) return;
    if (!withdrawReason.trim()) {
      setErrorMsg('Please specify a reason for withdrawing this request.');
      return;
    }
    setWithdrawing(true);
    setErrorMsg(null);
    try {
      await complaintService.withdrawComplaint(selectedTicket.complaint_id, withdrawReason.trim());
      setSuccessMsg(`Complaint ${selectedTicket.complaint_id} has been marked as Withdrawn.`);
      setWithdrawModalOpen(false);
      setDetailsModalOpen(false);
      setWithdrawReason('');
      fetchHistory(search);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to withdraw query.');
    } finally {
      setWithdrawing(false);
    }
  };

  // Submit Feedback Handler
  const handleFeedback = async () => {
    if (!selectedTicket) return;
    setSubmittingFeedback(true);
    setErrorMsg(null);
    try {
      await complaintService.submitFeedback(
        selectedTicket.complaint_id,
        feedbackRating,
        feedbackComments.trim() || undefined
      );
      setSuccessMsg('Thank you! Your resolution rating has been recorded.');
      // Refresh current ticket in modal
      const refreshed = await complaintService.getStudentComplaintDetails(selectedTicket.complaint_id);
      setSelectedTicket(refreshed);
      setFeedbackComments('');
      fetchHistory(search);
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to submit satisfaction rating.');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Search Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">Complaint History</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Monitor reported facility requests, live dispatch status, and resolution progress.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          {/* Status Filter Dropdown */}
          <div className="w-full sm:w-44">
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              options={[
                { value: 'All Statuses', label: 'All Statuses' },
                { value: 'Submitted', label: 'Submitted' },
                { value: 'Under Review', label: 'Under Review' },
                { value: 'Assigned', label: 'Assigned' },
                { value: 'In Progress', label: 'In Progress' },
                { value: 'Resolved', label: 'Resolved' },
                { value: 'Withdrawn', label: 'Withdrawn' },
              ]}
            />
          </div>

          <form onSubmit={handleSearch} className="flex gap-2 w-full sm:w-64">
            <Input
              placeholder="Search token, category, or title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
            <Button type="submit" variant="secondary" size="md">
              Filter
            </Button>
          </form>
        </div>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
      {successMsg && <Notification type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Total Queries</span>
          <p className="text-2xl font-bold text-[#172D28] mt-1">{data?.total_complaints ?? 0}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Active & In Progress</span>
          <p className="text-2xl font-bold text-amber-700 mt-1">{data?.open_complaints ?? 0}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Resolved / Closed</span>
          <p className="text-2xl font-bold text-emerald-700 mt-1">{data?.closed_complaints ?? 0}</p>
        </Card>
      </div>

      {/* History Ledger Table */}
      {loading ? (
        <LoadingSpinner label="Loading your complaint records..." className="py-16" />
      ) : !data || filteredRecords.length === 0 ? (
        <EmptyState
          title="No Complaint Records Found"
          description={
            search || statusFilter !== 'All Statuses'
              ? 'No requests match your search and filter criteria.'
              : 'You have not submitted any facility requests yet.'
          }
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Token</TableHead>
              <TableHead>Issue Title & Category</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Reported On</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredRecords.map((ticket) => (
              <TableRow key={ticket.complaint_id}>
                <TableCell className="font-mono text-xs font-bold text-[#203A32]">
                  {ticket.complaint_id}
                </TableCell>
                <TableCell>
                  <p className="font-semibold text-xs text-[#172D28] max-w-xs truncate">{ticket.title}</p>
                  <p className="text-[11px] text-[#52605B]">
                    {ticket.category} {ticket.sub_category && `› ${ticket.sub_category}`}
                  </p>
                </TableCell>
                <TableCell className="text-xs text-[#52605B] max-w-xs truncate">
                  {ticket.location}
                </TableCell>
                <TableCell className="text-xs text-[#52605B]">
                  {formatDate(ticket.date_reported)}
                </TableCell>
                <TableCell>
                  <Badge status={ticket.status} />
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openDetails(ticket)}
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                  >
                    View Details
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* COMPLAINT DETAILS & STATUS TIMELINE MODAL */}
      {/* --------------------------------------------------------------------- */}
      {selectedTicket && (
        <Modal
          isOpen={detailsModalOpen}
          onClose={() => setDetailsModalOpen(false)}
          title={`Ticket Details — ${selectedTicket.complaint_id}`}
          description={selectedTicket.title || selectedTicket.category}
          maxWidth="lg"
        >
          <div className="space-y-5">
            {/* 1. Core Header Attributes */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8]">
              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B] block">Current Status</span>
                <div className="mt-1">
                  <Badge status={selectedTicket.status} />
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B] block">Reported Date</span>
                <p className="text-xs font-semibold text-[#172D28] mt-1">{selectedTicket.date_reported}</p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B] block">Message Classification</span>
                <p className="text-xs font-semibold text-[#172D28] mt-1">
                  {selectedTicket.message_type || 'Grievance'}
                </p>
              </div>
            </div>

            {/* 2. Real Status Progression Timeline */}
            <div className="p-4 rounded-xl border border-[#DCE5D8] bg-white space-y-3">
              <span className="text-xs font-bold text-[#172D28] uppercase tracking-wider block">
                Official Complaint Lifecycle
              </span>

              {selectedTicket.status === 'Withdrawn' ? (
                /* Terminal Withdrawn State */
                <div className="p-3.5 rounded-lg border border-red-200 bg-red-50 text-red-900 flex items-start gap-3">
                  <Ban className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-semibold text-xs">Complaint Withdrawn by Student</h5>
                    <p className="text-xs text-red-800 mt-0.5">
                      This query was withdrawn by the ticket owner and marked terminal in the campus ledger.
                    </p>
                  </div>
                </div>
              ) : (
                /* 5-Stage Stepper */
                <div className="relative pt-2 pb-1">
                  <div className="grid grid-cols-5 gap-2 text-center">
                    {LIFECYCLE_STAGES.map((stage, idx) => {
                      const currentRank = STAGE_ORDER[selectedTicket.status] || 1;
                      const stageRank = STAGE_ORDER[stage];
                      const isCompleted = currentRank > stageRank || selectedTicket.status === stage;
                      const isCurrent = selectedTicket.status === stage;

                      // Find matching event timestamp from genuine status_history
                      const historyMatch = selectedTicket.status_history?.find(
                        (h) => h.status.toLowerCase() === stage.toLowerCase()
                      );

                      return (
                        <div key={stage} className="flex flex-col items-center space-y-1.5 relative">
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                              isCurrent
                                ? 'bg-[#203A32] text-white ring-4 ring-[#DCE5D8]'
                                : isCompleted
                                ? 'bg-[#DCE5D8] text-[#203A32]'
                                : 'bg-gray-100 text-gray-400 border border-gray-200'
                            }`}
                          >
                            {isCompleted && !isCurrent ? (
                              <CheckCircle2 className="w-4 h-4 text-[#203A32]" />
                            ) : (
                              idx + 1
                            )}
                          </div>
                          <span
                            className={`text-[11px] font-medium leading-tight ${
                              isCurrent
                                ? 'text-[#172D28] font-bold'
                                : isCompleted
                                ? 'text-[#203A32]'
                                : 'text-gray-400'
                            }`}
                          >
                            {stage}
                          </span>
                          {historyMatch && (historyMatch.timestamp || historyMatch.date) && (
                            <span className="text-[9px] text-[#52605B] font-mono leading-none">
                              {(historyMatch.timestamp || historyMatch.date || '').split('T')[0]}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* 3. Location & Availability Details */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg border border-[#DCE5D8] space-y-1 bg-[#F5F7F2]/40">
                <span className="text-[10px] uppercase font-semibold text-[#52605B] flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-[#203A32]" /> Campus Location
                </span>
                <p className="text-[#172D28] font-medium">{selectedTicket.location}</p>
                {selectedTicket.room_number && (
                  <p className="text-[11px] text-[#52605B]">Room / Unit: {selectedTicket.room_number}</p>
                )}
              </div>

              <div className="p-3 rounded-lg border border-[#DCE5D8] space-y-1 bg-[#F5F7F2]/40">
                <span className="text-[10px] uppercase font-semibold text-[#52605B] flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-[#203A32]" /> Preferred Availability
                </span>
                <p className="text-[#172D28] font-medium">
                  {selectedTicket.time_slot || 'General Working Hours'}
                </p>
                {selectedTicket.availability_date && (
                  <p className="text-[11px] text-[#52605B]">Date: {selectedTicket.availability_date}</p>
                )}
              </div>
            </div>

            {/* 4. Description */}
            <div className="p-3.5 rounded-lg border border-[#DCE5D8] bg-white space-y-1">
              <span className="text-[10px] uppercase font-semibold text-[#52605B] block">Description</span>
              <p className="text-xs text-[#172D28] leading-relaxed whitespace-pre-wrap">
                {selectedTicket.description}
              </p>
            </div>

            {/* 5. Attached Photo */}
            {selectedTicket.photo_stored_filename && (
              <div className="p-3 rounded-lg border border-[#DCE5D8] bg-[#F5F7F2]/60 flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 font-medium text-[#172D28]">
                  <ImageIcon className="w-4 h-4 text-[#203A32]" /> Attached Defect Photo
                </span>
                <button
                  type="button"
                  onClick={() => handleViewAttachment(selectedTicket.photo_stored_filename!)}
                  disabled={loadingPhoto}
                  className="text-xs font-semibold text-[#203A32] underline hover:text-[#172D28] cursor-pointer disabled:opacity-50"
                >
                  {loadingPhoto ? 'Opening...' : 'View Attachment'}
                </button>
              </div>
            )}

            {/* 6. Remarks Audit Trail */}
            {selectedTicket.remarks_history && selectedTicket.remarks_history.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-[#172D28] uppercase tracking-wider flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-[#203A32]" /> Facility Remarks Trail
                </h4>
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                  {selectedTicket.remarks_history.map((entry, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg border border-[#DCE5D8] bg-white text-xs space-y-1">
                      <div className="flex justify-between items-center text-[10px] text-[#52605B]">
                        <span className="font-semibold text-[#203A32]">{entry.name}</span>
                        <span>{entry.update_date}</span>
                      </div>
                      <p className="text-xs text-[#172D28]">{entry.remarks}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 7. Resolution Details (Only when actually resolved) */}
            {selectedTicket.status === 'Resolved' && (
              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-3">
                <h4 className="text-xs font-semibold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" /> Resolution Confirmation
                </h4>

                {(selectedTicket.resolved_at || selectedTicket.resolution_date) && (
                  <p className="text-xs text-emerald-900">
                    Resolved on: <strong>{selectedTicket.resolved_at || selectedTicket.resolution_date}</strong>
                  </p>
                )}

                {selectedTicket.closing_remarks && (
                  <p className="text-xs text-emerald-950 bg-white p-2.5 rounded-lg border border-emerald-200">
                    <strong>Resolution Summary:</strong> {selectedTicket.closing_remarks}
                  </p>
                )}

                {/* Feedback / Rating Section */}
                {selectedTicket.feedback ? (
                  <div className="p-3 rounded-lg bg-white border border-emerald-200 text-xs text-emerald-900 space-y-1">
                    <div className="flex items-center gap-1">
                      <span className="font-semibold">Recorded Rating:</span>
                      <div className="flex items-center">
                        {[1, 2, 3, 4, 5].map((s) => (
                          <Star
                            key={s}
                            className={`w-4 h-4 ${
                              s <= selectedTicket.feedback!.rating
                                ? 'fill-amber-400 text-amber-500'
                                : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-[11px] text-[#52605B] ml-1">
                        ({selectedTicket.feedback.rating}/5)
                      </span>
                    </div>
                    {selectedTicket.feedback.comments && (
                      <p className="italic text-[#52605B]">"{selectedTicket.feedback.comments}"</p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-2 pt-1 border-t border-emerald-200/60">
                    <span className="text-xs font-medium text-emerald-950 block">
                      Rate the maintenance resolution quality:
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            type="button"
                            onClick={() => setFeedbackRating(star)}
                            className="p-1 text-amber-500 hover:scale-110 transition-transform"
                          >
                            <Star
                              className={`w-5 h-5 ${
                                star <= feedbackRating ? 'fill-amber-400 text-amber-500' : 'text-gray-300'
                              }`}
                            />
                          </button>
                        ))}
                      </div>
                      <span className="text-xs font-mono text-[#52605B]">({feedbackRating} / 5 Stars)</span>
                    </div>
                    <Input
                      placeholder="Optional feedback comments regarding the work done..."
                      value={feedbackComments}
                      onChange={(e) => setFeedbackComments(e.target.value)}
                    />
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleFeedback}
                      isLoading={submittingFeedback}
                    >
                      Submit Satisfaction Rating
                    </Button>
                  </div>
                )}
              </div>
            )}

            {/* 8. Withdrawal Action (if Open & Not Withdrawn) */}
            {selectedTicket.status !== 'Resolved' && selectedTicket.status !== 'Withdrawn' && (
              <div className="pt-2 border-t border-[#DCE5D8] flex justify-between items-center">
                <span className="text-xs text-[#52605B]">Issue already fixed or raised by mistake?</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setWithdrawModalOpen(true)}
                  className="text-red-700 border-red-300 hover:bg-red-50"
                  leftIcon={<Ban className="w-3.5 h-3.5" />}
                >
                  Withdraw Query
                </Button>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* WITHDRAW CONFIRMATION MODAL */}
      {/* --------------------------------------------------------------------- */}
      <Modal
        isOpen={withdrawModalOpen}
        onClose={() => setWithdrawModalOpen(false)}
        title="Withdraw Facility Query"
        description="Are you sure you want to withdraw this request? This action will cancel technician dispatch."
        maxWidth="sm"
      >
        <div className="space-y-4">
          <Input
            label="Reason for Withdrawal (Mandatory)"
            placeholder="e.g. Fixed by resident, duplicate query lodged..."
            value={withdrawReason}
            onChange={(e) => setWithdrawReason(e.target.value)}
            required
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setWithdrawModalOpen(false)}>
              Keep Query Open
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleWithdraw}
              isLoading={withdrawing}
            >
              Confirm Withdrawal
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
