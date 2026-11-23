import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Modal } from '../../components/ui/Modal';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Notification } from '../../components/ui/Notification';
import { formatDate } from '../../utils/formatters';
import type { ComplaintDetail } from '../../types';
import {
  CheckCircle2,
  RotateCcw,
  Star,
  Eye,
  RefreshCw,
  Send,
  Clock,
} from 'lucide-react';

export const AdminResolvedPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Details Modal
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);
  const [detailsModalOpen, setDetailsModalOpen] = useState<boolean>(false);

  // Reopen Modal
  const [reopenModalOpen, setReopenModalOpen] = useState<boolean>(false);
  const [reopenRemarks, setReopenRemarks] = useState<string>('');
  const [reopening, setReopening] = useState<boolean>(false);

  const fetchResolved = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getResolvedComplaints();
      setComplaints(res.records);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load resolved complaint records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResolved();
  }, []);

  const openReopenModal = (ticket: ComplaintDetail) => {
    setSelectedTicket(ticket);
    setReopenRemarks('Student reported defect reoccurred after technician departure.');
    setReopenModalOpen(true);
  };

  const handleReopenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;
    if (reopenRemarks.trim().length < 3) {
      setErrorMsg('Reopening remarks must be at least 3 characters.');
      return;
    }

    setReopening(true);
    setErrorMsg(null);
    try {
      await complaintService.reopenComplaint(selectedTicket.complaint_id, reopenRemarks.trim());
      setSuccessMsg(`Ticket ${selectedTicket.complaint_id} has been reopened and queued for review.`);
      setReopenModalOpen(false);
      setDetailsModalOpen(false);
      fetchResolved();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to reopen ticket.');
    } finally {
      setReopening(false);
    }
  };

  const ratedTickets = complaints.filter((c) => c.feedback?.rating);
  const averageRating =
    ratedTickets.length > 0
      ? (
          ratedTickets.reduce((acc, c) => acc + (c.feedback?.rating || 0), 0) / ratedTickets.length
        ).toFixed(1)
      : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">Resolved Complaint Archive</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Audit history of completed facility repairs, closing remarks, and student satisfaction ratings.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchResolved}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh
        </Button>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
      {successMsg && <Notification type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Total Completed</span>
          <p className="text-3xl font-bold text-emerald-700 mt-1">{complaints.length}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Average Student Rating</span>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-3xl font-bold text-[#172D28]">{averageRating || '—'}</p>
            {averageRating && <Star className="w-6 h-6 text-amber-500 fill-amber-400" />}
          </div>
        </Card>
      </div>

      {/* Resolved Archive Table */}
      {loading ? (
        <LoadingSpinner label="Loading resolved archives..." className="py-20" />
      ) : complaints.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 className="w-6 h-6 text-emerald-600" />}
          title="No Resolved Complaints in Archive"
          description="Resolved records will appear here as soon as active work orders are completed."
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Token</TableHead>
              <TableHead>Issue & Category</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Lead Technician</TableHead>
              <TableHead>Feedback</TableHead>
              <TableHead>Closing Date</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {complaints.map((ticket) => (
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
                  {ticket.allotted_person || 'Facility Squad'}
                </TableCell>
                <TableCell>
                  {ticket.feedback?.rating ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700">
                      <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" />
                      {ticket.feedback.rating} / 5
                    </span>
                  ) : (
                    <span className="text-xs text-[#52605B]">Pending</span>
                  )}
                </TableCell>
                <TableCell className="text-xs text-[#52605B]">
                  {ticket.resolved_at || formatDate(ticket.date_reported)}
                </TableCell>
                <TableCell className="text-right space-x-1.5">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedTicket(ticket);
                      setDetailsModalOpen(true);
                    }}
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                  >
                    Audit
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => openReopenModal(ticket)}
                    leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                  >
                    Reopen
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Details & Audit Modal */}
      {selectedTicket && (
        <Modal
          isOpen={detailsModalOpen}
          onClose={() => setDetailsModalOpen(false)}
          title={`Resolution Record — ${selectedTicket.complaint_id}`}
          description={`Completed work order details for: ${selectedTicket.title}`}
          maxWidth="lg"
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-950 space-y-1">
              <span className="text-[10px] uppercase font-semibold text-emerald-800">Final Closing Remarks</span>
              <p className="font-medium text-xs">
                {selectedTicket.closing_remarks || 'Work completed per standard operating procedure.'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-2.5 rounded-lg border border-[#DCE5D8]">
                <span className="text-[10px] text-[#52605B] block">Resolved Lead</span>
                <span className="font-semibold text-[#172D28]">
                  {selectedTicket.allotted_person || 'Assigned Squad'}
                </span>
              </div>
              <div className="p-2.5 rounded-lg border border-[#DCE5D8]">
                <span className="text-[10px] text-[#52605B] block">Completion Timestamp</span>
                <span className="font-semibold text-[#172D28]">{selectedTicket.resolved_at || 'Recorded'}</span>
              </div>
            </div>

            {/* Remarks History */}
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-semibold text-[#52605B]">Complete Remarks Log</span>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {selectedTicket.remarks_history.map((entry, idx) => (
                  <div key={idx} className="p-2 rounded border border-[#DCE5D8] bg-[#F5F7F2]/60 space-y-0.5">
                    <div className="flex justify-between text-[10px] text-[#52605B]">
                      <span className="font-semibold text-[#203A32]">{entry.name}</span>
                      <span>{entry.update_date}</span>
                    </div>
                    <p className="text-[#172D28]">{entry.remarks}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 border-t border-[#DCE5D8] flex justify-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setDetailsModalOpen(false);
                  openReopenModal(selectedTicket);
                }}
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
              >
                Reopen This Ticket
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Reopen Modal */}
      {selectedTicket && (
        <Modal
          isOpen={reopenModalOpen}
          onClose={() => setReopenModalOpen(false)}
          title={`Reopen Complaint ${selectedTicket.complaint_id}`}
          description="Ticket will transition to 'Under Review' and be re-queued for engineering inspection."
          maxWidth="md"
        >
          <form onSubmit={handleReopenSubmit} className="space-y-4">
            <Textarea
              label="Mandatory Reason for Reopening"
              placeholder="Specify resident complaint, incomplete work, or recurring defect..."
              value={reopenRemarks}
              onChange={(e) => setReopenRemarks(e.target.value)}
              rows={3}
              required
            />

            <div className="flex justify-end gap-2 pt-1">
              <Button variant="outline" size="sm" onClick={() => setReopenModalOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={reopening}
                leftIcon={<Send className="w-3.5 h-3.5" />}
              >
                Confirm Reopening
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
