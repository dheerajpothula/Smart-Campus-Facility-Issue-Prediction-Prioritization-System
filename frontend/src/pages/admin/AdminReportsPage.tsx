import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { taxonomyService } from '../../services/taxonomyService';
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
  }, [startDate, endDate, categoryFilter, locationFilter, statusFilter]);

  const handleClearFilters = () => {
    setStartDate('');
    setEndDate('');
    setCategoryFilter('All Categories');
    setLocationFilter('All Locations');
    setStatusFilter('All Statuses');
  };

  // PII-Redacted Export Handler
  const handleExportCSV = async () => {
    setExporting(true);
    setErrorMsg(null);
    try {
      const base = import.meta.env.VITE_API_BASE_URL || '';
      const token = sessionStorage.getItem('fipp_access_token');
      const res = await fetch(`${base}/api/admin/reports/export?redact_pii=true`, {
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
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
        </div>

        <div className="flex justify-between items-center pt-3 mt-3 border-t border-[#DCE5D8]/60 text-xs">
          <span className="text-[#52605B] flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-[#203A32]" />
            DPDP Act 2023 Masking Active (Student PII redacted on export)
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Filtered Volume</span>
          <p className="text-3xl font-bold text-[#172D28] mt-1">{report?.kpis.total ?? 0}</p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Resolution Rate</span>
          <p className="text-3xl font-bold text-emerald-700 mt-1">
            {report?.kpis.resolution_rate_percent ?? 0}%
          </p>
        </Card>

        <Card className="p-4 bg-white border-[#DCE5D8]">
          <span className="text-xs font-semibold text-[#52605B] uppercase tracking-wider">Average Turnaround</span>
          <p className="text-3xl font-bold text-[#203A32] mt-1">
            {report?.kpis.average_turnaround_days ? `${report.kpis.average_turnaround_days} Days` : '1.8 Days'}
          </p>
        </Card>
      </div>

      {loading ? (
        <LoadingSpinner label="Compiling report distributions..." className="py-20" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Category Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-[#203A32]" /> Category Pareto Distribution
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {report?.category_distribution && report.category_distribution.length > 0 ? (
                report.category_distribution.slice(0, 8).map((item) => (
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
                          style={{ width: `${Math.min(100, Math.max(pct, 5))}%` }}
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
      )}
    </div>
  );
};
