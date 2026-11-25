import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { complaintService } from '../../services/complaintService';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Notification } from '../../components/ui/Notification';
import { ComplaintDetailsDrawer } from '../../components/admin/ComplaintDetailsDrawer';
import { formatDate } from '../../utils/formatters';
import type { ComplaintDetail, DashboardKPIs } from '../../types';
import {
  Inbox,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Building,
  RefreshCw,
  Eye,
} from 'lucide-react';

export const AdminOverviewPage: React.FC = () => {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [recentComplaints, setRecentComplaints] = useState<ComplaintDetail[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<ComplaintDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchOverviewData = async (silent = false) => {
    if (!silent) setLoading(true);
    setErrorMsg(null);
    try {
      const [kpiRes, listRes] = await Promise.all([
        complaintService.getAdminKPIs(),
        complaintService.getAllAdminComplaints({ limit: 6 }),
      ]);
      setKpis(kpiRes);
      setRecentComplaints(listRes.records);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch operational overview metrics.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverviewData();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Compiling live campus facility metrics..." className="py-24" />;
  }

  return (
    <div className="space-y-6">
      {/* Page Title & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">Executive Operations Overview</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Real-time infrastructure health, operational queues, and priority incident triage.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => fetchOverviewData(false)}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh Data
        </Button>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Requests */}
        <Link to="/admin/all-requests">
          <Card className="p-5 bg-white border-[#DCE5D8] hover:border-[#203A32] transition-colors cursor-pointer h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Total Ledger</span>
              <Building className="w-4 h-4 text-[#A8B9A3]" />
            </div>
            <p className="text-3xl font-bold text-[#172D28] mt-2">{kpis?.total ?? 0}</p>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-[#52605B]">
              <TrendingUp className="w-3.5 h-3.5 text-[#203A32]" />
              <span>Resolution Rate: {kpis?.resolution_rate_percent ?? 0}%</span>
            </div>
          </Card>
        </Link>

        {/* New / Unassigned */}
        <Link to="/admin/unassigned">
          <Card className="p-5 bg-white border-[#DCE5D8] hover:border-[#203A32] transition-colors cursor-pointer h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">New / Unassigned</span>
              <Inbox className="w-4 h-4 text-amber-600" />
            </div>
            <p className="text-3xl font-bold text-amber-700 mt-2">{kpis?.new ?? 0}</p>
            <div className="mt-3 flex items-center justify-between text-xs text-[#52605B]">
              <span>Requires Triage</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#A8B9A3]" />
            </div>
          </Card>
        </Link>

        {/* In Progress */}
        <Link to="/admin/in-progress">
          <Card className="p-5 bg-white border-[#DCE5D8] hover:border-[#203A32] transition-colors cursor-pointer h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">In Progress</span>
              <Clock className="w-4 h-4 text-blue-600" />
            </div>
            <p className="text-3xl font-bold text-[#203A32] mt-2">{kpis?.in_progress ?? 0}</p>
            <div className="mt-3 flex items-center justify-between text-xs text-[#52605B]">
              <span>Active Work Orders</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#A8B9A3]" />
            </div>
          </Card>
        </Link>

        {/* Resolved */}
        <Link to="/admin/resolved">
          <Card className="p-5 bg-white border-[#DCE5D8] hover:border-[#203A32] transition-colors cursor-pointer h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Resolved</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <p className="text-3xl font-bold text-emerald-700 mt-2">{kpis?.resolved ?? 0}</p>
            <div className="mt-3 flex items-center justify-between text-xs text-[#52605B]">
              <span>Completed Works</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#A8B9A3]" />
            </div>
          </Card>
        </Link>
      </div>

      {/* Recent Incident Ledger */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Recent Facility Requests</CardTitle>
            <p className="text-xs text-[#52605B]">Latest submissions queued into the campus ticketing ledger</p>
          </div>
          <Link to="/admin/all-requests">
            <Button variant="outline" size="sm">
              View All Requests
            </Button>
          </Link>
        </CardHeader>

        <CardContent className="p-0">
          {recentComplaints.length === 0 ? (
            <EmptyState
              title="No Facility Requests Recorded"
              description="Recent campus complaints will appear here once submitted."
              className="m-4"
            />
          ) : (
            <Table className="border-0 shadow-none">
              <TableHeader>
                <TableRow>
                  <TableHead>Token</TableHead>
                  <TableHead>Issue & Category</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Reported</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentComplaints.map((ticket) => (
                  <TableRow
                    key={ticket.complaint_id}
                    onClick={() => setSelectedTicket(ticket)}
                    className="cursor-pointer hover:bg-[#F5F7F2]/80 transition-colors"
                  >
                    <TableCell className="font-mono text-xs font-bold text-[#203A32]">
                      {ticket.complaint_id}
                    </TableCell>
                    <TableCell>
                      <p className="font-semibold text-xs text-[#172D28] max-w-[210px] truncate">{ticket.title}</p>
                      <p className="text-[11px] text-[#52605B] max-w-[210px] truncate">{ticket.category}</p>
                    </TableCell>
                    <TableCell className="text-xs text-[#52605B] max-w-[170px] truncate">
                      {ticket.location}
                    </TableCell>
                    <TableCell>
                      <Badge priority={ticket.priority_tier} />
                    </TableCell>
                    <TableCell>
                      <Badge status={ticket.status} />
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
        </CardContent>
      </Card>

      {/* Details & Triage Drawer */}
      <ComplaintDetailsDrawer
        isOpen={!!selectedTicket}
        ticket={selectedTicket}
        onClose={() => setSelectedTicket(null)}
        onTicketUpdated={(updated) => {
          setSelectedTicket(updated);
          fetchOverviewData(true);
        }}
      />
    </div>
  );
};
