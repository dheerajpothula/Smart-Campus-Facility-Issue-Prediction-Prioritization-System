import React from 'react';
import { BrainCircuit, Info, AlertCircle } from 'lucide-react';
import { LoadingSpinner } from '../../ui/LoadingSpinner';
import type { ShapAvailabilityResponse } from '../../../types';

interface ShapExplainabilityCardProps {
  shap: ShapAvailabilityResponse | null;
  loading?: boolean;
  error?: string | null;
}

export const ShapExplainabilityCard: React.FC<ShapExplainabilityCardProps> = ({
  shap,
  loading = false,
  error = null,
}) => {
  return (
    <div
      className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-3"
      data-testid="shap-explainability-card"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider flex items-center gap-1.5">
          <BrainCircuit className="w-3.5 h-3.5 text-[#203A32]" />
          ML Prediction &amp; SHAP Explainability
        </span>
        <span
          className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
            shap?.available
              ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
              : 'bg-stone-100 text-stone-700 border-stone-200'
          }`}
        >
          {loading
            ? 'Checking Model Registry...'
            : shap?.available
            ? 'Model + SHAP Active'
            : 'Unavailable'}
        </span>
      </div>

      {loading ? (
        <LoadingSpinner label="Verifying ML model & SHAP availability..." className="py-4" />
      ) : error ? (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-900 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-700 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : shap?.available && shap.features.length > 0 ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="p-2 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">Model Prediction</span>
              <strong className="text-[#172D28]">{String(shap.prediction ?? '—')}</strong>
            </div>
            <div className="p-2 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">Base / Output</span>
              <strong className="font-mono text-[#172D28]">
                {shap.base_value ?? '—'} → {shap.output_value ?? '—'}
              </strong>
            </div>
            <div className="p-2 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">Model Version</span>
              <strong className="font-mono text-[#172D28]">{shap.model_version || '—'}</strong>
            </div>
            <div className="p-2 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8]">
              <span className="text-[10px] text-[#52605B] block">Predicted At</span>
              <strong className="font-mono text-[#172D28]">
                {shap.prediction_timestamp || '—'}
              </strong>
            </div>
          </div>

          <div className="space-y-2">
            {shap.features.map((feat) => {
              const isPos = feat.contribution === 'increase' || feat.shap_value >= 0;
              return (
                <div
                  key={feat.feature_name}
                  className="p-2.5 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] text-xs space-y-1"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-[#172D28]">
                      {feat.feature_name} ({String(feat.feature_value)})
                    </span>
                    <span
                      className={`font-mono font-bold ${
                        isPos ? 'text-amber-800' : 'text-emerald-800'
                      }`}
                    >
                      {feat.shap_value >= 0 ? `+${feat.shap_value}` : feat.shap_value} (
                      {isPos ? 'Positive' : 'Negative'})
                    </span>
                  </div>
                  <p className="text-[11px] text-[#52605B]">{feat.description}</p>
                </div>
              );
            })}
          </div>

          <p className="text-[11px] text-[#52605B] leading-relaxed">
            <strong>Model Note:</strong> {shap.summary} Statistical feature attributions describe model behavior and do not represent confirmed operational causation.
          </p>
        </div>
      ) : (
        <div className="p-3 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] space-y-2">
          <div className="flex items-start gap-2 text-xs text-[#172D28]">
            <Info className="w-4 h-4 text-[#203A32] shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold">
                SHAP Feature Attribution Unavailable
              </p>
              <p className="text-[#52605B] leading-relaxed">
                {shap?.reason ||
                  'No compatible trained ML model artifact or SHAP explainer is currently available for complaint-level attribution.'}
              </p>
              <p className="text-[11px] text-[#52605B]">
                Model Artifacts Present:{' '}
                <strong className="text-[#172D28]">
                  {shap?.model_artifact_present ? 'Yes' : 'No'}
                </strong>{' '}
                • SHAP Library Installed:{' '}
                <strong className="text-[#172D28]">
                  {shap?.shap_library_installed ? 'Yes' : 'No'}
                </strong>
                . Refer to the Rule-Based MCPI Breakdown above for deterministic score contributions.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
