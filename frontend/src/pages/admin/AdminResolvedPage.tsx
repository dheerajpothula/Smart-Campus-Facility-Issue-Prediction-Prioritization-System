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
import { formatDateTime } from '../../utils/formatters';
import type { ComplaintDetail } from '../../types';
import {
  CheckCircle2,
  Star,
  Eye,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export const AdminResolvedPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintDetail[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const limit = 50;
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Inspector & Reopen Drawer
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);

  const fetchResolved = async (silent = false) => {
    if (!silent) setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getResolvedComplaints(limit, page * limit);
      setComplaints(res.records);
      setTotalCount(res.total_count);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load resolved complaint records.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchResolved();
  }, [page]);

  const totalPages = Math.ceil(totalCount / limit);

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
          onClick={() => fetchResolved(false)}
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
          <p className="text-3xl font-bold text-emerald-700 mt-1">{totalCount || complaints.length}</p>
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
                <TableCell className="text-xs text-[#52605B]">
                  {ticket.allotted_person || ticket.department || '—'}
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
                  {ticket.resolved_at ? formatDateTime(ticket.resolved_at) : '—'}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedTicket(ticket);
                    }}
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                  >
                    Audit / Reopen
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

      {/* Resolution Details & Reopen Drawer */}
      <ComplaintDetailsDrawer
        isOpen={!!selectedTicket}
        ticket={selectedTicket}
        onClose={() => setSelectedTicket(null)}
        onTicketUpdated={(updated) => {
          setSelectedTicket(updated);
          setSuccessMsg(`Ticket ${updated.complaint_id} updated/reopened successfully.`);
          fetchResolved(true);
        }}
      />
    </div>
  );
};
