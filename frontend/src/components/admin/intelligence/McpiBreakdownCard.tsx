import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { Badge } from '../../ui/Badge';
import type { ComplaintDetail, McpiExplanation } from '../../../types';

interface McpiBreakdownCardProps {
  ticket: ComplaintDetail;
  mcpiDetails?: McpiExplanation | null;
}

const DEFAULT_THRESHOLDS = [
  { tier: 'Critical', rule: '>= 75.0', min_score: 75.0 },
  { tier: 'High', rule: '50.0 – 74.9', min_score: 50.0 },
  { tier: 'Medium', rule: '28.0 – 49.9', min_score: 28.0 },
  { tier: 'Low', rule: '< 28.0', min_score: 0.0 },
];

export const McpiBreakdownCard: React.FC<McpiBreakdownCardProps> = ({
  ticket,
  mcpiDetails,
}) => {
  const details = mcpiDetails || ticket.mcpi_details;
  const score = details ? details.priority_score : Number(ticket.priority_score ?? 0);
  const tier = details ? details.priority_tier : ticket.priority_tier;
  const thresholds = details?.thresholds || DEFAULT_THRESHOLDS;

  const fallbackEntries = ticket.score_breakdown
    ? Object.entries(ticket.score_breakdown)
    : [];
  const isLegacyRatio =
    fallbackEntries.length > 0 &&
    fallbackEntries.every(([, v]) => Number(v) <= 1.0);

  return (
    <div
      className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-3"
      data-testid="mcpi-breakdown-card"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-[#203A32]" />
            Multi-Criteria Priority (MCPI)
          </span>
          <span
            className="px-2 py-0.5 rounded-md bg-[#F5F7F2] border border-[#DCE5D8] text-[10px] font-semibold text-[#203A32]"
            title="MCPI is a deterministic rule-based weighted score, not an ML prediction."
          >
            Rule-Based Scoring (Non-ML)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Badge priority={tier} />
          <span className="text-xs font-mono font-bold text-[#172D28]">
            Score: {score.toFixed(1)} / 100
          </span>
        </div>
      </div>

      {/* Component Contributions */}
      {details?.components && details.components.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
          {details.components.map((comp) => {
            const fillPct =
              comp.max_points > 0
                ? Math.min(100, Math.max(4, (comp.points / comp.max_points) * 100))
                : 0;
            return (
              <div
                key={comp.key}
                className="p-2.5 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] uppercase font-semibold text-[#52605B] truncate">
                    {comp.label} (wt {comp.weight.toFixed(2)})
                  </span>
                  <span className="text-xs font-bold text-[#172D28] font-mono shrink-0">
                    {comp.points.toFixed(1)} pts
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[#DCE5D8] overflow-hidden">
                  <div
                    className="h-full bg-[#203A32] rounded-full"
                    style={{ width: `${comp.points > 0 ? fillPct : 0}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] text-[#52605B]">
                  <span className="truncate" title={comp.raw_label}>
                    Input: <strong className="text-[#172D28]">{comp.raw_label}</strong>
                  </span>
                  <span className="font-mono shrink-0">
                    max {comp.max_points.toFixed(0)} pts
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        fallbackEntries.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
            {fallbackEntries.map(([k, val]) => (
              <div
                key={k}
                className="p-2 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] text-center"
              >
                <span
                  className="text-[9px] uppercase font-semibold text-[#52605B] block truncate"
                  title={k}
                >
                  {k
                    .replace('weight_', '')
                    .replace(' Contribution', '')
                    .replace(/_/g, ' ')}
                </span>
                <span className="text-xs font-bold text-[#172D28] font-mono mt-0.5 block">
                  {isLegacyRatio
                    ? `${(Number(val) * 100).toFixed(0)}%`
                    : `${Number(val).toFixed(1)} pts`}
                </span>
              </div>
            ))}
          </div>
        )
      )}

      {/* Priority Thresholds & Rationale */}
      <div className="pt-2 border-t border-[#DCE5D8]/70 space-y-2">
        <div className="flex flex-wrap gap-1.5">
          {thresholds.map((t) => {
            const isActive = t.tier.toLowerCase() === String(tier).toLowerCase();
            return (
              <span
                key={t.tier}
                className={`px-2 py-0.5 rounded-md text-[10px] font-mono border ${
                  isActive
                    ? 'bg-[#203A32] text-white border-[#203A32] font-bold'
                    : 'bg-[#F5F7F2] text-[#52605B] border-[#DCE5D8]'
                }`}
              >
                {t.tier}: {t.rule}
              </span>
            );
          })}
        </div>
        <p className="text-[11px] text-[#52605B] leading-relaxed flex items-start gap-1.5">
          <Info className="w-3.5 h-3.5 text-[#203A32] shrink-0 mt-0.5" />
          <span>
            {details?.classification_rationale ||
              `Composite MCPI score of ${score.toFixed(
                1
              )} / 100 maps to '${tier}' under authoritative weights (0.35 Severity, 0.25 Location, 0.25 Recurrence, 0.15 Impact).`}
          </span>
        </p>
      </div>
    </div>
  );
};
