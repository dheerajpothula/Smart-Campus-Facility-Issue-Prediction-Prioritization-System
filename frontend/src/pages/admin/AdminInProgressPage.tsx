import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { Card } from '../../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Notification } from '../../components/ui/Notification';
import { ComplaintDetailsDrawer } from '../../components/admin/ComplaintDetailsDrawer';
import { formatDate } from '../../utils/formatters';
import type { ComplaintDetail } from '../../types';
import {
  Clock,
  Wrench,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export const AdminInProgressPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintDetail[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const limit = 50;
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Inspector & Resolution Drawer
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);

  const fetchInProgress = async (silent = false) => {
    if (!silent) setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getInProgressComplaints(limit, page * limit);
      setComplaints(res.records);
      setTotalCount(res.total_count);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load active work orders.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchInProgress();
  }, [page]);

  const totalPages = Math.ceil(totalCount / limit);

  const assignedCount = complaints.filter((c) => c.status === 'Assigned').length;
  const inProgressCount = complaints.filter((c) => c.status === 'In Progress').length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">In Progress Work Orders</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Dispatched work orders with status &ldquo;Assigned&rdquo; or &ldquo;In Progress&rdquo; (&ldquo;Under Review&rdquo; tickets are managed in All Requests).
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => fetchInProgress(false)}
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
          <p className="text-3xl font-bold text-[#172D28] mt-1">{totalCount || complaints.length}</p>
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
              <TableRow
                key={ticket.complaint_id}
                onClick={() => setSelectedTicket(ticket)}
                className="cursor-pointer hover:bg-[#F5F7F2]/80 transition-colors"
              >
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
                  {ticket.allotted_person || ticket.department || 'Unassigned'}
                </TableCell>
                <TableCell>
                  <Badge status={ticket.status} />
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedTicket(ticket);
                    }}
                    leftIcon={<Wrench className="w-3.5 h-3.5" />}
                  >
                    Inspect & Manage
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-[#52605B] pt-2">
          <span>Page {page + 1} of {totalPages}</span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Details & Resolution Drawer */}
      <ComplaintDetailsDrawer
        isOpen={!!selectedTicket}
        ticket={selectedTicket}
        onClose={() => setSelectedTicket(null)}
        onTicketUpdated={(updated) => {
          setSelectedTicket(updated);
          setSuccessMsg(`Ticket ${updated.complaint_id} updated to "${updated.status}".`);
          fetchInProgress(true);
        }}
      />
    </div>
  );
};
