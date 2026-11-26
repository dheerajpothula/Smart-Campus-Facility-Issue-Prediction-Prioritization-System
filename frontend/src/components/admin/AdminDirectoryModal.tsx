import React, { useEffect, useState } from 'react';
import { complaintService } from '../../services/complaintService';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Notification } from '../ui/Notification';
import { X, UserPlus, Building2, CheckCircle2, ShieldAlert } from 'lucide-react';
import type { CampusBlockReference, ProvisionedStudent } from '../../types';

interface AdminDirectoryModalProps {
  initialTab: 'students' | 'blocks';
  onClose: () => void;
}

export const AdminDirectoryModal: React.FC<AdminDirectoryModalProps> = ({ initialTab, onClose }) => {
  const [tab, setTab] = useState<'students' | 'blocks'>(initialTab);
  const [students, setStudents] = useState<ProvisionedStudent[]>([]);
  const [blocks, setBlocks] = useState<CampusBlockReference[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Student form & name correction state
  const [stuId, setStuId] = useState('');
  const [stuName, setStuName] = useState('');
  const [stuBlock, setStuBlock] = useState('');
  const [editingStuId, setEditingStuId] = useState<string | null>(null);
  const [editingStuName, setEditingStuName] = useState('');

  // Block editor state
  const [editBlockId, setEditBlockId] = useState('');
  const [editFloorCsv, setEditFloorCsv] = useState('');
  const [editVerifyStatus, setEditVerifyStatus] = useState<'verified' | 'unverified_external_reference' | 'conflict_flagged'>('verified');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stuRes, blkRes] = await Promise.all([
        complaintService.getProvisionedStudents(),
        complaintService.getCampusBlocksReference(),
      ]);
      setStudents(stuRes.students || []);
      const blks = blkRes.blocks || [];
      setBlocks(blks);
      if (blks.length > 0 && !editBlockId) {
        setEditBlockId(blks[0].block_id);
        setEditFloorCsv((blks[0].floors || []).map((f: any) => f.floor_label).join(', '));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load directory metadata.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleProvisionStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!/^\d{8}$/.test(stuId.trim())) {
      setError('Student ID must be an exact 8-digit numeric string (leading zeroes preserved).');
      return;
    }
    if (stuName.trim().length < 2) {
      setError('Student name must be at least 2 characters.');
      return;
    }
    try {
      await complaintService.provisionStudent({
        student_id: stuId.trim(),
        name: stuName.trim(),
        block: stuBlock.trim() || undefined,
      });
      setSuccess(`Registered student profile ${stuId.trim()} (${stuName.trim()}).`);
      setStuId('');
      setStuName('');
      setStuBlock('');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Unable to register student profile.');
    }
  };

  const handleToggleStudent = async (student: ProvisionedStudent) => {
    setError(null);
    setSuccess(null);
    try {
      await complaintService.updateStudentEnrollment(student.student_id, {
        is_active: !student.is_active,
      });
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Unable to update student status.');
    }
  };

  const handleStartEditStudent = (student: ProvisionedStudent) => {
    setEditingStuId(student.student_id);
    setEditingStuName(student.name);
    setError(null);
    setSuccess(null);
  };

  const handleSaveStudentName = async (studentId: string) => {
    const trimmed = editingStuName.trim().replace(/\s+/g, ' ');
    if (trimmed.length < 2 || !/[a-zA-Z]/.test(trimmed)) {
      setError('Corrected student name must contain at least 2 alphabetic characters.');
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      await complaintService.updateStudentEnrollment(studentId, { name: trimmed });
      setSuccess(`Updated registered name for Student ID ${studentId} to ${trimmed}.`);
      setEditingStuId(null);
      setEditingStuName('');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Unable to correct student name.');
    }
  };

  const handleSelectEditBlock = (bid: string) => {
    setEditBlockId(bid);
    const blk = blocks.find((b) => b.block_id === bid);
    if (blk) {
      setEditFloorCsv((blk.floors || []).map((f) => f.floor_label).join(', '));
      setEditVerifyStatus(
        blk.verification_status === 'verified' || blk.verification_status === 'conflict_flagged'
          ? blk.verification_status
          : 'unverified_external_reference'
      );
    }
  };

  const handleSaveBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    const blk = blocks.find((b) => b.block_id === editBlockId);
    if (!blk) return;

    const labels = editFloorCsv
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      await complaintService.upsertCampusBlock(blk.block_id, {
        display_name: blk.display_name,
        block_category: blk.block_category,
        floor_labels: labels,
        verification_status: editVerifyStatus,
        notes: blk.notes || undefined,
      });
      setSuccess(`Updated ${blk.display_name} (${labels.length} configured floors, status: ${editVerifyStatus}).`);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Unable to save block configuration.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-[#DCE5D8] shadow-xl w-full max-w-3xl max-h-[88vh] flex flex-col overflow-hidden">
        <div className="px-5 py-4 border-b border-[#DCE5D8] bg-[#172D28] text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setTab('students')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 ${
                tab === 'students' ? 'bg-white text-[#172D28]' : 'text-[#DCE5D8] hover:bg-[#203A32]'
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" /> Student Profiles
            </button>
            <button
              type="button"
              onClick={() => setTab('blocks')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 ${
                tab === 'blocks' ? 'bg-white text-[#172D28]' : 'text-[#DCE5D8] hover:bg-[#203A32]'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" /> Block &amp; Floor Reference
            </button>
          </div>
          <button
            type="button"
            aria-label="Close Directory"
            onClick={onClose}
            className="p-1 rounded-lg text-[#DCE5D8] hover:bg-[#203A32]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4">
          {error && <Notification type="error" message={error} onClose={() => setError(null)} />}
          {success && <Notification type="success" message={success} onClose={() => setSuccess(null)} />}

          {tab === 'students' ? (
            <div className="space-y-4">
              <form onSubmit={handleProvisionStudent} className="p-4 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#172D28]">
                  Student Directory &amp; Identity Corrections
                </h3>
                <p className="text-[11px] text-[#52605B]">
                  Students self-register directly with their full name and 8-digit Student ID. Use this table to
                  correct mismatched student names, pre-add entries, or deactivate accounts if needed.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Input
                    label="8-Digit Student ID"
                    maxLength={8}
                    inputMode="numeric"
                    placeholder="8 digits (0-9)"
                    value={stuId}
                    onChange={(e) => setStuId(e.target.value)}
                    required
                  />
                  <Input
                    label="Student Full Name"
                    placeholder="Student full name"
                    value={stuName}
                    onChange={(e) => setStuName(e.target.value)}
                    required
                  />
                  <Input
                    label="Assigned Block (Optional)"
                    placeholder="e.g. Block 57"
                    value={stuBlock}
                    onChange={(e) => setStuBlock(e.target.value)}
                  />
                </div>
                <Button type="submit" size="sm" variant="primary" isLoading={loading}>
                  Add Student Profile
                </Button>
              </form>

              <div className="border border-[#DCE5D8] rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F5F7F2] text-[#172D28] uppercase text-[10px]">
                    <tr>
                      <th className="p-3">8-Digit ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Block</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#DCE5D8]">
                    {students.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="p-4 text-center text-[#52605B]">
                          No student records stored yet. Students appear here automatically upon self-registration.
                        </td>
                      </tr>
                    ) : (
                      students.map((s) => (
                        <tr key={s.student_id}>
                          <td className="p-3 font-mono font-semibold">{s.student_id}</td>
                          <td className="p-3">
                            {editingStuId === s.student_id ? (
                              <div className="flex items-center gap-1.5">
                                <input
                                  type="text"
                                  value={editingStuName}
                                  onChange={(e) => setEditingStuName(e.target.value)}
                                  className="px-2 py-1 text-xs border border-[#DCE5D8] rounded bg-white text-[#172D28]"
                                  aria-label={`Correct name for ${s.student_id}`}
                                />
                                <Button size="sm" variant="primary" onClick={() => handleSaveStudentName(s.student_id)}>
                                  Save
                                </Button>
                                <Button size="sm" variant="outline" onClick={() => setEditingStuId(null)}>
                                  Cancel
                                </Button>
                              </div>
                            ) : (
                              <span>{s.name}</span>
                            )}
                          </td>
                          <td className="p-3 text-[#52605B]">{s.block || '—'}</td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                s.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                              }`}
                            >
                              {s.is_active ? 'Active' : 'Disabled'}
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            <div className="inline-flex items-center gap-1.5">
                              {editingStuId !== s.student_id && (
                                <Button size="sm" variant="outline" onClick={() => handleStartEditStudent(s)}>
                                  Edit Name
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleToggleStudent(s)}
                              >
                                {s.is_active ? 'Deactivate' : 'Activate'}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <form onSubmit={handleSaveBlock} className="p-4 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#172D28]">
                  Verify or Configure Block &amp; Floor Hierarchy
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Select
                    label="Select Block"
                    value={editBlockId}
                    onChange={(e) => handleSelectEditBlock(e.target.value)}
                    options={blocks.map((b) => ({
                      value: b.block_id,
                      label: `${b.display_name} (${b.block_category})`,
                    }))}
                  />
                  <Select
                    label="Verification Status"
                    value={editVerifyStatus}
                    onChange={(e) => setEditVerifyStatus(e.target.value as any)}
                    options={[
                      { value: 'unverified_external_reference', label: 'Unverified External Reference' },
                      { value: 'verified', label: 'Verified Campus Record' },
                      { value: 'conflict_flagged', label: 'Conflict Flagged' },
                    ]}
                  />
                </div>
                <Input
                  label="Configured Floor Labels (comma-separated, leave blank if unknown)"
                  placeholder="Ground Floor, First Floor, Second Floor"
                  value={editFloorCsv}
                  onChange={(e) => setEditFloorCsv(e.target.value)}
                />
                <Button type="submit" size="sm" variant="primary" isLoading={loading}>
                  Save Block &amp; Floor Configuration
                </Button>
              </form>

              <div className="border border-[#DCE5D8] rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F5F7F2] text-[#172D28] uppercase text-[10px]">
                    <tr>
                      <th className="p-3">Block</th>
                      <th className="p-3">Category</th>
                      <th className="p-3">Floors</th>
                      <th className="p-3">Verification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#DCE5D8]">
                    {blocks.map((b) => (
                      <tr key={b.block_id}>
                        <td className="p-3 font-medium text-[#172D28]">{b.display_name}</td>
                        <td className="p-3 text-[#52605B]">{b.block_category}</td>
                        <td className="p-3">
                          {b.floor_count !== null ? `${b.floor_count} floors` : 'Unknown (Unverified)'}
                        </td>
                        <td className="p-3">
                          {b.verification_status === 'verified' ? (
                            <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-amber-700 font-medium">
                              <ShieldAlert className="w-3.5 h-3.5" /> Unverified Reference
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
