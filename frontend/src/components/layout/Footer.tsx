import React from 'react';
import { Building2, Shield, Lock, FileText } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-[#DCE5D8] bg-[#172D28] text-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand Col */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#203A32] border border-[#A8B9A3]/30 flex items-center justify-center">
                <Building2 className="w-4 h-4 text-[#DCE5D8]" />
              </div>
              <span className="font-bold text-base tracking-tight text-white">FIPP 2.0</span>
            </div>
            <p className="text-xs text-[#A8B9A3] max-w-md leading-relaxed">
              Facility Issue Prediction & Prioritisation Platform. Delivering AI-assisted predictive dispatch,
              multi-criteria prioritization (MCPI), and transparent facility workflow management across university campus infrastructure.
            </p>
            <div className="flex items-center gap-4 text-xs text-[#A8B9A3] pt-2">
              <span className="flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-[#DCE5D8]" /> ISO 27001 Aligned
              </span>
              <span className="flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-[#DCE5D8]" /> DPDP Act 2023 Compliant
              </span>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-3">
            <h5 className="text-xs font-semibold uppercase tracking-wider text-[#DCE5D8]">Portals</h5>
            <ul className="space-y-2 text-xs text-[#A8B9A3]">
              <li>
                <a href="/student" className="hover:text-white transition-colors">
                  Student Grievance Portal
                </a>
              </li>
              <li>
                <a href="/admin" className="hover:text-white transition-colors">
                  Administrator Control Centre
                </a>
              </li>
              <li>
                <a href="/login" className="hover:text-white transition-colors">
                  Campus Identity Sign In
                </a>
              </li>
            </ul>
          </div>

          {/* Governance & Privacy */}
          <div className="space-y-3">
            <h5 className="text-xs font-semibold uppercase tracking-wider text-[#DCE5D8]">Governance</h5>
            <ul className="space-y-2 text-xs text-[#A8B9A3]">
              <li className="flex items-center gap-1.5">
                <FileText className="w-3 h-3 text-[#A8B9A3]" />
                LPU RMS 19-Category Standard
              </li>
              <li>Audited PBKDF2-HMAC-SHA256 Auth</li>
              <li>Multi-Criteria Priority Index (MCPI)</li>
              <li>Campus Estate & Facilities Division</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-[#203A32] flex flex-col sm:flex-row items-center justify-between text-[11px] text-[#A8B9A3] gap-4">
          <p>© {new Date().getFullYear()} Campus Facilities Directorate. All rights reserved.</p>
          <p>FIPP 2.0 Dual-Engine Architecture (FastAPI REST Backend + Enterprise Frontend).</p>
        </div>
      </div>
    </footer>
  );
};
