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
  Clock,
  CheckCircle2,
  User,
  Wrench,
  RefreshCw,
  Send,
} from 'lucide-react';

export const AdminInProgressPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Resolve Modal
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);
  const [resolveModalOpen, setResolveModalOpen] = useState<boolean>(false);
  const [closingRemarks, setClosingRemarks] = useState<string>('');
  const [resolving, setResolving] = useState<boolean>(false);

  const fetchInProgress = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getInProgressComplaints();
      setComplaints(res.records);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load active work orders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInProgress();
  }, []);

  const openResolveModal = (ticket: ComplaintDetail) => {
    setSelectedTicket(ticket);
    setClosingRemarks('Issue resolved on-site. Defective component replaced and tested operational.');
    setResolveModalOpen(true);
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;
    if (!closingRemarks.trim()) {
      setErrorMsg('Closing remarks detailing the repair are mandatory.');
      return;
    }

    setResolving(true);
    setErrorMsg(null);
    try {
      await complaintService.updateComplaintStatus(selectedTicket.complaint_id, {
        status: 'Resolved',
        remarks: closingRemarks.trim(),
      });
      setSuccessMsg(`Complaint ${selectedTicket.complaint_id} marked as Resolved.`);
      setResolveModalOpen(false);
      fetchInProgress();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to complete resolution.');
    } finally {
      setResolving(false);
    }
  };

  const assignedCount = complaints.filter((c) => c.status === 'Assigned').length;
  const inProgressCount = complaints.filter((c) => c.status === 'In Progress').length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">In Progress Work Orders</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Active facility maintenance operations currently being executed by campus engineering squads.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchInProgress}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh
        </Button>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
      {successMsg && <Notification type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Metric Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Total Active Orders</span>
          <p className="text-3xl font-bold text-[#172D28] mt-1">{complaints.length}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Under Physical Repair</span>
          <p className="text-3xl font-bold text-[#203A32] mt-1">{inProgressCount}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Squad Dispatched</span>
          <p className="text-3xl font-bold text-amber-700 mt-1">{assignedCount}</p>
        </Card>
      </div>

      {/* Work Orders Table */}
      {loading ? (
        <LoadingSpinner label="Loading active work orders..." className="py-20" />
      ) : complaints.length === 0 ? (
        <EmptyState
          icon={<Clock className="w-6 h-6 text-[#203A32]" />}
          title="No Work Orders Currently In Progress"
          description="All assigned work orders have been resolved or are awaiting squad allocation."
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Token</TableHead>
              <TableHead>Issue & Category</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Lead Technician</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Action</TableHead>
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
                <TableCell>
                  <Badge priority={ticket.priority_tier} />
                </TableCell>
                <TableCell className="text-xs text-[#172D28] font-medium">
                  {ticket.allotted_person || 'Assigned Squad'}
                </TableCell>
                <TableCell>
                  <Badge status={ticket.status} />
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => openResolveModal(ticket)}
                    leftIcon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />}
                  >
                    Complete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Complete Resolution Modal */}
      {selectedTicket && (
        <Modal
          isOpen={resolveModalOpen}
          onClose={() => setResolveModalOpen(false)}
          title={`Complete Work Order — ${selectedTicket.complaint_id}`}
          description={`Record final repair details for: ${selectedTicket.title}`}
          maxWidth="md"
        >
          <form onSubmit={handleResolveSubmit} className="space-y-4">
            <div className="p-3 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] text-xs space-y-1">
              <span className="text-[10px] uppercase font-semibold text-[#52605B]">Location</span>
              <p className="font-medium text-[#172D28]">{selectedTicket.location}</p>
              <span className="text-[10px] uppercase font-semibold text-[#52605B] block pt-1">Assigned Lead</span>
              <p className="text-[#172D28]">{selectedTicket.allotted_person || 'Facility Squad'}</p>
            </div>

            <Textarea
              label="Mandatory Resolution Remarks"
              placeholder="Detail actions taken, repairs performed, and parts replaced..."
              value={closingRemarks}
              onChange={(e) => setClosingRemarks(e.target.value)}
              rows={3}
              required
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setResolveModalOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={resolving}
                leftIcon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />}
              >
                Mark as Resolved
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
