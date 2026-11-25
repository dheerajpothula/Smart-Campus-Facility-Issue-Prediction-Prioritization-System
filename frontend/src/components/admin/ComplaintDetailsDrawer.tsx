import React, { useState, useEffect } from 'react';
import { complaintService } from '../../services/complaintService';
import { uploadService } from '../../services/uploadService';
import { TokenManager } from '../../services/apiClient';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import { Notification } from '../ui/Notification';
import { formatDate, formatDateTime } from '../../utils/formatters';
import type { ComplaintDetail } from '../../types';
import {
  X,
  User,
  MapPin,
  Calendar,
  Clock,
  Phone,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Send,
  RotateCcw,
  Star,
  Shield,
  Layers,
  Wrench,
  Check,
  Ban,
  ExternalLink,
} from 'lucide-react';

interface ComplaintDetailsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  ticket: ComplaintDetail | null;
  onTicketUpdated: (updated: ComplaintDetail) => void;
}

const STAGES = ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved'] as const;
const STAGE_ORDER: Record<string, number> = {
  Submitted: 1,
  'Under Review': 2,
  Assigned: 3,
  'In Progress': 4,
  Resolved: 5,
};

export const ComplaintDetailsDrawer: React.FC<ComplaintDetailsDrawerProps> = ({
  isOpen,
  onClose,
  ticket,
  onTicketUpdated,
}) => {
  // Status & action state (hooks must always run unconditionally)
  const [newStatus, setNewStatus] = useState<any>(ticket?.status || 'Submitted');
  const [allottedPerson, setAllottedPerson] = useState<string>(ticket?.allotted_person || '');
  const [squadAssigned, setSquadAssigned] = useState<string>(ticket?.department || '');
  const [remarks, setRemarks] = useState<string>('');

  // Reopen state
  const [isReopening, setIsReopening] = useState<boolean>(false);
  const [reopenRemarks, setReopenRemarks] = useState<string>('');

  // Loading & notification state
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [loadingPhoto, setLoadingPhoto] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Sync state whenever selected ticket changes
  useEffect(() => {
    if (ticket) {
      setNewStatus(ticket.status === 'Resolved' ? 'Resolved' : ticket.status);
      setAllottedPerson(ticket.allotted_person || '');
      setSquadAssigned(ticket.department || '');
      setRemarks('');
      setIsReopening(false);
      setReopenRemarks('');
      setErrorMsg(null);
      setSuccessMsg(null);
    }
  }, [ticket]);

  // Close drawer on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !ticket) return null;

  // Authenticated attachment retrieval
  const handleViewAttachment = async () => {
    if (!ticket.photo_stored_filename) return;
    setLoadingPhoto(true);
    setErrorMsg(null);
    try {
      const token = TokenManager.getAccessToken();
      const res = await fetch(uploadService.getPhotoUrl(ticket.photo_stored_filename), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        throw new Error(`Unable to retrieve attachment (${res.status}).`);
      }
      const blob = await res.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      window.open(objectUrl, '_blank', 'noopener,noreferrer');
      setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to load attachment.');
    } finally {
      setLoadingPhoto(false);
    }
  };

  // Handle Standard Status & Allotment Update
  const handleUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticket) return;

    if (newStatus === 'Resolved' && !remarks.trim()) {
      setErrorMsg('Mandatory closing remarks detailing the resolution are required to mark a ticket as Resolved.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await complaintService.updateComplaintStatus(ticket.complaint_id, {
        status: newStatus,
        remarks: remarks.trim() || undefined,
        allotted_person: allottedPerson.trim(),
        squad_assigned: squadAssigned.trim(),
      });
      setSuccessMsg(`Complaint ${updated.complaint_id} updated to "${updated.status}".`);
      setRemarks('');
      onTicketUpdated(updated);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update complaint status.');
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Ticket Reopening
  const handleReopenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticket) return;

    if (reopenRemarks.trim().length < 3) {
      setErrorMsg('Mandatory reason for reopening must be at least 3 characters in length.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await complaintService.reopenComplaint(ticket.complaint_id, reopenRemarks.trim());
      setSuccessMsg(`Complaint ${updated.complaint_id} reopened and set to "Under Review".`);
      setIsReopening(false);
      setReopenRemarks('');
      onTicketUpdated(updated);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to reopen complaint.');
    } finally {
      setSubmitting(false);
    }
  };

  const currentRank = STAGE_ORDER[ticket.status] || 0;
  const isTerminalWithdrawn = ticket.status === 'Withdrawn';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-[#F5F7F2] shadow-2xl flex flex-col border-l border-[#DCE5D8]">
          {/* 1. Sticky Drawer Header */}
          <div className="p-4 sm:p-5 bg-white border-b border-[#DCE5D8] flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm sm:text-base font-bold text-[#172D28] tracking-tight">
                {ticket.complaint_id}
              </span>
              <Badge status={ticket.status} />
              <Badge priority={ticket.priority_tier} />
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#52605B] hover:text-[#172D28] hover:bg-[#F5F7F2] transition-colors"
              title="Close Drawer (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* 2. Scrollable Body Content */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
            {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}
            {successMsg && <Notification type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

            {/* Lifecycle Stepper */}
            <div className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <span className="text-[11px] font-semibold text-[#52605B] uppercase tracking-wider block">
                Official Complaint Lifecycle
              </span>

              {isTerminalWithdrawn ? (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-900 flex items-center gap-2.5 text-xs">
                  <Ban className="w-4 h-4 text-red-700 shrink-0" />
                  <span>
                    <strong>Query Withdrawn:</strong> This request was cancelled by the student and is terminal.
                  </span>
                </div>
              ) : (
                <div className="grid grid-cols-5 gap-1 text-center pt-2">
                  {STAGES.map((stage) => {
                    const stageRank = STAGE_ORDER[stage];
                    const isCompleted = currentRank > stageRank || ticket.status === stage;
                    const isCurrent = ticket.status === stage;

                    return (
                      <div key={stage} className="flex flex-col items-center space-y-1">
                        <div
                          className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                            isCurrent
                              ? 'bg-[#203A32] text-white ring-4 ring-[#DCE5D8]'
                              : isCompleted
                              ? 'bg-[#DCE5D8] text-[#203A32]'
                              : 'bg-gray-100 text-gray-400 border border-gray-200'
                          }`}
                        >
                          {isCompleted && !isCurrent ? (
                            <Check className="w-3.5 h-3.5" />
                          ) : (
                            <span>{stageRank}</span>
                          )}
                        </div>
                        <span
                          className={`text-[10px] font-medium leading-tight ${
                            isCurrent
                              ? 'text-[#172D28] font-bold'
                              : isCompleted
                              ? 'text-[#203A32]'
                              : 'text-gray-400'
                          }`}
                        >
                          {stage}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Issue Overview & Description */}
            <div className="p-4 sm:p-5 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-bold text-sm sm:text-base text-[#172D28]">{ticket.title || ticket.category}</h3>
                  <p className="text-xs text-[#52605B] mt-0.5">
                    {ticket.category} {ticket.sub_category && `› ${ticket.sub_category}`}
                  </p>
                </div>
                <span className="text-[11px] font-mono text-[#52605B] shrink-0">
                  {formatDate(ticket.date_reported)}
                </span>
              </div>

              {ticket.specific_categories && ticket.specific_categories.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {ticket.specific_categories.map((spec) => (
                    <span
                      key={spec}
                      className="px-2 py-0.5 rounded-md bg-[#F5F7F2] border border-[#DCE5D8] text-[11px] text-[#172D28]"
                    >
                      {spec}
                    </span>
                  ))}
                </div>
              )}

              <div className="pt-2 border-t border-[#DCE5D8]/60">
                <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider block mb-1">
                  Problem Description
                </span>
                <p className="text-xs text-[#172D28] leading-relaxed whitespace-pre-line bg-[#F5F7F2]/50 p-3 rounded-lg border border-[#DCE5D8]/50">
                  {ticket.description}
                </p>
              </div>

              {/* Photo Attachment if present */}
              {ticket.photo_stored_filename && (
                <div className="pt-2 flex items-center justify-between text-xs p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-950">
                  <span className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-700" />
                    <span>Verified Photo Attachment: <strong>{ticket.photo_name || ticket.photo_stored_filename}</strong></span>
                  </span>
                  <button
                    type="button"
                    onClick={handleViewAttachment}
                    disabled={loadingPhoto}
                    className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-800 hover:underline cursor-pointer disabled:opacity-50"
                  >
                    {loadingPhoto ? 'Opening...' : 'View'} <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>

            {/* Student Information & Campus Location */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Student Identity */}
              <div className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-2">
                <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider block flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-[#203A32]" /> Student Resident
                </span>
                <div className="text-xs space-y-1">
                  <p className="font-semibold text-[#172D28]">{ticket.student_name || 'Anonymous Resident'}</p>
                  <p className="font-mono text-[#52605B]">{ticket.student_id || 'ID Unavailable'}</p>
                  {ticket.contact_number && (
                    <p className="flex items-center gap-1.5 text-[#52605B] pt-1">
                      <Phone className="w-3.5 h-3.5 text-[#A8B9A3]" /> {ticket.contact_number}
                    </p>
                  )}
                </div>
              </div>

              {/* Campus Location */}
              <div className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-2">
                <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider block flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-[#203A32]" /> Campus Location
                </span>
                <div className="text-xs space-y-1">
                  <p className="font-semibold text-[#172D28]">{ticket.building || ticket.location}</p>
                  {ticket.room_number && (
                    <p className="text-[#52605B]">Room / Unit: <strong>{ticket.room_number}</strong></p>
                  )}
                  {ticket.specified_location && (
                    <p className="text-[#52605B] italic">{ticket.specified_location}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Inspection Availability & Assignment */}
            <div className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider block flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#203A32]" /> Inspection Window & Assignment
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-[10px] text-[#52605B] block">Preferred Date & Slot</span>
                  <p className="font-medium text-[#172D28] mt-0.5">
                    {ticket.availability_date || 'Standard Service'} • {ticket.time_slot || 'General Working Hours'}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] text-[#52605B] block">Current Assigned Squad</span>
                  <p className="font-medium text-[#172D28] mt-0.5">
                    {ticket.department || 'Awaiting Allocation'}
                    {ticket.allotted_person && ` (${ticket.allotted_person})`}
                  </p>
                </div>
              </div>
            </div>

            {/* MCPI Priority Details & Breakdown */}
            <div className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-[#203A32]" /> Multi-Criteria Priority (MCPI)
                </span>
                <span className="text-xs font-mono font-bold text-[#172D28]">
                  Score: {ticket.priority_score.toFixed(1)} / 100
                </span>
              </div>

              {ticket.score_breakdown && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                  {(() => {
                    const entries = Object.entries(ticket.score_breakdown);
                    const isRatioScale = entries.every(([, v]) => Number(v) <= 1.0);
                    return entries.map(([k, val]) => (
                      <div key={k} className="p-2 rounded-lg bg-[#F5F7F2] border border-[#DCE5D8] text-center">
                        <span className="text-[9px] uppercase font-semibold text-[#52605B] block truncate" title={k}>
                          {k.replace('weight_', '').replace(' Contribution', '').replace(/_/g, ' ')}
                        </span>
                        <span className="text-xs font-bold text-[#172D28] font-mono mt-0.5 block">
                          {isRatioScale
                            ? `${(Number(val) * 100).toFixed(0)}%`
                            : `${Number(val).toFixed(1)} pts`}
                        </span>
                      </div>
                    ));
                  })()}
                </div>
              )}
            </div>

            {/* Resolution & Prior Resolution History */}
            {(ticket.status === 'Resolved' || ticket.resolved_at || ticket.closing_remarks || ticket.is_reopened) && (
              <div className="p-4 rounded-xl bg-white border border-[#DCE5D8] space-y-2.5">
                <span className="text-[10px] font-semibold text-[#52605B] uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" /> Resolution Record
                </span>
                {(ticket.closing_remarks || ticket.previous_closing_remarks) && (
                  <p className="text-xs text-[#172D28] bg-[#F5F7F2]/60 p-2.5 rounded-lg border border-[#DCE5D8]/60">
                    {ticket.closing_remarks || ticket.previous_closing_remarks}
                  </p>
                )}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#52605B]">
                  <div>
                    <span className="text-[10px] block">Resolved Timestamp</span>
                    <strong className="text-[#172D28]">
                      {ticket.resolved_at ? formatDateTime(ticket.resolved_at) : '—'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-[10px] block">Resolving Administrator</span>
                    <strong className="text-[#172D28]">{ticket.resolved_by || '—'}</strong>
                  </div>
                </div>
                {ticket.is_reopened && (
                  <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-950 space-y-1">
                    <p className="font-semibold">
                      Reopened on {ticket.reopened_at ? formatDateTime(ticket.reopened_at) : 'record'}
                    </p>
                    {ticket.original_resolved_at && (
                      <p className="text-[11px] text-amber-900">
                        Prior resolution: {formatDateTime(ticket.original_resolved_at)}
                        {ticket.original_resolved_by ? ` by ${ticket.original_resolved_by}` : ''}
                      </p>
                    )}
                    {ticket.previous_closing_remarks && (
                      <p className="text-[11px] text-amber-900 italic">
                        Prior remarks: "{ticket.previous_closing_remarks}"
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Student Feedback (if Resolved & rated) */}
            {ticket.feedback && (
              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-2">
                <span className="text-[10px] font-semibold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                  <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-400" /> Student Satisfaction Feedback
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex items-center text-amber-500">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-4 h-4 ${
                          star <= (ticket.feedback?.rating || 0)
                            ? 'fill-amber-400 text-amber-500'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-xs font-bold text-emerald-950">
                    ({ticket.feedback.rating} / 5 Stars)
                  </span>
                </div>
                {ticket.feedback.comments && (
                  <p className="text-xs text-emerald-900 italic bg-white p-2.5 rounded-lg border border-emerald-200">
                    "{ticket.feedback.comments}"
                  </p>
                )}
              </div>
            )}

            {/* Remarks History / Audit Trail */}
            <div className="p-4 sm:p-5 rounded-xl bg-white border border-[#DCE5D8] space-y-3">
              <span className="text-[11px] font-semibold text-[#52605B] uppercase tracking-wider block">
                Administrative Remarks & Audit Trail
              </span>

              {ticket.remarks_history && ticket.remarks_history.length > 0 ? (
                <div className="space-y-3 border-l-2 border-[#DCE5D8] pl-3 ml-1">
                  {ticket.remarks_history.map((entry, idx) => (
                    <div key={idx} className="space-y-0.5 text-xs relative">
                      <div className="flex items-center justify-between text-[#52605B] text-[11px]">
                        <span className="font-semibold text-[#172D28]">{entry.name || 'Staff Member'}</span>
                        <span className="font-mono text-[10px]">{entry.update_date}</span>
                      </div>
                      <p className="text-[#172D28] leading-relaxed">{entry.remarks}</p>
                      {entry.new_status && (
                        <span className="text-[10px] font-mono text-[#52605B] block">
                          Transition: {entry.previous_status || 'Initial'} → <strong>{entry.new_status}</strong>
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-[#52605B] italic">No prior administrative remarks recorded.</p>
              )}
            </div>

            {/* 3. Action Form: Update Status / Reopen */}
            <div className="p-4 sm:p-5 rounded-xl bg-white border-2 border-[#203A32]/20 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#172D28] uppercase tracking-wider flex items-center gap-1.5">
                  <Shield className="w-4 h-4 text-[#203A32]" /> Control Actions
                </span>

                {ticket.status === 'Resolved' && !isReopening && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsReopening(true)}
                    leftIcon={<RotateCcw className="w-3.5 h-3.5 text-amber-700" />}
                    className="text-amber-800 border-amber-300 hover:bg-amber-50"
                  >
                    Reopen Ticket
                  </Button>
                )}
              </div>

              {isReopening ? (
                /* Reopening Form */
                <form onSubmit={handleReopenSubmit} className="space-y-3 p-3.5 rounded-lg bg-amber-50/60 border border-amber-200">
                  <span className="text-xs font-semibold text-amber-950 block">
                    Reopening Justification (Mandatory):
                  </span>
                  <Input
                    placeholder="e.g. Student reported issue recurred, replacement failed inspection..."
                    value={reopenRemarks}
                    onChange={(e) => setReopenRemarks(e.target.value)}
                    required
                  />
                  <div className="flex justify-end gap-2 pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      type="button"
                      onClick={() => {
                        setIsReopening(false);
                        setReopenRemarks('');
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      type="submit"
                      disabled={reopenRemarks.trim().length < 3 || submitting}
                      isLoading={submitting}
                    >
                      Confirm Reopen to Review
                    </Button>
                  </div>
                </form>
              ) : (
                /* Standard Status Update & Work Order Allotment Form */
                <form onSubmit={handleUpdateSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <Select
                      label="Transition Status"
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value as any)}
                      options={[
                        { value: 'Submitted', label: 'Submitted' },
                        { value: 'Under Review', label: 'Under Review' },
                        { value: 'Assigned', label: 'Assigned' },
                        { value: 'In Progress', label: 'In Progress' },
                        { value: 'Resolved', label: 'Resolved' },
                        { value: 'Withdrawn', label: 'Withdrawn' },
                      ]}
                      required
                    />

                    <Input
                      label="Allotted Technician"
                      placeholder="e.g. Rajesh Kumar"
                      value={allottedPerson}
                      onChange={(e) => setAllottedPerson(e.target.value)}
                    />

                    <Input
                      label="Assigned Squad / Dept"
                      placeholder="e.g. Electrical Squad B"
                      value={squadAssigned}
                      onChange={(e) => setSquadAssigned(e.target.value)}
                    />
                  </div>

                  <div>
                    <Textarea
                      label={newStatus === 'Resolved' ? 'Closing Resolution Remarks (Mandatory)' : 'Administrative / Triage Remarks'}
                      placeholder={
                        newStatus === 'Resolved'
                          ? 'Detail the exact physical repair, replacement components, and testing completed...'
                          : 'Enter supervisor remarks, technician dispatch instructions, or audit notes...'
                      }
                      value={remarks}
                      onChange={(e) => setRemarks(e.target.value)}
                      rows={2}
                    />
                  </div>

                  <div className="flex justify-end gap-3 pt-1">
                    <Button
                      variant="primary"
                      type="submit"
                      disabled={submitting}
                      isLoading={submitting}
                      leftIcon={<Send className="w-3.5 h-3.5" />}
                    >
                      Update Status & Work Order
                    </Button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
