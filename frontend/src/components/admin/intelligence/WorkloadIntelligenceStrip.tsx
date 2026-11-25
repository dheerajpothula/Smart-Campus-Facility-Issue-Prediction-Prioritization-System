import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/Card';
import { AlertTriangle, Clock, Users } from 'lucide-react';
import type { AnalyticsReportResponse } from '../../../types';

interface WorkloadIntelligenceStripProps {
  analytics: AnalyticsReportResponse | null;
}

const PRIORITY_ORDER = ['Critical', 'High', 'Medium', 'Low'] as const;

const PRIORITY_STYLES: Record<string, { badge: string; bar: string }> = {
  Critical: { badge: 'bg-red-100 text-red-900', bar: 'bg-red-600' },
  High: { badge: 'bg-orange-100 text-orange-900', bar: 'bg-orange-500' },
  Medium: { badge: 'bg-amber-100 text-amber-900', bar: 'bg-amber-500' },
  Low: { badge: 'bg-emerald-50 text-emerald-800', bar: 'bg-emerald-600' },
};

export const WorkloadIntelligenceStrip: React.FC<WorkloadIntelligenceStripProps> = ({
  analytics,
}) => {
  if (!analytics) return null;

  const total = analytics.kpis.total || 0;
  const prioDist = analytics.priority_distribution || {};
  const aging = analytics.aging_brackets || {};
  const workload = analytics.workload_summary;
  const avgMcpi = workload?.average_mcpi_score;
  const activeTotal = workload?.active_total ?? (analytics.kpis.new + analytics.kpis.in_progress);
  const unassignedActive = workload?.unassigned_active ?? analytics.kpis.new;
  const assignedActive = workload?.assigned_active ?? Math.max(0, activeTotal - unassignedActive);

  return (
    <div
      className="grid grid-cols-1 lg:grid-cols-3 gap-4"
      data-testid="workload-intelligence-strip"
    >
      {/* 1. Priority Distribution (Rule-Based MCPI) */}
      <Card className="bg-white border-[#DCE5D8]">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between w-full gap-2">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#172D28] flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-[#203A32]" />
              MCPI Priority Distribution
            </CardTitle>
            <span className="text-[10px] font-mono font-semibold text-[#52605B]">
              Avg MCPI: {avgMcpi !== null && avgMcpi !== undefined ? `${avgMcpi.toFixed(1)}` : 'Unavailable'}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-2.5 pt-2">
          {total === 0 ? (
            <p className="text-xs text-[#52605B] py-2">No persisted complaints available.</p>
          ) : (
            PRIORITY_ORDER.map((tier) => {
              const count = Number(prioDist[tier] || 0);
              const pct = total > 0 ? Math.round((count / total) * 100) : 0;
              const style = PRIORITY_STYLES[tier];
              return (
                <div key={tier} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${style.badge}`}>
                      {tier}
                    </span>
                    <span className="font-mono text-[11px] text-[#52605B]">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-[#EAEFE6] overflow-hidden">
                    <div
                      className={`h-full ${style.bar} rounded-full`}
                      style={{ width: `${count > 0 ? Math.max(4, pct) : 0}%` }}
                    />
                  </div>
                </div>
              );
            })
          )}
          <p className="text-[10px] text-[#52605B] pt-1 border-t border-[#DCE5D8]/60">
            Rule-based MCPI tiers across {total} persisted records.
          </p>
        </CardContent>
      </Card>

      {/* 2. Operational Workload Snapshot */}
      <Card className="bg-white border-[#DCE5D8]">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#172D28] flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-[#203A32]" />
            Operational Workload Balance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 pt-2">
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-2.5 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">Unassigned Staff</span>
              <strong className="text-base font-bold text-amber-700 font-mono">
                {unassignedActive} open
              </strong>
            </div>
            <div className="p-2.5 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">Assigned Staff</span>
              <strong className="text-base font-bold text-[#203A32] font-mono">
                {assignedActive} open
              </strong>
            </div>
            <div className="p-2.5 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">High / Critical Active</span>
              <strong className="text-base font-bold text-red-700 font-mono">
                {workload?.high_critical_active ?? 0} urgent
              </strong>
            </div>
            <div className="p-2.5 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">Reopened History</span>
              <strong className="text-base font-bold text-[#172D28] font-mono">
                {workload?.reopened_count ?? 0}{' '}
                {(workload?.reopened_count ?? 0) === 1 ? 'ticket' : 'tickets'}
              </strong>
            </div>
          </div>
          <p className="text-[10px] text-[#52605B] pt-1 border-t border-[#DCE5D8]/60">
            Confirmed operational counts from live complaint ledger.
          </p>
        </CardContent>
      </Card>

      {/* 3. Open Request Aging */}
      <Card className="bg-white border-[#DCE5D8]">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#172D28] flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-[#203A32]" />
            Open Queue Aging
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2.5 pt-2">
          {Object.keys(aging).length === 0 ? (
            <p className="text-xs text-[#52605B] py-2">No aging metrics available.</p>
          ) : (
            Object.entries(aging).map(([bracket, count]) => {
              const maxBracket = Math.max(...Object.values(aging).map(Number), 1);
              const pct = Math.round((Number(count) / maxBracket) * 100);
              return (
                <div key={bracket} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-[#172D28]">{bracket}</span>
                    <span className="font-mono text-[11px] text-[#52605B]">{count} active</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-[#EAEFE6] overflow-hidden">
                    <div
                      className="h-full bg-[#203A32] rounded-full"
                      style={{ width: `${Number(count) > 0 ? Math.max(4, pct) : 0}%` }}
                    />
                  </div>
                </div>
              );
            })
          )}
          <p className="text-[10px] text-[#52605B] pt-1 border-t border-[#DCE5D8]/60">
            Excludes Resolved, Withdrawn, and missing timestamps.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
