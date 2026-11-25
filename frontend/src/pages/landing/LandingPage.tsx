import React from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { Footer } from '../../components/layout/Footer';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import {
  GraduationCap,
  ShieldCheck,
  CheckCircle2,
  Cpu,
  Clock,
  Layers,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#F5F7F2]">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Content */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#DCE5D8] border border-[#A8B9A3]/50 text-xs font-semibold text-[#203A32]">
                <Sparkles className="w-3.5 h-3.5 text-[#203A32]" />
                FIPP 2.0 Enterprise University Operations
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#172D28] leading-[1.15]">
                Facility Issue Prediction & Prioritisation Platform
              </h1>

              <p className="text-base sm:text-lg text-[#52605B] max-w-2xl leading-relaxed">
                An intelligent campus infrastructure operations system. Connects student facility requests directly to rapid dispatch squads with machine learning severity triage and multi-criteria priority scoring.
              </p>

              {/* Action Entry Points */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <Link to="/student" className="flex-1">
                  <div className="group p-5 rounded-xl border border-[#DCE5D8] bg-white hover:border-[#203A32] hover:shadow-md transition-all cursor-pointer">
                    <div className="flex items-center justify-between mb-3">
                      <div className="w-10 h-10 rounded-lg bg-[#DCE5D8] flex items-center justify-center text-[#203A32] group-hover:bg-[#203A32] group-hover:text-white transition-colors">
                        <GraduationCap className="w-5 h-5" />
                      </div>
                      <ArrowRight className="w-4 h-4 text-[#A8B9A3] group-hover:text-[#203A32] group-hover:translate-x-1 transition-all" />
                    </div>
                    <h3 className="font-semibold text-base text-[#172D28]">Student Portal</h3>
                    <p className="text-xs text-[#52605B] mt-1">
                      Raise facility requests, track work progress in real time, and verify completion.
                    </p>
                  </div>
                </Link>

                <Link to="/admin" className="flex-1">
                  <div className="group p-5 rounded-xl border border-[#DCE5D8] bg-white hover:border-[#203A32] hover:shadow-md transition-all cursor-pointer">
                    <div className="flex items-center justify-between mb-3">
                      <div className="w-10 h-10 rounded-lg bg-[#203A32] flex items-center justify-center text-white group-hover:bg-[#172D28] transition-colors">
                        <ShieldCheck className="w-5 h-5" />
                      </div>
                      <ArrowRight className="w-4 h-4 text-[#A8B9A3] group-hover:text-[#203A32] group-hover:translate-x-1 transition-all" />
                    </div>
                    <h3 className="font-semibold text-base text-[#172D28]">Admin Control Centre</h3>
                    <p className="text-xs text-[#52605B] mt-1">
                      Operational overview, squad dispatch, MCPI prioritization, and analytics ledger.
                    </p>
                  </div>
                </Link>
              </div>

              {/* Campus Trust Indicators */}
              <div className="pt-4 flex flex-wrap items-center gap-6 text-xs text-[#52605B]">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#203A32]" />
                  <span>19-Category LPU RMS Taxonomy</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#203A32]" />
                  <span>Multi-Criteria Prioritization (MCPI)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#203A32]" />
                  <span>Audit Trail & Reopening</span>
                </div>
              </div>
            </div>

            {/* Right Campus Hero Graphic */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md lg:max-w-none rounded-2xl border border-[#DCE5D8] bg-white shadow-xl overflow-hidden">
                {/* Visual Header */}
                <div className="bg-[#203A32] px-6 py-5 text-white flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm tracking-wide">Campus Facility Operations</h4>
                    <p className="text-[11px] text-[#A8B9A3]">Live Infrastructure Telemetry</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-xs font-mono text-emerald-200">Active</span>
                  </div>
                </div>

                {/* Dashboard Card Teaser */}
                <div className="p-6 space-y-4 bg-gradient-to-b from-white to-[#F5F7F2]">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-white border border-[#DCE5D8]">
                      <span className="text-[10px] uppercase font-semibold text-[#52605B]">Campus Blocks</span>
                      <p className="text-lg font-bold text-[#172D28] mt-0.5">38 Buildings</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white border border-[#DCE5D8]">
                      <span className="text-[10px] uppercase font-semibold text-[#52605B]">Classification</span>
                      <p className="text-lg font-bold text-[#172D28] mt-0.5">19 Categories</p>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-[#DCE5D8] bg-white space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-[#172D28]">MCPI Priority Engine</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        Operational
                      </span>
                    </div>
                    <p className="text-xs text-[#52605B] leading-relaxed">
                      Continuous evaluation across Severity (35%), Location Criticality (25%), Recurrence Risk (25%), and Population Footfall (15%).
                    </p>
                  </div>

                  <div className="p-4 rounded-xl border border-[#DCE5D8] bg-white space-y-2">
                    <span className="text-xs font-semibold text-[#172D28]">Operational Lifecycle</span>
                    <div className="grid grid-cols-5 gap-1 text-center text-[10px] font-medium text-[#52605B] pt-1">
                      <div className="p-1.5 bg-[#F5F7F2] rounded border border-[#DCE5D8]">Submitted</div>
                      <div className="p-1.5 bg-[#F5F7F2] rounded border border-[#DCE5D8]">Under Review</div>
                      <div className="p-1.5 bg-[#F5F7F2] rounded border border-[#DCE5D8]">Assigned</div>
                      <div className="p-1.5 bg-[#DCE5D8] rounded text-[#203A32] font-semibold">In Progress</div>
                      <div className="p-1.5 bg-emerald-50 rounded text-emerald-800 border border-emerald-200">Resolved</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* How FIPP Works Section */}
      <section className="py-16 bg-white border-y border-[#DCE5D8]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-[#172D28]">How FIPP Works</h2>
            <p className="text-sm text-[#52605B] mt-2">
              A structured university facility lifecycle bridging student feedback and operational engineering squads.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <Card className="relative p-6">
              <div className="w-12 h-12 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] flex items-center justify-center text-[#203A32] font-bold text-lg mb-4">
                1
              </div>
              <h3 className="text-base font-semibold text-[#172D28] mb-1">Report</h3>
              <p className="text-xs text-[#52605B] leading-relaxed">
                Collect campus facility complaints with cascading 19-category taxonomy, location coordinates, photos, and inspection time slots.
              </p>
            </Card>

            {/* Step 2 */}
            <Card className="relative p-6">
              <div className="w-12 h-12 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] flex items-center justify-center text-[#203A32] font-bold text-lg mb-4">
                2
              </div>
              <h3 className="text-base font-semibold text-[#172D28] mb-1">Analyze</h3>
              <p className="text-xs text-[#52605B] leading-relaxed">
                Evaluate facility issues using rule-based severity assessment, campus location criticality, recurrence tracking, and impact scaling.
              </p>
            </Card>

            {/* Step 3 */}
            <Card className="relative p-6">
              <div className="w-12 h-12 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] flex items-center justify-center text-[#203A32] font-bold text-lg mb-4">
                3
              </div>
              <h3 className="text-base font-semibold text-[#172D28] mb-1">Prioritize</h3>
              <p className="text-xs text-[#52605B] leading-relaxed">
                Support maintenance dispatch decisions with multi-criteria priority scoring (MCPI) to optimize technician workload.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section className="py-16 bg-[#F5F7F2]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#DCE5D8] flex items-center justify-center text-[#203A32]">
                <Cpu className="w-5 h-5" />
              </div>
              <h4 className="font-semibold text-sm text-[#172D28]">Rule-Based Triage &amp; MCPI</h4>
              <p className="text-xs text-[#52605B] leading-relaxed">
                Deterministic 4-factor priority scoring and 19-category LPU RMS taxonomy routing executing inside the Python backend.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#DCE5D8] flex items-center justify-center text-[#203A32]">
                <Layers className="w-5 h-5" />
              </div>
              <h4 className="font-semibold text-sm text-[#172D28]">Complete Audit History</h4>
              <p className="text-xs text-[#52605B] leading-relaxed">
                Every triage remark, squad allocation, resolution note, and reopening action is appended immutably.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-[#DCE5D8] flex items-center justify-center text-[#203A32]">
                <Clock className="w-5 h-5" />
              </div>
              <h4 className="font-semibold text-sm text-[#172D28]">Strict Student Isolation</h4>
              <p className="text-xs text-[#52605B] leading-relaxed">
                Students can only view and manage their own submissions. Internal scoring models remain protected.
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};
