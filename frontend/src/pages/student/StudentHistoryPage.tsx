import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { uploadService } from '../../services/uploadService';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Modal } from '../../components/ui/Modal';
import { EmptyState } from '../../components/ui/EmptyState';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Notification } from '../../components/ui/Notification';
import { formatDate, formatDateTime } from '../../utils/formatters';
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
  CornerUpLeft,
  Calendar,
  MapPin,
  Image as ImageIcon,
} from 'lucide-react';

export const StudentHistoryPage: React.FC = () => {
  const [data, setData] = useState<StudentComplaintListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
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

  const fetchHistory = async (keyword?: string) => {
    setLoading(true);
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

  const openDetails = async (ticket: ComplaintDetail) => {
    setSelectedTicket(ticket);
    setDetailsModalOpen(true);
    // Refresh single ticket details
    try {
      const fresh = await complaintService.getStudentComplaintDetails(ticket.complaint_id);
      setSelectedTicket(fresh);
    } catch {
      // Use cached if fetch fails
    }
  };

  // Withdraw Query Handler
  const handleWithdraw = async () => {
    if (!selectedTicket) return;
    setWithdrawing(true);
    setErrorMsg(null);
    try {
      await complaintService.withdrawComplaint(selectedTicket.complaint_id, withdrawReason);
      setSuccessMsg(`Complaint ${selectedTicket.complaint_id} has been withdrawn.`);
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
        feedbackComments
      );
      setSuccessMsg('Thank you! Your feedback has been recorded.');
      setDetailsModalOpen(false);
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
            Track and monitor the status of your reported campus maintenance requests.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2 w-full sm:w-72">
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

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
      {successMsg && <Notification type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Total Filed</span>
          <p className="text-2xl font-bold text-[#172D28] mt-1">{data?.total_complaints ?? 0}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Open & Active</span>
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
      ) : !data || data.records.length === 0 ? (
        <EmptyState
          title="No Complaint Records Found"
          description={search ? 'No requests match your search criteria.' : 'You have not submitted any facility requests yet.'}
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
            {data.records.map((ticket) => (
              <TableRow key={ticket.complaint_id}>
                <TableCell className="font-mono text-xs font-bold text-[#203A32]">
                  {ticket.complaint_id}
                </TableCell>
                <TableCell>
                  <p className="font-semibold text-xs text-[#172D28] max-w-xs truncate">{ticket.title}</p>
                  <p className="text-[11px] text-[#52605B]">{ticket.category}</p>
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
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Complaint Inspection Modal */}
      {selectedTicket && (
        <Modal
          isOpen={detailsModalOpen}
          onClose={() => setDetailsModalOpen(false)}
          title={`Ticket Details — ${selectedTicket.complaint_id}`}
          description="Detailed progress, technician dispatch status, and audit history."
          maxWidth="lg"
        >
          <div className="space-y-5">
            {/* Top Status & Core Attributes */}
            <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Current Lifecycle</span>
                <div className="mt-0.5">
                  <Badge status={selectedTicket.status} />
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Reported Date</span>
                <p className="text-xs font-semibold text-[#172D28] mt-0.5">{selectedTicket.date_reported}</p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Estimated Turnaround</span>
                <p className="text-xs text-[#172D28] mt-0.5">{selectedTicket.estimated_resolution || '24-48 Hours'}</p>
              </div>
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg border border-[#DCE5D8] space-y-1">
                <span className="text-[10px] uppercase font-semibold text-[#52605B] flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-[#203A32]" /> Location
                </span>
                <p className="text-[#172D28] font-medium">{selectedTicket.location}</p>
              </div>

              <div className="p-3 rounded-lg border border-[#DCE5D8] space-y-1">
                <span className="text-[10px] uppercase font-semibold text-[#52605B] flex items-center gap-1">
                  <User className="w-3.5 h-3.5 text-[#203A32]" /> Assigned Personnel
                </span>
                <p className="text-[#172D28] font-medium">
                  {selectedTicket.allotted_person
                    ? `${selectedTicket.allotted_person} (${selectedTicket.department || 'Squad'})`
                    : 'Queued for Squad Allocation'}
                </p>
              </div>
            </div>

            {/* Description */}
            <div className="p-3 rounded-lg border border-[#DCE5D8] bg-white space-y-1">
              <span className="text-[10px] uppercase font-semibold text-[#52605B]">Issue Description</span>
              <p className="text-xs text-[#172D28] leading-relaxed">{selectedTicket.description}</p>
            </div>

            {/* Attached Photo */}
            {selectedTicket.photo_stored_filename && (
              <div className="p-3 rounded-lg border border-[#DCE5D8] bg-[#F5F7F2]/60 flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 font-medium text-[#172D28]">
                  <ImageIcon className="w-4 h-4 text-[#203A32]" /> Attached Defect Photo
                </span>
                <a
                  href={uploadService.getPhotoUrl(selectedTicket.photo_stored_filename)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs font-semibold text-[#203A32] underline hover:text-[#172D28]"
                >
                  View Attachment
                </a>
              </div>
            )}

            {/* Remarks Audit History */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-[#172D28] uppercase tracking-wider flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-[#203A32]" /> Action & Triage Trail
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
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

            {/* Feedback / Rating Section if Resolved */}
            {selectedTicket.status === 'Resolved' && (
              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-3">
                <h4 className="text-xs font-semibold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                  <Star className="w-4 h-4 text-emerald-700" /> Resolution Feedback
                </h4>

                {selectedTicket.feedback ? (
                  <div className="text-xs text-emerald-900 space-y-1">
                    <p className="font-semibold">Rating: {selectedTicket.feedback.rating} / 5 Stars</p>
                    {selectedTicket.feedback.comments && <p>"{selectedTicket.feedback.comments}"</p>}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-emerald-900 font-medium">Your Rating:</span>
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
                    </div>
                    <Input
                      placeholder="Optional comments on maintenance resolution..."
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

            {/* Withdrawal Option if Open */}
            {selectedTicket.status !== 'Resolved' && selectedTicket.status !== 'Withdrawn' && (
              <div className="pt-2 border-t border-[#DCE5D8] flex justify-between items-center">
                <span className="text-xs text-[#52605B]">Issue already fixed or raised by mistake?</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setWithdrawModalOpen(true)}
                  className="text-red-700 border-red-300 hover:bg-red-50"
                >
                  Withdraw Query
                </Button>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Withdraw Confirmation Dialog */}
      <Modal
        isOpen={withdrawModalOpen}
        onClose={() => setWithdrawModalOpen(false)}
        title="Withdraw Complaint"
        description="Are you sure you want to withdraw this facility request?"
        maxWidth="sm"
      >
        <div className="space-y-4">
          <Input
            label="Reason for withdrawal"
            placeholder="e.g. Fixed by resident, duplicate ticket"
            value={withdrawReason}
            onChange={(e) => setWithdrawReason(e.target.value)}
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setWithdrawModalOpen(false)}>
              Cancel
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
