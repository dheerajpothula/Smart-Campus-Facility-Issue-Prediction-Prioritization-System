import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { taxonomyService } from '../../services/taxonomyService';
import { TokenManager } from '../../services/apiClient';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Notification } from '../../components/ui/Notification';
import type { AnalyticsReportResponse, TaxonomyHierarchyResponse } from '../../types';
import {
  Download,
  Calendar,
  Filter,
  BarChart2,
  TrendingUp,
  Clock,
  Shield,
  RefreshCw,
  FileSpreadsheet,
  Building,
  AlertTriangle,
  CheckCircle2,
  Layers,
} from 'lucide-react';

export const AdminReportsPage: React.FC = () => {
  const [report, setReport] = useState<AnalyticsReportResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('All Categories');
  const [locationFilter, setLocationFilter] = useState<string>('All Locations');
  const [statusFilter, setStatusFilter] = useState<string>('All Statuses');
  const [trendAgg, setTrendAgg] = useState<'Daily' | 'Weekly' | 'Monthly'>('Daily');

  // Taxonomy
  const [taxonomy, setTaxonomy] = useState<TaxonomyHierarchyResponse | null>(null);

  // Export State
  const [exporting, setExporting] = useState<boolean>(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await complaintService.getAnalyticsReport({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        category: categoryFilter !== 'All Categories' ? categoryFilter : undefined,
        location: locationFilter !== 'All Locations' ? locationFilter : undefined,
        status: statusFilter !== 'All Statuses' ? statusFilter : undefined,
        trend_agg: trendAgg,
      });
      setReport(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate operational analytics report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    taxonomyService.getHierarchy().then(setTaxonomy).catch(() => {});
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [startDate, endDate, categoryFilter, locationFilter, statusFilter, trendAgg]);

  const handleClearFilters = () => {
    setStartDate('');
    setEndDate('');
    setCategoryFilter('All Categories');
    setLocationFilter('All Locations');
    setStatusFilter('All Statuses');
    setTrendAgg('Daily');
  };

  // Masked-Identifier Export Handler respecting active filters
  const handleExportCSV = async () => {
    setExporting(true);
    setErrorMsg(null);
    try {
      const base = import.meta.env.VITE_API_BASE_URL || '';
      const token = TokenManager.getAccessToken();
      const q = new URLSearchParams({ redact_pii: 'true' });
      if (startDate) q.append('start_date', startDate);
      if (endDate) q.append('end_date', endDate);
      if (categoryFilter !== 'All Categories') q.append('category', categoryFilter);
      if (locationFilter !== 'All Locations') q.append('location', locationFilter);
      if (statusFilter !== 'All Statuses') q.append('status', statusFilter);

      const res = await fetch(`${base}/api/admin/reports/export?${q.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!res.ok) {
        throw new Error('Export download failed.');
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fipp_operational_ledger_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to download PII-redacted CSV ledger.');
    } finally {
      setExporting(false);
    }
  };

  const priorityColors: Record<string, { bg: string; text: string; bar: string }> = {
    Critical: { bg: 'bg-red-50', text: 'text-red-800', bar: 'bg-red-600' },
    High: { bg: 'bg-amber-50', text: 'text-amber-800', bar: 'bg-amber-500' },
    Medium: { bg: 'bg-blue-50', text: 'text-blue-800', bar: 'bg-blue-500' },
    Low: { bg: 'bg-gray-50', text: 'text-gray-800', bar: 'bg-gray-400' },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">Reports & Analytics</h1>
          <p className="text-xs text-[#52605B] mt-0.5">
            Operational complaint volume, turnaround timelines, category distributions, and compliance export.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAnalytics}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleExportCSV}
            isLoading={exporting}
            leftIcon={<FileSpreadsheet className="w-3.5 h-3.5" />}
          >
            Export CSV (PII Redacted)
          </Button>
        </div>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      {/* Filter Ribbon */}
      <Card className="p-4 bg-white border-[#DCE5D8]">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <Input
            label="From Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />

          <Input
            label="To Date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />

          <Select
            label="Category"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            options={[
              { value: 'All Categories', label: 'All Categories' },
              ...(taxonomy?.maintenance_categories.map((c) => ({ value: c, label: c })) || []),
            ]}
          />

          <Select
            label="Campus Block"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            options={[
              { value: 'All Locations', label: 'All Locations' },
              ...(taxonomy?.campus_blocks.map((b) => ({ value: b, label: b })) || []),
            ]}
          />

          <Select
            label="Status"
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

          <Select
            label="Trend Grouping"
            value={trendAgg}
            onChange={(e) => setTrendAgg(e.target.value as 'Daily' | 'Weekly' | 'Monthly')}
            options={[
              { value: 'Daily', label: 'Daily Trends' },
              { value: 'Weekly', label: 'Weekly Summary' },
              { value: 'Monthly', label: 'Monthly Aggregate' },
            ]}
          />
        </div>

        <div className="flex justify-between items-center pt-3 mt-3 border-t border-[#DCE5D8]/60 text-xs">
          <span className="text-[#52605B] flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-[#203A32]" />
            Direct student identifiers (ID, name, phone) masked on CSV export
          </span>

          <button
            onClick={handleClearFilters}
            className="text-xs font-semibold text-[#203A32] hover:underline cursor-pointer"
          >
            Clear Active Filters
          </button>
        </div>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Filtered Volume</span>
          <p className="text-3xl font-bold text-[#172D28] mt-1">{report?.kpis.total ?? 0}</p>
          <span className="text-[11px] text-[#52605B] mt-1 block">Total incident entries</span>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Resolution Rate</span>
          <p className="text-3xl font-bold text-emerald-700 mt-1">
            {report?.kpis.resolution_rate_percent ?? 0}%
          </p>
          <span className="text-[11px] text-[#52605B] mt-1 block">
            {report?.kpis.resolved ?? 0} resolved
            {(report?.kpis.withdrawn ?? 0) > 0
              ? ` (${report?.kpis.withdrawn} withdrawn excluded)`
              : ' records'}
          </span>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Average Turnaround</span>
          <p className="text-3xl font-bold text-[#203A32] mt-1">
            {report?.kpis.average_turnaround_days !== null &&
            report?.kpis.average_turnaround_days !== undefined
              ? `${report.kpis.average_turnaround_days} Days`
              : 'Unavailable'}
          </p>
          <span className="text-[11px] text-[#52605B] mt-1 block">From report to resolution</span>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Active In-Flight</span>
          <p className="text-3xl font-bold text-amber-700 mt-1">
            {(report?.kpis.in_progress ?? 0) + (report?.kpis.new ?? 0)}
          </p>
          <span className="text-[11px] text-[#52605B] mt-1 block">
            {report?.kpis.new ?? 0} unassigned, {report?.kpis.in_progress ?? 0} in progress
          </span>
        </Card>
      </div>

      {loading ? (
        <LoadingSpinner label="Compiling report distributions..." className="py-20" />
      ) : (
        <div className="space-y-6">
          {/* Trend Breakdown Chart */}
          {report?.trends && report.trends.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between w-full">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#203A32]" />
                    Incident Volume & Resolution Velocity ({trendAgg.toUpperCase()})
                  </CardTitle>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="flex items-center gap-1.5 text-[#172D28]">
                      <span className="w-3 h-3 rounded-xs bg-[#203A32]" /> Reported
                    </span>
                    <span className="flex items-center gap-1.5 text-emerald-800">
                      <span className="w-3 h-3 rounded-xs bg-emerald-600" /> Resolved
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-48 flex items-end gap-2 pt-6 pb-2 overflow-x-auto">
                  {(() => {
                    const maxVal = Math.max(
                      ...report.trends.map((t) => Math.max(t.reported_count, t.resolved_count)),
                      1
                    );
                    return report.trends.map((t, idx) => {
                      const repHeight = Math.round((t.reported_count / maxVal) * 100);
                      const resHeight = Math.round((t.resolved_count / maxVal) * 100);
                      return (
                        <div key={idx} className="flex-1 min-w-[36px] flex flex-col items-center gap-1 h-full justify-end">
                          <div className="w-full flex items-end justify-center gap-1 h-36">
                            <div
                              className="w-1/2 bg-[#203A32] rounded-t-xs transition-all hover:bg-[#172D28]"
                              style={{ height: `${Math.max(repHeight, 4)}%` }}
                              title={`Reported: ${t.reported_count}`}
                            />
                            <div
                              className="w-1/2 bg-emerald-600 rounded-t-xs transition-all hover:bg-emerald-700"
                              style={{ height: `${Math.max(resHeight, 4)}%` }}
                              title={`Resolved: ${t.resolved_count}`}
                            />
                          </div>
                          <span className="text-[10px] font-mono text-[#52605B] truncate w-full text-center">
                            {trendAgg === 'Daily' ? t.period.slice(5) : t.period}
                          </span>
                        </div>
                      );
                    });
                  })()}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 4-way analytical breakdown grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Category Pareto Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-[#203A32]" /> Category Pareto Distribution
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {report?.category_distribution && report.category_distribution.length > 0 ? (
                  report.category_distribution.slice(0, 7).map((item) => (
                    <div key={item.category} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-medium text-[#172D28] truncate max-w-xs">{item.category}</span>
                        <span className="font-mono text-[#52605B]">
                          {item.count} tickets ({item.percentage}%)
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-[#EAEFE6] overflow-hidden">
                        <div
                          className="h-full bg-[#203A32] rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(item.percentage, 5))}%` }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-[#52605B]">No category distribution data for selected filter.</p>
                )}
              </CardContent>
            </Card>

            {/* Campus Location Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Building className="w-4 h-4 text-[#203A32]" /> Campus Location & Infrastructure Hotspots
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {report?.location_distribution && report.location_distribution.length > 0 ? (
                  report.location_distribution.slice(0, 7).map((locItem, idx) => {
                    const locName = locItem.location || locItem.building || `Zone ${idx + 1}`;
                    const count = locItem.count || 0;
                    const pct = locItem.percentage ?? Math.round((count / (report.kpis.total || 1)) * 100);
                    return (
                      <div key={locName} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium text-[#172D28] truncate max-w-xs">{locName}</span>
                          <span className="font-mono text-[#52605B]">
                            {count} tickets ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-[#EAEFE6] overflow-hidden">
                          <div
                            className="h-full bg-[#172D28] rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, Math.max(pct, 5))}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-[#52605B]">No campus location data for selected filter.</p>
                )}
              </CardContent>
            </Card>

            {/* Multi-Criteria Priority Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#203A32]" /> Priority Hazard Index Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {report?.priority_distribution ? (
                  Object.entries(report.priority_distribution).map(([tier, count]) => {
                    const total = report.kpis.total || 1;
                    const pct = Math.round((Number(count) / total) * 100);
                    const colorScheme = priorityColors[tier] || priorityColors.Low;
                    return (
                      <div key={tier} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className={`font-semibold px-2 py-0.5 rounded-md text-[11px] ${colorScheme.bg} ${colorScheme.text}`}>
                            {tier}
                          </span>
                          <span className="font-mono text-[#52605B] font-semibold">
                            {count} tickets ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-[#EAEFE6] overflow-hidden">
                          <div
                            className={`h-full ${colorScheme.bar} rounded-full transition-all duration-500`}
                            style={{ width: `${Number(count) > 0 ? Math.min(100, Math.max(pct, 4)) : 0}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-[#52605B]">No priority distribution data available.</p>
                )}
              </CardContent>
            </Card>

            {/* Ticket Aging Brackets */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="w-4 h-4 text-[#203A32]" /> Work Order Aging Brackets
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {report?.aging_brackets ? (
                  Object.entries(report.aging_brackets).map(([bracket, count]) => {
                    const maxCount = Math.max(...Object.values(report.aging_brackets), 1);
                    const pct = Math.round((Number(count) / maxCount) * 100);
                    return (
                      <div key={bracket} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium text-[#172D28]">{bracket}</span>
                          <span className="font-mono text-[#52605B] font-semibold">{count} active</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-[#EAEFE6] overflow-hidden">
                          <div
                            className="h-full bg-[#A8B9A3] rounded-full transition-all duration-500"
                            style={{ width: `${Number(count) > 0 ? Math.min(100, Math.max(pct, 5)) : 0}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-[#52605B]">No aging data available.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
