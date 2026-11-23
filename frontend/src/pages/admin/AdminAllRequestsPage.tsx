import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { taxonomyService } from '../../services/taxonomyService';
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
import type { ComplaintDetail, TaxonomyHierarchyResponse } from '../../types';
import {
  Search,
  Filter,
  Eye,
  Clock,
  User,
  Shield,
  Layers,
  Sparkles,
  MapPin,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Send,
} from 'lucide-react';

export const AdminAllRequestsPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintDetail[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters & Pagination
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('All Statuses');
  const [categoryFilter, setCategoryFilter] = useState<string>('All Categories');
  const [priorityFilter, setPriorityFilter] = useState<string>('All Priorities');
  const [sortBy, setSortBy] = useState<string>('Newest first');
  const [page, setPage] = useState<number>(0);
  const limit = 15;

  // Taxonomy for category options
  const [taxonomy, setTaxonomy] = useState<TaxonomyHierarchyResponse | null>(null);

  // Inspector Modal
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  // Status Update state in inspector
  const [newStatus, setNewStatus] = useState<any>('Assigned');
  const [updateRemarks, setUpdateRemarks] = useState<string>('');
  const [allottedPerson, setAllottedPerson] = useState<string>('');
  const [squadAssigned, setSquadAssigned] = useState<string>('');
  const [updating, setUpdating] = useState<boolean>(false);

  const fetchComplaints = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getAllAdminComplaints({
        search: search.trim() || undefined,
        status: statusFilter,
        category: categoryFilter,
        priority: priorityFilter,
        limit,
        offset: page * limit,
        sort_by: sortBy,
      });
      setComplaints(res.records);
      setTotalCount(res.total_count);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to query complaint ledger.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    taxonomyService.getHierarchy().then(setTaxonomy).catch(() => {});
  }, []);

  useEffect(() => {
    fetchComplaints();
  }, [statusFilter, categoryFilter, priorityFilter, sortBy, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchComplaints();
  };

  const openInspector = (ticket: ComplaintDetail) => {
    setSelectedTicket(ticket);
    setNewStatus(ticket.status === 'Resolved' ? 'Under Review' : 'In Progress');
    setAllottedPerson(ticket.allotted_person || '');
    setSquadAssigned(ticket.department || '');
    setUpdateRemarks('');
    setModalOpen(true);
  };

  const handleStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;

    setUpdating(true);
    setErrorMsg(null);
    try {
      const updated = await complaintService.updateComplaintStatus(selectedTicket.complaint_id, {
        status: newStatus,
        remarks: updateRemarks.trim() || undefined,
        allotted_person: allottedPerson.trim() || undefined,
        squad_assigned: squadAssigned.trim() || undefined,
      });
      setSelectedTicket(updated);
      setSuccessMsg(`Status for ${updated.complaint_id} updated to ${updated.status}.`);
      setUpdateRemarks('');
      fetchComplaints();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update ticket status.');
    } finally {
      setUpdating(false);
    }
  };

  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">All Requests Ledger</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Complete database of campus facility complaints with multi-criteria priority rankings.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setSearch('');
            setStatusFilter('All Statuses');
            setCategoryFilter('All Categories');
            setPriorityFilter('All Priorities');
            setPage(0);
          }}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Reset Filters
        </Button>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
      {successMsg && <Notification type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Filter Toolbar */}
      <Card className="p-4 bg-white border-[#DCE5D8]">
        <form onSubmit={handleSearchSubmit} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div className="lg:col-span-2">
              <Input
                placeholder="Search token (CMP-2026-...), title, student ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                leftIcon={<Search className="w-4 h-4" />}
              />
            </div>

            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(0);
              }}
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

            <Select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(0);
              }}
              options={[
                { value: 'All Categories', label: 'All Categories' },
                ...(taxonomy?.maintenance_categories.map((c) => ({ value: c, label: c })) || []),
              ]}
            />

            <Select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setPage(0);
              }}
              options={[
                { value: 'All Priorities', label: 'All Priorities' },
                { value: 'Critical', label: 'Critical' },
                { value: 'High', label: 'High' },
                { value: 'Medium', label: 'Medium' },
                { value: 'Low', label: 'Low' },
              ]}
            />
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-[#DCE5D8]/60 text-xs">
            <span className="text-[#52605B]">
              Showing <span className="font-semibold text-[#172D28]">{complaints.length}</span> of{' '}
              <span className="font-semibold text-[#172D28]">{totalCount}</span> total records
            </span>

            <div className="flex items-center gap-2">
              <span className="text-[#52605B]">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-transparent font-medium text-[#172D28] focus:outline-hidden cursor-pointer"
              >
                <option value="Newest first">Newest First</option>
                <option value="Oldest first">Oldest First</option>
                <option value="Highest priority">Highest Priority</option>
              </select>
            </div>
          </div>
        </form>
      </Card>

      {/* Ledger Table */}
      {loading ? (
        <LoadingSpinner label="Querying complaint ledger..." className="py-20" />
      ) : complaints.length === 0 ? (
        <EmptyState
          title="No Complaint Records Found"
          description="Try adjusting your search criteria or clearing active filters."
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Token</TableHead>
              <TableHead>Issue & Category</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Assigned To</TableHead>
              <TableHead>Reported</TableHead>
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
                <TableCell>
                  <Badge priority={ticket.priority_tier} />
                </TableCell>
                <TableCell>
                  <Badge status={ticket.status} />
                </TableCell>
                <TableCell className="text-xs text-[#52605B]">
                  {ticket.allotted_person || '—'}
                </TableCell>
                <TableCell className="text-xs text-[#52605B]">
                  {formatDate(ticket.date_reported)}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openInspector(ticket)}
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                  >
                    Inspect
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

      {/* Triage & Inspection Modal */}
      {selectedTicket && (
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={`Complaint Audit — ${selectedTicket.complaint_id}`}
          description="Operational triage, MCPI scoring breakdown, and maintenance squad assignment."
          maxWidth="2xl"
        >
          <div className="space-y-6">
            {/* Top Stat Ribbon */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] text-xs">
              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Status</span>
                <div className="mt-1">
                  <Badge status={selectedTicket.status} />
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Priority Tier</span>
                <div className="mt-1 flex items-center gap-1.5">
                  <Badge priority={selectedTicket.priority_tier} />
                  <span className="font-mono text-xs font-bold text-[#172D28]">
                    ({selectedTicket.priority_score.toFixed(1)})
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Reported By</span>
                <p className="font-semibold text-[#172D28] mt-1 truncate">
                  {selectedTicket.student_name || 'Resident'}
                </p>
                <p className="text-[10px] text-[#52605B] font-mono">{selectedTicket.student_id || '—'}</p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Date Reported</span>
                <p className="text-[#172D28] mt-1">{selectedTicket.date_reported}</p>
              </div>
            </div>

            {/* Location & Details */}
            <div className="p-3 rounded-lg border border-[#DCE5D8] space-y-1.5 text-xs">
              <span className="text-[10px] uppercase font-semibold text-[#52605B] flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-[#203A32]" /> Exact Campus Location
              </span>
              <p className="font-medium text-[#172D28]">{selectedTicket.location}</p>
              <div className="pt-2 border-t border-[#DCE5D8]/60">
                <span className="text-[10px] uppercase font-semibold text-[#52605B]">Description</span>
                <p className="text-[#172D28] mt-0.5 leading-relaxed">{selectedTicket.description}</p>
              </div>
            </div>

            {/* MCPI Score Breakdown */}
            {selectedTicket.score_breakdown && (
              <div className="p-3.5 rounded-xl border border-[#DCE5D8] bg-[#F5F7F2]/60 space-y-2">
                <span className="text-xs font-semibold text-[#172D28] uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#203A32]" /> MCPI Multi-Criteria Index Breakdown
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  {Object.entries(selectedTicket.score_breakdown).map(([k, v]) => (
                    <div key={k} className="p-2 rounded-lg bg-white border border-[#DCE5D8]">
                      <span className="text-[10px] text-[#52605B] block">{k}</span>
                      <span className="font-mono font-bold text-[#172D28]">{Number(v).toFixed(1)} pts</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action & Status Update Form */}
            <form onSubmit={handleStatusUpdate} className="p-4 rounded-xl border border-[#203A32]/20 bg-white space-y-3">
              <h4 className="text-xs font-semibold text-[#172D28] uppercase tracking-wider">
                Operational Triage & Status Update
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Select
                  label="Transition Status"
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  options={[
                    { value: 'Under Review', label: 'Under Review' },
                    { value: 'Assigned', label: 'Assigned' },
                    { value: 'In Progress', label: 'In Progress' },
                    { value: 'Resolved', label: 'Resolved' },
                  ]}
                />

                <Input
                  label="Assigned Lead"
                  placeholder="e.g. Ramesh Kumar"
                  value={allottedPerson}
                  onChange={(e) => setAllottedPerson(e.target.value)}
                />

                <Input
                  label="Squad / Division"
                  placeholder="e.g. Hostel Plumbing Squad"
                  value={squadAssigned}
                  onChange={(e) => setSquadAssigned(e.target.value)}
                />
              </div>

              <Input
                label="Triage / Resolution Remarks"
                placeholder="Log reason for status update, materials replaced, or inspection findings..."
                value={updateRemarks}
                onChange={(e) => setUpdateRemarks(e.target.value)}
              />

              <div className="flex justify-end pt-1">
                <Button type="submit" variant="primary" size="sm" isLoading={updating} leftIcon={<Send className="w-3.5 h-3.5" />}>
                  Save & Update Ticket
                </Button>
              </div>
            </form>

            {/* Remarks History */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-[#172D28] uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#203A32]" /> Audit Trail History ({selectedTicket.remarks_history.length})
              </h4>
              <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                {selectedTicket.remarks_history.map((entry, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg border border-[#DCE5D8] bg-[#F5F7F2]/40 text-xs space-y-0.5">
                    <div className="flex justify-between items-center text-[10px] text-[#52605B]">
                      <span className="font-semibold text-[#203A32]">{entry.name}</span>
                      <span>{entry.update_date}</span>
                    </div>
                    <p className="text-xs text-[#172D28]">{entry.remarks}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
