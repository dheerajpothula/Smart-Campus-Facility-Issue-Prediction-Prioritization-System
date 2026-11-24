import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { taxonomyService } from '../../services/taxonomyService';
import { Card } from '../../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Notification } from '../../components/ui/Notification';
import { ComplaintDetailsDrawer } from '../../components/admin/ComplaintDetailsDrawer';
import { formatDate } from '../../utils/formatters';
import type { ComplaintDetail, TaxonomyHierarchyResponse } from '../../types';
import {
  Search,
  Eye,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
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
  const [locationFilter, setLocationFilter] = useState<string>('All Locations');
  const [priorityFilter, setPriorityFilter] = useState<string>('All Priorities');
  const [sortBy, setSortBy] = useState<string>('Newest first');
  const [page, setPage] = useState<number>(0);
  const limit = 15;

  // Taxonomy for options
  const [taxonomy, setTaxonomy] = useState<TaxonomyHierarchyResponse | null>(null);

  // Inspector Drawer
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);

  const fetchComplaints = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await complaintService.getAllAdminComplaints({
        search: search.trim() || undefined,
        status: statusFilter !== 'All Statuses' ? statusFilter : undefined,
        category: categoryFilter !== 'All Categories' ? categoryFilter : undefined,
        location: locationFilter !== 'All Locations' ? locationFilter : undefined,
        priority: priorityFilter !== 'All Priorities' ? priorityFilter : undefined,
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
  }, [statusFilter, categoryFilter, locationFilter, priorityFilter, sortBy, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchComplaints();
  };

  const handleResetFilters = () => {
    setSearch('');
    setStatusFilter('All Statuses');
    setCategoryFilter('All Categories');
    setLocationFilter('All Locations');
    setPriorityFilter('All Priorities');
    setSortBy('Newest first');
    setPage(0);
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
          onClick={handleResetFilters}
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
            <div className="lg:col-span-1">
              <Input
                placeholder="Search token, title, student ID..."
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
              value={locationFilter}
              onChange={(e) => {
                setLocationFilter(e.target.value);
                setPage(0);
              }}
              options={[
                { value: 'All Locations', label: 'All Locations' },
                ...(taxonomy?.campus_blocks.map((b) => ({ value: b, label: b })) || []),
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
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedTicket(ticket);
                    }}
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

      {/* Inspection & Triage Drawer */}
      <ComplaintDetailsDrawer
        isOpen={!!selectedTicket}
        ticket={selectedTicket}
        onClose={() => setSelectedTicket(null)}
        onTicketUpdated={(updated) => {
          setSelectedTicket(updated);
          setSuccessMsg(`Ticket ${updated.complaint_id} updated successfully.`);
          fetchComplaints();
        }}
      />
    </div>
  );
};
