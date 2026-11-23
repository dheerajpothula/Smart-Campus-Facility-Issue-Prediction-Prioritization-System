import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Modal } from '../../components/ui/Modal';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Notification } from '../../components/ui/Notification';
import { formatDate } from '../../utils/formatters';
import type { ComplaintDetail } from '../../types';
import {
  Inbox,
  UserCheck,
  Send,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';

export const AdminUnassignedPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Assign Modal
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);
  const [assignModalOpen, setAssignModalOpen] = useState<boolean>(false);
  const [allottedPerson, setAllottedPerson] = useState<string>('');
  const [squadAssigned, setSquadAssigned] = useState<string>('');
  const [remarks, setRemarks] = useState<string>('');
  const [assigning, setAssigning] = useState<boolean>(false);

  const fetchUnassigned = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getUnassignedComplaints();
      setComplaints(res.records);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load unassigned complaints.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnassigned();
  }, []);

  const openAssignModal = (ticket: ComplaintDetail) => {
    setSelectedTicket(ticket);
    setAllottedPerson('');
    setSquadAssigned('Campus Rapid Response Squad');
    setRemarks('Assigned to maintenance squad for physical inspection.');
    setAssignModalOpen(true);
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;

    setAssigning(true);
    setErrorMsg(null);
    try {
      await complaintService.updateComplaintStatus(selectedTicket.complaint_id, {
        status: 'Assigned',
        remarks: remarks.trim() || undefined,
        allotted_person: allottedPerson.trim() || undefined,
        squad_assigned: squadAssigned.trim() || undefined,
      });
      setSuccessMsg(`Ticket ${selectedTicket.complaint_id} assigned successfully.`);
      setAssignModalOpen(false);
      fetchUnassigned();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to assign complaint.');
    } finally {
      setAssigning(false);
    }
  };

  const criticalCount = complaints.filter(
    (c) => c.priority_tier === 'Critical' || c.priority_tier === 'High'
  ).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">New / Unassigned Requests</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Incoming facility queries awaiting initial evaluation, squad assignment, and work order dispatch.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchUnassigned}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh
        </Button>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
      {successMsg && <Notification type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Metric Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Awaiting Triage</span>
          <p className="text-3xl font-bold text-amber-700 mt-1">{complaints.length}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">High & Critical Hazard</span>
          <p className="text-3xl font-bold text-red-700 mt-1">{criticalCount}</p>
        </Card>
      </div>

      {/* Queue Table */}
      {loading ? (
        <LoadingSpinner label="Fetching unassigned complaint queue..." className="py-20" />
      ) : complaints.length === 0 ? (
        <EmptyState
          icon={<Inbox className="w-6 h-6 text-emerald-600" />}
          title="Queue Clear — All Complaints Assigned"
          description="There are currently no new unassigned complaints requiring triage."
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Token</TableHead>
              <TableHead>Issue & Category</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Reported By</TableHead>
              <TableHead>Date Reported</TableHead>
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
                <TableCell className="text-xs text-[#52605B]">
                  {ticket.student_name || 'Resident'}
                </TableCell>
                <TableCell className="text-xs text-[#52605B]">
                  {formatDate(ticket.date_reported)}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => openAssignModal(ticket)}
                    leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                  >
                    Triage & Assign
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Assign Modal */}
      {selectedTicket && (
        <Modal
          isOpen={assignModalOpen}
          onClose={() => setAssignModalOpen(false)}
          title={`Assign Complaint ${selectedTicket.complaint_id}`}
          description={`Dispatch maintenance crew for: ${selectedTicket.title}`}
          maxWidth="md"
        >
          <form onSubmit={handleAssignSubmit} className="space-y-4">
            <div className="p-3 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] text-xs space-y-1">
              <span className="text-[10px] uppercase font-semibold text-[#52605B]">Location</span>
              <p className="font-medium text-[#172D28]">{selectedTicket.location}</p>
              <span className="text-[10px] uppercase font-semibold text-[#52605B] block pt-1">Description</span>
              <p className="text-[#172D28]">{selectedTicket.description}</p>
            </div>

            <Input
              label="Assigned Lead Technician"
              placeholder="e.g. Ramesh Kumar (Senior Electrician)"
              value={allottedPerson}
              onChange={(e) => setAllottedPerson(e.target.value)}
              required
            />

            <Input
              label="Department / Squad"
              placeholder="e.g. Electrical Maintenance Squad"
              value={squadAssigned}
              onChange={(e) => setSquadAssigned(e.target.value)}
              required
            />

            <Input
              label="Initial Triage Remarks"
              placeholder="Instructions or remarks for technician..."
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setAssignModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={assigning} leftIcon={<Send className="w-3.5 h-3.5" />}>
                Confirm Assignment
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
